"""
QBRawGuard 主流程编排模块。

职责：
1. 编排定时扫描、DownloadAdded 事件处理、命中处理、删除清理和删除结果确认。
2. 不定义 MoviePilot 插件生命周期，不构建 UI，不直接拼通知正文。
3. 所有原盘命中必须来自下载器真实文件列表经 matcher 判定后的结果，标题预检只能用于快速扫描降噪。
"""

import time
from datetime import datetime
from typing import Any, List

from app.log import logger

from .cleaner import cleanup_by_hash
from .rescan import enqueue_rescan, torrent_gone


def scan(plugin: Any, mode: str = "fast") -> None:
    """执行快速拦截或全量兜底扫描。"""
    is_fast = mode == "fast"
    label = "快速拦截" if is_fast else "全量兜底"
    start = time.time()
    total = checked = hits = 0
    hit_names: List[str] = []
    try:
        services_dict = plugin._services()
        if not services_dict:
            plugin._add_oplog(label, 0, 0, 0, 0, err="无可用下载器")
            logger.warning(f"{plugin.plugin_name} {label} 无可用 QB 下载器")
            return
        for downloader, service in services_dict.items():
            torrents, err = service.instance.get_torrents()
            if err:
                logger.warning(f"{plugin.plugin_name} 获取 {downloader} 种子列表失败：{err}")
                continue
            for torrent in torrents or []:
                h = plugin._val(torrent, "hash", "hashString")
                name = plugin._val(torrent, "name", "title") or ""
                if not h or plugin._skip(torrent):
                    continue
                with plugin._lock:
                    if plugin._processed_ok(h, present=True):
                        continue
                total += 1
                if is_fast and not plugin._suspect_name(name):
                    continue
                if not is_fast:
                    with plugin._lock:
                        if str(h).lower() in plugin._survivors:
                            continue
                checked += 1
                try:
                    files = plugin._file_names(service, h, downloader)
                    if not files:
                        logger.debug(f"{plugin.plugin_name} {label} 跳过文件列表未就绪任务：{plugin._short_name(name)}")
                        continue
                    matched = plugin._match(files)
                    if matched:
                        hits += 1
                        hit(plugin, downloader, service, torrent, matched)
                        hit_names.append(name)
                    else:
                        with plugin._lock:
                            plugin._mark_nonsuspect(h, name)
                except Exception as err:
                    logger.error(f"{plugin.plugin_name} {label} 异常 [{plugin._short_name(name)}]: {err}")
    except Exception as err:
        logger.error(f"{plugin.plugin_name} {label} 严重异常：{err}")
    finally:
        elapsed = time.time() - start
        plugin._add_oplog(
            label, total, checked, hits, elapsed,
            err="" if total > 0 else "无待检任务",
            hit_names=hit_names if hit_names else None,
        )


def handle_download_added(plugin: Any, event: Any) -> None:
    """处理 MoviePilot DownloadAdded 事件。"""
    if not plugin.enabled:
        return
    h = event.event_data.get("hash")
    if not h:
        return
    with plugin._lock:
        if plugin._processed_ok(h, present=True):
            return
    downloader = event.event_data.get("downloader")
    service = plugin._get_service(downloader)
    if not service:
        return
    try:
        files = plugin._file_names_with_retry(service, h, downloader)
        if not files:
            logger.debug(f"{plugin.plugin_name} 事件触发后文件列表仍未就绪，等待定时扫描兜底：{h[:8]}")
            return
        matched = plugin._match(files)
        if not matched:
            return
        torrents, err = service.instance.get_torrents(ids=h)
        if err or not torrents:
            return
        hit(plugin, downloader, service, torrents[0], matched)
    except Exception as err:
        logger.error(f"{plugin.plugin_name} 事件处理异常：{err}")


def hit(plugin: Any, downloader: str, service: Any, torrent: Any, matched: List[str]) -> None:
    """处理命中原盘结构后的动作。"""
    h = str(plugin._val(torrent, "hash", "hashString") or "").lower()
    name = plugin._val(torrent, "name", "title") or h
    with plugin._lock:
        if h in plugin._cleaning:
            return
        plugin._cleaning.add(h)
    if plugin.action == "delete":
        plugin._record(h, downloader, name, matched, False)
        full_cleanup(plugin, downloader, h, name, matched)
    else:
        ok = bool(plugin.chain.stop_torrents(hashs=[h], downloader=downloader))
        if plugin.tag:
            try:
                plugin.chain.set_torrents_tag(hashs=[h], tags=[plugin.tag], downloader=downloader)
            except Exception:
                pass
        plugin._record(h, downloader, name, matched, ok)
        with plugin._lock:
            plugin._cleaning.discard(h)
    if plugin.notify:
        plugin._notify(downloader, name, matched, torrent)


def full_cleanup(plugin: Any, downloader: str, h: str, name: str, matched: List[str]) -> None:
    """复用 MP Chain 与整理记录删除语义清理命中任务。"""
    try:
        try:
            plugin.chain.stop_torrents(hashs=[h], downloader=downloader)
        except Exception as err:
            logger.debug(f"{plugin.plugin_name} 删除前暂停任务失败：{err}")

        clean_result = cleanup_by_hash(h, delete_src=False, delete_dest=True, eventmanager=plugin.eventmanager)
        media_deleted = clean_result.total
        logger.info(
            f"{plugin.plugin_name} MP侧清理：转移记录 {clean_result.transfer_records}，"
            f"媒体库文件 {clean_result.dest_files}，下载历史 {clean_result.download_histories}，"
            f"下载文件记录 {clean_result.download_files}"
        )
        for err in clean_result.errors[:3]:
            logger.warning(f"{plugin.plugin_name} MP侧清理异常：{err}")

        enqueue_rescan(plugin, downloader, h, name)

        try:
            plugin.chain.remove_torrents(hashs=[h], delete_file=True, downloader=downloader)
        except Exception as err:
            logger.warning(f"{plugin.plugin_name} 删除下载器任务异常：{err}")

        time.sleep(2)
        deleted = torrent_gone(plugin, downloader, h)
        if not deleted:
            logger.warning(f"{plugin.plugin_name} 删除后任务仍存在，将保留失败状态等待下次重试：{plugin._short_name(name)}")

        with plugin._lock:
            if h in plugin.processed:
                plugin.processed[h]["ok"] = deleted and not clean_result.errors
                plugin.processed[h]["media_deleted"] = media_deleted
                plugin.processed[h]["time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                if not deleted:
                    plugin.processed[h]["err"] = "删除后任务仍在下载器中"
                elif clean_result.errors:
                    plugin.processed[h]["err"] = "; ".join(clean_result.errors[:2])
                else:
                    plugin.processed[h].pop("err", None)
                plugin.save_data("processed", plugin.processed)
            plugin._cleaning.discard(h)
            plugin._add_oplog("彻底清理", 0, 0, 0, media_deleted, sample=plugin._short_name(name))
    except Exception as err:
        logger.error(f"{plugin.plugin_name} 彻底清理异常 [{plugin._short_name(name)}]: {err}")
        with plugin._lock:
            plugin._cleaning.discard(h)



