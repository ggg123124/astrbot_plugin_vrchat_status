# 更新日志

本文件记录 VRChat 服务器状态插件的所有版本变更。

格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/)。

## [v1.2.0] - 2026-07-15

### 新增

- `/vrcincident` 改用 `incidents.json` 端点，可获取最近 50 个事件（含已解决的）
- `/vrcmaintenance` 改用 `scheduled-maintenances.json` 端点，可获取最近 50 个维护记录（含已完成的）
- 两个命令均限制显示最近 5 条记录，避免消息过长

### 修复

- 修正 `scheduled-maintenances.json` 的 URL 使用连字符 `-` 而非下划线 `_`，解决 404 错误

### 变更

- 更新 SKILL.md 中 `/vrcincident` 的描述（从"未解决事件"改为"最近事件"）
- 更新 SKILL.md 和 README 的数据源说明，列出各命令使用的独立 API 端点

## [v1.1.0] - 2026-07-15

### 新增

- 添加 Anthropic Skill（`skills/vrchat-status/SKILL.md`）
- 遵循 Anthropic Skills 规范，包含触发条件、命令说明、状态解读和使用示例
- Agent 可根据用户对话意图自动匹配并调用相关指令，无需手动输入命令

### 变更

- 重写 README 为完整的插件说明文档
- 更新作者信息和仓库地址

## [v1.0.1] - 2026-07-15

### 修复

- 修复 `/vrcmaintenance` 调用 `scheduled_maintenances.json` 返回 404 的问题
- 修复 `/vrcincident` 调用 `incidents.json` 可能返回 404 的问题
- 两个命令临时改用 `summary.json` 作为数据源（后在 v1.2.0 中修正为正确的独立端点）

## [v1.0.0] - 2026-07-15

### 新增

- 初始版本发布
- `/vrcstatus` — 查询 VRChat 整体服务器状态和各组件运行情况
- `/vrcincident` — 查询 VRChat 事件/故障记录
- `/vrcmaintenance` — 查询 VRChat 计划维护信息
- 基于 Statuspage.io 公共 API，使用 aiohttp 异步请求
- 支持组件分组展示、状态映射（emoji + 中文描述）
- 完善的错误处理和日志记录
