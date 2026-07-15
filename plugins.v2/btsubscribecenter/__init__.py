
import datetime
import re
import traceback
from typing import Any, Dict, List, Optional, Tuple

import pytz
from fastapi import Body
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app import schemas
from app.chain.download import DownloadChain
from app.chain.tmdb import TmdbChain
from app.db.downloadhistory_oper import DownloadHistoryOper
from app.db.transferhistory_oper import TransferHistoryOper
from app.db.systemconfig_oper import SystemConfigOper
from app.core.config import settings
from app.core.context import Context, MediaInfo, TorrentInfo
from app.core.metainfo import MetaInfo
from app.helper.downloader import DownloaderHelper
from app.helper.rss import RssHelper
from app.log import logger
from app.plugins import _PluginBase
from app.schemas.types import MediaType, SystemConfigKey

from .models import completed_count, episodes_from_meta, lack_count, new_subscription, now_str, parse_group, progress_percent, sub_id, to_int, total_count
from .store import BTSubscribeStore
from .ui import col, form_schema, page_schema


class BTSubscribeCenter(_PluginBase):
    """BT/RSS 私有订阅中心。"""

    plugin_name = "BT订阅中心"
    plugin_desc = "面向 BT/RSS 动漫源的番剧订阅中心，集中管理订阅、候选、识别异常、下载事实与整季替换。"
    plugin_icon = "rss.png"
    plugin_version = "0.14.0"
    plugin_author = "local"
    plugin_label = "订阅,BT,RSS"
    plugin_config_prefix = "btsubscribecenter_"
    plugin_order = 21
    auth_level = 2

    _enabled: bool = False
    _cron: str = "*/30 * * * *"
    _onlyonce: bool = False
    _proxy: bool = False
    _rss_urls: str = ""
    _include: str = ""
    _exclude: str = ""
    _size_range: str = ""
    _save_path: str = ""
    _auto_discover_airing: bool = True
    _airing_window_days: int = 45
    _early_episode_max: int = 3
    _auto_download: bool = False
    _recognition_issue_limit: int = 200
    _candidate_limit: int = 200
    _history_limit: int = 300
    _cleanup_after_library: bool = True
    _replacement_watch_enabled: bool = True
    _replacement_check_minutes: int = 30
    _failure_cooldown_hours: int = 24

    def _sync_runtime_facts_on_startup(self) -> None:
        """启动时轻量迁移旧状态并同步已知下载/入库事实。"""
        self.sync_runtime_facts(reason="startup")

    def sync_runtime_facts(self, reason: str = "timer") -> Dict[str, Any]:
        """后台同步下载器、下载历史、转移历史和候选诊断事实。"""
        stats = {"reason": reason, "changed": False, "subscriptions": 0, "candidates": 0, "submitted_no_hash": 0, "hash_tracked": 0, "cleanup_removed": 0, "cleanup_failed": 0}
        try:
            candidates = self._load_candidates()
            subs = BTSubscribeStore(self).load_subscriptions()
            changed = self._migrate_pending_candidates(candidates, subs)
            for item in candidates or []:
                before = dict(item)
                self._annotate_candidate_fact(item)
                changed = changed or before != item
                stats["candidates"] += 1
            for sub in subs.values():
                before = dict(sub)
                self._refresh_subscription_runtime_facts(sub, candidates)
                self._normalize_subscription(sub, candidates)
                changed = changed or before != sub
                stats["subscriptions"] += 1
                for fact in (sub.get("episode_facts") or {}).values():
                    if fact.get("final_state") == "submitted_no_hash":
                        stats["submitted_no_hash"] += 1
                    if fact.get("download_hash"):
                        stats["hash_tracked"] += 1
            cleanup_stats = self._cleanup_completed_torrents(subs, candidates)
            stats.update({k: stats.get(k, 0) + int(v or 0) for k, v in cleanup_stats.items() if k in ("cleanup_removed", "cleanup_failed")})
            changed = changed or bool(cleanup_stats.get("changed"))
            if changed:
                BTSubscribeStore(self).save_subscriptions(subs)
                self._save_candidates(candidates[:max(self._candidate_limit, 20)])
            stats["changed"] = bool(changed)
            logger.info(f"BT订阅中心下载事实同步完成：{stats}")
        except Exception as err:
            logger.warning(f"BT订阅中心下载事实同步失败：{err}")
            stats["error"] = str(err)
        return stats

    def init_plugin(self, config: dict = None) -> None:
        """根据配置初始化插件，并补齐/规范化旧版本缺失字段。"""
        self.stop_service()
        merged_config = self._normalize_config(config or {})
        self._enabled = bool(merged_config.get("enabled"))
        self._cron = str(merged_config.get("cron") or "*/30 * * * *").strip()
        self._onlyonce = bool(merged_config.get("onlyonce"))
        self._proxy = bool(merged_config.get("proxy"))
        self._rss_urls = str(merged_config.get("rss_urls") or "").strip()
        self._include = str(merged_config.get("include") or "").strip()
        self._exclude = str(merged_config.get("exclude") or "").strip()
        self._size_range = str(merged_config.get("size_range") or "").strip()
        self._save_path = str(merged_config.get("save_path") or "").strip()
        self._auto_discover_airing = bool(merged_config.get("auto_discover_airing", True))
        self._airing_window_days = to_int(merged_config.get("airing_window_days"), 45)
        self._early_episode_max = to_int(merged_config.get("early_episode_max"), 3)
        self._auto_download = bool(merged_config.get("auto_download"))
        self._recognition_issue_limit = to_int(merged_config.get("recognition_issue_limit"), 200)
        self._candidate_limit = to_int(merged_config.get("candidate_limit"), 200)
        self._history_limit = to_int(merged_config.get("history_limit"), 300)
        self._cleanup_after_library = bool(merged_config.get("cleanup_after_library", True))
        self._replacement_watch_enabled = bool(merged_config.get("replacement_watch_enabled", True))
        self._replacement_check_minutes = max(10, to_int(merged_config.get("replacement_check_minutes"), 30))
        self._failure_cooldown_hours = to_int(merged_config.get("failure_cooldown_hours", merged_config.get("failure_notify_cooldown_hours", merged_config.get("cleanup_notify_cooldown_hours", 24))), 24)
        if config is not None and merged_config != config:
            self.update_config(self._current_config())
        self._sync_runtime_facts_on_startup()
        if self._onlyonce:
            self._onlyonce = False
            self.update_config(self._current_config())
            self.scan_sources(manual=True)

    def get_state(self) -> bool:
        """获取插件启用状态。"""
        return self._enabled

    @staticmethod
    def get_command() -> List[Dict[str, Any]]:
        """返回插件命令。"""
        return []

    @staticmethod
    def get_render_mode() -> Tuple[str, str]:
        """声明插件使用 Vue 联邦组件渲染。"""
        return "vue", "dist/assets"

    def get_sidebar_nav(self) -> List[Dict[str, Any]]:
        """声明 BT 订阅中心侧栏入口。"""
        if not self.get_state():
            return []
        return [{"nav_key": "main", "title": "BT订阅中心", "icon": "mdi-rss", "section": "subscribe", "permission": "manage", "order": 50}]

    def get_service(self) -> List[Dict[str, Any]]:
        """返回定时服务配置。"""
        if not self._enabled:
            return []
        try:
            trigger = CronTrigger.from_crontab(self._cron, timezone=pytz.timezone(settings.TZ)) if self._cron else "interval"
            kwargs = {} if self._cron else {"minutes": 30}
        except Exception:
            trigger = "interval"
            kwargs = {"minutes": 30}
        services = [{"id": "BTSubscribeCenter", "name": "BT订阅中心刷新", "trigger": trigger, "func": self.scan_sources, "kwargs": kwargs}]
        services.append({
            "id": "BTSubscribeCenterFactSync",
            "name": "BT订阅中心下载事实同步",
            "trigger": IntervalTrigger(minutes=15),
            "func": self.sync_runtime_facts,
            "kwargs": {},
        })
        if self._replacement_watch_enabled:
            services.append({
                "id": "BTSubscribeCenterReplacementWatch",
                "name": "BT订阅中心整季包替换监控",
                "trigger": IntervalTrigger(minutes=self._replacement_check_minutes),
                "func": self.replacement_watch,
                "kwargs": {},
            })
        return services

    def get_api(self) -> List[Dict[str, Any]]:
        """返回插件 API。"""
        bear = "bear"
        return [
            {"path": "/status", "endpoint": self.api_status, "methods": ["GET"], "summary": "BT订阅中心状态", "auth": bear},
            {"path": "/overview", "endpoint": self.api_overview, "methods": ["GET"], "summary": "BT订阅中心总览数据", "auth": bear},
            {"path": "/refresh", "endpoint": self.api_refresh, "methods": ["POST"], "summary": "刷新 RSS 源", "auth": bear},
            {"path": "/subscriptions", "endpoint": self.api_subscriptions, "methods": ["GET"], "summary": "查询私有订阅", "auth": bear},
            {"path": "/subscription", "endpoint": self.api_subscription, "methods": ["GET"], "summary": "查询单个私有订阅", "auth": bear},
            {"path": "/candidates", "endpoint": self.api_candidates, "methods": ["GET"], "summary": "查询候选资源", "auth": bear},
            {"path": "/submitted_no_hash", "endpoint": self.api_submitted_no_hash, "methods": ["GET"], "summary": "查询历史缺 Hash 诊断", "auth": bear},
            {"path": "/recognition_issues", "endpoint": self.api_recognition_issues, "methods": ["GET"], "summary": "查询识别异常队列", "auth": bear},
            {"path": "/native_mappings", "endpoint": self.api_native_mappings, "methods": ["GET"], "summary": "兼容旧版原生订阅映射", "auth": bear},
            {"path": "/ignore_issue", "endpoint": self.api_ignore_issue, "methods": ["POST"], "summary": "忽略识别异常", "auth": bear},
            {"path": "/rescan_issue", "endpoint": self.api_rescan_issue, "methods": ["POST"], "summary": "重扫识别异常", "auth": bear},
            {"path": "/issue_identifier_preview", "endpoint": self.api_issue_identifier_preview, "methods": ["POST"], "summary": "预览识别异常的窄作用域识别词", "auth": bear},
            {"path": "/apply_issue_identifier", "endpoint": self.api_apply_issue_identifier, "methods": ["POST"], "summary": "确认写入识别异常识别词并回流候选", "auth": bear},
            {"path": "/issue_agent_hint", "endpoint": self.api_issue_agent_hint, "methods": ["POST"], "summary": "生成识别异常智能体处理提示", "auth": bear},
            {"path": "/issue_agent_apply", "endpoint": self.api_issue_agent_apply, "methods": ["POST"], "summary": "智能体高置信自动写入识别词并回流候选", "auth": bear},
            {"path": "/reflow_issue", "endpoint": self.api_reflow_issue, "methods": ["POST"], "summary": "将识别异常回流候选", "auth": bear},
            {"path": "/add_subscription", "endpoint": self.api_add_subscription, "methods": ["POST"], "summary": "添加私有订阅", "auth": bear},
            {"path": "/pause_subscription", "endpoint": self.api_pause_subscription, "methods": ["POST"], "summary": "暂停私有订阅", "auth": bear},
            {"path": "/resume_subscription", "endpoint": self.api_resume_subscription, "methods": ["POST"], "summary": "恢复私有订阅", "auth": bear},
            {"path": "/set_group", "endpoint": self.api_set_group, "methods": ["POST"], "summary": "设置发布组标记", "auth": bear},
            {"path": "/ignore_candidate", "endpoint": self.api_ignore_candidate, "methods": ["POST"], "summary": "忽略候选资源", "auth": bear},
            {"path": "/download_candidate", "endpoint": self.api_download_candidate, "methods": ["POST"], "summary": "下载候选资源", "auth": bear},
            {"path": "/delete_subscription", "endpoint": self.api_delete_subscription, "methods": ["POST"], "summary": "删除私有订阅", "auth": bear},
            {"path": "/create_subscription_from_candidate", "endpoint": self.api_create_subscription_from_candidate, "methods": ["POST"], "summary": "从候选创建私有订阅", "auth": bear},
            {"path": "/bind_candidate", "endpoint": self.api_bind_candidate, "methods": ["POST"], "summary": "绑定候选到私有订阅", "auth": bear},
            {"path": "/rss_search", "endpoint": self.api_rss_search, "methods": ["POST"], "summary": "搜索已配置 RSS/BT 源", "auth": bear},
            {"path": "/save_config", "endpoint": self.api_save_config, "methods": ["POST"], "summary": "保存 BT 订阅中心配置", "auth": bear},
            {"path": "/refresh_subscription_status", "endpoint": self.api_refresh_subscription_status, "methods": ["POST"], "summary": "刷新单个订阅入库状态", "auth": bear},
            {"path": "/update_subscription", "endpoint": self.api_update_subscription, "methods": ["POST"], "summary": "编辑私有订阅", "auth": bear},
            {"path": "/refresh_subscription_meta", "endpoint": self.api_refresh_subscription_meta, "methods": ["POST"], "summary": "刷新私有订阅媒体信息", "auth": bear},
            {"path": "/search_subscription_candidates", "endpoint": self.api_search_subscription_candidates, "methods": ["POST"], "summary": "搜索订阅候选", "auth": bear},
            {"path": "/clear_pending", "endpoint": self.api_clear_pending, "methods": ["POST"], "summary": "清空订阅等待队列", "auth": bear},
            {"path": "/reset_downloaded", "endpoint": self.api_reset_downloaded, "methods": ["POST"], "summary": "重置订阅下载记录", "auth": bear},
        ]

    def get_form(self) -> Tuple[List[dict], Dict[str, Any]]:
        """Vue 模式下返回默认配置。"""
        return [], self._default_config()

    def get_page(self) -> List[dict]:
        """Vue 模式下详情页由远程组件渲染。"""
        return []

    def stop_service(self) -> None:
        """停止插件服务。"""
        return None



    def _normalize_subscription(self, sub: dict, candidates: Optional[List[dict]] = None) -> dict:
        """轻量补齐接近 MP 原生订阅卡片所需字段。

        注意：该方法会在页面打开时被 /status 与 /subscriptions 调用，必须保持纯内存计算，
        不能触发 TMDB、媒体库扫描或媒体识别，否则大量订阅会导致接口 500/超时。
        """
        if not isinstance(sub, dict):
            return {}
        title = str(sub.get("title") or sub.get("name") or "").strip()
        sub["title"] = title
        sub.setdefault("description", sub.get("overview") or "")
        sub.setdefault("username", "BT订阅中心")
        sub.setdefault("source", "BT/RSS")
        try:
            total = int(sub.get("total_episode") or sub.get("episodes_total") or 0)
        except Exception:
            total = 0
        local_count = completed_count(sub)
        candidate_episodes = self._candidate_episode_numbers(sub, candidates or [])
        library_episodes = self._library_episode_numbers(sub)
        completed = max(len(library_episodes), local_count)
        sub["library_episodes"] = library_episodes
        sub["candidate_episodes"] = sorted(candidate_episodes)
        sub["library_completed_episode"] = len(library_episodes)
        sub["downloaded_count"] = local_count
        sub["completed_episode"] = completed
        if total:
            downloaded_keys = {int(ep) for ep in (sub.get("downloaded") or {}).keys() if str(ep).isdigit()}
            existing = set(library_episodes) | downloaded_keys
            missing = [ep for ep in range(1, total + 1) if ep not in existing]
            sub["total_episode"] = total
            sub["missing_episodes"] = missing
            sub["lack_episode"] = len(missing)
            sub["progress"] = min(100, int(completed * 100 / total))
        else:
            sub.setdefault("total_episode", 0)
            sub["missing_episodes"] = []
            sub["lack_episode"] = None
            sub["progress"] = 100 if completed else 0
        episode_facts = self._episode_facts(sub)
        sub["episode_facts"] = episode_facts
        fact_states: Dict[str, int] = {}
        for fact in episode_facts.values():
            state = str(fact.get("final_state") or fact.get("state") or fact.get("plugin_state") or "submitted")
            fact_states[state] = fact_states.get(state, 0) + 1
        sub["episode_fact_counts"] = fact_states
        sub["display_valid"] = bool(title and title not in ("----", "-")) and bool(sub.get("tmdbid") or sub.get("poster") or sub.get("subscription_id"))
        return sub

    def _refresh_subscription_runtime_facts(self, sub: dict, candidates: Optional[List[dict]] = None) -> bool:
        """按已知下载历史、转移记录和媒体库缓存刷新订阅运行事实。"""
        before = dict(sub)
        download_records = sub.setdefault("download_records", {})
        downloaded = sub.setdefault("downloaded", {})
        for ep, record in list(downloaded.items()):
            if not isinstance(record, dict):
                downloaded[str(ep)] = {"title": str(record), "time": now_str(), "state": "submitted"}
                record = downloaded[str(ep)]
            record.setdefault("state", "submitted")
            record.setdefault("status_text", "已提交下载")
            download_hash = str(record.get("hash") or record.get("download_hash") or "").strip()
            if download_hash:
                fact = self._download_fact_by_hash(download_hash)
                record.update(fact)
                download_records[str(ep)] = {k: v for k, v in record.items() if k in ("hash", "download_hash", "state", "status_text", "history_id", "transfer_history_ids", "cleanup_state", "cleanup_at", "updated_at")}
        for item in candidates or []:
            if item.get("subscription_id") != sub.get("id"):
                continue
            self._annotate_candidate_fact(item)
            if item.get("status") in ("downloaded", "submitted", "downloading", "transferred", "library_exists", "download_failed"):
                for ep in item.get("episodes") or []:
                    key = str(ep)
                    downloaded.setdefault(key, {})
                    downloaded[key].update({
                        "title": item.get("title"),
                        "group": item.get("group"),
                        "time": downloaded[key].get("time") or item.get("downloaded_at") or item.get("created_at") or now_str(),
                        "hash": item.get("download_hash") or downloaded[key].get("hash"),
                        "download_hash": item.get("download_hash") or downloaded[key].get("download_hash"),
                        "state": item.get("runtime_state") or item.get("status"),
                        "status_text": item.get("runtime_status_text") or item.get("reason"),
                    })
        return before != sub

    def _download_fact_by_hash(self, download_hash: str) -> Dict[str, Any]:
        """按 hash 查询 MP 下载历史、下载器任务和转移历史事实。"""
        fact: Dict[str, Any] = {"hash": download_hash, "download_hash": download_hash, "state": "submitted", "status_text": "已提交下载"}
        if not download_hash:
            return fact
        try:
            history = DownloadHistoryOper().get_by_hash(download_hash)
            if history:
                fact["history_id"] = getattr(history, "id", None)
                fact["history_title"] = getattr(history, "title", "")
                fact["history_downloader"] = getattr(history, "downloader", None)
                fact["state"] = "download_history"
                fact["status_text"] = "已写入下载历史"
        except Exception as err:
            logger.debug(f"BT订阅中心查询下载历史失败：{download_hash[:8]} - {err}")
        downloader_fact = self._downloader_fact_by_hash(download_hash)
        if downloader_fact:
            fact.update(downloader_fact)
        try:
            transfers = TransferHistoryOper().list_by_hash(download_hash) or []
            transfer_ids = [getattr(item, "id", None) for item in transfers if getattr(item, "id", None) is not None]
            success_ids = [getattr(item, "id", None) for item in transfers if bool(getattr(item, "status", None)) is True]
            if transfer_ids:
                fact["transfer_history_ids"] = transfer_ids
                fact["state"] = "transferred" if success_ids else "transfer_recorded"
                fact["status_text"] = "已入库/已转移" if success_ids else "已有转移记录"
        except Exception as err:
            logger.debug(f"BT订阅中心查询转移历史失败：{download_hash[:8]} - {err}")
        fact["updated_at"] = now_str()
        return fact

    def _downloader_fact_by_hash(self, download_hash: str) -> Dict[str, Any]:
        """按 hash 查询下载器当前任务事实。"""
        helper = DownloaderHelper()
        fact: Dict[str, Any] = {}
        if not download_hash:
            return fact
        completed_states = {"uploading", "stalledUP", "checkingUP", "pausedUP", "stoppedUP", "queuedUP", "forcedUP", "seeding", "seed_pending", "completed", "finished", "finishedDL", "uploading"}
        for service in helper.iterate_module_instances():
            instance = getattr(service, 'instance', None)
            if not instance:
                continue
            try:
                torrents, error = instance.get_torrents(ids=download_hash)
            except Exception as err:
                logger.debug(f"BT订阅中心查询下载器任务失败：{service.name} - {err}")
                continue
            if error or not torrents:
                continue
            torrent = torrents[0]
            state = str(getattr(torrent, 'state', None) or getattr(torrent, 'status', None) or '').strip()
            progress = getattr(torrent, 'progress', None)
            try:
                progress_value = float(progress or 0)
            except Exception:
                progress_value = 0.0
            downloaded = getattr(torrent, 'downloaded', None)
            total_size = getattr(torrent, 'target_size', None) or getattr(torrent, 'total_size', None) or getattr(torrent, 'size', None)
            completed = state.lower() in {s.lower() for s in completed_states} or progress_value >= 1 or (total_size and downloaded is not None and downloaded >= total_size)
            fact.update({
                'downloader_name': service.name,
                'downloader_type': service.type,
                'downloader_state': state,
                'downloader_progress': round(progress_value * 100 if progress_value <= 1 else progress_value, 2),
                'downloader_total_size': total_size,
                'downloader_downloaded': downloaded,
                'state': 'downloaded' if completed else 'downloading',
                'status_text': '下载器任务已完成' if completed else '下载器中',
                'downloader_title': getattr(torrent, 'title', None) or getattr(torrent, 'name', None),
            })
            break
        return fact

    def _annotate_candidate_fact(self, candidate: dict) -> bool:
        """给候选补充最终诊断状态和原因链。"""
        before = dict(candidate)
        status = candidate.get("status") or "unknown"
        reason_chain = list(candidate.get("reason_chain") or [])
        if candidate.get("reason") and candidate.get("reason") not in reason_chain:
            reason_chain.append(candidate.get("reason"))
        download_hash = str(candidate.get("download_hash") or candidate.get("hash") or "").strip()
        if download_hash:
            fact = self._download_fact_by_hash(download_hash)
            candidate["download_hash"] = download_hash
            candidate["runtime_state"] = fact.get("state")
            candidate["runtime_status_text"] = fact.get("status_text")
            candidate["download_fact"] = fact
            if fact.get("state") in ("transferred", "transfer_recorded", "download_history") and status in ("downloaded", "submitted", "ready"):
                candidate["status"] = "submitted" if fact.get("state") == "download_history" else fact.get("state")
        else:
            candidate.setdefault("runtime_state", self._candidate_runtime_state(candidate))
            candidate.setdefault("runtime_status_text", self._candidate_runtime_reason(candidate))
        candidate["reason_chain"] = reason_chain or [candidate.get("runtime_status_text") or candidate.get("reason") or "未记录原因"]
        return before != candidate

    @staticmethod
    def _candidate_runtime_state(candidate: dict) -> str:
        """根据候选字段推导运行时诊断状态。"""
        status = candidate.get("status") or "unknown"
        if status in ("unrecognized", "recognition_issue"):
            return "recognition_issue"
        if status in ("orphan",):
            return "unbound"
        if status in ("skipped", "ignored", "native_skipped"):
            return "filtered_or_duplicate"
        if status in ("pending", "native_pending"):
            return "pending_review"
        if status in ("download_failed", "failed"):
            return "download_failed"
        if status in ("downloaded", "submitted"):
            return "submitted_no_hash"
        if status in ("ready", "native_ready"):
            return "ready"
        return status

    @staticmethod
    def _candidate_runtime_reason(candidate: dict) -> str:
        """根据候选字段生成人类可读诊断说明。"""
        state = BTSubscribeCenter._candidate_runtime_state(candidate)
        mapping = {
            "recognition_issue": "识别异常：需确认 TMDB/季集/动画身份后再回流",
            "unbound": "未绑定订阅：不会自动下载，需创建或绑定私有订阅",
            "filtered_or_duplicate": "已被过滤、忽略或判定重复",
            "pending_review": "待处理：未识别集数或历史等待策略残留",
            "submitted_no_hash": "已提交下载但未记录 hash，需等待下载历史或人工核对",
            "download_failed": candidate.get("download_error") or "下载提交失败，等待人工处理或重试",
            "ready": "满足准入，可由 插件限定来源链路下载",
        }
        return mapping.get(state, candidate.get("reason") or "状态待诊断")

    def _migrate_pending_candidates(self, candidates: List[dict], subs: Dict[str, dict]) -> bool:
        """迁移历史偏好组等待残留，避免长期 pending 卡死。"""
        changed = False
        for sub in subs.values():
            pending = sub.get("pending") or {}
            if pending:
                sub["pending_legacy"] = pending
                sub["pending"] = {}
                sub["updated_at"] = now_str()
                changed = True
        for item in candidates or []:
            if item.get("status") == "pending" and "等待偏好组" in str(item.get("reason") or ""):
                item["status"] = "ready"
                item["legacy_status"] = "pending"
                item["reason"] = "历史偏好组等待已降级：重新标记为可诊断候选，后续按去重/准入重新处理"
                item["runtime_state"] = "ready"
                item["runtime_status_text"] = "历史 pending 已迁移"
                changed = True
            changed = self._annotate_candidate_fact(item) or changed
        return changed

    def _sync_download_and_library_facts(self, subs: Dict[str, dict], candidates: List[dict]) -> bool:
        """同步候选和订阅的下载/入库事实。"""
        changed = False
        for item in candidates or []:
            changed = self._annotate_candidate_fact(item) or changed
        for sub in subs.values():
            changed = self._refresh_subscription_runtime_facts(sub, candidates) or changed
        return changed

    def _episode_facts(self, sub: dict) -> Dict[str, Dict[str, Any]]:
        """汇总当前订阅每集的插件、下载器、下载历史和转移事实。"""
        facts: Dict[str, Dict[str, Any]] = {}
        library = {int(ep) for ep in (sub.get("library_episodes") or []) if str(ep).isdigit()}
        for ep in library:
            facts.setdefault(str(ep), {"episode": ep})["library_exists"] = True
        for ep, record in (sub.get("downloaded") or {}).items():
            ep_key = str(ep)
            fact = facts.setdefault(ep_key, {"episode": int(ep_key) if str(ep_key).isdigit() else ep_key})
            if isinstance(record, dict):
                fact.update({
                    "plugin_state": record.get("state") or "submitted",
                    "plugin_status_text": record.get("status_text") or record.get("reason") or "已提交下载",
                    "download_hash": record.get("download_hash") or record.get("hash") or "",
                    "download_time": record.get("time") or record.get("downloaded_at") or "",
                })
                if record.get("download_error"):
                    fact["download_error"] = record.get("download_error")
            else:
                fact.update({"plugin_state": "submitted", "plugin_status_text": str(record)})
            if fact.get("download_hash"):
                extra = self._download_fact_by_hash(str(fact.get("download_hash")))
                fact.update({k: v for k, v in extra.items() if k not in ("hash", "download_hash")})
                cleanup = self._cleanup_record(str(fact.get("download_hash")))
                if cleanup:
                    fact["cleanup_state"] = cleanup.get("state")
                    fact["cleanup_at"] = cleanup.get("time")
                    fact["cleanup_error"] = cleanup.get("error")
            fact["final_state"] = self._episode_final_state(fact)
            fact["final_status_text"] = self._episode_final_text(fact)
        return dict(sorted(facts.items(), key=lambda item: int(item[0]) if str(item[0]).isdigit() else 0))

    @staticmethod
    def _episode_final_state(fact: Dict[str, Any]) -> str:
        """根据多来源事实计算单集最终状态。"""
        if fact.get("library_exists") or fact.get("state") in ("transferred", "library_exists"):
            return "library_exists"
        if fact.get("state") == "transfer_recorded":
            return "transfer_recorded"
        if fact.get("state") == "downloaded":
            return "downloaded"
        if fact.get("state") == "downloading":
            return "downloading"
        if fact.get("download_error") or fact.get("plugin_state") == "download_failed":
            return "download_failed"
        if fact.get("history_id") or fact.get("state") == "download_history":
            return "download_history"
        if fact.get("download_hash"):
            return "submitted"
        if str(fact.get("plugin_state") or "") == "submitted":
            return "submitted_no_hash"
        return str(fact.get("plugin_state") or "submitted")

    @staticmethod
    def _episode_final_text(fact: Dict[str, Any]) -> str:
        """根据单集最终状态生成人类可读说明。"""
        mapping = {
            "library_exists": "已入库/转移成功",
            "transfer_recorded": "已有转移记录",
            "downloaded": "下载器任务已完成",
            "downloading": f"下载器中 {fact.get('downloader_progress', 0)}%",
            "download_failed": fact.get("download_error") or "下载失败",
            "download_history": "已写入下载历史",
            "submitted": "已提交下载，等待下载器/转移回写",
            "submitted_no_hash": "历史已提交但缺少 hash，无法追踪下载器/转移事实",
        }
        if fact.get("cleanup_state") == "removed":
            base = mapping.get(str(fact.get("final_state")), fact.get("plugin_status_text") or "状态待诊断")
            return f"{base}，下载器任务已清理（保留源文件）"
        if fact.get("cleanup_state") == "failed":
            base = mapping.get(str(fact.get("final_state")), fact.get("plugin_status_text") or "状态待诊断")
            return f"{base}，下载器任务清理失败"
        return mapping.get(str(fact.get("final_state")), fact.get("plugin_status_text") or "状态待诊断")

    def _replacement_summary(self) -> Dict[str, int]:
        """汇总整季包替换状态。"""
        summary = {"watching": 0, "submitted": 0, "downloading": 0, "verified": 0, "failed": 0, "candidates": 0}
        try:
            for sub in (self.get_data("subscriptions") or {}).values():
                state = str(sub.get("replacement_state") or "")
                if state in ("replacement_watch", "watching"):
                    summary["watching"] += 1
                elif state in ("replacement_submitted", "submitted"):
                    summary["submitted"] += 1
                elif state in ("replacement_downloading", "downloading"):
                    summary["downloading"] += 1
                elif state in ("replacement_verified", "verified", "archived"):
                    summary["verified"] += 1
                elif state in ("replacement_failed", "failed"):
                    summary["failed"] += 1
                if sub.get("replacement_candidate"):
                    summary["candidates"] += 1
        except Exception:
            pass
        return summary

    def replacement_watch(self) -> Dict[str, Any]:
        """检查完结订阅的同组整季包并自动提交替换。"""
        stats = {"checked": 0, "watching": 0, "submitted": 0, "verified": 0, "failed": 0, "skipped": 0}
        if not self._replacement_watch_enabled:
            return stats
        try:
            subs = BTSubscribeStore(self).load_subscriptions()
            candidates = self._load_candidates()
            changed = False
            for sub in subs.values():
                self._refresh_subscription_runtime_facts(sub, candidates)
                self._normalize_subscription(sub, candidates)
                if not self._is_subscription_complete_for_replacement(sub):
                    continue
                stats["checked"] += 1
                changed = self._update_replacement_fact(sub) or changed
                state = str(sub.get("replacement_state") or "")
                if state in ("replacement_verified", "archived"):
                    stats["verified"] += 1
                    continue
                if state in ("replacement_submitted", "replacement_downloading"):
                    stats["watching"] += 1
                    continue
                candidate, meta, mediainfo, message = self._find_replacement_candidate(sub)
                if not candidate:
                    sub["replacement_state"] = "replacement_watch"
                    sub["replacement_message"] = message or "暂无同组整季包候选，继续保留单集资源"
                    sub["replacement_checked_at"] = now_str()
                    stats["watching"] += 1
                    changed = True
                    continue
                ok, download_hash, error_msg = self._download_candidate(candidate, meta, mediainfo)
                candidate["replacement_for"] = sub.get("id")
                candidate["status"] = "replacement_submitted" if ok else "replacement_failed"
                candidate["reason"] = "整季包替换已提交" if ok else (error_msg or "整季包替换提交失败")
                self._remember_candidate(candidates, {item.get("key") for item in candidates}, candidate)
                if ok:
                    sub["replacement_state"] = "replacement_submitted"
                    sub["replacement_hash"] = download_hash
                    sub["replacement_group"] = candidate.get("group") or ""
                    sub["replacement_candidate"] = {k: candidate.get(k) for k in ("key", "title", "group", "size", "source_url", "episodes")}
                    sub["replacement_message"] = "已提交整季包替换，等待下载、转移和媒体库验证"
                    sub["replacement_started_at"] = now_str()
                    stats["submitted"] += 1
                else:
                    sub["replacement_state"] = "replacement_failed"
                    sub["replacement_error"] = error_msg or "整季包替换提交失败"
                    sub["replacement_checked_at"] = now_str()
                    stats["failed"] += 1
                changed = True
            if changed:
                BTSubscribeStore(self).save_subscriptions(subs)
                self._save_candidates(candidates[:max(self._candidate_limit, 20)])
            logger.info(f"BT订阅中心整季包替换检查完成：{stats}")
        except Exception as err:
            stats["failed"] += 1
            stats["error"] = str(err)
            logger.warning(f"BT订阅中心整季包替换检查失败：{err}")
        return stats

    def _is_subscription_complete_for_replacement(self, sub: dict) -> bool:
        """判断订阅是否达到整季包替换监控条件。"""
        if str(sub.get("state") or "active") != "active":
            return False
        total = to_int(sub.get("total_episode"), 0)
        if total <= 1:
            return False
        library = set(self._library_episode_numbers(sub))
        if len(library) >= total:
            return True
        facts = sub.get("episode_facts") or {}
        library_count = sum(1 for item in facts.values() if item.get("final_state") == "library_exists")
        return library_count >= total

    def _update_replacement_fact(self, sub: dict) -> bool:
        """刷新已提交整季包替换的下载、转移和入库状态。"""
        before = {k: sub.get(k) for k in ("replacement_state", "replacement_message", "replacement_verified_at")}
        download_hash = str(sub.get("replacement_hash") or "").strip()
        if not download_hash:
            return False
        fact = self._download_fact_by_hash(download_hash)
        sub["replacement_fact"] = fact
        state = str(fact.get("state") or "")
        if state == "downloading":
            sub["replacement_state"] = "replacement_downloading"
            sub["replacement_message"] = "整季包下载中"
        elif state in ("downloaded", "download_history", "transfer_recorded"):
            sub["replacement_state"] = "replacement_submitted"
            sub["replacement_message"] = fact.get("status_text") or "整季包已提交，等待转移/入库验证"
        elif state == "transferred" and self._is_subscription_complete_for_replacement(sub):
            sub["replacement_state"] = "replacement_verified"
            sub["replacement_message"] = "整季包已转移且媒体库仍完整，旧单集记录保留为历史事实"
            sub["replacement_verified_at"] = now_str()
        return before != {k: sub.get(k) for k in ("replacement_state", "replacement_message", "replacement_verified_at")}

    def _find_replacement_candidate(self, sub: dict) -> Tuple[Optional[dict], Optional[MetaInfo], Optional[MediaInfo], str]:
        """从已配置 BT/RSS 来源中查找同组整季包候选。"""
        title = str(sub.get("title") or "").strip()
        if not title or not self._rss_urls:
            return None, None, None, "缺少标题或 RSS 来源，无法检查整季包"
        dominant_group = self._dominant_group(sub)
        fallback: Tuple[Optional[dict], Optional[MetaInfo], Optional[MediaInfo], str] = (None, None, None, "暂无整季包候选")
        for url in [line.strip() for line in self._rss_urls.splitlines() if line.strip()]:
            try:
                for result in RssHelper().parse(url, proxy=self._proxy) or []:
                    raw_title = str(result.get("title") or "")
                    if title.lower() not in raw_title.lower():
                        continue
                    meta = MetaInfo(title=raw_title, subtitle=result.get("description") or "")
                    mediainfo = self.chain.recognize_media(meta=meta) if meta.name else None
                    if not mediainfo or str(mediainfo.tmdb_id) != str(sub.get("tmdbid")):
                        continue
                    if int(meta.begin_season or 1) != int(sub.get("season") or 1):
                        continue
                    if not self._is_season_pack_candidate(raw_title, meta, to_int(sub.get("total_episode"), 0)):
                        continue
                    group = parse_group(raw_title)
                    candidate = self._candidate_base(
                        f"replacement|{self._item_key(raw_title, result.get('enclosure') or result.get('link') or '')}",
                        raw_title,
                        result.get("description") or "",
                        url,
                        result.get("enclosure"),
                        result.get("link"),
                        result.get("size"),
                        result.get("pubdate"),
                        group,
                    )
                    candidate.update(self._media_fields(meta, mediainfo, sub.get("id") or sub_id(mediainfo.tmdb_id, mediainfo.type.value, meta.begin_season or 1, mediainfo.title)))
                    candidate["status"] = "replacement_ready"
                    candidate["reason"] = "完结后同组整季包替换候选"
                    candidate["season_pack"] = True
                    if dominant_group and group == dominant_group:
                        return candidate, meta, mediainfo, "找到同组整季包"
                    if not dominant_group and not fallback[0]:
                        fallback = (candidate, meta, mediainfo, "无主发布组，找到整季包候选")
                    elif dominant_group and not fallback[0]:
                        fallback = (None, None, None, f"找到整季包但发布组不是当前主组 {dominant_group}，继续等待同组")
            except Exception as err:
                logger.debug(f"BT订阅中心整季包来源检查失败：{url} - {err}")
        return fallback

    @staticmethod
    def _dominant_group(sub: dict) -> str:
        """根据已下载记录推断当前订阅主发布组。"""
        counts: Dict[str, int] = {}
        for record in (sub.get("downloaded") or {}).values():
            if isinstance(record, dict):
                group = str(record.get("group") or "").strip()
                if group:
                    counts[group] = counts.get(group, 0) + 1
        if not counts:
            seen = sub.get("seen_groups") or {}
            for group, info in seen.items():
                counts[str(group)] = to_int((info or {}).get("count") if isinstance(info, dict) else 0, 0)
        if not counts:
            return ""
        return sorted(counts.items(), key=lambda item: item[1], reverse=True)[0][0]

    @staticmethod
    def _is_season_pack_candidate(title: str, meta: MetaInfo, total_episode: int) -> bool:
        """判断标题是否像整季包候选。"""
        episodes = episodes_from_meta(meta)
        if total_episode and len(episodes) >= max(3, int(total_episode * 0.7)):
            return True
        if len(episodes) >= 6:
            return True
        text = str(title or "").lower()
        pack_patterns = [r"全集", r"合集", r"整季", r"全\s*\d{2}\s*(话|集)", r"complete", r"batch", r"season\s*\d+\s*(complete|batch)", r"s\d{2}\s*(complete|batch)", r"\d{2}\s*[-~]\s*\d{2}"]
        if any(re.search(pattern, text, re.IGNORECASE) for pattern in pack_patterns):
            return len(episodes) != 1
        return False

    def _load_cleanup_records(self) -> Dict[str, dict]:
        """读取下载器任务清理记录。"""
        data = self.get_data("cleanup_records") or {}
        return data if isinstance(data, dict) else {}

    def _save_cleanup_records(self, data: Dict[str, dict]) -> None:
        """保存下载器任务清理记录。"""
        self.save_data("cleanup_records", data)

    def _cleanup_record(self, download_hash: str) -> Dict[str, Any]:
        """读取单个 hash 的清理记录。"""
        if not download_hash:
            return {}
        return self._load_cleanup_records().get(str(download_hash)) or {}

    def _cleanup_summary(self) -> Dict[str, int]:
        """汇总下载器任务清理记录。"""
        summary = {"total": 0, "removed": 0, "failed": 0, "skipped": 0}
        for item in self._load_cleanup_records().values():
            summary["total"] += 1
            state = str(item.get("state") or "skipped")
            if state in summary:
                summary[state] += 1
            else:
                summary["skipped"] += 1
        return summary

    def _cleanup_completed_torrents(self, subs: Dict[str, dict], candidates: List[dict]) -> Dict[str, Any]:
        """入库成功后删除下载器任务但保留源文件。"""
        stats = {"changed": False, "cleanup_removed": 0, "cleanup_failed": 0}
        if not self._cleanup_after_library:
            return stats
        records = self._load_cleanup_records()
        for sub in subs.values():
            self._normalize_subscription(sub, candidates)
            for ep, fact in (sub.get("episode_facts") or {}).items():
                download_hash = str(fact.get("download_hash") or "").strip()
                if not download_hash:
                    continue
                if (records.get(download_hash) or {}).get("state") == "removed":
                    continue
                final_state = str(fact.get("final_state") or "")
                if final_state != "library_exists":
                    continue
                downloader = fact.get("downloader_name") or fact.get("history_downloader")
                if not downloader:
                    continue
                downloader_fact = self._downloader_fact_by_hash(download_hash)
                if not downloader_fact:
                    records[download_hash] = {
                        "state": "removed",
                        "reason": "下载器任务已不存在，视为已清理",
                        "time": now_str(),
                        "delete_file": False,
                        "sub_id": sub.get("id"),
                        "episode": ep,
                    }
                    stats["changed"] = True
                    continue
                ok, error = self._remove_downloader_task(download_hash, str(downloader), sub, ep)
                if ok:
                    records[download_hash] = {
                        "state": "removed",
                        "reason": "入库确认后已删除下载器任务，保留源文件",
                        "time": now_str(),
                        "delete_file": False,
                        "downloader": downloader,
                        "sub_id": sub.get("id"),
                        "episode": ep,
                        "title": sub.get("title"),
                    }
                    stats["cleanup_removed"] += 1
                    stats["changed"] = True
                    logger.info(f"BT订阅中心入库闭环：已删除下载器任务（保留源文件） {downloader} {download_hash[:8]} {sub.get('title')} E{ep}")
                else:
                    previous = records.get(download_hash) or {}
                    if previous.get("state") != "failed" or previous.get("error") != error:
                        records[download_hash] = {
                            "state": "failed",
                            "error": error,
                            "time": now_str(),
                            "delete_file": False,
                            "downloader": downloader,
                            "sub_id": sub.get("id"),
                            "episode": ep,
                            "title": sub.get("title"),
                        }
                        stats["changed"] = True
                    stats["cleanup_failed"] += 1
                    self._record_failure_once("cleanup", download_hash, error, str(sub.get("title") or ""))
        if stats["changed"]:
            self._save_cleanup_records(records)
        return stats

    def _remove_downloader_task(self, download_hash: str, downloader: str, sub: dict, episode: Any) -> Tuple[bool, str]:
        """删除下载器任务但不删除源文件。"""
        try:
            ok = bool(self.chain.remove_torrents(hashs=[download_hash], delete_file=False, downloader=downloader))
            if not ok:
                return False, "MoviePilot 删除下载器任务接口返回失败"
            remain = self._downloader_fact_by_hash(download_hash)
            if remain:
                return False, "删除后下载器任务仍存在"
            return True, ""
        except Exception as err:
            logger.warning(f"BT订阅中心删除下载器任务失败：{download_hash[:8]} {sub.get('title')} E{episode} - {err}")
            return False, str(err)

    def _record_cleanup_failure(self, download_hash: str, title: str, error: str) -> None:
        """记录清理失败冷却状态，不发送 MoviePilot 消息。"""
        self._record_failure_cooldown("cleanup", download_hash, error)
        logger.warning(f"BT订阅中心入库闭环清理失败：{title or '未知资源'} {download_hash[:8]} - {error}")

    def _hydrate_media_fields(self, sub: dict) -> None:
        """通过 MP 识别链路补齐图片、简介和季总集数。"""
        try:
            tmdbid = sub.get("tmdbid")
            mtype = MediaType.TV if str(sub.get("type") or "tv") in ("tv", "电视剧") else MediaType.MOVIE
            mediainfo = None
            if tmdbid:
                mediainfo = self.chain.recognize_media(tmdbid=int(tmdbid), mtype=mtype)
            if not mediainfo and sub.get("title"):
                meta = MetaInfo(sub.get("title"))
                meta.type = mtype
                mediainfo = self.chain.recognize_media(meta=meta)
            if mediainfo:
                sub["title"] = sub.get("title") or mediainfo.title
                sub["year"] = sub.get("year") or mediainfo.year
                sub["tmdbid"] = sub.get("tmdbid") or mediainfo.tmdb_id
                sub["poster"] = sub.get("poster") or mediainfo.get_poster_image()
                sub["backdrop"] = sub.get("backdrop") or mediainfo.get_backdrop_image()
                sub["description"] = sub.get("description") or mediainfo.overview
                total = self._resolve_total_episode(sub)
                if total:
                    sub["total_episode"] = total
        except Exception as err:
            logger.debug(f"BT订阅中心补齐媒体字段失败：{sub.get('title')} - {err}")

    def _library_completed_count(self, sub: dict) -> int:
        """使用 MP 媒体库存在判断计算当前季已入库集数。"""
        return len(self._library_episode_numbers(sub))

    @staticmethod
    def _candidate_episode_numbers(sub: dict, candidates: List[dict]) -> set:
        """从候选池中提取当前订阅已有候选集数。"""
        episodes = set()
        subid = sub.get("id")
        for item in candidates or []:
            if subid and item.get("subscription_id") != subid:
                continue
            for ep in item.get("episodes") or []:
                try:
                    episodes.add(int(ep))
                except Exception:
                    continue
        return episodes

    @staticmethod
    def _library_episode_numbers(sub: dict) -> List[int]:
        """读取已缓存的媒体库集数，避免打开页面时触发重型媒体库扫描。"""
        values = sub.get("library_episodes") or []
        episodes = []
        if isinstance(values, dict):
            values = values.keys()
        for ep in values:
            try:
                episodes.append(int(ep))
            except Exception:
                continue
        return sorted(set(episodes))

    def _query_library_episode_numbers(self, sub: dict) -> List[int]:
        """按需查询媒体库当前季已存在集数。"""
        tmdbid = sub.get("tmdbid")
        if not tmdbid:
            return []
        try:
            mediainfo = MediaInfo()
            mediainfo.type = MediaType.TV if str(sub.get("type") or "tv") in ("tv", "电视剧") else MediaType.MOVIE
            mediainfo.tmdb_id = int(tmdbid)
            mediainfo.title = sub.get("title") or ""
            mediainfo.year = sub.get("year") or ""
            exist = self.chain.media_exists(mediainfo=mediainfo)
            seasons = getattr(exist, "seasons", None) if exist else None
            if not seasons:
                return []
            season = int(sub.get("season") or 1)
            return sorted(int(ep) for ep in (seasons.get(season) or []))
        except Exception as err:
            logger.debug(f"BT订阅中心刷新入库状态失败：{sub.get('title')} - {err}")
            return []

    def _resolve_total_episode(self, sub: dict) -> int:
        """解析当前订阅季总集数。"""
        current = int(sub.get("total_episode") or 0)
        tmdbid = sub.get("tmdbid")
        if not tmdbid:
            return current
        try:
            season_number = int(sub.get("season") or 1)
            seasons = TmdbChain().tmdb_seasons(tmdbid=int(tmdbid)) or []
            for season in seasons:
                if getattr(season, "season_number", None) == season_number:
                    poster_path = getattr(season, "poster_path", "") or ""
                    if poster_path and not sub.get("poster"):
                        sub["poster"] = poster_path.replace("original", "w500")
                    return int(getattr(season, "episode_count", 0) or current)
        except Exception as err:
            logger.debug(f"BT订阅中心解析总集数失败：{sub.get('title')} - {err}")
        return current

    def _normalize_subscriptions(self, subs: Dict[str, dict], candidates: Optional[List[dict]] = None) -> Dict[str, dict]:
        """批量补齐私有订阅卡片字段。"""
        changed = False
        for sub in subs.values():
            before = dict(sub)
            self._normalize_subscription(sub, candidates or [])
            changed = changed or before != sub
        if changed:
            self._save_subscriptions(subs)
        return subs

    @staticmethod
    def _payload_value(payload: Optional[Dict[str, Any]], key: str, default: Any = None) -> Any:
        """从 JSON 请求体中安全读取字段。"""
        if isinstance(payload, dict) and key in payload:
            return payload.get(key)
        return default

    @staticmethod
    def _payload_bool(payload: Optional[Dict[str, Any]], key: str, default: bool = False) -> bool:
        """从 JSON 请求体中安全读取布尔字段。"""
        value = BTSubscribeCenter._payload_value(payload, key, default)
        if isinstance(value, str):
            return value.lower() in ("1", "true", "yes", "on")
        return bool(value)

    @staticmethod
    def _payload_int(payload: Optional[Dict[str, Any]], key: str, default: int = 0) -> int:
        """从 JSON 请求体中安全读取整数字段。"""
        return to_int(BTSubscribeCenter._payload_value(payload, key, default), default)

    def _submitted_no_hash_diagnostics(self, limit: int = 200) -> List[Dict[str, Any]]:
        """生成历史缺 Hash 记录的只读诊断列表。"""
        subs = self._normalize_subscriptions(self._load_subscriptions(), self._load_candidates())
        candidates = self._load_candidates()
        diagnostics: List[Dict[str, Any]] = []
        max_items = max(1, min(to_int(limit, 200), 1000))
        for sub in subs.values():
            sub_candidates = [item for item in candidates if item.get("subscription_id") == sub.get("id")]
            candidate_eps = {}
            for item in sub_candidates:
                for ep in item.get("episodes") or []:
                    candidate_eps.setdefault(str(ep), 0)
                    candidate_eps[str(ep)] += 1
            for ep, fact in (sub.get("episode_facts") or {}).items():
                if fact.get("final_state") != "submitted_no_hash":
                    continue
                record = (sub.get("downloaded") or {}).get(str(ep)) or {}
                title = record.get("title") if isinstance(record, dict) else str(record)
                suggestion = "历史记录缺少 download_hash，无法自动追踪下载器/转移事实；建议先核对媒体库是否已存在，再决定是否重新下载或保留记录。"
                diagnostics.append({
                    "sub_id": sub.get("id"),
                    "title": sub.get("title"),
                    "year": sub.get("year"),
                    "season": sub.get("season") or 1,
                    "episode": ep,
                    "tmdbid": sub.get("tmdbid"),
                    "record_title": title or "",
                    "group": record.get("group") if isinstance(record, dict) else "",
                    "time": record.get("time") if isinstance(record, dict) else "",
                    "candidate_count": candidate_eps.get(str(ep), 0),
                    "library_cached": int(ep) in {int(v) for v in (sub.get("library_episodes") or []) if str(v).isdigit()},
                    "suggestion": suggestion,
                })
                if len(diagnostics) >= max_items:
                    return diagnostics
        return diagnostics

    def _download_fact_summary(self) -> Dict[str, Any]:
        """汇总订阅下载事实概览。"""
        subs = self._load_subscriptions()
        summary = {"submitted": 0, "submitted_no_hash": 0, "hash_tracked": 0, "downloading": 0, "downloaded": 0, "download_history": 0, "transfer_recorded": 0, "transferred": 0, "download_failed": 0, "library_exists": 0, "total_records": 0}
        for sub in subs.values():
            self._normalize_subscription(sub, [])
            for fact in (sub.get("episode_facts") or {}).values():
                summary["total_records"] += 1
                state = str(fact.get("final_state") or "submitted")
                if fact.get("download_hash"):
                    summary["hash_tracked"] += 1
                if state in summary:
                    summary[state] += 1
                else:
                    summary["submitted"] += 1
        return summary

    def api_status(self) -> schemas.Response:
        """返回插件状态。"""
        return schemas.Response(success=True, data={"config": self._safe_config(), "stats": self._stats(), "recognition_issue_count": len(self._load_recognition_issues()), "download_fact_summary": self._download_fact_summary(), "cleanup_summary": self._cleanup_summary(), "replacement_summary": self._replacement_summary(), "failure_cooldown_summary": self._failure_cooldown_summary()})


    def api_overview(self) -> schemas.Response:
        """返回前端首页所需的聚合数据，减少多接口重复加载。"""
        candidates = self._load_candidates()
        subs = self._normalize_subscriptions(self._load_subscriptions(), candidates)
        issues = self._load_recognition_issues()
        return schemas.Response(success=True, data={
            "config": self._safe_config(),
            "stats": self._stats(),
            "subscriptions": subs,
            "candidates": self._public_candidates(candidates),
            "recognition_issues": self._public_issues(issues),
            "recognition_issue_count": len(issues),
            "download_fact_summary": self._download_fact_summary(),
            "cleanup_summary": self._cleanup_summary(),
            "replacement_summary": self._replacement_summary(),
            "failure_cooldown_summary": self._failure_cooldown_summary(),
        })

    def api_native_mappings(self) -> schemas.Response:
        """兼容旧前端入口：原生订阅桥接已下线，固定返回空映射。"""
        return schemas.Response(success=True, data={})

    def api_refresh(self) -> schemas.Response:
        """手动刷新 RSS 源。"""
        result = self.scan_sources(manual=True)
        return schemas.Response(success=True, data=result)

    def api_subscriptions(self) -> schemas.Response:
        """查询私有订阅。"""
        return schemas.Response(success=True, data=self._normalize_subscriptions(self._load_subscriptions(), self._load_candidates()))

    def api_subscription(self, sub_id: str) -> schemas.Response:
        """查询单个私有订阅及相关候选。"""
        subs = self._normalize_subscriptions(self._load_subscriptions(), self._load_candidates())
        sub = subs.get(sub_id)
        if not sub:
            return schemas.Response(success=False, message="订阅不存在")
        candidates = [item for item in self._load_candidates() if item.get("subscription_id") == sub_id]
        return schemas.Response(success=True, data={"subscription": sub, "candidates": self._public_candidates(candidates)})

    def api_candidates(self, subscription_id: str = "", status: str = "") -> schemas.Response:
        """查询候选资源，可按订阅和状态过滤。"""
        items = self._load_candidates()
        if subscription_id:
            items = [item for item in items if item.get("subscription_id") == subscription_id]
        if status:
            items = [item for item in items if item.get("status") == status]
        return schemas.Response(success=True, data=self._public_candidates(items))

    def api_submitted_no_hash(self, limit: int = 200) -> schemas.Response:
        """查询历史已提交但缺少 Hash 的只读诊断列表。"""
        return schemas.Response(success=True, data=self._submitted_no_hash_diagnostics(limit=limit))

    def api_recognition_issues(self, status: str = "") -> schemas.Response:
        """查询识别异常队列。"""
        items = self._load_recognition_issues()
        if status:
            items = [item for item in items if item.get("status") == status]
        return schemas.Response(success=True, data=self._public_issues(items))

    def api_ignore_issue(self, payload: Dict[str, Any] = Body(default_factory=dict)) -> schemas.Response:
        """忽略一条识别异常。"""
        key = str(self._payload_value(payload, "key", "") or "")
        issues = self._load_recognition_issues()
        changed = False
        for item in issues:
            if item.get("key") == key:
                item["status"] = "ignored"
                item["handled_at"] = now_str()
                changed = True
                break
        if not changed:
            return schemas.Response(success=False, message="识别异常不存在")
        self._save_recognition_issues(issues)
        return schemas.Response(success=True, message="已忽略识别异常")

    def api_rescan_issue(self, payload: Dict[str, Any] = Body(default_factory=dict)) -> schemas.Response:
        """重新识别一条异常并给出处理建议。"""
        key = str(self._payload_value(payload, "key", "") or "")
        issues = self._load_recognition_issues()
        issue = next((item for item in issues if item.get("key") == key), None)
        if not issue:
            return schemas.Response(success=False, message="识别异常不存在")
        meta = MetaInfo(title=issue.get("title") or "", subtitle=issue.get("description") or "")
        mediainfo = self.chain.recognize_media(meta=meta) if meta.name else None
        if not mediainfo:
            issue["suggestion"] = self._identifier_suggestion(issue, meta=meta, mediainfo=None)
            issue["last_check"] = now_str()
            self._save_recognition_issues(issues)
            return schemas.Response(success=True, message="仍未识别，已生成识别词建议", data=issue)
        issue.update(self._media_fields(meta, mediainfo, sub_id(mediainfo.tmdb_id, mediainfo.type.value, meta.begin_season or 1, mediainfo.title)))
        issue["media_category"] = str(getattr(mediainfo, "category", "") or "")
        issue["media_title"] = mediainfo.title
        issue["media_type"] = mediainfo.type.value
        issue["tmdbid"] = mediainfo.tmdb_id
        issue["last_check"] = now_str()
        if mediainfo.type == MediaType.TV and self._is_anime_like(meta, mediainfo):
            issue["status"] = "resolved"
            issue["suggestion"] = "重新识别已符合动画新番准入，可刷新 RSS 重新进入候选/订阅流程。"
        else:
            issue["status"] = "open"
            issue["suggestion"] = self._identifier_suggestion(issue, meta=meta, mediainfo=mediainfo)
        self._save_recognition_issues(issues)
        return schemas.Response(success=True, message="重扫完成", data=issue)

    def api_issue_identifier_preview(self, payload: Dict[str, Any] = Body(default_factory=dict)) -> schemas.Response:
        """预览识别异常对应的窄作用域自定义识别词。"""
        key = str(self._payload_value(payload, "key", "") or "")
        issue = self._find_recognition_issue(key)
        if not issue:
            return schemas.Response(success=False, message="识别异常不存在")
        suggestion = self._issue_identifier_rule(issue, payload or {})
        if not suggestion:
            return schemas.Response(success=False, message="缺少 TMDB 或标题，无法生成安全识别词")
        existing = self._get_custom_identifiers()
        return schemas.Response(success=True, message="已生成识别词预览", data={
            "key": key,
            "identifier": suggestion,
            "exists": suggestion in existing,
            "title": issue.get("title"),
            "target": self._issue_target_summary(issue),
            "warning": "该规则会写入全局自定义识别词；已按异常样本标题生成窄作用域锚定规则。",
        })

    def api_apply_issue_identifier(self, payload: Dict[str, Any] = Body(default_factory=dict)) -> schemas.Response:
        """确认写入识别异常识别词，并把异常回流候选。"""
        key = str(self._payload_value(payload, "key", "") or "")
        confirm = self._payload_bool(payload, "confirm", False)
        issues = self._load_recognition_issues()
        issue = next((item for item in issues if item.get("key") == key), None)
        if not issue:
            return schemas.Response(success=False, message="识别异常不存在")
        identifier = str(self._payload_value(payload, "identifier", "") or "").strip() or self._issue_identifier_rule(issue, payload or {})
        if not identifier:
            return schemas.Response(success=False, message="缺少可写入的识别词")
        preview = {"key": key, "identifier": identifier, "target": self._issue_target_summary(issue), "exists": identifier in self._get_custom_identifiers()}
        if not confirm:
            return schemas.Response(success=False, message="写入识别词需要 confirm=true 确认", data=preview)
        write_result = self._append_custom_identifier_with_snapshot(identifier, key)
        issue["identifier_rule"] = identifier
        issue["identifier_written_at"] = now_str()
        issue["identifier_snapshot_key"] = write_result.get("snapshot_key")
        issue["status"] = "identifier_written"
        reflow = self._reflow_issue_to_candidate(issue, status="ready", reason="识别词已写入，异常已回流候选，等待插件准入/去重/下载决策")
        issue["reflowed_at"] = now_str()
        issue["reflow_candidate_key"] = reflow.get("candidate", {}).get("key")
        issue["last_check"] = now_str()
        self._save_recognition_issues(issues)
        return schemas.Response(success=True, message="识别词已写入并回流候选", data={"write": write_result, "issue": issue, "reflow": reflow})

    def api_issue_agent_hint(self, payload: Dict[str, Any] = Body(default_factory=dict)) -> schemas.Response:
        """生成给智能体处理识别异常的结构化提示。"""
        key = str(self._payload_value(payload, "key", "") or "")
        issue = self._find_recognition_issue(key)
        if not issue:
            return schemas.Response(success=False, message="识别异常不存在")
        prompt = self._agent_issue_prompt(issue)
        suggested_identifier = self._issue_identifier_rule(issue, payload or {})
        return schemas.Response(success=True, message="已生成智能体处理提示", data={"key": key, "prompt": prompt, "issue": issue, "suggested_identifier": suggested_identifier, "can_auto_write": bool(suggested_identifier)})

    def api_issue_agent_apply(self, payload: Dict[str, Any] = Body(default_factory=dict)) -> schemas.Response:
        """由智能体高置信自动写入识别词并回流候选。"""
        key = str(self._payload_value(payload, "key", "") or "")
        issues = self._load_recognition_issues()
        issue = next((item for item in issues if item.get("key") == key), None)
        if not issue:
            return schemas.Response(success=False, message="识别异常不存在")
        identifier = str(self._payload_value(payload, "identifier", "") or "").strip() or self._issue_identifier_rule(issue, payload or {})
        if not identifier:
            return schemas.Response(success=False, message="缺少可自动写入的识别词")
        write_result = self._append_custom_identifier_with_snapshot(identifier, key)
        issue["identifier_rule"] = identifier
        issue["identifier_written_at"] = now_str()
        issue["identifier_snapshot_key"] = write_result.get("snapshot_key")
        issue["status"] = "identifier_written"
        issue["auto_written_by"] = "agent"
        reflow = self._reflow_issue_to_candidate(issue, status="ready", reason="智能体已自动写入识别词，异常已回流候选，等待插件准入/去重/下载决策")
        issue["reflowed_at"] = now_str()
        issue["reflow_candidate_key"] = reflow.get("candidate", {}).get("key")
        issue["last_check"] = now_str()
        self._save_recognition_issues(issues)
        return schemas.Response(success=True, message="智能体已自动写入识别词并回流候选", data={"write": write_result, "issue": issue, "reflow": reflow})

    def api_reflow_issue(self, payload: Dict[str, Any] = Body(default_factory=dict)) -> schemas.Response:
        """将识别异常回流候选，必须确认。"""
        key = str(self._payload_value(payload, "key", "") or "")
        confirm = self._payload_bool(payload, "confirm", False)
        issues = self._load_recognition_issues()
        issue = next((item for item in issues if item.get("key") == key), None)
        if not issue:
            return schemas.Response(success=False, message="识别异常不存在")
        if not confirm:
            return schemas.Response(success=False, message="回流候选需要 confirm=true 确认", data={"key": key, "title": issue.get("title"), "target": self._issue_target_summary(issue)})
        reflow = self._reflow_issue_to_candidate(issue, status="ready", reason="识别异常已手动回流候选，等待插件准入/去重/下载决策")
        issue["status"] = "reflowed"
        issue["reflowed_at"] = now_str()
        issue["reflow_candidate_key"] = reflow.get("candidate", {}).get("key")
        self._save_recognition_issues(issues)
        return schemas.Response(success=True, message="识别异常已回流候选", data={"issue": issue, "reflow": reflow})

    def api_save_config(self, payload: Dict[str, Any] = Body(default_factory=dict)) -> schemas.Response:
        """保存侧栏页提交的插件配置。"""
        kwargs = payload or {}
        config = self._current_config()
        for key in config.keys():
            if key in kwargs:
                config[key] = kwargs.get(key)
        self.update_config(config)
        self.init_plugin(config)
        return schemas.Response(success=True, message="配置已保存", data=self._safe_config())

    def api_rss_search(self, payload: Dict[str, Any] = Body(default_factory=dict)) -> schemas.Response:
        """在已配置 RSS/BT 源中实时搜索资源。"""
        keyword = str(self._payload_value(payload, "keyword", "") or "")
        limit = self._payload_int(payload, "limit", 80)
        keyword = str(keyword or "").strip().lower()
        if not keyword:
            return schemas.Response(success=False, message="搜索关键字不能为空")
        items: List[dict] = []
        seen = set()
        max_count = max(1, min(to_int(limit, 80), 200))
        for url in [line.strip() for line in self._rss_urls.splitlines() if line.strip()]:
            try:
                for result in RssHelper().parse(url, proxy=self._proxy) or []:
                    title = str(result.get("title") or "")
                    desc = str(result.get("description") or "")
                    if keyword not in f"{title} {desc}".lower():
                        continue
                    key = self._item_key(title, result.get("enclosure") or result.get("link") or "")
                    if key in seen:
                        continue
                    seen.add(key)
                    group = parse_group(title)
                    item = self._candidate_base(key, title, desc, url, result.get("enclosure"), result.get("link"), result.get("size"), result.get("pubdate"), group)
                    item.update({"status": "rss_search", "reason": "实时搜索命中已配置 RSS/BT 源"})
                    items.append(item)
                    if len(items) >= max_count:
                        return schemas.Response(success=True, data=items)
            except Exception as err:
                logger.warning(f"BT订阅中心搜索 RSS 源失败：{url} - {err}")
        return schemas.Response(success=True, data=items)

    def api_refresh_subscription_status(self, payload: Dict[str, Any] = Body(default_factory=dict)) -> schemas.Response:
        """刷新单个私有订阅的媒体库入库状态。"""
        sub_id = str(self._payload_value(payload, "sub_id", "") or "")
        subs = self._load_subscriptions()
        sub = subs.get(sub_id)
        if not sub:
            return schemas.Response(success=False, message="订阅不存在")
        sub["library_episodes"] = self._query_library_episode_numbers(sub)
        self._normalize_subscription(sub, self._load_candidates())
        sub["updated_at"] = now_str()
        self._save_subscriptions(subs)
        return schemas.Response(success=True, message="入库状态已刷新", data=sub)

    def api_update_subscription(self, payload: Dict[str, Any] = Body(default_factory=dict)) -> schemas.Response:
        """编辑私有订阅基础字段。"""
        sub_id = str(self._payload_value(payload, "sub_id", "") or "")
        kwargs = payload or {}
        subs = self._load_subscriptions()
        sub = subs.get(sub_id)
        if not sub:
            return schemas.Response(success=False, message="订阅不存在")
        allowed = ["title", "year", "season", "mode", "state", "preferred_group", "total_episode", "description"]
        for key in allowed:
            if key in kwargs:
                value = kwargs.get(key)
                if key in ("season", "total_episode"):
                    value = to_int(value, sub.get(key) or 0)
                sub[key] = value
        sub["updated_at"] = now_str()
        self._normalize_subscription(sub, self._load_candidates())
        self._save_subscriptions(subs)
        return schemas.Response(success=True, message="订阅已更新", data=sub)

    def api_refresh_subscription_meta(self, payload: Dict[str, Any] = Body(default_factory=dict)) -> schemas.Response:
        """按需刷新私有订阅媒体信息。"""
        sub_id = str(self._payload_value(payload, "sub_id", "") or "")
        subs = self._load_subscriptions()
        sub = subs.get(sub_id)
        if not sub:
            return schemas.Response(success=False, message="订阅不存在")
        self._hydrate_media_fields(sub)
        self._normalize_subscription(sub, self._load_candidates())
        sub["updated_at"] = now_str()
        self._save_subscriptions(subs)
        return schemas.Response(success=True, message="媒体信息已刷新", data=sub)

    def api_search_subscription_candidates(self, payload: Dict[str, Any] = Body(default_factory=dict)) -> schemas.Response:
        """搜索指定订阅的已有候选和已配置 RSS/BT 源。"""
        sub_id = str(self._payload_value(payload, "sub_id", "") or "")
        include_rss = self._payload_bool(payload, "include_rss", True)
        subs = self._load_subscriptions()
        sub = subs.get(sub_id)
        if not sub:
            return schemas.Response(success=False, message="订阅不存在")
        title = str(sub.get("title") or "").strip()
        if not title:
            return schemas.Response(success=False, message="订阅标题为空，无法搜索")
        existing = [item for item in self._load_candidates() if item.get("subscription_id") == sub_id or title.lower() in str(item.get("title") or "").lower()]
        rss_items: List[dict] = []
        if include_rss:
            response = self.api_rss_search({"keyword": title, "limit": 80})
            if response.success and isinstance(response.data, list):
                rss_items = response.data
        return schemas.Response(success=True, data={"subscription": sub, "candidates": existing, "rss_results": rss_items})

    def api_clear_pending(self, payload: Dict[str, Any] = Body(default_factory=dict)) -> schemas.Response:
        """清空订阅等待队列，必须确认。"""
        sub_id = str(self._payload_value(payload, "sub_id", "") or "")
        confirm = self._payload_bool(payload, "confirm", False)
        subs = self._load_subscriptions()
        sub = subs.get(sub_id)
        if not sub:
            return schemas.Response(success=False, message="订阅不存在")
        pending_count = len(sub.get("pending") or {})
        if not confirm:
            return schemas.Response(success=False, message="清空等待队列需要 confirm=true 确认", data={"pending_count": pending_count})
        sub["pending"] = {}
        sub["updated_at"] = now_str()
        self._save_subscriptions(subs)
        return schemas.Response(success=True, message=f"已清空 {pending_count} 条等待记录", data=sub)

    def api_reset_downloaded(self, payload: Dict[str, Any] = Body(default_factory=dict)) -> schemas.Response:
        """重置订阅下载记录，必须确认。"""
        sub_id = str(self._payload_value(payload, "sub_id", "") or "")
        confirm = self._payload_bool(payload, "confirm", False)
        subs = self._load_subscriptions()
        sub = subs.get(sub_id)
        if not sub:
            return schemas.Response(success=False, message="订阅不存在")
        downloaded_count = len(sub.get("downloaded") or {})
        if not confirm:
            return schemas.Response(success=False, message="重置下载记录需要 confirm=true 确认", data={"downloaded_count": downloaded_count})
        sub["downloaded"] = {}
        sub["updated_at"] = now_str()
        self._normalize_subscription(sub, self._load_candidates())
        self._save_subscriptions(subs)
        return schemas.Response(success=True, message=f"已重置 {downloaded_count} 条下载记录", data=sub)

    def api_add_subscription(self, payload: Dict[str, Any] = Body(default_factory=dict)) -> schemas.Response:
        """添加私有订阅。"""
        title = str(self._payload_value(payload, "title", "") or "")
        tmdbid = self._payload_value(payload, "tmdbid", None)
        season = self._payload_int(payload, "season", 1)
        mode = str(self._payload_value(payload, "mode", "backfill") or "backfill")
        group = str(self._payload_value(payload, "group", "") or "")
        if not title and not tmdbid:
            return schemas.Response(success=False, message="标题或 TMDB ID 不能为空")
        sub_id_value = sub_id(tmdbid=tmdbid, mtype="tv", season=season, title=title)
        subs = self._load_subscriptions()
        if sub_id_value not in subs:
            subs[sub_id_value] = self._new_subscription(sub_id=sub_id_value, title=title, year="", mtype="tv", tmdbid=tmdbid, season=season, mode=mode, group=group)
        else:
            subs[sub_id_value]["state"] = "active"
            if group:
                subs[sub_id_value]["preferred_group"] = group
            subs[sub_id_value]["updated_at"] = now_str()
        self._save_subscriptions(subs)
        return schemas.Response(success=True, message="已添加私有订阅", data=subs[sub_id_value])

    def api_pause_subscription(self, payload: Dict[str, Any] = Body(default_factory=dict)) -> schemas.Response:
        """暂停私有订阅。"""
        sub_id = str(self._payload_value(payload, "sub_id", "") or "")
        return self._set_subscription_state(sub_id, "paused")

    def api_resume_subscription(self, payload: Dict[str, Any] = Body(default_factory=dict)) -> schemas.Response:
        """恢复私有订阅。"""
        sub_id = str(self._payload_value(payload, "sub_id", "") or "")
        return self._set_subscription_state(sub_id, "active")


    def api_delete_subscription(self, payload: Dict[str, Any] = Body(default_factory=dict)) -> schemas.Response:
        """删除私有订阅，必须确认后执行。"""
        sub_id = str(self._payload_value(payload, "sub_id", "") or "")
        confirm = self._payload_bool(payload, "confirm", False)
        subs = self._load_subscriptions()
        if sub_id not in subs:
            return schemas.Response(success=False, message="订阅不存在")
        if not confirm:
            return schemas.Response(success=False, message="删除私有订阅需要 confirm=true 确认", data={"subscription": subs[sub_id]})
        removed = subs.pop(sub_id)
        self._save_subscriptions(subs)
        return schemas.Response(success=True, message="私有订阅已删除", data=removed)

    def api_create_subscription_from_candidate(self, payload: Dict[str, Any] = Body(default_factory=dict)) -> schemas.Response:
        """从候选创建私有订阅。"""
        key = str(self._payload_value(payload, "key", "") or "")
        mode = str(self._payload_value(payload, "mode", "backfill") or "backfill")
        candidates = self._load_candidates()
        item = next((candidate for candidate in candidates if candidate.get("key") == key), None)
        if not item:
            return schemas.Response(success=False, message="候选不存在")
        if not item.get("subscription_id"):
            return schemas.Response(success=False, message="候选缺少识别媒体信息，不能创建订阅")
        subs = self._load_subscriptions()
        sid = item.get("subscription_id")
        if sid not in subs:
            subs[sid] = self._new_subscription(
                sub_id=sid,
                title=item.get("media_title") or item.get("title") or "",
                year=str(item.get("year") or ""),
                mtype=item.get("type") or "tv",
                tmdbid=item.get("tmdbid"),
                season=int(item.get("season") or 1),
                mode=mode,
                group="",
            )
        item["status"] = "ready"
        item["reason"] = "已从候选创建私有订阅"
        self._save_subscriptions(subs)
        self._save_candidates(candidates)
        return schemas.Response(success=True, message="已从候选创建私有订阅", data=subs[sid])

    def api_bind_candidate(self, payload: Dict[str, Any] = Body(default_factory=dict)) -> schemas.Response:
        """把候选绑定到指定私有订阅。"""
        key = str(self._payload_value(payload, "key", "") or "")
        sub_id = str(self._payload_value(payload, "sub_id", "") or "")
        subs = self._load_subscriptions()
        if sub_id not in subs:
            return schemas.Response(success=False, message="订阅不存在")
        candidates = self._load_candidates()
        item = next((candidate for candidate in candidates if candidate.get("key") == key), None)
        if not item:
            return schemas.Response(success=False, message="候选不存在")
        item["subscription_id"] = sub_id
        item["status"] = "ready"
        item["reason"] = "用户已绑定到私有订阅"
        self._record_seen_group(subs[sub_id], item.get("group"))
        self._save_subscriptions(subs)
        self._save_candidates(candidates)
        return schemas.Response(success=True, message="候选已绑定", data=item)


    def api_set_group(self, payload: Dict[str, Any] = Body(default_factory=dict)) -> schemas.Response:
        """设置私有订阅偏好发布组。"""
        sub_id = str(self._payload_value(payload, "sub_id", "") or "")
        group = str(self._payload_value(payload, "group", "") or "")
        subs = self._load_subscriptions()
        if sub_id not in subs:
            return schemas.Response(success=False, message="订阅不存在")
        subs[sub_id]["preferred_group"] = group or ""
        subs[sub_id]["updated_at"] = now_str()
        self._save_subscriptions(subs)
        return schemas.Response(success=True, message="发布组标记已更新", data=subs[sub_id])

    def api_ignore_candidate(self, payload: Dict[str, Any] = Body(default_factory=dict)) -> schemas.Response:
        """忽略候选资源。"""
        key = str(self._payload_value(payload, "key", "") or "")
        candidates = self._load_candidates()
        changed = False
        for item in candidates:
            if item.get("key") == key:
                item["status"] = "ignored"
                item["reason"] = "用户已忽略"
                changed = True
                break
        if not changed:
            return schemas.Response(success=False, message="候选不存在")
        self._save_candidates(candidates)
        return schemas.Response(success=True, message="已忽略候选")

    def api_download_candidate(self, payload: Dict[str, Any] = Body(default_factory=dict)) -> schemas.Response:
        """下载候选资源，必须确认后执行。"""
        key = str(self._payload_value(payload, "key", "") or "")
        confirm = self._payload_bool(payload, "confirm", False)
        candidates = self._load_candidates()
        candidate = next((item for item in candidates if item.get("key") == key), None)
        if not candidate:
            return schemas.Response(success=False, message="候选不存在")
        if not confirm:
            return schemas.Response(success=False, message="下载需要 confirm=true 确认", data={"candidate": candidate})
        meta = MetaInfo(title=candidate.get("title") or "", subtitle=candidate.get("description") or "")
        mediainfo: Optional[MediaInfo] = self.chain.recognize_media(meta=meta)
        if not mediainfo:
            return schemas.Response(success=False, message="候选媒体识别失败，不能下载")
        ok, download_hash, error_msg = self._download_candidate(candidate, meta, mediainfo)
        if not ok:
            self._mark_candidate_download_failed(candidate, error_msg)
            self._save_candidates(candidates)
            return schemas.Response(success=False, message=error_msg or "添加下载失败", data={"candidate": candidate})
        candidate["status"] = "submitted"
        candidate["reason"] = "用户手动确认下载"
        subid = candidate.get("subscription_id")
        subs = self._load_subscriptions()
        if subid and subid in subs:
            self._mark_downloaded(subs[subid], candidate, download_hash)
            self._save_subscriptions(subs)
        self._save_candidates(candidates)
        return schemas.Response(success=True, message="已提交下载", data=candidate)

    def scan_sources(self, manual: bool = False) -> Dict[str, Any]:
        """刷新全部 RSS 源并处理候选。"""
        if not self._rss_urls:
            return {"total": 0, "accepted": 0, "message": "未配置 RSS 地址"}
        stats = {"total": 0, "accepted": 0, "downloaded": 0, "skipped": 0, "errors": 0, "issue": 0}
        candidates = self._load_candidates()
        seen_keys = {item.get("key") for item in candidates}
        subscriptions = self._load_subscriptions()
        recognition_issues = self._load_recognition_issues()
        for url in [line.strip() for line in self._rss_urls.splitlines() if line.strip()]:
            try:
                logger.info(f"BT订阅中心开始刷新 RSS：{url}")
                results = RssHelper().parse(url, proxy=self._proxy) or []
                for result in results:
                    stats["total"] += 1
                    outcome = self._process_rss_item(result, url, subscriptions, candidates, seen_keys, recognition_issues)
                    stats[outcome] = stats.get(outcome, 0) + 1
            except Exception as err:
                stats["errors"] += 1
                logger.error(f"BT订阅中心刷新 RSS 出错：{url} - {str(err)} - {traceback.format_exc()}")
        self._save_subscriptions(subscriptions)
        self._save_recognition_issues(recognition_issues)
        self._save_candidates(candidates[:max(self._candidate_limit, 20)])
        logger.info(f"BT订阅中心刷新完成：{stats}")
        return stats

    def _process_rss_item(self, result: dict, source_url: str, subscriptions: Dict[str, dict], candidates: List[dict], seen_keys: set, recognition_issues: List[dict]) -> str:
        """处理单条 RSS 资源。"""
        title = result.get("title") or ""
        description = result.get("description") or ""
        enclosure = result.get("enclosure")
        link = result.get("link")
        size = result.get("size")
        pubdate = result.get("pubdate")
        key = self._item_key(title, enclosure or link)
        if not title or key in seen_keys:
            return "skipped"
        group = parse_group(title)
        base_candidate = self._candidate_base(key, title, description, source_url, enclosure, link, size, pubdate, group)
        reason = self._pre_filter(title, description, size, pubdate)
        if reason:
            base_candidate.update({"status": "skipped", "reason": reason})
            self._remember_candidate(candidates, seen_keys, base_candidate)
            return "skipped"
        meta = MetaInfo(title=title, subtitle=description)
        if not meta.name:
            base_candidate.update({"status": "skipped", "reason": "标题无法提取媒体名称"})
            self._remember_candidate(candidates, seen_keys, base_candidate)
            return "skipped"
        mediainfo: Optional[MediaInfo] = self.chain.recognize_media(meta=meta)
        if not mediainfo:
            base_candidate.update({"status": "unrecognized", "reason": "MP 未识别媒体，可能需要识别词"})
            self._remember_recognition_issue(recognition_issues, base_candidate, "未识别媒体", meta=meta)
            self._remember_candidate(candidates, seen_keys, base_candidate)
            return "issue"
        sub_id_value = sub_id(tmdbid=mediainfo.tmdb_id, mtype=mediainfo.type.value, season=meta.begin_season or 1, title=mediainfo.title)
        subscription = subscriptions.get(sub_id_value)
        if not subscription and self._should_create_airing(meta, mediainfo, pubdate):
            subscription = self._new_subscription(sub_id_value, mediainfo.title, mediainfo.year, mediainfo.type.value, mediainfo.tmdb_id, meta.begin_season or 1, "airing", "", mediainfo)
            subscriptions[sub_id_value] = subscription
        if not subscription:
            base_candidate.update(self._media_fields(meta, mediainfo, sub_id_value))
            base_candidate.update({"status": "orphan", "reason": "未匹配私有订阅；如为老番需先添加订阅"})
            self._remember_candidate(candidates, seen_keys, base_candidate)
            return "accepted"
        candidate = dict(base_candidate)
        candidate.update(self._media_fields(meta, mediainfo, sub_id_value))
        admission = self._resource_admission(meta=meta, mediainfo=mediainfo)
        candidate["admission_state"] = admission.get("state")
        candidate["admission_reason"] = admission.get("reason")
        if admission.get("state") == "recognition_conflict":
            candidate.update({"status": "recognition_conflict", "reason": admission.get("reason")})
            self._remember_recognition_issue(recognition_issues, candidate, admission.get("reason") or "识别冲突", meta=meta, mediainfo=mediainfo)
            self._remember_candidate(candidates, seen_keys, candidate)
            return "issue"
        self._record_seen_group(subscription, group)
        decision = self._decide_candidate(subscription, candidate, meta)
        candidate.update(decision)
        if decision.get("status") == "ready" and self._auto_download:
            ok, download_hash, error_msg = self._download_candidate(candidate, meta, mediainfo)
            if ok:
                self._mark_downloaded(subscription, candidate, download_hash)
                candidate["status"] = "submitted"
                candidate["reason"] = "已添加下载并记录私有订阅状态"
                self._remember_candidate(candidates, seen_keys, candidate)
                return "downloaded"
            self._mark_candidate_download_failed(candidate, error_msg)
        self._remember_candidate(candidates, seen_keys, candidate)
        return "accepted"

    def _find_recognition_issue(self, key: str) -> Optional[dict]:
        """按 key 查找识别异常记录。"""
        return next((item for item in self._load_recognition_issues() if item.get("key") == key), None)

    @staticmethod
    def _issue_signature(candidate: dict, reason: str) -> str:
        """生成识别异常稳定指纹。"""
        raw = f"{candidate.get('key') or candidate.get('title') or ''}|{reason or ''}"
        return re.sub(r"\s+", " ", raw.strip())[:240]

    @staticmethod
    def _issue_target_summary(issue: dict) -> Dict[str, Any]:
        """返回识别异常目标摘要。"""
        return {
            "title": issue.get("media_title") or issue.get("target_title") or "",
            "type": issue.get("media_type") or issue.get("type") or "tv",
            "tmdbid": issue.get("tmdbid"),
            "season": issue.get("season") or 1,
            "episodes": issue.get("episodes") or [],
        }

    def _issue_identifier_rule(self, issue: dict, payload: Optional[Dict[str, Any]] = None) -> str:
        """为识别异常生成窄作用域 TMDB 绑定识别词。"""
        payload = payload or {}
        title = str(payload.get("sample_title") or issue.get("title") or "").strip()
        tmdbid = payload.get("tmdbid") or issue.get("tmdbid")
        media_type = str(payload.get("media_type") or issue.get("media_type") or issue.get("type") or "tv").lower()
        season = to_int(payload.get("season") or issue.get("season") or 1, 1)
        if not title or not tmdbid:
            return ""
        compact_title = re.sub(r"\s+", " ", title)[:160]
        target = f"{{[tmdbid={tmdbid};type={'movie' if media_type == 'movie' else 'tv'}"
        if media_type != "movie":
            target += f";s={season or 1}"
        target += "]}"
        return f"^{re.escape(compact_title)}$ => {target}"

    def _get_custom_identifiers(self) -> List[str]:
        """读取系统自定义识别词。"""
        data = SystemConfigOper().get(SystemConfigKey.CustomIdentifiers) or []
        return data if isinstance(data, list) else []

    def _append_custom_identifier_with_snapshot(self, identifier: str, issue_key: str = "") -> Dict[str, Any]:
        """创建快照后追加一条自定义识别词。"""
        identifier = str(identifier or "").strip()
        existing = self._get_custom_identifiers()
        snapshot_key = f"identifier_snapshot_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        self.save_data(snapshot_key, {"created_at": now_str(), "issue_key": issue_key, "identifiers": existing})
        if not identifier:
            return {"added": False, "message": "识别词为空", "snapshot_key": snapshot_key, "total_count": len(existing)}
        if identifier in existing:
            return {"added": False, "message": "识别词已存在", "snapshot_key": snapshot_key, "total_count": len(existing)}
        merged = existing + [identifier]
        SystemConfigOper().set(SystemConfigKey.CustomIdentifiers, merged)
        return {"added": True, "identifier": identifier, "snapshot_key": snapshot_key, "total_count": len(merged)}

    def _reflow_issue_to_candidate(self, issue: dict, status: str = "ready", reason: str = "识别异常已回流候选") -> Dict[str, Any]:
        """将识别异常回流到候选池，等待原下载决策链路处理。"""
        candidates = self._load_candidates()
        candidate = {k: v for k, v in issue.items() if k not in ("suggestion", "identifier_snapshot", "identifier_before", "identifier_after")}
        candidate["status"] = status
        candidate["reason"] = reason
        candidate["runtime_state"] = status
        candidate["runtime_status_text"] = reason
        candidate["reflowed_from_issue"] = True
        candidate["reflowed_at"] = now_str()
        candidate.setdefault("key", issue.get("key") or self._item_key(str(issue.get("title") or ""), str(issue.get("enclosure") or issue.get("link") or "")))
        chain = list(candidate.get("reason_chain") or [])
        if reason not in chain:
            chain.append(reason)
        candidate["reason_chain"] = chain
        candidates = [item for item in candidates if item.get("key") != candidate.get("key")]
        candidates.insert(0, candidate)
        self._save_candidates(candidates)
        return {"candidate": candidate, "candidate_count": len(candidates)}

    def _agent_issue_prompt(self, issue: dict) -> str:
        """构造智能体处理识别异常的提示文本。"""
        return (
            "请分析 BT订阅中心识别异常资源，目标是确认动漫/特摄媒体身份并生成窄作用域 MoviePilot 自定义识别词。\n"
            f"标题：{issue.get('title')}\n"
            f"描述：{str(issue.get('description') or '')[:500]}\n"
            f"当前识别：{issue.get('media_title') or '-'} / {issue.get('media_type') or '-'} / {issue.get('media_category') or '-'} / TMDB={issue.get('tmdbid') or '-'}\n"
            f"季集：S{issue.get('season') or 1} / E{issue.get('episodes') or []}\n"
            f"异常原因：{issue.get('issue_reason') or issue.get('reason') or '-'}\n"
            "要求：如果高置信确认目标，请生成包含原始标题上下文的窄作用域规则，不要生成宽泛裸词；写入前需要快照，写入后重扫并回流候选。"
        )

    def _record_failure_cooldown(self, stage: str, object_key: str, error: str) -> bool:
        """记录失败冷却指纹，不发送 MoviePilot 消息。"""
        cooldown_hours = max(1, to_int(getattr(self, "_failure_cooldown_hours", 24), 24))
        fingerprint = f"{stage}:{object_key}:{str(error)[:160]}"
        data = self.get_data("failure_cooldowns") or {}
        if not isinstance(data, dict):
            data = {}
        now = datetime.datetime.now()
        last_text = data.get(fingerprint)
        if last_text:
            try:
                last = datetime.datetime.strptime(last_text, "%Y-%m-%d %H:%M:%S")
                if (now - last).total_seconds() < cooldown_hours * 3600:
                    return False
            except Exception:
                pass
        data[fingerprint] = now.strftime("%Y-%m-%d %H:%M:%S")
        self.save_data("failure_cooldowns", data)
        return True

    def _record_failure_once(self, stage: str, object_key: str, error: str, title: str = "") -> bool:
        """记录失败状态到日志与冷却指纹，不发送 MoviePilot 消息。"""
        recorded = self._record_failure_cooldown(stage, object_key, error)
        if recorded:
            logger.warning(f"BT订阅中心失败：{stage} {title or object_key or '未知对象'} - {error}")
        return recorded

    def _failure_cooldown_summary(self) -> Dict[str, Any]:
        """返回失败冷却概要。"""
        data = self.get_data("failure_cooldowns") or {}
        return {"cooldown_hours": getattr(self, "_failure_cooldown_hours", 24), "fingerprints": len(data) if isinstance(data, dict) else 0}

    @staticmethod
    def _identifier_suggestion(issue: dict, meta: MetaInfo = None, mediainfo: MediaInfo = None) -> str:
        """生成保守的识别词处理建议。"""
        title = str(issue.get("title") or getattr(meta, "title", "") or "").strip()
        clean_title = re.sub(r"\s+", " ", title)
        tmdbid = getattr(mediainfo, "tmdb_id", None) if mediainfo else issue.get("tmdbid")
        if tmdbid and mediainfo and mediainfo.type == MediaType.TV:
            target = f"{{[tmdbid={tmdbid};type=tv;s={getattr(meta, 'begin_season', None) or issue.get('season') or 1}]}}"
            return f"建议人工确认目标后添加窄作用域绑定：`^{re.escape(clean_title[:80])}$ => {target}`。不要把它当真人订阅，也不要直接下载。"
        return "建议进入待处理：先用标题规范化/别名搜索确认动画目标，再生成窄作用域 TMDB/Bangumi 绑定识别词；确认前不下载、不建订阅。"

    def _decide_candidate(self, subscription: dict, candidate: dict, meta: MetaInfo) -> Dict[str, Any]:
        """判断候选是否可下载。"""
        if subscription.get("state") != "active":
            return {"status": "skipped", "reason": "订阅已暂停"}
        episodes = episodes_from_meta(meta)
        if not episodes:
            return {"status": "pending", "reason": "未识别集数，保留候选供人工确认"}
        downloaded = subscription.setdefault("downloaded", {})
        dup_eps = [ep for ep in episodes if str(ep) in downloaded]
        if dup_eps:
            return {"status": "skipped", "reason": f"集数 {dup_eps} 已记录下载，避免重复"}
        return {"status": "ready", "reason": "通过过滤和去重，可下载；发布组不阻塞，仅用于后续整季包收敛"}

    def _download_candidate(self, candidate: dict, meta: MetaInfo, mediainfo: MediaInfo) -> Tuple[bool, str, str]:
        """调用 MP 下载链路添加候选资源并返回下载 hash。"""
        torrentinfo = TorrentInfo(
            title=candidate.get("title"),
            description=candidate.get("description"),
            enclosure=candidate.get("enclosure"),
            page_url=candidate.get("link"),
            size=candidate.get("size"),
            pubdate=candidate.get("pubdate"),
            site_proxy=self._proxy,
        )
        try:
            download_chain = DownloadChain()
            download_chain.post_message = lambda *args, **kwargs: None
            download_hash, error_msg = download_chain.download_single(
                Context(meta_info=meta, media_info=mediainfo, torrent_info=torrentinfo),
                save_path=self._save_path,
                username=None,
                source="BTSubscribeCenter",
                return_detail=True,
            )
        except Exception as err:
            logger.error(f"BT订阅中心添加下载异常：{candidate.get('title')} - {err}")
            return False, "", str(err)
        download_hash = str(download_hash or "").strip()
        error_msg = str(error_msg or "").strip()
        if download_hash:
            self._mark_candidate_submitted(candidate, download_hash)
            return True, download_hash, ""
        return False, "", error_msg or "下载链路未返回任务 hash"

    def _mark_candidate_submitted(self, candidate: dict, download_hash: str) -> None:
        """给候选写入已提交下载的 hash 与运行时状态。"""
        candidate["download_hash"] = download_hash
        candidate["hash"] = download_hash
        candidate["status"] = "submitted"
        candidate["runtime_state"] = "submitted"
        candidate["runtime_status_text"] = "已提交下载，等待下载器/转移事实回写"
        candidate["downloaded_at"] = now_str()
        chain = list(candidate.get("reason_chain") or [])
        if "已提交下载并记录 hash" not in chain:
            chain.append("已提交下载并记录 hash")
        candidate["reason_chain"] = chain

    def _mark_candidate_download_failed(self, candidate: dict, error_msg: str) -> None:
        """给候选写入下载提交失败状态。"""
        candidate["status"] = "download_failed"
        candidate["runtime_state"] = "download_failed"
        candidate["runtime_status_text"] = error_msg or "添加下载失败"
        candidate["reason"] = error_msg or "添加下载失败"
        candidate["download_error"] = error_msg or "添加下载失败"
        candidate["failed_at"] = now_str()
        chain = list(candidate.get("reason_chain") or [])
        text = f"下载失败：{candidate['download_error']}"
        if text not in chain:
            chain.append(text)
        candidate["reason_chain"] = chain

    def _pre_filter(self, title: str, description: str, size: Any, pubdate: Any) -> str:
        """执行 RSS 初筛。"""
        text = f"{title} {description}"
        if self._include and not re.search(self._include, text, re.IGNORECASE):
            return "不符合包含规则"
        if self._exclude and re.search(self._exclude, text, re.IGNORECASE):
            return "命中排除规则"
        if self._size_range and size:
            try:
                ranges = [float(v) * 1024 ** 3 for v in self._size_range.split("-")]
                fsize = float(size)
                if len(ranges) == 1 and fsize < ranges[0]:
                    return "种子大小低于限制"
                if len(ranges) > 1 and not ranges[0] <= fsize <= ranges[1]:
                    return "种子大小不在范围内"
            except Exception:
                return "大小规则配置错误"
        return ""

    def _should_create_airing(self, meta: MetaInfo, mediainfo: MediaInfo, pubdate: Any) -> bool:
        """判断是否自动创建新番私有订阅。"""
        if not self._auto_discover_airing or mediainfo.type != MediaType.TV:
            return False
        episodes = episodes_from_meta(meta)
        if episodes and min(episodes) > self._early_episode_max:
            return False
        if pubdate and isinstance(pubdate, datetime.datetime):
            now = datetime.datetime.now(tz=pubdate.tzinfo) if pubdate.tzinfo else datetime.datetime.now()
            if (now - pubdate).days > self._airing_window_days:
                return False
        admission = self._resource_admission(meta=meta, mediainfo=mediainfo)
        return bool(admission.get("accepted"))

    def _resource_admission(self, meta: MetaInfo, mediainfo: MediaInfo) -> Dict[str, Any]:
        """判断可信 BT/RSS 来源资源是否应进入动漫/特摄订阅链路。"""
        category = str(getattr(mediainfo, "category", "") or "").lower()
        text = f"{getattr(meta, 'title', '')} {getattr(meta, 'subtitle', '')} {getattr(mediainfo, 'title', '')}".lower()
        anime_words = ["动漫", "动画", "anime", "animation", "番剧"]
        if any(word in category for word in anime_words):
            return {"accepted": True, "state": "anime", "reason": "MP 分类为动画/番剧"}
        if self._has_tokusatsu_hint(text):
            return {"accepted": True, "state": "tokusatsu", "reason": "标题命中特摄信号，按动漫源业务资源准入"}
        if self._has_anime_source_hint(text):
            return {"accepted": True, "state": "source_anime", "reason": "标题或发布信息命中动漫源信号"}
        conflict_words = ["综艺", "纪录", "国产剧", "欧美剧", "日韩剧", "真人"]
        if any(word in category for word in conflict_words):
            return {"accepted": False, "state": "recognition_conflict", "reason": "可信动漫源资源被 MP 识别为真人/剧集分类，需要智能体纠偏"}
        return {"accepted": True, "state": "trusted_source", "reason": "来自用户配置的可信动漫源，暂按候选准入"}

    @staticmethod
    def _has_anime_source_hint(text: str) -> bool:
        """判断标题是否包含常见动漫源信号。"""
        anime_hints = ["[ani]", "ani ", "baha", "bangumi", "dmhy", "lilith-raws", "nix-raws", "nc-raws", "喵萌", "桜都", "字幕组", "b-global", "cr web", "abema", "bilibili", "web-dl", "webrip"]
        return any(hint in text for hint in anime_hints)

    @staticmethod
    def _has_tokusatsu_hint(text: str) -> bool:
        """判断标题是否包含特摄系列信号。"""
        hints = [
            "假面骑士", "假面騎士", "kamen rider", "仮面ライダー",
            "奥特曼", "奧特曼", "ultraman", "ウルトラマン",
            "超级战队", "超級戰隊", "super sentai", "戦隊", "sentai",
            "牙狼", "garo", "布莱泽", "blazar", "德凯", "decker", "泽塔", "zett",
        ]
        return any(hint in text for hint in hints)

    def _is_anime_like(self, meta: MetaInfo, mediainfo: MediaInfo) -> bool:
        """兼容旧调用：返回资源准入是否通过。"""
        return bool(self._resource_admission(meta=meta, mediainfo=mediainfo).get("accepted"))

    def _new_subscription(self, sub_id: str, title: str, year: str, mtype: str, tmdbid: Optional[int], season: int, mode: str, group: str = "", mediainfo: Optional[MediaInfo] = None) -> dict:
        """创建私有订阅结构。"""
        poster = mediainfo.get_poster_image() if mediainfo else ""
        backdrop = mediainfo.get_backdrop_image() if mediainfo and hasattr(mediainfo, "get_backdrop_image") else ""
        overview = getattr(mediainfo, "overview", "") if mediainfo else ""
        total_episode = getattr(mediainfo, "number_of_episodes", 0) or 0 if mediainfo else 0
        return new_subscription(sub_id, title, year, mtype, tmdbid, season, mode, group, poster, backdrop, overview, total_episode)

    def _mark_downloaded(self, subscription: dict, candidate: dict, download_hash: str = "") -> None:
        """标记候选已提交下载并保存 hash。"""
        fact = self._download_fact_by_hash(download_hash) if download_hash else {}
        for ep in candidate.get("episodes") or []:
            record = {
                "title": candidate.get("title"),
                "group": candidate.get("group"),
                "time": now_str(),
                "hash": download_hash or candidate.get("download_hash") or "",
                "download_hash": download_hash or candidate.get("download_hash") or "",
                "state": fact.get("state") or "submitted",
                "status_text": fact.get("status_text") or "已提交下载，等待下载器/转移事实回写",
            }
            if fact:
                record.update(fact)
            subscription.setdefault("downloaded", {})[str(ep)] = record
        subscription["updated_at"] = now_str()

    def _candidate_base(self, key: str, title: str, description: str, source_url: str, enclosure: str, link: str, size: Any, pubdate: Any, group: str) -> dict:
        """构造候选基础字段。"""
        return {"key": key, "title": title, "description": description or "", "source_url": source_url, "enclosure": enclosure, "link": link, "size": size, "pubdate": self._format_pubdate(pubdate), "group": group, "created_at": now_str()}

    def _media_fields(self, meta: MetaInfo, mediainfo: MediaInfo, sub_id: str) -> dict:
        """构造媒体识别字段。"""
        return {"subscription_id": sub_id, "media_title": mediainfo.title, "year": mediainfo.year, "type": mediainfo.type.value, "tmdbid": mediainfo.tmdb_id, "season": meta.begin_season or 1, "episodes": episodes_from_meta(meta)}

    def _remember_candidate(self, candidates: List[dict], seen_keys: set, candidate: dict) -> None:
        """保存候选并去重。"""
        seen_keys.add(candidate.get("key"))
        candidates.insert(0, candidate)

    @staticmethod
    def _append_limited(items: List[dict], item: dict, limit: int) -> List[dict]:
        """追加并限制列表长度。"""
        small = {k: item.get(k) for k in ["key", "title", "group", "created_at", "status", "reason"]}
        return [small] + [i for i in items if i.get("key") != item.get("key")][:max(limit - 1, 0)]

    @staticmethod
    def _record_seen_group(subscription: dict, group: str) -> None:
        """记录订阅已出现的发布组统计。"""
        if not group:
            return
        seen = subscription.setdefault("seen_groups", {})
        current = seen.get(group) or {"count": 0, "last_seen": ""}
        current["count"] = int(current.get("count") or 0) + 1
        current["last_seen"] = now_str()
        seen[group] = current
        subscription["updated_at"] = now_str()

    def _set_subscription_state(self, sub_id: str, state: str) -> schemas.Response:
        """设置私有订阅状态。"""
        subs = self._load_subscriptions()
        if sub_id not in subs:
            return schemas.Response(success=False, message="订阅不存在")
        subs[sub_id]["state"] = state
        subs[sub_id]["updated_at"] = now_str()
        self._save_subscriptions(subs)
        return schemas.Response(success=True, message="状态已更新", data=subs[sub_id])


    @staticmethod
    def _public_candidates(items: List[dict]) -> List[dict]:
        """返回前端候选列表所需字段，避免首页传输过多内部上下文。"""
        keys = {
            "key", "title", "subtitle", "site", "site_name", "group", "status", "runtime_state",
            "runtime_status_text", "reason", "reason_chain", "subscription_id", "tmdbid", "year",
            "type", "season", "episodes", "episode", "size", "free_state", "publish_time",
            "source_url", "download_hash", "download_error", "failed_at", "created_at", "updated_at",
            "media_title", "media_name", "poster", "backdrop", "vote_average", "recognition_status",
            "admission_status", "admission_reason", "replacement_for", "replacement_state"
        }
        result = []
        for item in items or []:
            if not isinstance(item, dict):
                continue
            result.append({k: item.get(k) for k in keys if k in item})
        return result

    @staticmethod
    def _public_issues(items: List[dict]) -> List[dict]:
        """返回前端识别异常列表所需字段，隐藏冗余内部字段。"""
        keys = {
            "key", "title", "subtitle", "site", "site_name", "status", "reason", "suggestion",
            "created_at", "updated_at", "tmdbid", "doubanid", "season", "episodes", "type",
            "media_title", "media_name", "confidence", "identifier", "candidate_key"
        }
        result = []
        for item in items or []:
            if not isinstance(item, dict):
                continue
            result.append({k: item.get(k) for k in keys if k in item})
        return result

    def _stats(self) -> Dict[str, int]:
        """统计运行状态。"""
        candidates = self._load_candidates()
        subs = self._normalize_subscriptions(self._load_subscriptions(), candidates)
        downloaded = sum(completed_count(sub) for sub in subs.values())
        lack = sum(lack_count(sub) for sub in subs.values())
        pending = sum(1 for item in candidates if item.get("status") == "pending")
        return {"subscriptions": len(subs), "candidates": len(candidates), "downloaded": downloaded, "lack": lack, "pending": pending, "recognition_issues": len(self._load_recognition_issues())}

    def _load_native_mappings(self) -> Dict[str, dict]:
        """读取 历史原生订阅映射。"""
        return BTSubscribeStore(self).load_native_mappings()

    def _save_native_mappings(self, data: Dict[str, dict]) -> None:
        """保存 历史原生订阅映射。"""
        BTSubscribeStore(self).save_native_mappings(data)

    def _load_recognition_issues(self) -> List[dict]:
        """读取识别异常队列。"""
        return BTSubscribeStore(self).load_recognition_issues()

    def _save_recognition_issues(self, data: List[dict]) -> None:
        """保存识别异常队列。"""
        BTSubscribeStore(self).save_recognition_issues(data, self._recognition_issue_limit)

    def _load_subscriptions(self) -> Dict[str, dict]:
        """读取私有订阅并补齐 MP 风格展示字段。"""
        data = BTSubscribeStore(self).load_subscriptions()
        changed = False
        for key, value in list(data.items()):
            before = dict(value) if isinstance(value, dict) else {}
            data[key] = self._normalize_subscription(value)
            if before != data[key]:
                changed = True
        if changed:
            BTSubscribeStore(self).save_subscriptions(data)
        return data

    def _save_subscriptions(self, data: Dict[str, dict]) -> None:
        """保存私有订阅。"""
        BTSubscribeStore(self).save_subscriptions(data)

    def _load_candidates(self) -> List[dict]:
        """读取候选资源。"""
        return BTSubscribeStore(self).load_candidates()

    def _save_candidates(self, data: List[dict]) -> None:
        """保存候选资源。"""
        BTSubscribeStore(self).save_candidates(data, self._candidate_limit)

    @staticmethod
    def _item_key(title: str, url: str) -> str:
        """生成 RSS 条目去重键。"""
        return f"{title}|{url}"[:500]

    @staticmethod
    def _format_pubdate(pubdate: Any) -> str:
        """格式化发布时间。"""
        if isinstance(pubdate, datetime.datetime):
            return pubdate.strftime("%Y-%m-%d %H:%M:%S")
        return str(pubdate or "")

    @staticmethod
    def _minutes_since(time_str: str) -> float:
        """计算距离指定时间的分钟数。"""
        try:
            dt = datetime.datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
            return (datetime.datetime.now() - dt).total_seconds() / 60
        except Exception:
            return 0

    def _default_config(self) -> Dict[str, Any]:
        """返回默认配置。"""
        return {"enabled": False, "cron": "*/30 * * * *", "onlyonce": False, "proxy": False, "rss_urls": "", "include": "", "exclude": "", "size_range": "", "save_path": "", "auto_discover_airing": True, "airing_window_days": 45, "early_episode_max": 3, "auto_download": False, "recognition_issue_limit": 200, "candidate_limit": 200, "history_limit": 300, "cleanup_after_library": True, "replacement_watch_enabled": True, "replacement_check_minutes": 30, "failure_cooldown_hours": 24}

    def _normalize_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """合并默认配置并清理字符串字段，保证旧配置迁移后可直接使用。"""
        normalized = self._default_config()
        normalized.update(config or {})
        for key in ["cron", "rss_urls", "include", "exclude", "size_range", "save_path"]:
            normalized[key] = str(normalized.get(key) or "").strip()
        return normalized

    def _current_config(self) -> Dict[str, Any]:
        """返回当前配置。"""
        return self._normalize_config(self._safe_config())

    def _safe_config(self) -> Dict[str, Any]:
        """返回当前配置快照。"""
        return {
            "enabled": self._enabled,
            "cron": self._cron,
            "onlyonce": self._onlyonce,
            "proxy": self._proxy,
            "rss_urls": self._rss_urls,
            "include": self._include,
            "exclude": self._exclude,
            "size_range": self._size_range,
            "save_path": self._save_path,
            "auto_discover_airing": self._auto_discover_airing,
            "airing_window_days": self._airing_window_days,
            "early_episode_max": self._early_episode_max,
            "auto_download": self._auto_download,
            "recognition_issue_limit": self._recognition_issue_limit,
            "candidate_limit": self._candidate_limit,
            "history_limit": self._history_limit,
            "cleanup_after_library": self._cleanup_after_library,
            "replacement_watch_enabled": self._replacement_watch_enabled,
            "replacement_check_minutes": self._replacement_check_minutes,
            "failure_cooldown_hours": self._failure_cooldown_hours,
        }
