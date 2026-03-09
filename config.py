import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
OWNER_ID = os.getenv('OWNER_ID')
OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY', '')

# Danh sách ID các kênh được phép sử dụng bot
# Thay thế các ID này bằng ID kênh của bạn
ALLOWED_CHANNELS = [
    1418088580344971375,1446865411814588426,1467752219012108446,1467224738308030474,1439553447384060047,1471789145725862010,1471804180514476043,1474535485488631911

      # Thay thế bằng ID channel 2
    # Thêm ID channel khác tại đây
]

# Server để lọc bot (tài khoản bị xâm nhập)
# Thay thế bằng ID server của bạn

BOT_FILTER_CHANNELS = [1411448689192603669]  # Thay bằng ID kênh thực

# ID kênh để gửi tin nhắn hàng ngày lúc 5h sáng GMT+0 
DAILY_MESSAGE_CHANNEL_ID = 1446865411814588426  # Thay bằng ID kênh của bạn

# ===== CẤU HÌNH ĐẾM NGƯỢC =====
# ID kênh để gửi thông báo đếm ngược lúc 7h sáng GMT+7
COUNTDOWN_CHANNEL_ID = [1446865411814588426,1446866616452386856]  # Thay bằng ID kênh của bạn

# Tên sự kiện đếm ngược
COUNTDOWN_EVENT_NAME = "Kỳ thi Đánh giá năng lực (V-ACT) của ĐHQG-HCM"

# Ngày mục tiêu (năm, tháng, ngày) - định dạng: "YYYY-MM-DD"
COUNTDOWN_TARGET_DATE = "2026-04-05"

# ===== CẤU HÌNH NHẮC NHỞ THPT =====
# ID kênh mặc định gửi đếm ngược THPT lúc 7h30 GMT+7 (dùng khi chưa set bằng !setremainch)
THPT_REMINDER_CHANNEL_ID = [1446865411814588426,1446866616452386856]  # Thay bằng ID kênh của bạn

# ===== CẤU HÌNH DONATE =====
# # ID kênh để gửi nhắc nhở donate mỗi 1 giờ
DONATE_CHANNEL_ID = [1446865411814588426]  # Thay bằng ID kênh của bạn1

# Link donate
DONATE_LINK = "https://s.shopee.vn/3VfIUZpo9p"

# Số tin nhắn liên tục trong khoảng thời gian để trigger donate
DONATE_TRIGGER_COUNT = 10  # Số tin nhắn cần đạt
DONATE_TRIGGER_WINDOW = 60  # Khoảng thời gian (giây) để đếm tin nhắn (mặc định 60s)
DONATE_COOLDOWN = 3600  # Thời gian chờ giữa 2 lần gửi donate (giây, mặc định 1 giờ)

# ===== CẤU HÌNH TIN NHẮN THEO GIỜ =====
# ID kênh (hoặc danh sách ID) nhận tin nhắn tự động theo lịch
# Chỉnh lịch & nội dung tin nhắn trong cogs/daily.py
SCHEDULED_CHANNEL_ID = [1439553447384060047,1446865411814588426]  # Thay bằng ID kênh của bạn

# ===== CẤU HÌNH CALL =====
# Danh sách ID kênh được phép sử dụng chức năng gọi điện

CALL_ALLOWED_CHANNELS = [
    # Thêm ID kênh vào đây
   1446865411814588426



]

# ===== CẤU HÌNH PHOTOBOOTH =====
# Role ID mặc định cho lệnh !chuphinh / /chuphinh
# Thay 123 bằng ID role thực tế của bạn
PHOTOBOOTH_ROLE_ID = 1474535485488631911


