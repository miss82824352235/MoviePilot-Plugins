"""BT订阅中心持久化访问。"""

from typing import Any, Dict, List


class BTSubscribeStore:
    """插件数据读写封装。"""

    def __init__(self, plugin: Any):
        """初始化存储封装。"""
        self.plugin = plugin

    def load_subscriptions(self) -> Dict[str, dict]:
        """读取私有订阅。"""
        data = self.plugin.get_data("subscriptions") or {}
        return data if isinstance(data, dict) else {}

    def save_subscriptions(self, data: Dict[str, dict]) -> None:
        """保存私有订阅。"""
        self.plugin.save_data("subscriptions", data)

    def load_candidates(self) -> List[dict]:
        """读取候选资源。"""
        data = self.plugin.get_data("candidates") or []
        return data if isinstance(data, list) else []

    def save_candidates(self, data: List[dict], limit: int) -> None:
        """保存候选资源。"""
        self.plugin.save_data("candidates", data[:max(limit, 20)])

    def load_native_mappings(self) -> Dict[str, dict]:
        """读取 RSS-only 原生订阅映射。"""
        data = self.plugin.get_data("native_mappings") or {}
        return data if isinstance(data, dict) else {}

    def save_native_mappings(self, data: Dict[str, dict]) -> None:
        """保存 RSS-only 原生订阅映射。"""
        self.plugin.save_data("native_mappings", data)

    def load_recognition_issues(self) -> List[dict]:
        """读取识别异常队列。"""
        data = self.plugin.get_data("recognition_issues") or []
        return data if isinstance(data, list) else []

    def save_recognition_issues(self, data: List[dict], limit: int = 200) -> None:
        """保存识别异常队列。"""
        self.plugin.save_data("recognition_issues", data[:max(limit, 20)])
