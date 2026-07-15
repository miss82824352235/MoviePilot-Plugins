"""DiscRemux 可视化任务队列与控制编排。

职责：
- 维护可限流并行重封装任务队列与任务状态
- 持久化任务快照供前端轮询
- 对接 DiscRemuxer 的进度/暂停/继续/终止
- 不负责真实 MakeMKV 调用细节，只编排任务生命周期
"""

from __future__ import annotations

import shutil
import threading
import time
import uuid
from copy import deepcopy
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set


def _now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _now_ts() -> float:
    return time.time()


@dataclass
class RemuxTask:
    """单个可视化重封装任务。"""

    id: str
    title: str
    source_path: str
    output_path: str
    disc_type: str = "unknown"
    mode: str = "library_scan"  # library_scan / intercept / manual
    status: str = "waiting"
    stage: str = "queued"
    progress: float = 0.0
    message: str = "等待中"
    source_size: int = 0
    selected: bool = False
    created_at: str = field(default_factory=_now_str)
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    elapsed_seconds: float = 0.0
    eta_seconds: Optional[float] = None
    speed: Optional[float] = None
    error: Optional[str] = None
    download_hash: Optional[str] = None
    downloader: Optional[str] = None
    tmdbid: Optional[int] = None
    media_type: Optional[str] = None
    library_path: Optional[str] = None
    dedupe_key: Optional[str] = None
    control_flags: Dict[str, bool] = field(default_factory=lambda: {
        "pause_requested": False,
        "resume_requested": False,
        "skip_requested": False,
        "terminate_requested": False,
    })
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["progress_percent"] = round(float(self.progress or 0.0), 1)
        data["elapsed_text"] = _format_duration(self.elapsed_seconds)
        data["eta_text"] = (
            "计算中"
            if self.eta_seconds is None and self.status in {"remuxing", "scanning", "normalizing", "transferring", "verifying"}
            else _format_duration(self.eta_seconds) if self.eta_seconds is not None else "-"
        )
        data["can_pause"] = self.status in {"waiting", "scanning", "remuxing", "normalizing", "transferring", "verifying"}
        data["can_resume"] = self.status == "paused"
        data["can_skip"] = self.status in {
            "waiting", "scanning", "remuxing", "normalizing", "transferring", "verifying", "paused"
        }
        data["can_terminate"] = self.status in {
            "waiting", "scanning", "remuxing", "normalizing", "transferring", "verifying", "paused"
        }
        return data


