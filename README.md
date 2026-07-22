# astrbot_plugin_vrchat_status

一个 [AstrBot](https://github.com/AstrBotDevs/AstrBot) 插件，用于查询 VRChat 服务器状态、事件、计划维护和实时指标信息。

## 功能

- 📊 查询 VRChat 整体服务器状态及各组件运行情况
- 🔍 查询未解决的事件/故障记录
- 🔧 查询计划维护信息（含受影响组件）
- 📈 查询实时指标（在线用户数、API延迟、请求量、错误率、Steam/Meta认证成功率）
- 🕐 所有时间显示为北京时间 (UTC+8)
- 🤖 内置 Anthropic Skill，Agent 可根据用户意图自动匹配并调用相关指令

## 指令

| 指令 | 说明 |
|------|------|
| `/vrcstatus` | 查询整体状态和各组件运行情况 |
| `/vrcincident` | 查询未解决的事件/故障记录 |
| `/vrcmaintenance` | 查询计划维护信息 |
| `/vrcmetrics` | 查询实时指标（在线用户、API延迟、错误率等） |

## Skill

本插件内置了 `vrchat-status` Skill（位于 `skills/vrchat-status/SKILL.md`），遵循 Anthropic Skills 规范。当用户在对话中询问 VRChat 是否宕机、服务器状态、故障或维护时，Agent 会自动匹配该 Skill 并调用相应指令，无需手动输入命令。

## 数据源

所有数据通过 [Statuspage.io](https://www.atlassian.com/software/statuspage) 公共 API 获取，来自 VRChat 官方状态页：

- 状态页：https://status.vrchat.com/
- API 端点：`https://status.vrchat.com/api/v2/summary.json`

| 指令 | API 端点 | 数据内容 |
|------|---------|--------|
| `/vrcstatus` | `summary.json` | 整体状态、组件、未解决事件、计划维护 |
| `/vrcincident` | `incidents.json` | 最近 50 个事件（含已解决的） |
| `/vrcmaintenance` | `scheduled-maintenances.json` | 最近 50 个维护记录（含已完成的） |
| `/vrcmetrics` | CloudFront CDN | 在线用户、API延迟/请求/错误率、Steam/Meta认证率 |

### 指标数据端点

`/vrcmetrics` 指令从 CloudFront CDN 获取以下指标（24小时时间序列）：

| 指标 | CDN 路径 | 说明 |
|------|---------|------|
| 在线用户 | `visits.json` | 当前在线用户数 |
| API 延迟 | `apilatency.json` | API 响应延迟 (ms) |
| API 请求量 | `apirequests.json` | API 请求数 |
| API 错误率 | `apierrors.json` | API 错误百分比 |
| Steam 认证 | `extauth_steam.json` | Steam 认证成功率 |
| Meta 认证 | `extauth_oculus.json` | Meta/Oculus 认证成功率 |

## 安装

在 AstrBot WebUI 的插件管理页面，通过仓库地址安装：

```
https://github.com/ggg123124/astrbot_plugin_vrchat_status
```

或手动克隆到 AstrBot 的 `data/plugins/` 目录：

```bash
cd AstrBot/data/plugins
git clone https://github.com/ggg123124/astrbot_plugin_vrchat_status
```

## 相关链接

- [AstrBot](https://github.com/AstrBotDevs/AstrBot)
- [AstrBot 插件开发文档](https://docs.astrbot.app/dev/star/plugin-new.html)
