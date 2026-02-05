from discord.ext import commands
from utils.logger import setup_logger
from utils.helpers import is_allowed_channel_for_message
import asyncio
import re
import discord
from datetime import datetime
from core.ai_handler import AIHandler

logger = setup_logger(__name__)

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ai_handler = AIHandler()

    def _is_timed_out(self, member: discord.Member) -> bool:
        return member.is_timed_out()

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """Xử lý lỗi commands - bỏ qua CommandNotFound để không ảnh hưởng đến on_message events"""
        if isinstance(error, commands.CommandNotFound):
            # Bỏ qua lỗi CommandNotFound vì chúng ta đang xử lý các lệnh trong on_message
            return
        else:
            # Log các lỗi khác
            logger.error(f"Command error in {ctx.command}: {error}")

    @commands.Cog.listener()
    async def on_message(self, message):
        # Bỏ qua tin nhắn của bot NGAY LẬP TỨC
        if message.author.bot:
            return
        
        if message.author == self.bot.user:
            return

        # Kiểm tra xem channel có được phép không
        if not is_allowed_channel_for_message(message.channel.id):
            return

        if message.guild and isinstance(message.author, discord.Member):
            if self._is_timed_out(message.author):
                try:
                    await message.delete()
                except Exception:
                    pass
                return

        # Greeting feature - các từ phải đơn lẻ
        greetings = ['chào','hí', 'hello', 'hey', 'chao']
        message_content = message.content.lower().strip()
        
        # Kiểm tra xem có từ nào trong greetings là từ riêng lẻ
        # Sử dụng regex để kiểm tra word boundaries
        for greeting in greetings:
            if re.search(r'\b' + re.escape(greeting) + r'\b', message_content):
                # Mention người dùng
                bot_message = await message.reply(f'Ờ anh chào {message.author.mention} Nhá 👋 em là {message.author.mention} hả, em chối làm sao được ')
                
                # Xóa tin nhắn sau 10 giây
                await asyncio.sleep(10)
                try:
                    await bot_message.delete()
                    await message.delete()
                except:
                    pass
                return  # Dừng xử lý sau khi reply
        
        # Kiểm tra tin nhắn chứa từ cấm -> xóa ngay tin nhắn người dùng
        banned_phrases = ["chó độ", "độ ngu", "từ cha","độ shisha","xin lỗi,tày"]
        if any(phrase in message_content for phrase in banned_phrases):
            if message.guild:
                permissions = message.channel.permissions_for(message.guild.me)
                if not permissions.manage_messages:
                    logger.warning("Missing Manage Messages permission to delete user message.")
                    return
            try:
                await message.delete()
            except Exception as e:
                logger.warning(f"Failed to delete message: {e}")
            return
        
        # Kiểm tra tin nhắn chứa "khô gà1"
        if 'khô gà1' in message_content:
            bot_message = await message.reply('https://media.discordapp.net/attachments/1439553447384060047/1461010970682986658/508669079_1261013605577267_5195994080152027537_n.png?ex=6968ffff&is=6967ae7f&hm=75e359f1213ffba9f8fb756922147bb6cf8daa5af70d8db44fa1967a887ce733&=&format=webp&quality=lossless&width=1191&height=894')
            
            # Xóa tin nhắn sau 10 giây
            await asyncio.sleep(10)
            try:
                await bot_message.delete()
                await message.delete()
            except:
                pass
            return  # Thêm return
        
        # Kiểm tra tin nhắn chứa "xây trường", "xây nhà" hoặc "việc tốt anh độ"
        good_deeds = ['xây trường', 'xây nhà', 'việc tốt anh độ']
        for deed in good_deeds:
            if deed in message_content:
                bot_message = await message.reply(f'Anh gửi Khô Gà mixi cho {message.author.mention} nhé 🥳 https://media.discordapp.net/attachments/1459229057706364939/1461582560332087399/shopee_vn-11134103-22120-depw1vmsf0kv16.png?ex=696b1455&is=6969c2d5&hm=eddc74afe016d7f9dd4e1922f6ab7930a0446e1e29ba21bc988cf1c817a93d58&=&format=webp&quality=lossless&width=555&height=740')
                
                # Xóa tin nhắn sau 20 giây
                await asyncio.sleep(10)
                try:
                    await bot_message.delete()
                    await message.delete()
                except:
                    pass
                return  # Thêm return
        
        # Kiểm tra tin nhắn chứa "anh độ" - sử dụng AI
        if 'anh độ4444' in message_content:
            try:
                async with message.channel.typing():
                    # Tạo phản hồi từ AI
                    response = await self.ai_handler.generate_response(
                        message.content,
                        user_id=str(message.author.id),
                        username=message.author.name
                    )
                    bot_message = await message.reply(response)
                    
                    # Xóa tin nhắn sau 15 giây
                    await asyncio.sleep(20)
                    try:
                        await bot_message.delete()
                        await message.delete()
                    except:
                        pass
            except Exception as e:
                logger.error(f"Error in anh độ AI response: {e}")
            return  # Thêm return
        
        # Kiểm tra tin nhắn chứa "tóm tắt đoạn chat" hoặc "tóm tắt chat"
        if 'tóm tắt đoạn chat1111111' in message_content or 'tóm tắt chat1111111' in message_content:
            try:
                async with message.channel.typing():
                    # Lấy 20 tin nhắn gần nhất (không tính tin nhắn lệnh)
                    messages = []
                    async for msg in message.channel.history(limit=21):
                        if msg.id != message.id and msg.content.strip():  # Bỏ qua lệnh và tin nhắn rỗng
                            messages.append(msg)
                        if len(messages) == 20:
                            break
                    
                    if len(messages) == 0:
                        bot_message = await message.reply("⚠️ Không có tin nhắn nào để tóm tắt!")
                        await asyncio.sleep(20)
                        try:
                            await bot_message.delete()
                            await message.delete()
                        except:
                            pass
                        return
                    
                                        # Kiểm tra tin nhắn chứa "uia"
                    if 'uia22222' in message_content:
                        bot_message = await message.reply("https://media.discordapp.net/attachments/1459229057706364939/1466773166641647730/maxresdefault.png?ex=697df676&is=697ca4f6&hm=37067284bb32395bf695e36afbba9ff9be73761e0e035a1a165b1e7084994da5&=&format=webp&quality=lossless&width=1401&height=788")
                        
                        # Xóa tin nhắn sau 10 giây
                        await asyncio.sleep(10)
                        try:
                            await bot_message.delete()
                            await message.delete()
                        except:
                            pass
                    
                    # Đảo ngược để có thứ tự từ cũ đến mới
                    messages.reverse()
                    
                    # Tạo văn bản từ các tin nhắn để AI tóm tắt
                    messages_text = ""
                    for i, msg in enumerate(messages, 1):
                        author = msg.author.display_name
                        content = msg.content
                        time = msg.created_at.strftime('%H:%M')
                        
                        if msg.attachments:
                            content += f" [đính kèm {len(msg.attachments)} file]"
                        
                        messages_text += f"{i}. {author} ({time}): {content}\n"
                    
                    # Gọi AI để tóm tắt
                    ai_summary = await self.ai_handler.summarize_messages(messages_text)
                    
                    if ai_summary:
                        # Tạo embed đẹp cho kết quả
                        embed = discord.Embed(
                            title="📊 TÓM TẮT HỘI THOẠI",
                            description=ai_summary,
                            color=discord.Color.blue(),
                            timestamp=datetime.now()
                        )
                        embed.set_footer(text=f"Tóm tắt {len(messages)} tin nhắn | Kênh #{message.channel.name}")
                        embed.add_field(name="Người yêu cầu", value=message.author.mention, inline=True)
                        
                        bot_message = await message.channel.send(embed=embed)
                    else:
                        # Fallback: nếu AI lỗi, hiển thị danh sách tin nhắn
                        summary_lines = [
                            f"📊 **TÓM TẮT {len(messages)} TIN NHẮN GẦN NHẤT**",
                            f"_(AI không khả dụng, hiển thị danh sách tin nhắn)_",
                            f"Kênh: #{message.channel.name}",
                            "",
                            "─" * 50,
                            ""
                        ]
                        
                        for i, msg in enumerate(messages, 1):
                            author = msg.author.display_name
                            content = msg.content[:80] + "..." if len(msg.content) > 80 else msg.content
                            time = msg.created_at.strftime('%H:%M')
                            summary_lines.append(f"`{i}.` **{author}** ({time}): {content}")
                        
                        summary_text = "\n".join(summary_lines)
                        
                        if len(summary_text) > 2000:
                            chunks = [summary_text[i:i+1900] for i in range(0, len(summary_text), 1900)]
                            bot_message = None
                            for chunk in chunks:
                                bot_message = await message.channel.send(chunk)
                        else:
                            bot_message = await message.channel.send(summary_text)
                    
                    # Xóa tin nhắn sau 20 giây
                    await asyncio.sleep(20)
                    try:
                        await bot_message.delete()
                        await message.delete()
                    except:
                        pass

                        
            except Exception as e:
                logger.error(f"Error in summarize chat: {e}")
                error_msg = await message.reply("❌ Có lỗi xảy ra khi tóm tắt chat!")
                await asyncio.sleep(20)
                try:
                    await error_msg.delete()
                    await message.delete()
                except:
                    pass
        
        # Kiểm tra lệnh !id để hiển thị ID người dùng
        if message_content.startswith('!id'):
            try:
                # Kiểm tra xem có mention ai không
                if message.mentions:
                    target_user = message.mentions[0]
                else:
                    target_user = message.author
                
                # Tạo embed hiển thị ID
                embed = discord.Embed(
                    title=f"🆔 Thông tin ID của {target_user.display_name}",
                    color=discord.Color.green(),
                    timestamp=datetime.now()
                )
                embed.add_field(name="User ID", value=f"`{target_user.id}`", inline=False)
                embed.add_field(name="Username", value=f"`{target_user.name}`", inline=True)
                embed.add_field(name="Display Name", value=f"`{target_user.display_name}`", inline=True)
                embed.set_thumbnail(url=target_user.display_avatar.url)
                embed.set_footer(text=f"Yêu cầu bởi {message.author.display_name}")
                
                bot_message = await message.reply(embed=embed)
                
                # Xóa tin nhắn sau 10 giây
                await asyncio.sleep(10)
                try:
                    await bot_message.delete()
                    await message.delete()
                except:
                    pass
            except Exception as e:
                logger.error(f"Error showing user ID: {e}")
            return  # Thêm return để tránh xử lý tiếp
        
        # Kiểm tra lệnh !avt để hiển thị avatar
        if message_content.startswith('!avt'):
            logger.info(f"Processing !avt command from {message.author.name} (ID: {message.author.id})")
            try:
                # Kiểm tra xem có mention ai không
                if message.mentions:
                    target_user = message.mentions[0]
                else:
                    target_user = message.author
                
                logger.info(f"Target user: {target_user.name}")
                
                # Lấy avatar URL
                avatar_url = target_user.display_avatar.url
                
                # Tạo embed hiển thị avatar
                embed = discord.Embed(
                    title=f"🖼️ Avatar của {target_user.display_name}",
                    color=discord.Color.blue(),
                    timestamp=datetime.now()
                )
                embed.set_image(url=avatar_url)
                embed.set_footer(text=f"Yêu cầu bởi {message.author.display_name}")
                
                # Thêm link tải avatar
                embed.add_field(
                    name="📥 Tải avatar",
                    value=f"[Click để tải]({avatar_url})",
                    inline=False
                )
                
                bot_message = await message.reply(embed=embed)
                
                # Xóa tin nhắn sau 5 giây
                await asyncio.sleep(5)
                try:
                    await bot_message.delete()
                    await message.delete()
                except:
                    pass
            except Exception as e:
                logger.error(f"Error showing avatar: {e}")
            return  # Thêm return để tránh xử lý tiếp
        
        # Kiểm tra lệnh !timeout để xóa timeout của tất cả người dùng
        if message_content.startswith('!1timeout'):
            # Danh sách ID role được phép sử dụng
            ALLOWED_ROLE_IDS = [
                1185158470958333953,  # Mod
                1401564796553265162,1185183734153097296   # Supervisor
            ]
            
            # Kiểm tra quyền admin hoặc role được phép
            is_admin = message.author.guild_permissions.administrator
            has_allowed_role = any(role.id in ALLOWED_ROLE_IDS for role in message.author.roles)
            
            # Debug: log thông tin để kiểm tra
            logger.info(f"User {message.author.name} (ID: {message.author.id}) attempted !1timeout")
            logger.info(f"Is admin: {is_admin}")
            logger.info(f"User roles: {[f'{role.name} (ID: {role.id})' for role in message.author.roles]}")
            logger.info(f"Has allowed role: {has_allowed_role}")
            
            if not (is_admin or has_allowed_role):
                bot_message = await message.reply(f"❌ Bạn không có quyền sử dụng lệnh này!\n**Your roles:** {', '.join([f'{role.name} ({role.id})' for role in message.author.roles if role.name != '@everyone'])}")
                await asyncio.sleep(10)
                try:
                    await bot_message.delete()
                    await message.delete()
                except:
                    pass
                return
            
            try:
                # Đếm số người bị timeout dưới 2 tiếng
                from datetime import timedelta
                
                timed_out_members = []
                skipped_members = []
                
                for member in message.guild.members:
                    if member.is_timed_out():
                        # Kiểm tra thời gian timeout còn lại
                        if member.timed_out_until:
                            time_remaining = member.timed_out_until - datetime.now(member.timed_out_until.tzinfo)
                            
                            # Nếu thời gian còn lại dưới 2 tiếng (7200 giây)
                            if time_remaining.total_seconds() < 7200:
                                timed_out_members.append(member)
                            else:
                                skipped_members.append(member)
                
                if not timed_out_members:
                    if skipped_members:
                        bot_message = await message.reply(f"⚠️ Không có người dùng nào bị timeout dưới 2 tiếng!\n({len(skipped_members)} người bị timeout trên 2 tiếng sẽ không được xóa)")
                    else:
                        bot_message = await message.reply("✅ Không có người dùng nào bị timeout!")
                    await asyncio.sleep(5)
                    try:
                        await bot_message.delete()
                        await message.delete()
                    except:
                        pass
                    return
                
                # Xóa timeout cho các thành viên có timeout dưới 2 tiếng
                success_count = 0
                fail_count = 0
                
                status_msg = f"⏳ Đang xóa timeout cho {len(timed_out_members)} người dùng (dưới 2 tiếng)..."
                if skipped_members:
                    status_msg += f"\n⚠️ Bỏ qua {len(skipped_members)} người (timeout trên 2 tiếng)"
                
                status_message = await message.reply(status_msg)
                
                for member in timed_out_members:
                    try:
                        await member.timeout(None, reason=f"Timeout removed by {message.author.name}")
                        success_count += 1
                    except Exception as e:
                        logger.error(f"Failed to remove timeout for {member.name}: {e}")
                        fail_count += 1
                
                # Tạo embed kết quả
                embed = discord.Embed(
                    title="✅ XÓA TIMEOUT HOÀN TẤT",
                    color=discord.Color.green(),
                    timestamp=datetime.now()
                )
                embed.add_field(name="Thành công", value=f"✅ {success_count} người", inline=True)
                embed.add_field(name="Thất bại", value=f"❌ {fail_count} người", inline=True)
                embed.set_footer(text=f"Thực hiện bởi {message.author.display_name}")
                
                await status_message.edit(content=None, embed=embed)
                
                # Xóa tin nhắn sau 15 giây
                await asyncio.sleep(15)
                try:
                    await status_message.delete()
                    await message.delete()
                except:
                    pass
                
            except Exception as e:
                logger.error(f"Error in timeout removal: {e}")
                error_msg = await message.reply("❌ Có lỗi xảy ra khi xóa timeout!")
                await asyncio.sleep(5)
                try:
                    await error_msg.delete()
                    await message.delete()
                except:
                    pass





























async def setup(bot):
    await bot.add_cog(Events(bot))
