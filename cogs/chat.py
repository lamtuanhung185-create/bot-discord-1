from discord.ext import commands
from utils.logger import setup_logger
from utils.helpers import is_allowed_channel
from core.ai_handler import AIHandler
import discord
import asyncio
from datetime import datetime
import time

logger = setup_logger(__name__)

class Chat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ai_handler = AIHandler()
        self.tomtat_cooldown = {}  # Lưu thời gian sử dụng lệnh !tomtat theo user_id

    @commands.command(name='ai', aliases=['chat', 'ask'])
    @is_allowed_channel()
    async def ai(self, ctx, *, message: str):
        """Tương tác với AI bot. Sử dụng: !ai <tin nhắn>"""
        try:
            async with ctx.typing():
                response = await self.ai_handler.generate_response(
                    message, 
                    user_id=str(ctx.author.id),
                    username=ctx.author.name
                )
                bot_message = await ctx.reply(response, mention_author=False)
                
                # Tự động xóa tin nhắn sau 15 giây
                await asyncio.sleep(15)
                try:
                    await bot_message.delete()
                    await ctx.message.delete()
                except:
                    pass  # Bỏ qua nếu không thể xóa
        except Exception as e:
            logger.error(f"Error in ai command: {e}")
            error_msg = await ctx.reply("Xin lỗi, có lỗi xảy ra khi xử lý yêu cầu của bạn.")
            await asyncio.sleep(15)
            try:
                await error_msg.delete()
                await ctx.message.delete()
            except:
                pass
    @commands.command(name='clear', aliases=['reset'])
    @is_allowed_channel()
    async def clear_history(self, ctx):
        """Xóa lịch sử hội thoại với AI"""
        user_id = str(ctx.author.id)
        if self.ai_handler.context_manager.clear_conversation(user_id):
            msg = await ctx.reply("✅ Đã xóa lịch sử hội thoại của bạn!")
        else:
            msg = await ctx.reply("⚠️ Bạn chưa có lịch sử hội thoại nào!")
        
        # Tự động xóa sau 8 giây
        await asyncio.sleep(8)
        try:
            await msg.delete()
            await ctx.message.delete()
        except:
            pass
    @commands.command(name='tomtat', aliases=['summary', 'tóm tắt'])
    @is_allowed_channel()
    async def summarize_chat(self, ctx):
        """Tóm tắt 20 tin nhắn gần nhất trong kênh bằng AI"""
        try:
            # Kiểm tra cooldown (30 giây)
            user_id = ctx.author.id
            current_time = time.time()
            
            if user_id in self.tomtat_cooldown:
                time_since_last = current_time - self.tomtat_cooldown[user_id]
                if time_since_last < 30:  # 30 giây cooldown
                    # Gửi link ảnh khi spam
                    await ctx.reply("https://media.discordapp.net/attachments/1467224738308030474/1467918946144485617/24695f6a9571439a8526f2f078282f54tplv-jj85edgx6n-image-origin.png?ex=6982ca4d&is=698178cd&hm=ff1b39a5425c5c08786ba1b46f5b4e25db362fd5aef979eee0b0e1d408a8cbb5&=")
                    return
            
            # Cập nhật thời gian sử dụng
            self.tomtat_cooldown[user_id] = current_time
            
            async with ctx.typing():
                # Lấy 50 tin nhắn gần nhất (không tính tin nhắn lệnh)
                messages = []
                async for message in ctx.channel.history(limit=100):
                    if message.id != ctx.message.id and message.content.strip():  # Bỏ qua lệnh và tin nhắn rỗng
                        messages.append(message)
                    if len(messages) == 80:  # Giới hạn tối đa 80 tin nhắn
                        break
                
                if len(messages) == 0:
                    await ctx.reply("⚠️ Không có tin nhắn nào để tóm tắt!")
                    return
                
                # Đảo ngược để có thứ tự từ cũ đến mới
                messages.reverse()
                
                # Tạo văn bản từ các tin nhắn để AI tóm tắt
                messages_text = ""
                for i, msg in enumerate(messages, 1):
                    author = msg.author.display_name
                    content = msg.content
                    msg_time = msg.created_at.strftime('%H:%M')
                    
                    if msg.attachments:
                        content += f" [đính kèm {len(msg.attachments)} file]"
                    
                    messages_text += f"{i}. {author} ({msg_time}): {content}\n"
                
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
                    embed.set_footer(text=f"Tóm tắt {len(messages)} tin nhắn | Kênh #{ctx.channel.name}")
                    embed.add_field(name="Người yêu cầu", value=ctx.author.mention, inline=True)
                    
                    await ctx.send(embed=embed)
                else:
                    # Fallback: nếu AI lỗi, hiển thị danh sách tin nhắn
                    summary_lines = [
                        f"📊 **TÓM TẮT {len(messages)} TIN NHẮN GẦN NHẤT**",
                        f"_(AI không khả dụng, hiển thị danh sách tin nhắn)_",
                        f"Kênh: #{ctx.channel.name}",
                        "",
                        "─" * 50,
                        ""
                    ]
                    
                    for i, msg in enumerate(messages, 1):
                        author = msg.author.display_name
                        content = msg.content[:80] + "..." if len(msg.content) > 80 else msg.content
                        msg_time = msg.created_at.strftime('%H:%M')
                        summary_lines.append(f"`{i}.` **{author}** ({msg_time}): {content}")
                    
                    summary_text = "\n".join(summary_lines)
                    
                    if len(summary_text) > 2000:
                        chunks = [summary_text[i:i+1900] for i in range(0, len(summary_text), 1900)]
                        for chunk in chunks:
                            await ctx.send(chunk)
                    else:
                        await ctx.send(summary_text)
                
                # Xóa tin nhắn lệnh sau khi gửi
                try:
                    await ctx.message.delete()
                except:
                    pass
                    
        except Exception as e:
            logger.error(f"Error in summarize_chat command: {e}")
            await ctx.reply("❌ Có lỗi xảy ra khi tóm tắt chat!")

            

async def setup(bot):
    await bot.add_cog(Chat(bot))
