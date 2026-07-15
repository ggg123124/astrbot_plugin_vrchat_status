import aiohttp
from datetime import datetime

from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger

# VRChat Statuspage API 基础地址
VRCHAT_STATUS_API = "https://status.vrchat.com/api/v2"

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
}


@register("vrchat_status", "超级有节操的逆袭", "查询 VRChat 服务器状态及相关信息", "1.1.0")
class VRChatStatusPlugin(Star):
    """VRChat 服务器状态查询插件

    提供以下指令：
      /vrcstatus     - 查询整体状态及各组件运行情况
      /vrcincident   - 查询未解决的事件/故障
      /vrcmaintenance - 查询计划维护
    """

    def __init__(self, context: Context):
        super().__init__(context)
        self._session: aiohttp.ClientSession | None = None

    async def initialize(self):
        """插件初始化，创建 aiohttp 会话"""
        self._session = self._create_session()
        logger.info("VRChat 状态查询插件已加载")

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

    @staticmethod
    def _format_date(date_str: str | None) -> str:
        """将 ISO 8601 日期字符串格式化为可读形式"""
        if not date_str:
            return "未知"
        try:
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            return dt.strftime("%Y-%m-%d %H:%M UTC")
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

        lines.append(f"🔗 详情: https://status.vrchat.com/")

        yield event.plain_result("\n".join(lines))

    @filter.command("vrcincident")
    async def vrcincident(self, event: AstrMessageEvent):
        """查询 VRChat 未解决的事件/故障记录"""
        try:
            # summary.json 包含未解决的事件信息
            data = await self._fetch_json("summary.json")
        except Exception as e:
            logger.error(f"获取 VRChat 事件失败: {e}")
            yield event.plain_result(f"❌ 获取 VRChat 事件失败: {e}")
            return

        incidents = data.get("incidents", [])
        if not incidents:
            yield event.plain_result("✅ 当前没有未解决的 VRChat 事件")
            return

        lines: list[str] = []
        lines.append("🎮 VRChat 未解决事件")
        lines.append("━" * 24)

        for inc in incidents:
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
            # summary.json 包含计划维护信息
            data = await self._fetch_json("summary.json")
        except Exception as e:
            logger.error(f"获取 VRChat 维护信息失败: {e}")
            yield event.plain_result(f"❌ 获取 VRChat 维护信息失败: {e}")
            return

        maintenances = data.get("scheduled_maintenances", [])
        if not maintenances:
            yield event.plain_result("✅ 目前没有 VRChat 计划维护")
            return

        lines: list[str] = []
        lines.append("🎮 VRChat 计划维护")
        lines.append("━" * 24)

        for mnt in maintenances:
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

        lines.append("\n" + "━" * 24)
        lines.append(f"🔗 详情: https://status.vrchat.com/")

        yield event.plain_result("\n".join(lines))
