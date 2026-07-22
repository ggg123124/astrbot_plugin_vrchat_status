import aiohttp
from datetime import datetime, timedelta, timezone

from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger

# VRChat Statuspage API 基础地址
VRCHAT_STATUS_API = "https://status.vrchat.com/api/v2"

# CloudFront CDN 基础地址（公开指标数据）
CDN_BASE = "https://d31qqo63tn8lj0.cloudfront.net"

# 北京时间 UTC+8
CST = timezone(timedelta(hours=8))

# ── 状态映射表 ──

# 整体状态指示器
STATUS_INDICATOR_MAP = {
    "none": "✅ 所有系统正常运行",
    "minor": "⚠️ 轻微服务中断",
    "major": "🟠 部分系统中断",
    "critical": "🔴 严重服务中断",
    "maintenance": "🔧 服务维护中",
}

# 组件状态 → (emoji, 中文描述)
COMPONENT_STATUS_MAP = {
    "operational": ("✅", "正常"),
    "degraded_performance": ("⚠️", "性能下降"),
    "partial_outage": ("🟠", "部分中断"),
    "major_outage": ("🔴", "严重中断"),
    "under_maintenance": ("🔧", "维护中"),
}

# 事件状态
INCIDENT_STATUS_MAP = {
    "investigating": "🔍 调查中",
    "identified": "📌 已定位",
    "monitoring": "👀 监控中",
    "resolved": "✅ 已解决",
    "postmortem": "📝 事后总结",
}

# 维护状态
MAINTENANCE_STATUS_MAP = {
    "scheduled": "📅 已计划",
    "in_progress": "🔄 进行中",
    "verifying": "✓ 验证中",
    "completed": "✅ 已完成",
}

# 影响程度
IMPACT_MAP = {
    "none": "无影响",
    "minor": "轻微影响",
    "major": "较大影响",
    "critical": "严重影响",
    "maintenance": "计划维护",
}

# 指标定义: (名称, emoji, CDN路径, 格式, 是否毫秒, 是否百分比)
METRICS_DEF = [
    ("在线用户", "👥", "visits.json", "int", False, False),
    ("API 延迟", "⏱️", "apilatency.json", "ms", True, False),
    ("API 请求量", "📈", "apirequests.json", "float", False, False),
    ("API 错误率", "❌", "apierrors.json", "pct", False, True),
    ("Steam 认证", "🔐", "extauth_steam.json", "pct", False, True),
    ("Meta 认证", "🔐", "extauth_oculus.json", "pct", False, True),
]


