# MoviePilot-Plugins

这是 MoviePilot 插件发布仓库，当前维护插件：

| 插件 | 目录 | 说明 |
|---|---|---|
| 原盘通知（QBRawGuard） | `plugins.v2/qbrawguard` | 基于下载器真实文件列表识别 ISO/BDMV/DVD 等原盘结构，并按配置暂停或删除任务、清理 MoviePilot 侧关联记录。 |

## 仓库结构

```text
package.v2.json              # MoviePilot V2 插件市场元数据
plugins.v2/qbrawguard/       # 原盘通知插件源码
```

## 发布规则

- 只提交插件源码、说明文档和 `package.v2.json`。
- 不提交运行时缓存、日志、数据库、密钥、Cookie、Token、`__pycache__` 等文件。
- 插件运行逻辑修改后应先在 MoviePilot 本地完成语法检查、插件重载和日志验证，再发布。
