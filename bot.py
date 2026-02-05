import discord
from discord.ext import commands
import config
import os
from utils.logger import setup_logger
import asyncio
import threading
from core.ai_handler import AIHandler
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

logger = setup_logger(__name__)

# Channel ID để gửi tin nhắn (thay đổi ID này)
TARGET_CHANNEL_ID = 1467752219012108446

class CogReloader(FileSystemEventHandler):
    """Tự động reload cogs khi file thay đổi"""
    def __init__(self, bot):
        self.bot = bot
        self.cooldown = {}  # Tránh reload nhiều lần
        
    def on_modified(self, event):
        if event.src_path.endswith('.py') and 'cogs' in event.src_path and not event.is_directory:
            # Lấy tên cog từ đường dẫn
            cog_name = os.path.basename(event.src_path)[:-3]
            
            # Cooldown 1 giây để tránh reload nhiều lần
            import time
            current_time = time.time()
            if cog_name in self.cooldown and current_time - self.cooldown[cog_name] < 1:
                return
            
            self.cooldown[cog_name] = current_time
            
            # Reload cog trong bot's event loop
            asyncio.run_coroutine_threadsafe(
                self.reload_cog(cog_name),
                self.bot.loop
            )
    
    async def reload_cog(self, cog_name):
        """Reload một cog"""
        try:
            await self.bot.reload_extension(f'cogs.{cog_name}')
            logger.info(f'🔄 Auto-reloaded: {cog_name}')
            print(f'✅ Đã reload cog: {cog_name}')
        except Exception as e:
            logger.error(f'❌ Failed to reload {cog_name}: {e}')
            print(f'❌ Lỗi khi reload {cog_name}: {e}')

class MixiBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix='!',
            intents=discord.Intents.all(),
            help_command=None
        )
        self.ai_handler = AIHandler()

    async def setup_hook(self):
        # Load cogs
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py') and filename != '__init__.py':
                try:
                    await self.load_extension(f'cogs.{filename[:-3]}')
                    logger.info(f'Loaded extension: {filename}')
                except Exception as e:
                    logger.error(f'Failed to load extension {filename}: {e}')

    async def on_ready(self):
        logger.info(f'Logged in as {self.user} (ID: {self.user.id})')
        logger.info('------')
        
        # Bắt đầu file watcher để auto-reload cogs
        if not hasattr(self, 'watcher_started'):
            self.watcher_started = True
            self.start_file_watcher()
        
        # Bắt đầu thread đọc input từ terminal
        if not hasattr(self, 'input_thread_started'):
            self.input_thread_started = True
            input_thread = threading.Thread(target=self.read_terminal_input, daemon=True)
            input_thread.start()
            logger.info("✅ Terminal input thread started")

    def start_file_watcher(self):
        """Khởi động file watcher để auto-reload cogs"""
        event_handler = CogReloader(self)
        observer = Observer()
        observer.schedule(event_handler, './cogs', recursive=False)
        observer.start()
        logger.info("👀 File watcher started - Auto-reload enabled")
        print("👀 File watcher đã bắt đầu - Tự động reload khi có thay đổi!")

    def read_terminal_input(self):
        """Đọc input từ terminal trong một thread riêng"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        while True:
            try:
                user_input = input("📝 Nhập tin nhắn (hoặc 'exit' để thoát): ").strip()
                
                if user_input.lower() == 'exit':
                    logger.info("Thoát chương trình...")
                    break
                
                if user_input:
                    # Gửi task tới event loop của bot
                    asyncio.run_coroutine_threadsafe(
                        self.send_ai_response(user_input),
                        self.loop
                    )
            except Exception as e:
                logger.error(f"Error reading terminal input: {e}")

    async def send_ai_response(self, user_message: str):
        """Gửi tin nhắn tới channel được chỉ định"""
        try:
            # Đợi bot hoàn toàn sẵn sàng
            await self.wait_until_ready()
            
            channel = self.get_channel(TARGET_CHANNEL_ID)
            
            if not channel:
                print(f"❌ Không tìm thấy channel với ID: {TARGET_CHANNEL_ID}")
                logger.error(f"Channel {TARGET_CHANNEL_ID} not found")
                return
            
            # Log thông tin channel
            print(f"📍 Channel: {channel.name} (Type: {type(channel).__name__})")
            
            # Kiểm tra nếu là text channel trong guild
            if isinstance(channel, discord.TextChannel):
                permissions = channel.permissions_for(channel.guild.me)
                print(f"🔑 Quyền bot - Send Messages: {permissions.send_messages}, View Channel: {permissions.view_channel}")
                
                if not permissions.send_messages:
                    print("❌ Bot không có quyền Send Messages!")
                    print(f"💡 Hãy cấp quyền 'Send Messages' cho bot trong channel #{channel.name}")
                    return
                    
                if not permissions.view_channel:
                    print("❌ Bot không có quyền View Channel!")
                    return
            
            # Gửi tin nhắn
            await channel.send(user_message)
            print(f"✅ Đã gửi tin nhắn tới #{channel.name}!")
            
        except discord.Forbidden as e:
            logger.error(f"Forbidden error: {e}")
            print(f"❌ Lỗi quyền: Bot không được phép gửi tin nhắn!")
            print(f"💡 Kiểm tra quyền của bot trong Server Settings > Roles hoặc Channel Settings > Permissions")
        except discord.HTTPException as e:
            logger.error(f"HTTP error: {e}")
            print(f"❌ Lỗi Discord API: {str(e)}")
        except Exception as e:
            logger.error(f"Error sending AI response: {e}")
            print(f"❌ Lỗi không xác định: {str(e)}")












if __name__ == '__main__':
    bot = MixiBot()
    bot.run(config.TOKEN)
