"""
QBRawGuard MoviePilot 原生清理模块。

职责：
1. 只处理 MoviePilot 侧的转移历史、媒体库目标文件、下载历史等记录清理。
2. 清理语义尽量对齐 MP 媒体整理页面“删除整理记录”的后端实现，避免插件自造专用删除链路。
3. 自动清理只按 download_hash 精确关联，不根据种子名猜标题去删除媒体库内容，降低误删风险。
4. 下载器任务和源文件优先交给 MoviePilot 下载器 Chain 的 remove_torrents(delete_file=True) 处理；只有明确 delete_src=True 时才删除 src_fileitem。
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, List

from app.chain.storage import StorageChain
from app.core.event import EventManager
from app.db.downloadhistory_oper import DownloadHistoryOper
from app.db.models.downloadhistory import DownloadFiles
from app.db.transferhistory_oper import TransferHistoryOper
from app.log import logger
from app.schemas.file import FileItem
from app.schemas.types import EventType


@dataclass
class CleanResult:
    """MoviePilot 侧清理结果。"""

    transfer_records: int = 0
    dest_files: int = 0
    src_files: int = 0
    download_histories: int = 0
    download_files: int = 0
    errors: List[str] = field(default_factory=list)

    @property
    def total(self) -> int:
        """返回清理动作总数。"""
        return self.transfer_records + self.dest_files + self.src_files + self.download_histories + self.download_files


def _history_id(history: Any) -> Any:
    """读取整理历史 ID。"""
    return getattr(history, "id", None) or (history.get("id") if isinstance(history, dict) else None)


def _fileitem_path(fileitem: Any) -> str:
    """读取 FileItem 字典或对象中的路径。"""
    if not fileitem:
        return ""
    if isinstance(fileitem, dict):
        return str(fileitem.get("path") or "")
    return str(getattr(fileitem, "path", "") or "")


def _to_fileitem(fileitem: Any) -> FileItem:
    """将序列化文件对象转换为 FileItem。"""
    if isinstance(fileitem, FileItem):
        return fileitem
    return FileItem(**fileitem)


def delete_transfer_history_like_mp(
    history: Any,
    storage_chain: StorageChain,
    transfer_oper: TransferHistoryOper,
    eventmanager: EventManager,
    delete_src: bool = False,
    delete_dest: bool = True,
) -> CleanResult:
    """按 MP 删除整理记录语义删除单条整理历史及关联文件。"""
    result = CleanResult()
    hid = _history_id(history)
    download_hash = getattr(history, "download_hash", "") or ""
    src = getattr(history, "src", "") or ""

    try:
        if delete_dest and getattr(history, "dest_fileitem", None):
            dest_fileitem = _to_fileitem(history.dest_fileitem)
            if storage_chain.delete_media_file(dest_fileitem):
                result.dest_files += 1

        if delete_src and getattr(history, "src_fileitem", None):
            src_fileitem = _to_fileitem(history.src_fileitem)
            if storage_chain.delete_media_file(src_fileitem):
                result.src_files += 1
            src_path = Path(src_fileitem.path).as_posix()
            DownloadFiles.delete_by_fullpath(transfer_oper._db, src_path)
            result.download_files += 1
            eventmanager.send_event(EventType.DownloadFileDeleted, {"src": src or src_fileitem.path, "hash": download_hash})

        if hid is not None:
            transfer_oper.delete(hid)
            result.transfer_records += 1
    except Exception as err:
        message = f"删除整理记录失败 id={hid}: {err}"
        logger.warning(f"原盘通知 {message}")
        result.errors.append(message)
    return result


def cleanup_by_hash(
    download_hash: str,
    delete_src: bool = False,
    delete_dest: bool = True,
    delete_download_history: bool = True,
    eventmanager: EventManager = None,
) -> CleanResult:
    """按 download_hash 精确清理 MP 侧整理记录、媒体库文件和下载历史。"""
    result = CleanResult()
    if not download_hash:
        return result

    transfer_oper = TransferHistoryOper()
    download_oper = DownloadHistoryOper()
    storage_chain = StorageChain()
    eventmanager = eventmanager or EventManager()

    histories = transfer_oper.list_by_hash(download_hash) or []
    for history in histories:
        one = delete_transfer_history_like_mp(
            history=history,
            storage_chain=storage_chain,
            transfer_oper=transfer_oper,
            eventmanager=eventmanager,
            delete_src=delete_src,
            delete_dest=delete_dest,
        )
        result.transfer_records += one.transfer_records
        result.dest_files += one.dest_files
        result.src_files += one.src_files
        result.download_files += one.download_files
        result.errors.extend(one.errors)

    if delete_download_history:
        try:
            history = download_oper.get_by_hash(download_hash)
            if history:
                download_oper.delete_history(history.id)
                result.download_histories += 1
        except Exception as err:
            message = f"删除下载历史失败 hash={download_hash[:8]}: {err}"
            logger.warning(f"原盘通知 {message}")
            result.errors.append(message)

    return result