@register("vrchat_status", "超级有节操的逆袭", "查询 VRChat 服务器状态及相关信息", "1.3.0")
class VRChatStatusPlugin(Star):
    """VRChat 服务器状态查询插件

    提供以下指令：
      /vrcstatus       - 查询整体状态及各组件运行情况
      /vrcincident     - 查询最近的事件/故障
      /vrcmaintenance  - 查询计划维护
      /vrcmetrics      - 查询实时指标（在线用户、API延迟、错误率等）
    """

    def __init__(self, context: Context):
        super().__init__(context)
        self._session: aiohttp.ClientSession | None = None

    async def initialize(self):
        """插件初始化，创建 aiohttp 会话"""
        self._session = self._create_session()
        logger.info("VRChat 状态查询插件已加载 (v1.3.0)")

    async def terminate(self):
        """插件销毁，关闭 aiohttp 会话"""
        if self._session and not self._session.closed:
            await self._session.close()

    # ── 内部工具方法 ──

    def _create_session(self) -> aiohttp.ClientSession:
        """创建 aiohttp 客户端会话"""
        return aiohttp.ClientSession(
            headers={"User-Agent": "AstrBot-VRChatStatus/1.0"},
            timeout=aiohttp.ClientTimeout(total=15),
        )

    async def _get_session(self) -> aiohttp.ClientSession:
        """获取可用的 aiohttp 会话（惰性创建）"""
        if self._session is None or self._session.closed:
            self._session = self._create_session()
        return self._session

    async def _fetch_json(self, path: str) -> dict:
        """从 Statuspage API 获取 JSON 数据

        Args:
            path: API 路径，如 "summary.json"

        Returns:
            解析后的 JSON 字典

        Raises:
            aiohttp.ClientError: 网络请求失败时抛出
        """
        session = await self._get_session()
        url = f"{VRCHAT_STATUS_API}/{path}"
        async with session.get(url) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def _fetch_cdn_json(self, path: str) -> list:
        """从 CloudFront CDN 获取指标 JSON 数据

        Args:
            path: CDN 路径，如 "visits.json"

        Returns:
            解析后的 JSON 列表（时间序列数据点）

        Raises:
            aiohttp.ClientError: 网络请求失败时抛出
        """
        session = await self._get_session()
        url = f"{CDN_BASE}/{path}"
        async with session.get(url) as resp:
            resp.raise_for_status()
            return await resp.json()

    @staticmethod
    def _format_date(date_str: str | None) -> str:
        """将 ISO 8601 日期字符串格式化为北京时间 (UTC+8)"""
        if not date_str:
            return "未知"
        try:
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            dt_cst = dt.astimezone(CST)
            return dt_cst.strftime("%Y-%m-%d %H:%M CST")
        except (ValueError, AttributeError):
            return date_str

    @staticmethod
    def _get_latest_update(incident: dict) -> dict | None:
        """从事件/维护中获取最新的更新记录"""
        updates = incident.get("incident_updates", [])
        if not updates:
            return None
        return max(
            updates,
            key=lambda u: u.get("created_at", ""),
            default=None,
        )

    @staticmethod
    def _truncate(text: str, max_len: int = 200) -> str:
        """截断文本，超长时添加省略号"""
        if len(text) > max_len:
            return text[:max_len] + "..."
        return text

    @staticmethod
    def _calc_stats(data_points: list, *, is_ms: bool = False, is_pct: bool = False) -> dict | None:
        """计算时间序列的统计值（最新、平均、最小、最大）"""
        if not data_points:
            return None
        values = [p[1] for p in data_points]
        if is_ms:
            values = [v * 1000 for v in values]
        if is_pct:
            values = [v * 100 for v in values]
        return {
            "latest": values[-1],
            "avg": sum(values) / len(values),
            "min": min(values),
            "max": max(values),
        }

    @staticmethod
    def _fmt_val(v: float, fmt: str) -> str:
        """按格式类型格式化数值"""
        if fmt == "int":
            return f"{int(v):,}"
        if fmt == "ms":
            return f"{v:.0f}ms"
        if fmt == "pct":
            return f"{v:.2f}%"
        if fmt == "float":
            return f"{v:.2f}"
        return str(v)

    # ── 指令处理 ──

    @filter.command("vrcstatus")
    async def vrcstatus(self, event: AstrMessageEvent):
        """查询 VRChat 服务器整体状态和各组件运行情况"""
        try:
            data = await self._fetch_json("summary.json")
        except Exception as e:
            logger.error(f"获取 VRChat 状态失败: {e}")
            yield event.plain_result(f"❌ 获取 VRChat 状态失败: {e}")
            return

        # 整体状态
        status = data.get("status", {})
        indicator = status.get("indicator", "none")
        overall_text = STATUS_INDICATOR_MAP.get(indicator, f"未知状态 ({indicator})")

        # 组件分类：组组件 / 独立组件
        components = data.get("components", [])
        groups: dict[str, dict] = {}
        standalone: list[dict] = []

        for comp in components:
            if comp.get("group"):
                # 这是一个组组件（如 "Core Services"）
                groups[comp["id"]] = {**comp, "children": []}
            elif comp.get("group_id") and comp["group_id"] in groups:
                # 属于某个组的子组件
                groups[comp["group_id"]]["children"].append(comp)
            else:
                # 独立组件（不属于任何组）
                standalone.append(comp)

        # 构建输出文本
        lines: list[str] = []
        lines.append("🎮 VRChat 服务器状态")
        lines.append("")
        lines.append(f"📊 整体状态: {overall_text}")
        lines.append("━" * 24)

        # 按组显示组件
        for group in groups.values():
            group_name = group.get("name", "未命名组")
            lines.append(f"\n📁 {group_name}")
            for child in group.get("children", []):
                name = child.get("name", "未知组件")
                comp_status = child.get("status", "operational")
                emoji, text = COMPONENT_STATUS_MAP.get(
                    comp_status, ("❓", comp_status)
                )
                lines.append(f"  {emoji} {text} - {name}")

        # 独立组件
        if standalone:
            lines.append("\n📋 组件状态:")
            for comp in standalone:
                name = comp.get("name", "未知组件")
                comp_status = comp.get("status", "operational")
                emoji, text = COMPONENT_STATUS_MAP.get(
                    comp_status, ("❓", comp_status)
                )
                lines.append(f"{emoji} {text} - {name}")

        # 事件和维护摘要
        incidents = data.get("incidents", [])
        maintenances = data.get("scheduled_maintenances", [])
        unresolved = [i for i in incidents if i.get("status") != "resolved"]
        active_maint = [
            m for m in maintenances if m.get("status") not in ("completed",)
        ]

        lines.append("\n" + "━" * 24)
        lines.append(f"🔍 未解决事件: {len(unresolved)}")
        lines.append(f"🔄 进行中维护: {len(active_maint)}")

        # 如果有未解决事件，简要列出
        if unresolved:
            lines.append("")
            for inc in unresolved[:3]:
                name = inc.get("name", "未知事件")
                inc_status = inc.get("status", "unknown")
                status_text = INCIDENT_STATUS_MAP.get(inc_status, inc_status)
                lines.append(f"  • {name} [{status_text}]")

        # 展开未完成维护的详细信息（含受影响组件）
        if active_maint:
            lines.append("\n🔧 未完成维护详情:")
            for mnt in active_maint:
                name = mnt.get("name", "未知维护")
                mnt_status = mnt.get("status", "unknown")
                status_text = MAINTENANCE_STATUS_MAP.get(mnt_status, mnt_status)
                scheduled_for = self._format_date(mnt.get("scheduled_for"))
                scheduled_until = self._format_date(mnt.get("scheduled_until"))
                # 最新更新内容
                latest = self._get_latest_update(mnt)
                latest_body = self._truncate(latest["body"]) if latest and latest.get("body") else "暂无更新"
                # 受影响组件
                affected = mnt.get("components", [])
                comp_names = [c.get("name", "未知") for c in affected] if affected else ["无"]
                lines.extend([
                    f"\n  🔧 {name}",
                    f"     状态: {status_text}",
                    f"     计划时间: {scheduled_for} ~ {scheduled_until}",
                    f"     最新更新: {latest_body}",
                    f"     受影响组件: {', '.join(comp_names)}",
                ])

        lines.append(f"🔗 详情: https://status.vrchat.com/")

        yield event.plain_result("\n".join(lines))

    @filter.command("vrcincident")
    async def vrcincident(self, event: AstrMessageEvent):
        """查询 VRChat 最近的事件/故障记录"""
        try:
            # incidents.json 返回最近 50 个事件（含已解决的）
            data = await self._fetch_json("incidents.json")
        except Exception as e:
            logger.error(f"获取 VRChat 事件失败: {e}")
            yield event.plain_result(f"❌ 获取 VRChat 事件失败: {e}")
            return

        incidents = data.get("incidents", [])
        if not incidents:
            yield event.plain_result("✅ 最近没有 VRChat 事件记录")
            return

        # 只显示最近 5 个事件
        recent = incidents[:5]

        lines: list[str] = []
        lines.append("🎮 VRChat 最近事件")
        lines.append("━" * 24)

        for inc in recent:
            name = inc.get("name", "未知事件")
            inc_status = inc.get("status", "unknown")
            status_text = INCIDENT_STATUS_MAP.get(inc_status, inc_status)
            impact = inc.get("impact", "none")
            impact_text = IMPACT_MAP.get(impact, impact)
            created = self._format_date(inc.get("created_at"))

            lines.append(f"\n📌 {name}")
            lines.append(f"   状态: {status_text} | 影响: {impact_text}")
            lines.append(f"   时间: {created}")

            # 最新更新
            latest = self._get_latest_update(inc)
            if latest:
                body = latest.get("body", "")
                if body:
                    body = self._truncate(body)
                    lines.append(f"   更新: {body}")

        lines.append("\n" + "━" * 24)
        lines.append(f"🔗 详情: https://status.vrchat.com/")

        yield event.plain_result("\n".join(lines))

    @filter.command("vrcmaintenance")
    async def vrcmaintenance(self, event: AstrMessageEvent):
        """查询 VRChat 计划维护"""
        try:
            # scheduled-maintenances.json 返回最近 50 个维护记录（含已完成的）
            data = await self._fetch_json("scheduled-maintenances.json")
        except Exception as e:
            logger.error(f"获取 VRChat 维护信息失败: {e}")
            yield event.plain_result(f"❌ 获取 VRChat 维护信息失败: {e}")
            return

        maintenances = data.get("scheduled_maintenances", [])
        if not maintenances:
            yield event.plain_result("✅ 目前没有 VRChat 计划维护")
            return

        # 只显示最近 5 个维护记录
        recent_maintenances = maintenances[:5]

        lines: list[str] = []
        lines.append("🎮 VRChat 计划维护")
        lines.append("━" * 24)

        for mnt in recent_maintenances:
            name = mnt.get("name", "未知维护")
            mnt_status = mnt.get("status", "unknown")
            status_text = MAINTENANCE_STATUS_MAP.get(mnt_status, mnt_status)
            impact = mnt.get("impact", "none")
            impact_text = IMPACT_MAP.get(impact, impact)
            scheduled_for = self._format_date(mnt.get("scheduled_for"))
            scheduled_until = self._format_date(mnt.get("scheduled_until"))

            lines.append(f"\n🔧 {name}")
            lines.append(f"   状态: {status_text} | 影响: {impact_text}")
            lines.append(f"   开始: {scheduled_for}")
            lines.append(f"   结束: {scheduled_until}")

            # 最新更新
            latest = self._get_latest_update(mnt)
            if latest:
                body = latest.get("body", "")
                if body:
                    body = self._truncate(body)
                    lines.append(f"   更新: {body}")

            # 受影响组件
            affected = mnt.get("components", [])
            if affected:
                comp_names = [c.get("name", "未知") for c in affected]
                lines.append(f"   受影响组件: {', '.join(comp_names)}")

        lines.append("\n" + "━" * 24)
        lines.append(f"🔗 详情: https://status.vrchat.com/")

        yield event.plain_result("\n".join(lines))

    @filter.command("vrcmetrics")
    async def vrcmetrics(self, event: AstrMessageEvent):
        """查询 VRChat 实时指标（在线用户、API延迟、请求量、错误率、认证成功率）"""
        lines: list[str] = []
        lines.append("📊 VRChat 实时指标 (24h)")
        lines.append("━" * 24)

        for label, emoji, cdn_path, fmt, is_ms, is_pct in METRICS_DEF:
            try:
                data = await self._fetch_cdn_json(cdn_path)
                stats = self._calc_stats(data, is_ms=is_ms, is_pct=is_pct)
            except Exception as e:
                logger.warning(f"获取指标 {cdn_path} 失败: {e}")
                stats = None

            if stats is None:
                lines.append(f"\n{emoji} {label}: 暂无数据")
            else:
                lines.append(
                    f"\n{emoji} {label}: {self._fmt_val(stats['latest'], fmt)} | "
                    f"平均: {self._fmt_val(stats['avg'], fmt)} | "
                    f"最低: {self._fmt_val(stats['min'], fmt)} | "
                    f"最高: {self._fmt_val(stats['max'], fmt)}"
                )

        lines.append("\n" + "━" * 24)
        lines.append("🔗 官方状态页: https://status.vrchat.com/")

        yield event.plain_result("\n".join(lines))
