### 本仓库地址

```
https://github.com/miss82824352235/MoviePilot-Plugins/
```

## 原盘通知 (QBRawGuard) v2.6.1

智能拦截 BDMV / ISO / DVD 原盘种子，事件驱动秒级响应 + 定时扫描兜底；命中后联动清理下载文件与入库记录，杜绝 Emby 无法播放的媒体污染。

### 功能特性

- **事件驱动**：DownloadAdded 事件秒级拦截，不受标题预检限制
- **快速拦截**：标题预检 → 文件结构正则匹配 → 命中处理
- **全量兜底**：低频补漏扫描，可独立开关
- **延迟回扫**：清理拦截后异步产生的孤儿入库记录
- **四件套联动清理**：下载任务 → 源文件 → 转移记录 → 媒体库文件

### 拦截范围

- BDMV 原盘目录结构（BDMV/、CERTIFICATE/ 等）
- ISO / IMG 光盘镜像
- DVD / HD DVD / VCD 原盘结构
- BDMV 目录下的 m2ts / ssif 流文件（精准识别，不误判 WEB-DL 的独立 .m2ts）

## 参考与致谢

- [MoviePilot](https://github.com/jxxghp/MoviePilot) — 感谢 jxxghp 提供卓越的开源家庭媒体管理平台
- [MoviePilot V2 插件开发文档](https://github.com/jxxghp/MoviePilot-Plugins/blob/main/docs/V2_Plugin_Development.md) — V2 插件结构、`_PluginBase`、表单/页面/API 开发规范
- [InfinityPacer/MoviePilot-Plugins](https://github.com/InfinityPacer/MoviePilot-Plugins) — 插件市场 `package.v2.json` 字段标准参考（`labels`/`history`/`release`/`v2`）

## License

仓库许可协议见 [`LICENSE`](./LICENSE)。
