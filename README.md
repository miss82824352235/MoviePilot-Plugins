### MoviePilot-Plugins 本仓库地址

```
https://github.com/miss82824352235/MoviePilot-Plugins/
```

## 插件详解

### 1. 原盘通知 (QBRawGuard) v2.6.1

智能拦截 BDMV / ISO / DVD 原盘种子，事件驱动秒级响应 + 定时扫描兜底；命中后联动清理下载文件与入库记录，杜绝 Emby 无法播放的媒体污染。

#### 功能特性

- **事件驱动**：DownloadAdded 事件秒级拦截，不受标题预检限制
- **快速拦截**：标题预检 → 文件结构正则匹配 → 命中处理
- **全量兜底**：低频补漏扫描，可独立开关
- **延迟回扫**：清理拦截后异步产生的孤儿入库记录
- **四件套联动清理**：下载任务 → 源文件 → 转移记录 → 媒体库文件

#### 拦截范围

- BDMV 原盘目录结构（BDMV/、CERTIFICATE/ 等）
- ISO / IMG 光盘镜像
- DVD / HD DVD / VCD 原盘结构
- BDMV 目录下的 m2ts / ssif 流文件（精准识别，不误判 WEB-DL 的独立 .m2ts）

### 2. Bangumi每日放送

用于把 Bangumi 的每日放送数据转成可视化海报页面，方便用户快速挑选新番并添加到 MoviePilot 订阅中。

#### 适用场景

- 想每天浏览当日或次日的 Bangumi 放送内容
- 想把新番订阅流程从"手动搜索"简化为"看海报后一键订阅"
- 想结合站点、分辨率、规则组等参数自动完成订阅注入

### 3. 豆瓣将映魔改版

用于监控豆瓣即将开播电视剧，在热度满足阈值时自动添加订阅，并在开播前发送提醒。

#### 适用场景

- 想提前锁定高热度即将开播新剧
- 想在开播前收到提醒，而不是等剧集开始更新后再处理
- 想用"热度阈值 + 提前订阅窗口"减少操作

## 参考与致谢

- [MoviePilot](https://github.com/jxxghp/MoviePilot) — 感谢 jxxghp 提供卓越的开源家庭媒体管理平台
- [MoviePilot V2 插件开发文档](https://github.com/jxxghp/MoviePilot-Plugins/blob/main/docs/V2_Plugin_Development.md) — V2 插件结构、`_PluginBase`、表单/页面/API 开发规范
- [PR #5687](https://github.com/jxxghp/MoviePilot/pull/5687) — 原盘格式检测与下载拦截的实现思路参考
- [InfinityPacer/MoviePilot-Plugins](https://github.com/InfinityPacer/MoviePilot-Plugins) — 插件市场规范与 package.v2.json 字段标准参考
- [luanyi143/MoviePilot-Plugins](https://github.com/luanyi143/MoviePilot-Plugins) — 本仓库 Fork 来源，提供 Bangumi 与豆瓣插件

## License

仓库许可协议见 [`LICENSE`](./LICENSE)。
