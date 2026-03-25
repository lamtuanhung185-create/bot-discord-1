import json
from datetime import timedelta

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands

import config
from utils.logger import setup_logger

logger = setup_logger(__name__)

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"

REPORT_FETCH_LIMIT = 250
REPORT_MESSAGE_COUNT = 10
MAX_CONTEXT_CHARS = 6000
SEVERITY_TIMEOUT_THRESHOLD = 70
TIMEOUT_HIGH_SEVERITY = timedelta(hours=6)

SYSTEM_PROMPT = """Bạn là trợ lý kiểm duyệt Discord. Bạn nhận tối đa 10 tin nhắn gần đây của MỘT người dùng trong một kênh (có thể tiếng Việt/Anh, teencode).

Nhiệm vụ: đánh giá xem có nên áp dụng **timeout** (tạm khóa chat) hay không, dựa trên: quấy rối, thù ghét, đe dọa, lạm dụng nặng, spam/scam rõ ràng, NSFW công khai, v.v.
- Phân biệt đùa vừa phải / tranh luận bình thường với hành vi độc hại thật sự.
- severity: 0-100 (mức độ vi phạm tổng thể trong các tin đã cho).

Chỉ trả lời ĐÚNG một JSON (không markdown, không giải thích ngoài JSON):
{"should_timeout": <true hoặc false>, "duration_minutes": <số nguyên 5-60 nếu should_timeout true và severity ≤70, ngược lại 0>, "severity": <0-100>, "reason": "<giải thích ngắn gọn bằng tiếng Việt>"}

Lưu: severity > 70 = vi phạm nặng; hệ thống sẽ áp dụng timeout 6 giờ (không dùng duration_minutes cho trường hợp đó)."""


def _message_text_for_ai(message: discord.Message) -> str:
    parts = []
    if message.content and message.content.strip():
        parts.append(message.content.strip())
    for em in message.embeds:
        if em.title:
            parts.append(em.title)
        if em.description:
            parts.append(em.description)
    return " ".join(parts).strip() or "(không có nội dung chữ)"


async def _fetch_recent_messages(
    channel: discord.abc.Messageable, member: discord.Member, limit: int
) -> list[discord.Message]:
    out: list[discord.Message] = []
    try:
        async for msg in channel.history(limit=REPORT_FETCH_LIMIT):
            if msg.author.id != member.id:
                continue
            if msg.author.bot:
                continue
            out.append(msg)
            if len(out) >= limit:
                break
    except (discord.Forbidden, discord.HTTPException) as e:
        logger.warning("[REPORT] Không đọc được lịch sử kênh: %s", e)
        return []
    out.reverse()
    return out


def _build_user_payload(messages: list[discord.Message], member: discord.Member) -> str:
    lines: list[str] = [f"Thành viên báo cáo: {member.display_name} (id {member.id})", "Các tin (cũ → mới):"]
    for i, msg in enumerate(messages, 1):
        text = _message_text_for_ai(msg)
        lines.append(f'{i}. [{msg.created_at.isoformat()}] {text[:800]}')
    blob = "\n".join(lines)
    if len(blob) > MAX_CONTEXT_CHARS:
        blob = blob[: MAX_CONTEXT_CHARS - 20] + "\n...(đã cắt bớt)"
    return blob


async def _analyze_report(context_text: str) -> dict | None:
    api_key = config.GROQ_API_KEY
    if not api_key:
        logger.error("[REPORT] GROQ_API_KEY chưa được cấu hình")
        return None

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": context_text},
        ],
        "temperature": 0.15,
        "max_tokens": 350,
    }

    content = ""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(GROQ_API_URL, headers=headers, json=payload) as resp:
                if resp.status != 200:
                    logger.error("[REPORT] Groq HTTP %s: %s", resp.status, await resp.text())
                    return None
                data = await resp.json()
                content = data["choices"][0]["message"]["content"].strip()
                if content.startswith("```"):
                    content = content.split("\n", 1)[1].rsplit("```", 1)[0].strip()
                return json.loads(content)
    except json.JSONDecodeError as e:
        logger.error("[REPORT] JSON Groq lỗi: %s | raw=%s", e, content[:500])
        return None
    except Exception as e:
        logger.error("[REPORT] Lỗi Groq: %s", e, exc_info=True)
        return None


def _clamp_duration(minutes: int) -> int:
    return max(5, min(60, int(minutes)))


async def _maybe_timeout(
    guild: discord.Guild,
    moderator: discord.abc.User,
    target: discord.Member,
    should: bool,
    delta: timedelta | None,
    reason: str,
) -> tuple[bool, str | None]:
    if not should or delta is None:
        return False, None
    if not isinstance(moderator, discord.Member) or not moderator.guild_permissions.moderate_members:
        return False, "Chỉ thành viên có quyền **Moderate Members** mới để bot tự động timeout."
    me = guild.me
    if not me or not me.guild_permissions.moderate_members:
        return False, "Bot thiếu quyền **Moderate Members**."
    if target.id == guild.owner_id:
        return False, "Không timeout được chủ server."
    if target.guild_permissions.administrator:
        return False, "Không timeout được người có quyền Administrator."
    if target.top_role >= me.top_role:
        return False, "Không thể timeout: vai trò của người này cao hơn hoặc bằng bot."
    try:
        await target.timeout(delta, reason=f"[Report AI] {reason[:200]} — bởi {moderator}")
        return True, None
    except discord.Forbidden:
        return False, "Discord từ chối (thiếu quyền hoặc không hợp lệ)."
    except Exception as e:
        logger.error("[REPORT] timeout error: %s", e, exc_info=True)
        return False, f"Lỗi khi timeout: `{e}`"