def _format_duration(seconds: Optional[float]) -> str:
    if seconds is None:
        return "-"
    try:
        total = max(0, int(seconds))
    except Exception:
        return "-"
    hours, rem = divmod(total, 3600)
    minutes, secs = divmod(rem, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


class TaskManager:
    """任务管理器：最多两个 worker 并行 + 可控制当前 remuxer。"""

    _MAX_TASKS = 200
    _MAX_WORKERS = 2

    def __init__(self, plugin: Any):
        self.plugin = plugin
        self._lock = threading.RLock()
        self._tasks: Dict[str, RemuxTask] = {}
        self._queue: List[str] = []
        self._current_task_id: Optional[str] = None
        self._current_task_ids: Set[str] = set()
        self._workers: List[threading.Thread] = []
        self._worker: Optional[threading.Thread] = None
        self._stop_worker = threading.Event()
        self._wake = threading.Event()
        self._current_remuxer = None
        self._current_remuxers: Dict[str, Any] = {}
        self._progress_samples: Dict[str, List[tuple]] = {}
        self._started_ts: Dict[str, float] = {}
        self._load_snapshot()

    # ------------------------------------------------------------------
    # 持久化
    # ------------------------------------------------------------------
    def _load_snapshot(self) -> None:
        data = self.plugin.get_data("task_queue") or {}
        tasks = data.get("tasks") if isinstance(data, dict) else None
        if not isinstance(tasks, list):
            return
        for item in tasks:
            if not isinstance(item, dict) or not item.get("id"):
                continue
            task = RemuxTask(
                id=str(item.get("id")),
                title=str(item.get("title") or item.get("source_path") or "未命名任务"),
                source_path=str(item.get("source_path") or ""),
                output_path=str(item.get("output_path") or ""),
                disc_type=str(item.get("disc_type") or "unknown"),
                mode=str(item.get("mode") or "manual"),
                status=str(item.get("status") or "waiting"),
                stage=str(item.get("stage") or "queued"),
                progress=float(item.get("progress") or 0.0),
                message=str(item.get("message") or ""),
                source_size=int(item.get("source_size") or 0),
                created_at=str(item.get("created_at") or _now_str()),
                started_at=item.get("started_at"),
                finished_at=item.get("finished_at"),
                elapsed_seconds=float(item.get("elapsed_seconds") or 0.0),
                eta_seconds=item.get("eta_seconds"),
                speed=item.get("speed"),
                error=item.get("error"),
                download_hash=item.get("download_hash"),
                downloader=item.get("downloader"),
                tmdbid=item.get("tmdbid"),
                media_type=item.get("media_type"),
                library_path=item.get("library_path"),
                dedupe_key=item.get("dedupe_key"),
                extra=item.get("extra") or {},
            )
            # 重载后运行中任务标记为 interrupted，可重新排队
            if task.status in {"scanning", "remuxing", "normalizing", "transferring", "verifying", "paused"}:
                task.status = "interrupted"
                task.stage = "interrupted"
                task.message = "插件重载后中断，可重新排队"
                task.finished_at = _now_str()
            self._tasks[task.id] = task
            if task.status == "waiting":
                self._queue.append(task.id)

    def _save_snapshot(self) -> None:
        tasks = [task.to_dict() for task in self._ordered_tasks()]
        # 去掉前端计算字段
        cleaned = []
        for item in tasks:
            cleaned.append({
                k: v for k, v in item.items()
                if k not in {
                    "progress_percent", "elapsed_text", "eta_text",
                    "can_pause", "can_resume", "can_skip", "can_terminate"
                }
            })
        self.plugin.save_data("task_queue", {
            "tasks": cleaned[-self._MAX_TASKS:],
            "updated_at": _now_str(),
            "current_task_id": self._current_task_id,
            "current_task_ids": list(self._current_task_ids),
        })

    def _ordered_tasks(self) -> List[RemuxTask]:
        active = []
        waiting = []
        done = []
        for task in self._tasks.values():
            if task.id == self._current_task_id or task.status in {
                "scanning", "remuxing", "normalizing", "transferring", "verifying", "paused"
            }:
                active.append(task)
            elif task.status == "waiting":
                waiting.append(task)
            else:
                done.append(task)
        waiting.sort(key=lambda t: t.created_at)
        done.sort(key=lambda t: t.finished_at or t.created_at, reverse=True)
        return active + waiting + done

    # ------------------------------------------------------------------
    # 查询
    # ------------------------------------------------------------------
    def status(self) -> Dict[str, Any]:
        with self._lock:
            tasks = [t.to_dict() for t in self._ordered_tasks()]
            counts: Dict[str, int] = {}
            for task in self._tasks.values():
                counts[task.status] = counts.get(task.status, 0) + 1
            worker_count = len([worker for worker in self._workers if worker.is_alive()])
            max_workers = self._configured_max_workers()
            return {
                "current_task_id": self._current_task_id,
                "current_task_ids": list(self._current_task_ids),
                "queue_size": len(self._queue),
                "worker_running": bool(worker_count),
                "worker_count": worker_count,
                "max_workers": max_workers,
                "counts": counts,
                "tasks": tasks[:100],
                "updated_at": _now_str(),
            }

    def list_tasks(self, limit: int = 100) -> List[Dict[str, Any]]:
        with self._lock:
            return [t.to_dict() for t in self._ordered_tasks()[: max(1, min(limit, 200))]]

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            task = self._tasks.get(task_id)
            return task.to_dict() if task else None

    # ------------------------------------------------------------------
    # 入队
    # ------------------------------------------------------------------
    def enqueue(
        self,
        *,
        title: str,
        source_path: str,
        output_path: str,
        disc_type: str = "unknown",
        mode: str = "manual",
        source_size: int = 0,
        download_hash: Optional[str] = None,
        downloader: Optional[str] = None,
        tmdbid: Optional[int] = None,
        media_type: Optional[str] = None,
        library_path: Optional[str] = None,
        dedupe_key: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
        start_worker: bool = True,
    ) -> RemuxTask:
        with self._lock:
            # 去重：同源路径且未结束的任务不重复入队
            for task in self._tasks.values():
                if task.source_path == source_path and task.status in {
                    "waiting", "scanning", "remuxing", "normalizing",
                    "transferring", "verifying", "paused"
                }:
                    return task
            task = RemuxTask(
                id=str(uuid.uuid4()),
                title=title or source_path,
                source_path=source_path,
                output_path=output_path,
                disc_type=disc_type,
                mode=mode,
                status="waiting",
                stage="queued",
                message="已入队，等待执行",
                source_size=source_size or 0,
                download_hash=download_hash,
                downloader=downloader,
                tmdbid=tmdbid,
                media_type=media_type,
                library_path=library_path,
                dedupe_key=dedupe_key,
                extra=extra or {},
            )
            self._tasks[task.id] = task
            self._queue.append(task.id)
            self._trim_tasks()
            self._save_snapshot()
        if start_worker:
            self.ensure_worker()
        return task

    def _trim_tasks(self) -> None:
        if len(self._tasks) <= self._MAX_TASKS:
            return
        ordered = self._ordered_tasks()
        keep_ids = {t.id for t in ordered[: self._MAX_TASKS]}
        # 永远保留当前与队列中
        keep_ids.update(self._queue)
        if self._current_task_id:
            keep_ids.add(self._current_task_id)
        self._tasks = {tid: task for tid, task in self._tasks.items() if tid in keep_ids}

    # ------------------------------------------------------------------
    # 控制
    # ------------------------------------------------------------------
    def control(
        self,
        *,
        action: str,
        task_ids: Optional[List[str]] = None,
        select_all: bool = False,
        confirm: bool = False,
    ) -> Dict[str, Any]:
        action = (action or "").strip().lower()
        if action not in {"pause", "resume", "skip", "terminate", "requeue", "select", "clear_finished"}:
            return {"success": False, "message": f"不支持的动作: {action}"}

        if action in {"skip", "terminate"} and not confirm:
            return {
                "success": False,
                "message": f"{action} 为危险操作，请 confirm=true 后执行",
                "data": {"need_confirm": True, "action": action},
            }

        with self._lock:
            targets = self._resolve_targets(task_ids=task_ids, select_all=select_all)
            if not targets and action != "clear_finished":
                return {"success": False, "message": "未选中任何任务"}

            results = []
            if action == "clear_finished":
                remove_ids = [
                    tid for tid, task in self._tasks.items()
                    if task.status in {"success", "failed", "skipped", "terminated", "interrupted"}
                ]
                for tid in remove_ids:
                    self._tasks.pop(tid, None)
                self._save_snapshot()
                return {"success": True, "message": f"已清理 {len(remove_ids)} 条结束任务", "data": {"removed": len(remove_ids)}}

            for task in targets:
                results.append(self._control_one(task, action))
            self._save_snapshot()

        self.ensure_worker()
        self._wake.set()
        ok = sum(1 for item in results if item.get("ok"))
        return {
            "success": ok > 0,
            "message": f"动作 {action} 完成：成功 {ok}/{len(results)}",
            "data": {"results": results},
        }

    def _resolve_targets(self, task_ids: Optional[List[str]], select_all: bool) -> List[RemuxTask]:
        if select_all:
            return list(self._tasks.values())
        if task_ids:
            return [self._tasks[tid] for tid in task_ids if tid in self._tasks]
        return [task for task in self._tasks.values() if task.selected]

    def _control_one(self, task: RemuxTask, action: str) -> Dict[str, Any]:
        tid = task.id
        if action == "select":
            task.selected = not task.selected
            return {"task_id": tid, "ok": True, "message": "已切换选中状态"}

        if action == "requeue":
            if task.status not in {"failed", "skipped", "terminated", "interrupted", "success"}:
                return {"task_id": tid, "ok": False, "message": "当前状态不可重新排队"}
            task.status = "waiting"
            task.stage = "queued"
            task.progress = 0.0
            task.message = "已重新入队"
            task.error = None
            task.finished_at = None
            task.eta_seconds = None
            for key in task.control_flags:
                task.control_flags[key] = False
            if tid not in self._queue:
                self._queue.append(tid)
            return {"task_id": tid, "ok": True, "message": "已重新入队"}

        if action == "pause":
            if task.status == "waiting":
                task.status = "paused"
                task.stage = "paused"
                task.message = "队列中已暂停"
                if tid in self._queue:
                    self._queue = [x for x in self._queue if x != tid]
                return {"task_id": tid, "ok": True, "message": "等待任务已暂停"}
            if task.id == self._current_task_id and self._current_remuxer is not None:
                task.control_flags["pause_requested"] = True
                try:
                    self._current_remuxer.pause()
                    task.status = "paused"
                    task.stage = "paused"
                    task.message = "已暂停 MakeMKV 进程"
                    return {"task_id": tid, "ok": True, "message": "当前任务已暂停"}
                except Exception as err:
                    return {"task_id": tid, "ok": False, "message": f"暂停失败: {err}"}
            task.control_flags["pause_requested"] = True
            task.status = "paused"
            task.stage = "paused"
            task.message = "已请求暂停"
            return {"task_id": tid, "ok": True, "message": "已请求暂停"}

        if action == "resume":
            if task.status != "paused":
                return {"task_id": tid, "ok": False, "message": "任务不在暂停状态"}
            task.control_flags["pause_requested"] = False
            task.control_flags["resume_requested"] = True
            if task.id == self._current_task_id and self._current_remuxer is not None:
                try:
                    self._current_remuxer.resume()
                except Exception as err:
                    return {"task_id": tid, "ok": False, "message": f"继续失败: {err}"}
                task.status = "remuxing"
                task.stage = "remuxing"
                task.message = "已继续重封装"
            else:
                task.status = "waiting"
                task.stage = "queued"
                task.message = "已恢复到队列"
                if tid not in self._queue:
                    self._queue.insert(0, tid)
            return {"task_id": tid, "ok": True, "message": "已继续"}

        if action == "skip":
            task.control_flags["skip_requested"] = True
            remuxer = self._current_remuxers.get(task.id) or (self._current_remuxer if task.id == self._current_task_id else None)
            if task.id in self._current_task_ids and remuxer is not None:
                try:
                    remuxer.terminate()
                except Exception:
                    pass
            elif tid in self._queue:
                self._queue = [x for x in self._queue if x != tid]
                task.status = "skipped"
                task.stage = "skipped"
                task.message = "已从队列跳过"
                task.finished_at = _now_str()
                return {"task_id": tid, "ok": True, "message": "已跳过等待任务"}
            task.status = "skipped"
            task.stage = "skipped"
            task.message = "已请求跳过，等待当前阶段安全结束"
            task.finished_at = _now_str()
            return {"task_id": tid, "ok": True, "message": "已请求跳过"}

        if action == "terminate":
            task.control_flags["terminate_requested"] = True
            remuxer = self._current_remuxers.get(task.id) or (self._current_remuxer if task.id == self._current_task_id else None)
            if task.id in self._current_task_ids and remuxer is not None:
                try:
                    remuxer.terminate()
                except Exception:
                    pass
            elif tid in self._queue:
                self._queue = [x for x in self._queue if x != tid]
            task.status = "terminated"
            task.stage = "terminated"
            task.message = "已终止（未删除源原盘）"
            task.finished_at = _now_str()
            return {"task_id": tid, "ok": True, "message": "已终止任务"}

        return {"task_id": tid, "ok": False, "message": f"未知动作 {action}"}

    # ------------------------------------------------------------------
    # worker
    # ------------------------------------------------------------------
    def _configured_max_workers(self) -> int:
        """读取配置中的最大并行 worker 数。"""
        try:
            config = self.plugin.get_config() or {}
            return max(1, min(4, int(config.get("max_workers") or self._MAX_WORKERS)))
        except Exception:
            return self._MAX_WORKERS

    def ensure_worker(self) -> None:
        """确保并行 worker 数量达到上限。"""
        with self._lock:
            max_workers = self._configured_max_workers()
            self._workers = [worker for worker in self._workers if worker.is_alive()]
            self._worker = self._workers[0] if self._workers else None
            self._stop_worker.clear()
            while len(self._workers) < max_workers:
                worker = threading.Thread(
                    target=self._worker_loop,
                    name=f"DiscRemuxTaskWorker-{len(self._workers) + 1}",
                    daemon=True,
                )
                self._workers.append(worker)
                if self._worker is None:
                    self._worker = worker
                worker.start()
            self._wake.set()

    def stop(self) -> None:
        self._stop_worker.set()
        self._wake.set()
        with self._lock:
            remuxers = list(self._current_remuxers.values()) or ([self._current_remuxer] if self._current_remuxer else [])
            workers = list(self._workers)
        for remuxer in remuxers:
            if remuxer is not None:
                try:
                    remuxer.terminate()
                except Exception:
                    pass
        for worker in workers:
            if worker and worker.is_alive():
                worker.join(timeout=3)

    def _worker_loop(self) -> None:
        while not self._stop_worker.is_set():
            task = self._pop_next_task()
            if not task:
                self._wake.wait(timeout=1.0)
                self._wake.clear()
                continue
            try:
                self._run_task(task)
            except Exception as err:
                self._finish_task(task, status="failed", message=f"任务异常: {err}", error=str(err))

    def _pop_next_task(self) -> Optional[RemuxTask]:
        with self._lock:
            while self._queue:
                tid = self._queue.pop(0)
                task = self._tasks.get(tid)
                if not task:
                    continue
                if task.status == "paused":
                    continue
                if task.status not in {"waiting", "interrupted"}:
                    continue
                self._current_task_ids.add(tid)
                self._current_task_id = next(iter(self._current_task_ids), tid)
                task.status = "scanning"
                task.stage = "scanning"
                task.message = "准备扫描原盘"
                task.started_at = _now_str()
                task.progress = 1.0
                self._started_ts[tid] = _now_ts()
                self._progress_samples[tid] = []
                self._save_snapshot()
                return task
            if not self._current_task_ids:
                self._current_task_id = None
            return None

    def _update_task(self, task: RemuxTask, **kwargs) -> None:
        with self._lock:
            for key, value in kwargs.items():
                if hasattr(task, key):
                    setattr(task, key, value)
            started = self._started_ts.get(task.id)
            if started:
                task.elapsed_seconds = max(0.0, _now_ts() - started)
            self._save_snapshot()

    def _finish_task(
        self,
        task: RemuxTask,
        *,
        status: str,
        message: str,
        error: Optional[str] = None,
        progress: Optional[float] = None,
    ) -> None:
        with self._lock:
            task.status = status
            task.stage = status
            task.message = message
            task.error = error
            task.finished_at = _now_str()
            if progress is not None:
                task.progress = progress
            elif status == "success":
                task.progress = 100.0
            started = self._started_ts.pop(task.id, None)
            if started:
                task.elapsed_seconds = max(0.0, _now_ts() - started)
            self._current_task_ids.discard(task.id)
            if self._current_task_id == task.id:
                self._current_task_id = next(iter(self._current_task_ids), None)
            self._current_remuxers.pop(task.id, None)
            self._progress_samples.pop(task.id, None)
            self._current_remuxer = next(iter(self._current_remuxers.values()), None) if self._current_remuxers else None
            self._save_snapshot()

    def _on_progress(self, task: RemuxTask, payload: Dict[str, Any]) -> None:
        percent = float(payload.get("percent") or 0.0)
        stage = str(payload.get("stage") or "remuxing")
        message = str(payload.get("message") or "重封装中")
        now = _now_ts()
        with self._lock:
            if task.control_flags.get("skip_requested"):
                raise RuntimeError("任务已请求跳过")
            if task.control_flags.get("terminate_requested"):
                raise RuntimeError("任务已请求终止")
            task.progress = max(task.progress, min(99.0, percent))
            task.stage = stage
            task.status = "paused" if task.control_flags.get("pause_requested") else stage
            task.message = message
            started = self._started_ts.get(task.id)
            if started:
                task.elapsed_seconds = max(0.0, now - started)
            samples = self._progress_samples.setdefault(task.id, [])
            samples.append((now, percent))
            self._progress_samples[task.id] = samples[-20:]
            samples = self._progress_samples[task.id]
            if len(samples) >= 2:
                t0, p0 = samples[0]
                t1, p1 = samples[-1]
                dt = max(0.001, t1 - t0)
                dp = max(0.0, p1 - p0)
                speed = dp / dt
                task.speed = speed
                remain = max(0.0, 100.0 - percent)
                task.eta_seconds = (remain / speed) if speed > 0.01 else None
            self._save_snapshot()


    def _has_enough_free_space(self, source_root, config: dict) -> bool:
        """检查源文件所在磁盘是否有足够剩余空间。"""
        try:
            threshold_gb = float(config.get("min_free_space_gb") or 120)
        except Exception:
            threshold_gb = 120.0
        try:
            usage = shutil.disk_usage(str(source_root if source_root.is_dir() else source_root.parent))
            free_gb = usage.free / 1024 / 1024 / 1024
        except Exception:
            return True
        if free_gb < threshold_gb:
            self.plugin.info(f"蓝光原盘重封装跳过：剩余空间 {free_gb:.1f}GB 低于阈值 {threshold_gb:.1f}GB")
            return False
        return True

    def _run_task(self, task: RemuxTask) -> None:
        """执行单个任务：扫描→重封装→规范轨道→整理→验证。"""
        plugin = self.plugin
        config = plugin.get_config() or {}

        # 跳过/终止检查
        if task.control_flags.get("skip_requested"):
            self._finish_task(task, status="skipped", message="已跳过", progress=task.progress)
            return
        if task.control_flags.get("terminate_requested"):
            self._finish_task(task, status="terminated", message="已终止", progress=task.progress)
            return

        source_path = task.source_path
        output_path = task.output_path
        media_kind = str((task.extra or {}).get("source_media_kind") or "unknown")
        self._update_task(task, status="scanning", stage="scanning", message="校验源文件原盘", progress=5.0)

        if not plugin._is_valid_disc_source(__import__("pathlib").Path(source_path)):
            self._finish_task(task, status="failed", message="源文件原盘无效或不存在", error="invalid source")
            return

        min_size_gb = float(config.get("min_mkv_size_gb") or 5)
        output_file = __import__("pathlib").Path(output_path)
        source_root = __import__("pathlib").Path(source_path)
        if not self._has_enough_free_space(source_root, config):
            self._finish_task(
                task,
                status="failed",
                message="磁盘剩余空间不足，已跳过本轮重封装",
                error="insufficient free space",
                progress=task.progress,
            )
            return
        if media_kind != "tv" and plugin._target_mkv_exists(output_file, min_size_gb):
            self._update_task(task, status="transferring", stage="transferring", message="MKV 已存在，进入整理", progress=80.0)
            ok = self._post_process(task, source_root, output_file, config)
            if ok:
                self._finish_task(task, status="success", message="已存在 MKV 整理完成", progress=100.0)
            return

        # 重封装
        from .disc_remuxer import DiscRemuxer

        remuxer = DiscRemuxer(
            progress_callback=lambda payload: self._on_progress(task, payload),
            control_checker=lambda: self._control_checker(task),
        )
        with self._lock:
            self._current_remuxer = remuxer
            self._current_remuxers[task.id] = remuxer
        plugin._register_remuxer(remuxer)
        try:
            self._update_task(task, status="remuxing", stage="remuxing", message="开始 MakeMKV 重封装", progress=8.0)
            remuxer.validate_environment()
            if media_kind == "tv":
                episode_plan = remuxer.select_tv_episode_titles(source_root.as_posix())
                if not episode_plan:
                    raise RuntimeError("电视剧目录未找到可映射的单集 Title，按硬边界跳过，禁止回退最长主片")
                start_episode = plugin._tv_episode_start_for_disc(source_root, len(episode_plan))
                outputs = []
                for index, item in enumerate(episode_plan):
                    episode_number = start_episode + index
                    episode_output = plugin._tv_episode_output_for_disc(source_root, episode_number)
                    if plugin._target_mkv_exists(episode_output, min_size_gb):
                        outputs.append(episode_output)
                        continue
                    self._update_task(
                        task,
                        status="remuxing",
                        stage="remuxing",
                        message=f"提取第 {episode_number} 集 Title={item['title_id']}",
                        progress=8.0 + min(70.0, index * 70.0 / max(1, len(episode_plan))),
                    )
                    remuxer.remux_title_to_mkv(
                        source_root_path=source_root.as_posix(),
                        output_file_path=episode_output.as_posix(),
                        title_id=int(item["title_id"]),
                    )
                    outputs.append(episode_output)
                task.extra["episode_outputs"] = [item.as_posix() for item in outputs]
            else:
                remuxer.remux_to_mkv(
                    source_root_path=source_root.as_posix(),
                    output_file_path=output_file.as_posix(),
                )
                outputs = [output_file]
            if task.control_flags.get("skip_requested"):
                self._finish_task(task, status="skipped", message="重封装后跳过后续阶段", progress=task.progress)
                return
            if task.control_flags.get("terminate_requested"):
                self._finish_task(task, status="terminated", message="重封装后终止", progress=task.progress)
                return

            if bool(config.get("normalize_tracks", True)):
                self._update_task(task, status="normalizing", stage="normalizing", message="规范化音轨/字幕", progress=82.0)
                for item in outputs:
                    plugin._normalize_mkv_tracks(
                        item,
                        reset_video_language=bool(config.get("reset_video_language", True)),
                    )

            self._update_task(task, status="transferring", stage="transferring", message="通过 MP 硬链接整理入库", progress=90.0)
            ok = True
            if media_kind == "tv":
                # 电视剧多集盘必须先全部硬链接入库成功，再统一清理一次源原盘。
                # 避免第一集后处理删除 ISO，导致后续集记录反复出现 source_missing。
                tv_config = deepcopy(config)
                tv_config["source_disc_action"] = "keep"
                episode_post_actions = []
                for item in outputs:
                    ok = self._post_process(task, source_root, item, tv_config) and ok
                    episode_post_actions.append({
                        "output_file": item.as_posix(),
                        "post_action": deepcopy(task.extra.get("post_action") or {}),
                    })
                if ok:
                    task.extra["tv_source_cleanup"] = plugin._cleanup_source_disc_after_success(source_root, config)
                task.extra["episode_post_actions"] = episode_post_actions
            else:
                ok = self._post_process(task, source_root, output_file, config)
            if ok:
                self._update_task(task, status="verifying", stage="verifying", message="验证输出与入库结果", progress=98.0)
                self._finish_task(task, status="success", message="重封装并整理完成", progress=100.0)
        except Exception as err:
            msg = str(err)
            if "跳过" in msg or task.control_flags.get("skip_requested"):
                self._finish_task(task, status="skipped", message="已跳过", error=msg, progress=task.progress)
            elif "终止" in msg or task.control_flags.get("terminate_requested"):
                self._finish_task(task, status="terminated", message="已终止", error=msg, progress=task.progress)
            else:
                self._finish_task(task, status="failed", message=f"失败: {msg}", error=msg, progress=task.progress)
        finally:
            plugin._unregister_remuxer(remuxer)
            with self._lock:
                self._current_remuxers.pop(task.id, None)
                if self._current_remuxer is remuxer:
                    self._current_remuxer = next(iter(self._current_remuxers.values()), None) if self._current_remuxers else None

    def _control_checker(self, task: RemuxTask) -> Optional[str]:
        if task.control_flags.get("terminate_requested"):
            return "terminate"
        if task.control_flags.get("skip_requested"):
            return "skip"
        if task.control_flags.get("pause_requested"):
            return "pause"
        return None

    def _post_process(self, task: RemuxTask, source_root, output_file, config: dict) -> bool:
        """按任务模式走整理与清理。失败时返回 False。"""
        plugin = self.plugin
        mode = task.mode
        from pathlib import Path
        try:
            if mode == "intercept":
                download_history = None
                if task.download_hash:
                    from app.db.downloadhistory_oper import DownloadHistoryOper
                    download_history = DownloadHistoryOper().get_by_hash(task.download_hash)
                if download_history is None:
                    download_history = plugin._resolve_intercept_download_history(source_root)
                triggered_transfer, new_transfer_history_id = plugin._post_process_intercept_output(
                    output_file=output_file,
                    download_history=download_history,
                    config=config,
                )
                source_cleanup = plugin._cleanup_intercept_source(
                    source_root, config, download_history=download_history
                )
                task.extra["post_action"] = {
                    "triggered_transfer": triggered_transfer,
                    "new_transfer_history_id": new_transfer_history_id,
                    "source_cleanup": source_cleanup,
                }
                plugin._update_history_record(
                    task.dedupe_key or f"intercept:{source_root.as_posix()}",
                    status="success",
                    post_action=task.extra["post_action"],
                    finished_at=plugin._now_str(),
                )
                return True

            # library_scan / manual
            history = None
            history_id = (task.extra or {}).get("transfer_history_id")
            if history_id:
                from app.db.transferhistory_oper import TransferHistoryOper
                try:
                    history = TransferHistoryOper().get(history_id)
                except Exception:
                    history = None
            if history is None and task.library_path:
                history = plugin._find_related_transfer_history(Path(task.library_path), source_root)
            state, errmsg = plugin._transfer_source_mkv(output_file, history=history, source_root=source_root)
            if not state:
                raise RuntimeError(f"源文件 MKV 整理失败: {errmsg}")
            from app.db.transferhistory_oper import TransferHistoryOper
            new_history = TransferHistoryOper().get_by_src(output_file.as_posix(), storage="local")
            library_action = plugin._apply_library_disc_action(
                Path(task.library_path) if task.library_path else None,
                plugin._library_disc_action(config),
            )
            source_cleanup = plugin._cleanup_source_disc_after_success(
                source_root=source_root,
                source_disc_action=plugin._source_disc_action(config),
                download_history=history,
            )
            if new_history and bool(config.get("refresh_media_server", True)):
                plugin._refresh_media_server(new_history, output_file)
            plugin._save_library_scan_record(
                source_movie_dir=source_root,
                library_movie_dir=Path(task.library_path) if task.library_path else None,
                output_file=output_file,
                history=history,
                status="success",
                library_bdmv_action=library_action,
                new_transfer_history_id=new_history.id if new_history else None,
            )
            task.extra["post_action"] = {
                "source_cleanup": source_cleanup,
                "library_bdmv_action": library_action,
                "new_transfer_history_id": new_history.id if new_history else None,
            }
            return True
        except Exception as err:
            self._finish_task(task, status="failed", message=f"后处理失败: {err}", error=str(err))
            return False
