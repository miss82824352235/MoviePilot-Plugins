
"""
QBRawGuard 自动延迟回扫模块。

职责：
1. 维护 delete 模式下的残留回扫队列。
2. 在下载器任务确认消失后，按 download_hash 继续清理 MP 异步整理残留。
3. 不做原盘判定，不直接处理命中扫描，不按标题猜测删除媒体库文件。
"""

import time
from typing import Any

from app.log import logger

from .cleaner import cleanup_by_hash


def torrent_gone(plugin: Any, downloader: str, h: str) -> bool:
    """确认任务是否已从下载器消失。"""
    try:
        torrents = plugin.chain.list_torrents(hashs=[h], downloader=downloader, include_all_tags=True)
        return not torrents
    except Exception as err:
        logger.warning(f"{plugin.plugin_name} 删除结果确认异常：{err}")
        return False

def enqueue_rescan(plugin: Any, downloader: str, h: str, name: str) -> None:
    """将删除任务加入自动延迟回扫队列。"""
    now = time.time()
    with plugin._lock:
        queue = getattr(plugin, "_rescan_queue", {}) or {}
        item = queue.get(h) or {}
        queue[h] = {
            "downloader": downloader,
            "name": name,
            "first_ts": item.get("first_ts") or now,
            "last_ts": item.get("last_ts") or 0,
            "rounds": int(item.get("rounds") or 0),
            "empty_rounds": int(item.get("empty_rounds") or 0),
        }
        plugin._rescan_queue = queue
        plugin.save_data("rescan_queue", queue)


def run_orphan_rescan(plugin: Any) -> None:
    """执行自动延迟回扫，清理删除任务的异步整理残留。"""
    queue = dict(getattr(plugin, "_rescan_queue", {}) or {})
    if not queue:
        return
    now = time.time()
    changed = False
    cleaned_total = 0
    errors = []
    for h, item in list(queue.items()):
        downloader = item.get("downloader") or ""
        name = item.get("name") or h
        rounds = int(item.get("rounds") or 0)
        first_ts = float(item.get("first_ts") or now)
        # 多轮递增节奏：30s/90s/180s/300s/600s/900s，兼顾异步整理和性能。
        delays = [30, 90, 180, 300, 600, 900]
        delay = delays[min(rounds, len(delays) - 1)]
        if now - float(item.get("last_ts") or 0) < delay:
            continue
        if not torrent_gone(plugin, downloader, h):
            logger.debug(f"{plugin.plugin_name} 回扫跳过仍在下载器中的任务：{plugin._short_name(name)}")
            item["last_ts"] = now
            item["rounds"] = rounds + 1
            queue[h] = item
            changed = True
            continue
        result = plugin._cleanup_by_hash(h, delete_src=True, delete_dest=True)             if hasattr(plugin, "_cleanup_by_hash") else None
        if result is None:
            result = cleanup_by_hash(h, delete_src=True, delete_dest=True, eventmanager=plugin.eventmanager)
        cleaned_total += result.total
        errors.extend(result.errors)
        item["last_ts"] = now
        item["rounds"] = rounds + 1
        item["empty_rounds"] = 0 if result.total else int(item.get("empty_rounds") or 0) + 1
        # 连续两轮无残留、超过 60 分钟或达到最大轮数后出队。
        if item["empty_rounds"] >= 2 or now - first_ts > 3600 or item["rounds"] >= len(delays):
            queue.pop(h, None)
            logger.info(f"{plugin.plugin_name} 自动回扫出队：{plugin._short_name(name)}，本轮清理 {result.total} 项")
        else:
            queue[h] = item
            logger.info(f"{plugin.plugin_name} 自动回扫：{plugin._short_name(name)}，清理 {result.total} 项，等待后续轮次")
        changed = True
    if changed:
        with plugin._lock:
            plugin._rescan_queue = queue
            plugin.save_data("rescan_queue", queue)
        if cleaned_total or errors:
            plugin._add_oplog("自动回扫", 0, 0, 0, cleaned_total, sample="rescan", err="; ".join(errors[:2]))