def _result_embed(
    target: discord.Member,
    message_count: int,
    analysis: dict,
    timeout_applied: bool,
    timeout_note: str | None,
    high_severity: bool,
) -> discord.Embed:
    should = bool(analysis.get("should_timeout"))
    sev = analysis.get("severity", 0)
    try:
        sev = int(sev)
    except (TypeError, ValueError):
        sev = 0
    sev = max(0, min(100, sev))
    reason = str(analysis.get("reason", "Không có mô tả."))[:1024]
    dur = analysis.get("duration_minutes", 0)
    try:
        dur = int(dur)
    except (TypeError, ValueError):
        dur = 0

    wants_timeout = high_severity or should
    color = discord.Color.red() if wants_timeout else discord.Color.green()
    title = "📋 Kết quả"
    desc = (
        f"**Đối tượng:** {target.mention}\n"
        f"**Đã phân tích:** {message_count} tin gần nhất trong kênh này.\n"
        f"**Khuyến nghị timeout:** {'Có' if wants_timeout else 'Không'}\n"
        f"**Mức độ (severity):** {sev}/100\n"
    )
    if high_severity:
        desc += f"**Vi phạm >{SEVERITY_TIMEOUT_THRESHOLD}:** áp dụng timeout **6 giờ** (khi đủ quyền).\n"
    elif should:
        desc += f"**Thời gian gợi ý:** {_clamp_duration(dur)} phút\n"

    embed = discord.Embed(title=title, description=desc, color=color)
    embed.add_field(name="Lý do", value=reason, inline=False)
    if wants_timeout and not timeout_applied and timeout_note:
        embed.add_field(name="Timeout tự động", value=timeout_note, inline=False)
    elif timeout_applied and high_severity:
        embed.add_field(name="Timeout tự động", value="Đã timeout **6 giờ** (severity > 70).", inline=False)
    elif timeout_applied:
        embed.add_field(name="Timeout tự động", value="Đã áp dụng theo khuyến nghị AI.", inline=False)
    return embed


class Report(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _run_report(
        self,
        guild: discord.Guild,
        channel: discord.abc.Messageable,
        author: discord.abc.User,
        target: discord.Member,
    ) -> discord.Embed:
        if target.bot:
            return discord.Embed(
                title="Không hợp lệ",
                description="Không báo cáo tài khoản bot.",
                color=discord.Color.orange(),
            )
        if author.id == target.id:
            return discord.Embed(
                title="Không hợp lệ",
                description="Bạn không thể báo cáo chính mình.",
                color=discord.Color.orange(),
            )

        messages = await _fetch_recent_messages(channel, target, REPORT_MESSAGE_COUNT)
        if not messages:
            return discord.Embed(
                title="Không có dữ liệu",
                description=(
                    f"Không tìm thấy tin nhắn nào gần đây của {target.mention} trong kênh này "
                    f"(hoặc bot không đọc được lịch sử). Thử kênh khác nơi người đó đã chat."
                ),
                color=discord.Color.orange(),
            )

        payload = _build_user_payload(messages, target)
        analysis = await _analyze_report(payload)
        if not analysis:
            return discord.Embed(
                title="Lỗi phân tích",
                description="Không gọi được AI (kiểm tra `GROQ_API_KEY` hoặc thử lại sau).",
                color=discord.Color.red(),
            )

        should = bool(analysis.get("should_timeout"))
        raw_dur = analysis.get("duration_minutes", 10)
        try:
            raw_dur = int(raw_dur)
        except (TypeError, ValueError):
            raw_dur = 10

        sev = analysis.get("severity", 0)
        try:
            sev = int(sev)
        except (TypeError, ValueError):
            sev = 0
        sev = max(0, min(100, sev))
        high_severity = sev > SEVERITY_TIMEOUT_THRESHOLD

        applied = False
        note = None
        if high_severity:
            applied, note = await _maybe_timeout(
                guild,
                author,
                target,
                True,
                TIMEOUT_HIGH_SEVERITY,
                str(analysis.get("reason", "")),
            )
        elif should:
            applied, note = await _maybe_timeout(
                guild,
                author,
                target,
                True,
                timedelta(minutes=_clamp_duration(raw_dur)),
                str(analysis.get("reason", "")),
            )

        return _result_embed(target, len(messages), analysis, applied, note, high_severity)

    @app_commands.command(name="1report", description="Báo cáo thành viên — AI phân tích 10 tin gần nhất (chỉ bạn thấy)")
    @app_commands.describe(thanh_vien="Thành viên cần báo cáo")
    async def report_slash(self, interaction: discord.Interaction, thanh_vien: discord.Member):
        if not interaction.guild:
            await interaction.response.send_message("Lệnh chỉ dùng trong server.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        embed = await self._run_report(
            interaction.guild,
            interaction.channel,
            interaction.user,
            thanh_vien,
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

    @commands.command(name="report", aliases=["bao_cao"])
    async def report_prefix(self, ctx: commands.Context, thanh_vien: discord.Member):
        """!report @member — Hiển thị kết quả trong kênh (công khai). Dùng /report để chỉ mình bạn thấy."""
        if not ctx.guild:
            return
        async with ctx.channel.typing():
            embed = await self._run_report(ctx.guild, ctx.channel, ctx.author, thanh_vien)
        await ctx.channel.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Report(bot))
