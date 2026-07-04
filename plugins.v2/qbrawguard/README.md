# 原盘通知（QBRawGuard）

基于 MoviePilot 下载器链路的原盘格式拦截插件，用于识别并处理 Emby/Jellyfin/Plex 等媒体库通常无法直接友好播放或刮削的原盘结构。

## 核心能力

- **真实文件列表判定**：通过 MoviePilot 下载器 Chain 获取下载器返回的真实文件列表，不依赖种子标题猜测。
- **事件驱动拦截**：监听 `DownloadAdded` 事件，新任务加入后短轮询等待文件列表就绪并及时处理。
- **定时兜底扫描**：快速拦截与全量兜底可独立启停，避免事件漏网。
- **原盘结构识别**：覆盖 ISO/IMG 镜像、BDMV/CERTIFICATE、VIDEO_TS、HVDVD_TS、VCD/SVCD 等结构。
- **安全清理**：删除模式下按 `download_hash` 精确关联 MoviePilot 转移记录和下载历史，避免按标题误删同名媒体。
- **通知推送**：复用 MoviePilot 原生通知链路，可选择智能体/插件等通知场景。

## 识别边界

会拦截：

- `*.iso`、`*.img`、`*.nrg` 等光盘镜像；
- `BDMV/`、`CERTIFICATE/`、`VIDEO_TS/`、`HVDVD_TS/` 等原盘目录；
- BDMV 结构内的 `.m2ts` / `.ssif` 文件。

会放行：

- 普通 Web/HDTV 单文件封装，例如 `.mkv`、`.mp4`、`.ts`；
- 扁平目录下的普通 `.m2ts` 流媒体封装。

## 推荐配置

1. 先启用插件并选择要监控的下载器。
2. 初期建议动作设为 **暂停并打标签**，确认命中准确后再切换为 **删除任务及源文件**。
3. 保持事件驱动与快速拦截开启；全量兜底可按机器性能和任务量决定是否开启。
4. 删除模式会清理关联的下载器任务、源文件、转移记录和媒体库目标文件，请确认路径映射正常后使用。

## 模块说明

- `__init__.py`：MoviePilot 插件入口、生命周期、API、调度器和委托包装。
- `orchestrator.py`：扫描、事件处理、命中处理、删除清理编排。
- `downloader.py`：通过 MoviePilot Chain 获取下载器真实文件列表并执行下载器动作。
- `matcher.py`：原盘判定纯函数。
- `cleaner.py`：按 `download_hash` 精确清理 MoviePilot 侧记录和文件。
- `notifier.py`：通知内容构造。
- `ui.py`：MoviePilot Vuetify JSON 页面和配置表单。
- `status.py`：运行状态与健康检查。
- `constants.py` / `models.py` / `utils.py`：常量、数据结构与通用工具。

## 维护约束

- 原盘命中必须来自下载器真实文件列表，标题预检只能用于降低扫描范围。
- 自动删除只能按 `download_hash` 精确关联，不允许按片名/年份猜测媒体库文件后删除。
- 普通 `.ts` 和扁平 `.m2ts` 不应被当作原盘。

更多维护细节见 [`README_AGENT.md`](./README_AGENT.md)。
