"""
Cog Fuel — !giaxang / /giaxang
Check current fuel prices in Vietnam.
"""

import discord
import aiohttp
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime, timezone, timedelta
import config
from utils.logger import setup_logger

logger = setup_logger(__name__)
GMT7 = timezone(timedelta(hours=7))


class Fuel(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.daily_fuel_task.start()  # Bắt đầu task gửi tự động

    def cog_unload(self):
        """Stop tasks when cog is unloaded."""
        self.daily_fuel_task.cancel()

    async def get_fuel_prices(self):
        """Fetch fuel prices from GitHub JSON source."""
        try:
            url = "https://raw.githubusercontent.com/toanqng/fuel/main/fuel-vietnam.json"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        # Read as text first, then parse JSON
                        text = await response.text()
                        import json
                        data = json.loads(text)
                        # Data is an array, get the first (latest) entry
                        if data and len(data) > 0:
                            return data[0]
                        return None
        except Exception as e:
            print(f"Error fetching fuel prices: {e}")
            return None

    def create_fuel_embed(self, data: dict, requester_name: str):
        """Create an embed with fuel price information."""
        if not data:
            embed = discord.Embed(
                title="⛽ Giá Xăng Dầu",
                description="❌ Không thể lấy thông tin giá xăng dầu lúc này.",
                color=discord.Color.red()
            )
            return embed

        embed = discord.Embed(
            title="⛽ Giá Xăng Dầu Hôm Nay",
            description="📊 Bảng giá bán lẻ tại Việt Nam",
            color=discord.Color.from_rgb(255, 165, 0),  # Orange color
            timestamp=datetime.now()
        )
        
        # Add update date
        if "date" in data:
            embed.add_field(
                name="📅 Ngày cập nhật",
                value=data["date"],
                inline=False
            )
        
        # Add fuel prices from list
        if "list" in data and data["list"]:
            for fuel in data["list"]:
                fuel_name = fuel.get("name", "N/A")
                region1 = fuel.get("region1", "N/A")
                region2 = fuel.get("region2", "")
                
                # Format price display
                if region2 and region2 != "":
                    price_text = f"**Khu vực 1:** {region1} đ/lít\n**Khu vực 2:** {region2} đ/lít"
                else:
                    price_text = f"**{region1}** đ/lít"
                
                embed.add_field(
                    name=f"🔸 {fuel_name}",
                    value=price_text,
                    inline=True
                )
        
        # Add unit info
        if "unit" in data:
            unit_text = data["unit"]
        else:
            unit_text = "VND"
        
        embed.set_footer(
            text=f"📍 Đơn vị: {unit_text} | Yêu cầu bởi {requester_name}",
            icon_url="https://cdn-icons-png.flaticon.com/512/2917/2917995.png"
        )
        
        embed.add_field(
            name="💡 Lưu ý",
            value="Giá có thể thay đổi theo địa phương. Khu vực 1: Miền Bắc, Khu vực 2: Miền Nam",
            inline=False
        )
        
        return embed

    # ─── Prefix command: !giaxang ─────────────────────────────────────
    @commands.command(name="giaxang", aliases=["fuel", "petrol", "gas"])
    async def giaxang_prefix(self, ctx: commands.Context):
        """
        Xem giá xăng dầu hiện tại tại Việt Nam.
        Usage: !giaxang
        """
        async with ctx.typing():
            data = await self.get_fuel_prices()
            embed = self.create_fuel_embed(data, ctx.author.display_name)
            await ctx.send(embed=embed)

    # ─── Slash command: /giaxang ──────────────────────────────────────
    @app_commands.command(name="giaxang", description="⛽ Xem giá xăng dầu hiện tại tại Việt Nam")
    async def giaxang_slash(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)
        
        data = await self.get_fuel_prices()
        embed = self.create_fuel_embed(data, interaction.user.display_name)
        
        await interaction.followup.send(embed=embed)

    # ─── Auto Daily Fuel Price Task ───────────────────────────────────
    @tasks.loop(hours=24)
    async def daily_fuel_task(self):
        """
        Gửi thông báo giá xăng hàng ngày vào 10:00 GMT+7
        """
        try:
            # Lấy danh sách channel ID từ config
            channel_ids = config.FUEL_CHANNEL_ID
            if not isinstance(channel_ids, list):
                channel_ids = [channel_ids]
            
            # Lấy dữ liệu giá xăng
            data = await self.get_fuel_prices()
            
            # Gửi thông báo đến các kênh
            for channel_id in channel_ids:
                try:
                    channel = self.bot.get_channel(channel_id)
                    if channel:
                        embed = self.create_fuel_embed(data, "Bot Auto")
                        await channel.send("⛽ **Thông báo giá xăng dầu hôm nay!**", embed=embed)
                        logger.info(f"✅ Đã gửi thông báo giá xăng đến kênh {channel_id}")
                    else:
                        logger.warning(f"⚠️ Không tìm thấy kênh {channel_id}")
                except Exception as e:
                    logger.error(f"❌ Lỗi khi gửi thông báo giá xăng đến kênh {channel_id}: {e}")
                    
        except Exception as e:
            logger.error(f"❌ Lỗi trong daily_fuel_task: {e}")

    @daily_fuel_task.before_loop
    async def before_daily_fuel_task(self):
        """Đợi bot sẵn sàng và tính toán thời gian gửi tiếp theo."""
        await self.bot.wait_until_ready()
        
        now = datetime.now(GMT7)
        target_hour = 10  # 10 giờ sáng
        target_minute = 0
        
        # Tính thời gian gửi tiếp theo
        next_run = now.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)
        
        # Nếu đã qua giờ gửi hôm nay, chuyển sang ngày mai
        if now >= next_run:
            next_run += timedelta(days=1)
        
        wait_seconds = (next_run - now).total_seconds()
        logger.info(f"⏰ Task giá xăng sẽ chạy lần đầu vào {next_run.strftime('%Y-%m-%d %H:%M:%S')} GMT+7")
        logger.info(f"⏳ Đợi {wait_seconds:.0f} giây ({wait_seconds/3600:.2f} giờ)...")
        
        await discord.utils.sleep_until(next_run)


async def setup(bot: commands.Bot):
    await bot.add_cog(Fuel(bot))







