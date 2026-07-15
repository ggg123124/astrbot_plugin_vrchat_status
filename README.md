# astrbot_plugin_vrchat_status

一个 [AstrBot](https://github.com/AstrBotDevs/AstrBot) 插件，用于查询 VRChat 服务器状态、事件和计划维护信息。

## 功能

- 📊 查询 VRChat 整体服务器状态及各组件运行情况
- 🔍 查询未解决的事件/故障记录
- 🔧 查询计划维护信息
- 🤖 内置 Anthropic Skill，Agent 可根据用户意图自动匹配并调用相关指令

## 指令

| 指令 | 说明 |
|------|------|
| `/vrcstatus` | 查询整体状态和各组件运行情况 |
| `/vrcincident` | 查询未解决的事件/故障记录 |
| `/vrcmaintenance` | 查询计划维护信息 |

## Skill

本插件内置了 `vrchat-status` Skill（位于 `skills/vrchat-status/SKILL.md`），遵循 Anthropic Skills 规范。当用户在对话中询问 VRChat 是否宕机、服务器状态、故障或维护时，Agent 会自动匹配该 Skill 并调用相应指令，无需手动输入命令。

## 数据源

所有数据通过 [Statuspage.io](https://www.atlassian.com/software/statuspage) 公共 API 获取，来自 VRChat 官方状态页：

- 状态页：https://status.vrchat.com/
- API 端点：`https://status.vrchat.com/api/v2/summary.json`

> **注意**：VRChat 的 Statuspage 不支持 `incidents.json` 和 `scheduled_maintenances.json` 等独立端点，本插件统一使用 `summary.json` 获取所有状态信息。

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
