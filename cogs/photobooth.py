"""
Cog Photobooth — !chuphinh / /chuphinh
Create a group photo collage from role members or mentioned users.
"""

import discord
import asyncio
from discord.ext import commands
from discord import app_commands
from utils.helpers import is_allowed_channel
import config
from photobooth import create_group_photo

DELETE_AFTER = 20  # Tự động xoá sau 20 giây


class Photobooth(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ─── Prefix command: !chuphinh ────────────────────────────────────
    @commands.command(name="chuphinh", aliases=["photobooth", "groupphoto"])
    async def chuphinh_prefix(self, ctx: commands.Context, targets: commands.Greedy[discord.Member] = None, *, role_id: int = None):
        """
        Create a group photo collage!
        Usage:
          !chuphinh                        → members with default role
          !chuphinh @user1 @user2 ...      → specific users
          !chuphinh 123456789              → members with that role ID
        """
        # Kiểm tra kênh chat
        if ctx.channel.id != 1439553447384060047:
            return
        
        # If users were mentioned, use them directly
        if targets:
            members = [m for m in targets if not m.bot]
            # Remove duplicates while preserving order
            seen = set()
            unique = []
            for m in members:
                if m.id not in seen:
                    seen.add(m.id)
                    unique.append(m)
            members = unique
            await self._do_photobooth_members(ctx, ctx.guild, members)
        else:
            # Fallback: try to parse a role_id from the first argument
            await self._do_photobooth_role(ctx, ctx.guild, role_id)

    # ─── Slash command: /chuphinh ─────────────────────────────────────
    @app_commands.command(name="chuphinh", description="✨ Create a cute group photo collage!")
    @app_commands.describe(
        role="Pick a role to include (leave empty = default role)",
        user1="Tag a friend! (optional)",
        user2="Tag another friend! (optional)",
        user3="Tag another friend! (optional)",
        user4="Tag another friend! (optional)",
        user5="Tag another friend! (optional)",
    )
    async def chuphinh_slash(
        self,
        interaction: discord.Interaction,
        role: discord.Role = None,
        user1: discord.Member = None,
        user2: discord.Member = None,
        user3: discord.Member = None,
        user4: discord.Member = None,
        user5: discord.Member = None,
    ):
        # Kiểm tra kênh chat
        if interaction.channel.id != 1439553447384060047:
            await interaction.response.send_message(
                "❌ Lệnh này chỉ có thể sử dụng trong kênh chat được chỉ định!",
                ephemeral=True
            )
            return
        
        await interaction.response.defer(thinking=True)

        # Collect mentioned users
        mentioned = [u for u in [user1, user2, user3, user4, user5] if u is not None and not u.bot]
        # Remove duplicates
        seen = set()
        unique = []
        for m in mentioned:
            if m.id not in seen:
                seen.add(m.id)
                unique.append(m)

        if unique:
            await self._do_photobooth_members(interaction, interaction.guild, unique)
        else:
            role_id = role.id if role else None
            await self._do_photobooth_role(interaction, interaction.guild, role_id)

    # ─── Mode 1: Specific mentioned members ──────────────────────────
    async def _do_photobooth_members(self, ctx_or_inter, guild: discord.Guild, members: list):
        """Create photo from a list of specific members."""
        if not members:
            msg = await self._send(ctx_or_inter, "😿 No valid members found! Please mention someone~")
            self._schedule_delete(ctx_or_inter, msg)
            return

        processing_msg = None
        if isinstance(ctx_or_inter, commands.Context):
            names = ", ".join(m.display_name for m in members[:5])
            extra = f" +{len(members) - 5} more" if len(members) > 5 else ""
            processing_msg = await ctx_or_inter.send(
                f"✨ Creating photo for **{names}**{extra}... please wait! 💕"
            )

        try:
            buf = await create_group_photo(
                members=members,
                title="~ Friends Photo ~",
                subtitle=f"in {guild.name}",
            )

            file = discord.File(buf, filename="group_photo.png")

            names_list = ", ".join(f"**{m.display_name}**" for m in members[:10])
            extra = f" and **{len(members) - 10}** more" if len(members) > 10 else ""

            embed = discord.Embed(
                title="✨ Group Photo ✨",
                description=f"💕 {names_list}{extra}\n🌟 Total: **{len(members)}** friends!",
                color=discord.Color.from_rgb(255, 182, 193),  # cute pink
            )
            embed.set_image(url="attachment://group_photo.png")
            embed.set_footer(text=f"📸 Requested by {self._get_author_name(ctx_or_inter)} ♡ | 🗑️ Tự xoá sau {DELETE_AFTER}s")

            if processing_msg:
                try:
                    await processing_msg.delete()
                except Exception:
                    pass

            bot_msg = await self._send(ctx_or_inter, embed=embed, file=file)
            self._schedule_delete(ctx_or_inter, bot_msg)

        except Exception as e:
            msg = await self._send(ctx_or_inter, f"❌ Oops! Something went wrong: {e}")
            self._schedule_delete(ctx_or_inter, msg)

    # ─── Mode 2: Members by role ─────────────────────────────────────
    async def _do_photobooth_role(self, ctx_or_inter, guild: discord.Guild, role_id: int | None):
        """Create photo from all members with a specific role."""

        if role_id is None:
            role_id = getattr(config, "PHOTOBOOTH_ROLE_ID", None)

        if role_id is None:
            msg = await self._send(
                ctx_or_inter,
                "💡 Please provide a Role ID or mention users!\n"
                "Usage: `!chuphinh @user1 @user2` or `!chuphinh <role_id>`"
            )
            self._schedule_delete(ctx_or_inter, msg)
            return

        role = guild.get_role(role_id)
        if role is None:
            msg = await self._send(ctx_or_inter, f"😿 Can't find role with ID `{role_id}`!")
            self._schedule_delete(ctx_or_inter, msg)
            return

        members = [m for m in guild.members if role in m.roles and not m.bot]

        if not members:
            msg = await self._send(ctx_or_inter, f"😿 No members found with role **{role.name}**!")
            self._schedule_delete(ctx_or_inter, msg)
            return

        processing_msg = None
        if isinstance(ctx_or_inter, commands.Context):
            processing_msg = await ctx_or_inter.send(
                f"✨ Gathering **{len(members)}** members from **{role.name}**... 💕"
            )

        try:
            buf = await create_group_photo(
                members=members,
                title=f"~ {role.name} ~",
                subtitle=f"in {guild.name}",
            )

            file = discord.File(buf, filename="group_photo.png")

            embed = discord.Embed(
                title=f"✨ {role.name} — Group Photo ✨",
                description=f"💕 **{len(members)}** lovely members with role **{role.name}**!",
                color=role.color if role.color != discord.Color.default() else discord.Color.from_rgb(255, 182, 193),
            )
            embed.set_image(url="attachment://group_photo.png")
            embed.set_footer(text=f"📸 Requested by {self._get_author_name(ctx_or_inter)} ♡ | 🗑️ Tự xoá sau {DELETE_AFTER}s")

            if processing_msg:
                try:
                    await processing_msg.delete()
                except Exception:
                    pass

            bot_msg = await self._send(ctx_or_inter, embed=embed, file=file)
            self._schedule_delete(ctx_or_inter, bot_msg)

        except Exception as e:
            msg = await self._send(ctx_or_inter, f"❌ Oops! Something went wrong: {e}")
            self._schedule_delete(ctx_or_inter, msg)

    # ─── Helper: send message ─────────────────────────────────────────
    @staticmethod
    async def _send(ctx_or_inter, content: str = None, embed: discord.Embed = None, file: discord.File = None):
        """Send message compatible with both Context and Interaction. Returns the sent message."""
        kwargs = {}
        if content:
            kwargs["content"] = content
        if embed:
            kwargs["embed"] = embed
        if file:
            kwargs["file"] = file
        # Tắt mọi mention để tránh ping người khác
        kwargs["allowed_mentions"] = discord.AllowedMentions.none()

        if isinstance(ctx_or_inter, discord.Interaction):
            return await ctx_or_inter.followup.send(**kwargs)
        else:
            return await ctx_or_inter.send(**kwargs)

    def _schedule_delete(self, ctx_or_inter, bot_msg):
        """Lên lịch xoá tin nhắn của bot và người dùng sau DELETE_AFTER giây."""
        async def _delete_messages():
            await asyncio.sleep(DELETE_AFTER)
            # Xoá tin nhắn của bot
            try:
                if bot_msg:
                    await bot_msg.delete()
            except Exception:
                pass
            # Xoá tin nhắn lệnh của người dùng (chỉ prefix command)
            try:
                if isinstance(ctx_or_inter, commands.Context):
                    await ctx_or_inter.message.delete()
            except Exception:
                pass

        asyncio.create_task(_delete_messages())

    @staticmethod
    def _get_author_name(ctx_or_inter) -> str:
        if isinstance(ctx_or_inter, discord.Interaction):
            return ctx_or_inter.user.display_name
        return ctx_or_inter.author.display_name


async def setup(bot: commands.Bot):
    await bot.add_cog(Photobooth(bot))
