# QBRawGuard AI 维护导航

本插件目标：基于 qBittorrent 返回的真实文件列表识别 ISO / BDMV / DVD / HD DVD / VCD 等 Emby 不友好的原盘结构，并按配置暂停或删除下载任务，同时清理 MoviePilot 侧可能产生的入库痕迹。

## 当前模块地图

- `__init__.py`：MoviePilot 插件入口、生命周期、事件、调度器、当前主流程编排和 UI。后续应继续瘦身。
- `constants.py`：默认配置、标题预检提示词、原盘结构正则、版本号。
- `models.py`：跨模块数据结构，后续拆分时优先补充和复用。
- `downloader.py`：通过 MoviePilot Chain 读取下载器返回的真实文件列表，兼容字段并在事件触发时短轮询等待文件列表就绪。
- `matcher.py`：原盘判定纯函数，只根据下载器真实文件列表返回命中证据；普通 Web/HDTV 的单文件 `.ts`、扁平 `.m2ts` 应放行。
- `cleaner.py`：按 download_hash 精确复用 MP 整理记录删除语义，清理转移记录、媒体库目标文件和下载历史；不按标题猜测删除媒体库。
- `utils.py`：通用字段读取、文本清洗、大小/时间格式化、标题预检、通知图片兜底。
- `notifier.py`：通知类型映射、原盘格式归纳、脱敏依据、下载通知样式正文构造。
- `status.py`：插件健康检查构造，只读探测下载器、通知通道、识别规则和历史命中。

## AI 优先阅读顺序

1. 先读本文件确认模块边界。
2. 读 `__init__.py` 的 `on_download_added()`、`_scan()`、`_hit()` 理解当前主链路。
3. 判定误报/漏报时读 `constants.py` 与 `matcher.py`。
4. 清理问题读 `cleaner.py` 和 `__init__.py` 的 `_full_cleanup()`；自动清理只按 download_hash 精确关联。
5. 通知问题读 `notifier.py` 和 `__init__.py` 的 `_notify()`；发送动作通过 `_PluginBase.post_message()` 复用 MP 原生通知链路。
6. UI 问题读 `ui.py`，入口 `__init__.py` 只保留 `get_page()` / `get_form()` 委托。

## 当前主链路

```text
DownloadAdded 事件 / QBRawGuardFast 定时扫描
→ downloader.get_file_names_from_chain()/get_file_names_from_chain_with_retry() 通过 MP Chain 获取下载器真实文件列表
→ matcher.match_raw_disc()
→ _hit()
→ stop 或 delete
→ cleaner.cleanup_by_hash() 按 MP 原生整理删除语义清理 MP 侧记录和媒体库目标文件
→ post_message() 发送通知
```

## 后续拆分目标

为了方便 AI 定位和维护，后续建议继续拆成：

- `orchestrator.py`：事件/定时扫描/命中处理的显式编排层。
- `downloader.py`：qBittorrent 获取文件、暂停、删除任务封装。
- `cleaner.py`：转移历史、下载历史、媒体库文件清理。
- `rescan.py`：延迟回扫队列。
- `notifier.py`：通知类型映射、通知内容构造和脱敏；不直接发送通知，发送必须走 `_PluginBase.post_message()`。
- `status.py`：下载器、通知、调度器等健康检查。
- `ui.py`：Vuetify JSON 页面与配置表单。

## 维护边界

- `downloader.py` 禁止根据种子名判定原盘，只能通过 MP Chain 返回真实文件列表。
- `matcher.py` 禁止操作下载器、删除文件、发送通知；禁止把普通 Web/HDTV 单文件 `.ts` 当原盘拦截。
- `cleaner.py` 自动删除只能按 download_hash 精确关联；禁止通过种子名/标题猜测媒体库内容后自动删除。
- `constants.py` 禁止访问运行时状态。
- `models.py` 禁止引入 MoviePilot 重型依赖。
- `__init__.py` 新增复杂逻辑前，应优先考虑是否属于 downloader / cleaner / notifier / ui / status。

## 已移除的风险路径

- 旧的按种子名提取标题/年份自动删除媒体库逻辑已移除。
- 自动清理只能按 `download_hash` 关联的 TransferHistory / DownloadHistory 执行。
- 如需兜底查媒体库，只能做只读提示，不应自动删除。
