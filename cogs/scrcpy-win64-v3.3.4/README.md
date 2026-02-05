# 📱 Tool Scrcpy Wireless Connection

Tool tự động hóa kết nối điện thoại Android với máy tính qua mạng nội bộ (WiFi) sử dụng scrcpy.

## ✨ Tính năng

- 🔄 Tự động phát hiện thiết bị USB
- 🌐 Tự động lấy địa chỉ IP của điện thoại
- 🔌 Tự động bật chế độ TCP/IP
- 📡 Kết nối qua mạng WiFi nội bộ
- 🚀 Tự động khởi chạy scrcpy

## 📋 Yêu cầu

1. **ADB (Android Debug Bridge)**
   - Tải từ: https://developer.android.com/studio/releases/platform-tools
   - Hoặc cài đặt qua package manager:
     - Windows: `choco install adb`
     - Linux: `sudo apt install adb`
     - Mac: `brew install android-platform-tools`

2. **Scrcpy**
   - Windows: `choco install scrcpy` hoặc tải từ [GitHub Releases](https://github.com/Genymobile/scrcpy/releases)
   - Linux: `sudo apt install scrcpy`
   - Mac: `brew install scrcpy`

3. **Điện thoại Android**
   - Đã bật USB Debugging
   - Cùng mạng WiFi với máy tính

## 🚀 Cách sử dụng

### Phương pháp 1: Python Script (Khuyến nghị)

```bash
# Lần đầu kết nối (cần USB)
python scrcpy_wireless.py

# Kết nối trực tiếp nếu đã biết IP
python scrcpy_wireless.py --ip 192.168.1.100

# Bỏ qua bước USB (nếu đã bật TCP/IP trước đó)
python scrcpy_wireless.py --skip-usb

# Thêm tùy chọn cho scrcpy
python scrcpy_wireless.py --scrcpy-options "--max-size 1024 --bit-rate 2M"
```

### Phương pháp 2: Batch Script (Windows)

Chỉ cần chạy file `scrcpy_wireless.bat` (double-click hoặc chạy từ terminal).

### Phương pháp 3: Thủ công

Nếu bạn muốn tự làm thủ công:

```bash
# 1. Kết nối USB và kiểm tra
adb devices

# 2. Bật TCP/IP
adb tcpip 5555

# 3. Lấy IP của điện thoại (chạy trên điện thoại hoặc xem trong Settings)
# Hoặc dùng: adb shell ip route

# 4. Kết nối qua mạng (thay IP bằng IP thực của bạn)
adb connect 192.168.1.100:5555

# 5. Ngắt USB
adb disconnect

# 6. Chạy scrcpy
scrcpy
```

## 📖 Các tùy chọn

### Python Script

- `--ip <IP>`: Kết nối trực tiếp với IP đã biết (bỏ qua bước USB)
- `--port <PORT>`: Chỉ định cổng TCP/IP (mặc định: 5555)
- `--skip-usb`: Bỏ qua bước kết nối USB
- `--scrcpy-options "<options>"`: Thêm tùy chọn cho scrcpy

### Ví dụ tùy chọn scrcpy phổ biến

```bash
# Giảm kích thước màn hình
--max-size 1024

# Giảm bitrate để tiết kiệm băng thông
--bit-rate 2M

# Tắt màn hình điện thoại khi mirror
--turn-screen-off

# Luôn bật màn hình
--stay-awake

# Ghi lại màn hình
--record file.mp4
```

## 🔧 Xử lý sự cố

### Không tìm thấy thiết bị USB
- Kiểm tra cáp USB
- Bật USB Debugging trong Developer Options
- Chấp nhận yêu cầu USB Debugging trên điện thoại
- Thử cài lại USB driver

### Không thể kết nối qua mạng
- Đảm bảo điện thoại và máy tính cùng mạng WiFi
- Kiểm tra firewall không chặn cổng 5555
- Thử reset TCP/IP: `adb tcpip 5555` (khi đã kết nối USB)
- Kiểm tra IP có đúng không

### Scrcpy không chạy
- Đảm bảo đã cài đặt scrcpy
- Kiểm tra scrcpy có trong PATH không
- Thử chạy `scrcpy` trực tiếp để xem lỗi

## 📝 Lưu ý

1. **Lần đầu tiên**: Phải kết nối qua USB để bật TCP/IP
2. **Sau khi khởi động lại điện thoại**: Cần bật lại TCP/IP (kết nối USB một lần nữa)
3. **Bảo mật**: Chỉ dùng trong mạng nội bộ an toàn, không dùng trên mạng công cộng
4. **Hiệu suất**: Kết nối WiFi phụ thuộc vào chất lượng mạng, có thể có độ trễ

## 🎯 Tips

- Sau khi kết nối lần đầu, bạn có thể lưu IP và dùng `--ip` để kết nối nhanh hơn
- Nếu điện thoại có IP tĩnh, sẽ dễ dàng hơn
- Có thể tạo shortcut với IP cố định để kết nối nhanh

## 📄 License

MIT License - Tự do sử dụng và chỉnh sửa

