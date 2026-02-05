import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
OWNER_ID = os.getenv('OWNER_ID')

# Danh sách ID các kênh được phép sử dụng bot
# Thay thế các ID này bằng ID kênh của bạn
ALLOWED_CHANNELS = [
    1418088580344971375,1446865411814588426,1467752219012108446

      # Thay thế bằng ID channel 2
    # Thêm ID channel khác tại đây
]
