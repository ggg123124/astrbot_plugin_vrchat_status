---
name: vrchat-status
description: Check VRChat server status, incidents, scheduled maintenance, and real-time metrics. Use this skill when the user asks about VRChat server status, downtime, outages, maintenance schedules, online player count, API performance, or whether VRChat is down.
---

# VRChat Server Status

This skill helps the user query the real-time status of VRChat's servers, including overall health, individual component status, ongoing incidents, scheduled maintenance, and real-time performance metrics.

## When to use

Trigger this skill when the user:

- Asks whether VRChat is down or experiencing issues
- Wants to check VRChat server status or service health
- Asks about VRChat incidents, outages, or disruptions
- Wants to know about VRChat scheduled maintenance
- Asks about VRChat online player count or API performance
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
| `/vrcstatus` | Shows overall VRChat server status and individual component health, with details on unresolved incidents and active maintenance (including affected components) |
| `/vrcincident` | Lists recent incidents (including resolved ones) |
| `/vrcmaintenance` | Shows scheduled and active maintenance windows with affected components |
| `/vrcmetrics` | Shows real-time metrics: online users, API latency, API requests, API error rate, Steam/Meta auth success rate (24h stats) |

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

### Metrics interpretation

- **Online Users**: Current number of users online in VRChat
- **API Latency**: Average response time of VRChat API (lower is better)
- **API Requests**: Number of API requests being processed
- **API Error Rate**: Percentage of failed API requests (lower is better)
- **Steam/Meta Auth**: Authentication success rate for Steam and Meta/Oculus (higher is better)

## Examples

**User:** "VRChat是不是挂了？"
**Action:** Run `/vrcstatus` to check the overall server status and component health.

**User:** "VRChat最近有什么故障吗？"
**Action:** Run `/vrcincident` to list recent incidents.

**User:** "VRChat有维护计划吗？"
**Action:** Run `/vrcmaintenance` to check for scheduled or active maintenance.

**User:** "VRChat在线人数多少？"
**Action:** Run `/vrcmetrics` to see current online player count and other real-time metrics.

**User:** "VRChat API 正常吗？"
**Action:** Run `/vrcmetrics` to check API latency, request volume, and error rates.

**User:** "我登录不了VRChat，是服务器的问题吗？"
**Action:** Run `/vrcstatus` first. If the Authentication component shows non-operational status, it's likely a server-side issue. If all systems are operational, run `/vrcmetrics` to check Steam/Meta auth success rates.

## Data source

All data is fetched from the official VRChat Statuspage at https://status.vrchat.com/ via the Statuspage.io public API:

- `/api/v2/summary.json` — overall status, components, unresolved incidents, and upcoming/active maintenances (used by `/vrcstatus`)
- `/api/v2/incidents.json` — 50 most recent incidents including resolved ones (used by `/vrcincident`)
- `/api/v2/scheduled-maintenances.json` — 50 most recent scheduled maintenances including completed ones (used by `/vrcmaintenance`)

Real-time metrics are fetched from VRChat's CloudFront CDN:

- `visits.json` — online user count
- `apilatency.json` — API response latency
- `apirequests.json` — API request volume
- `apierrors.json` — API error rate
- `extauth_steam.json` — Steam authentication success rate
- `extauth_oculus.json` — Meta/Oculus authentication success rate

All times are displayed in Beijing Time (UTC+8).
