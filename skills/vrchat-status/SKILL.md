---
name: vrchat-status
description: Check VRChat server status, incidents, and scheduled maintenance. Use this skill when the user asks about VRChat server status, downtime, outages, maintenance schedules, or whether VRChat is down.
---

# VRChat Server Status

This skill helps the user query the real-time status of VRChat's servers, including overall health, individual component status, ongoing incidents, and scheduled maintenance.

## When to use

Trigger this skill when the user:

- Asks whether VRChat is down or experiencing issues
- Wants to check VRChat server status or service health
- Asks about VRChat incidents, outages, or disruptions
- Wants to know about VRChat scheduled maintenance
- Mentions VRChat lag, connection problems, or login issues and wants to verify server-side causes

## When NOT to use

Do NOT trigger this skill when:

- The user is asking about VRChat game features, avatars, or worlds (not server status)
- The user is discussing non-VRChat platforms
- The user is asking about general VR or gaming topics unrelated to VRChat server status

## Available Commands

The following commands are available through the VRChat status plugin:

| Command | Description |
|---------|-------------|
| `/vrcstatus` | Shows overall VRChat server status and individual component health |
| `/vrcincident` | Lists current unresolved incidents/disruptions |
| `/vrcmaintenance` | Shows scheduled and active maintenance windows |

## How to interpret results

### Overall status indicators

- ✅ All Systems Operational — everything is running normally
- ⚠️ Minor Service Disruption — minor issues, most services still work
- 🟠 Partial System Outage — some services are down
- 🔴 Major Service Outage — major services are down
- 🔧 Service Under Maintenance — maintenance in progress

### Component status

- ✅ Operational — component is running normally
- ⚠️ Degraded Performance — component is running but with issues
- 🟠 Partial Outage — component is partially down
- 🔴 Major Outage — component is completely down
- 🔧 Under Maintenance — component is under maintenance

## Examples

**User:** "VRChat是不是挂了？"
**Action:** Run `/vrcstatus` to check the overall server status and component health.

**User:** "VRChat最近有什么故障吗？"
**Action:** Run `/vrcincident` to list any unresolved incidents.

**User:** "VRChat有维护计划吗？"
**Action:** Run `/vrcmaintenance` to check for scheduled or active maintenance.

**User:** "我登录不了VRChat，是服务器的问题吗？"
**Action:** Run `/vrcstatus` first. If the Authentication component shows non-operational status, it's likely a server-side issue. If all systems are operational, the problem is likely on the user's end.

## Data source

All data is fetched from the official VRChat Statuspage at https://status.vrchat.com/ via the Statuspage.io public API (`/api/v2/summary.json`).
