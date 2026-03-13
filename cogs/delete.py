import discord
from discord.ext import commands
from utils.logger import setup_logger

logger = setup_logger(__name__)

ALLOWED_ROLE_IDS = [1185158470958333953]

class Delete(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="delete")
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True, read_message_history=True)
    async def delete_user_messages(self, ctx: commands.Context, member: discord.Member, amount: int = 30):
        """
        Xóa tin nhắn của người dùng được đề cập
        
        Sử dụng: !delete @user [số lượng]
        Ví dụ: !delete @user 30
        """
        # Kiểm tra role của người dùng
        user_role_ids = [role.id for role in ctx.author.roles]
        has_required_role = any(role_id in ALLOWED_ROLE_IDS for role_id in user_role_ids)
        
        if not has_required_role:
            await ctx.send(f"❌ Bạn không có quyền sử dụng lệnh này! Cần một trong các role ID: {', '.join(map(str, ALLOWED_ROLE_IDS))}")
            logger.warning(f"{ctx.author} cố gắng dùng !delete nhưng không có role phù hợp")
            return
        
        if amount <= 0:
            await ctx.send("❌ Số lượng tin nhắn phải lớn hơn 0!")
            return
        
        if amount > 100:
            await ctx.send("❌ Chỉ có thể xóa tối đa 100 tin nhắn mỗi lần!")
            return
        
        try:
            # Gửi thông báo đang xử lý
            processing_msg = await ctx.send(f"🔍 Đang tìm và xóa tin nhắn của {member.mention}...")
            
            # Xóa tin nhắn lệnh
            try:
                await ctx.message.delete()
            except:
                pass
            
            # Lọc và xóa tin nhắn của user được đề cập
            deleted = 0
            checked = 0
            
            # Tăng limit lên để tìm đủ tin nhắn
            async for message in ctx.channel.history(limit=1000):
                checked += 1
                if message.author.id == member.id:
                    try:
                        await message.delete()
                        deleted += 1
                        logger.info(f"Đã xóa tin nhắn ID {message.id} của {member}")
                        if deleted >= amount:
                            break
                    except discord.errors.NotFound:
                        logger.warning(f"Tin nhắn {message.id} không tìm thấy")
                        continue
                    except discord.errors.Forbidden:
                        logger.error(f"Không có quyền xóa tin nhắn {message.id}")
                        continue
                    except Exception as e:
                        logger.error(f"Lỗi khi xóa tin nhắn {message.id}: {e}")
                        continue
            
            # Xóa thông báo đang xử lý
            try:
                await processing_msg.delete()
            except:
                pass
            
            # Gửi thông báo kết quả
            if deleted > 0:
                result_msg = await ctx.send(f"✅ Đã xóa **{deleted}** tin nhắn của {member.mention} (đã kiểm tra {checked} tin nhắn)")
                logger.info(f"{ctx.author} (roles: {user_role_ids}) đã xóa {deleted} tin nhắn của {member} trong #{ctx.channel.name}")
            else:
                result_msg = await ctx.send(f"⚠️ Không tìm thấy tin nhắn nào của {member.mention} trong {checked} tin nhắn gần nhất")
                logger.warning(f"{ctx.author} không tìm thấy tin nhắn của {member} trong #{ctx.channel.name}")
            
            # Tự xóa sau 5 giây
            await result_msg.delete(delay=5)
            
        except discord.Forbidden as e:
            await ctx.send(f"❌ Bot không có quyền cần thiết! Cần: Manage Messages, Read Message History\nLỗi: {e}")
            logger.error(f"Forbidden error: {e}")
        except Exception as e:
            await ctx.send(f"❌ Có lỗi xảy ra: {str(e)}")
            logger.error(f"Lỗi trong lệnh delete: {e}", exc_info=True)

    @delete_user_messages.error
    async def delete_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.BotMissingPermissions):
            await ctx.send("❌ Bot không có quyền cần thiết! (Cần quyền: Manage Messages, Read Message History)")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("❌ Vui lòng đề cập người dùng cần xóa tin nhắn!\nSử dụng: `!delete @user [số lượng]`")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("❌ Không tìm thấy người dùng hoặc số lượng không hợp lệ!")
        else:
            await ctx.send(f"❌ Có lỗi xảy ra: {str(error)}")
            logger.error(f"Lỗi trong delete command: {error}", exc_info=True)

async def setup(bot):
    await bot.add_cog(Delete(bot))
