#!/usr/bin/env python3
"""
Tool scrcpy để kết nối điện thoại Android với máy tính qua mạng nội bộ
"""

import subprocess
import sys
import re
import time
import argparse

def run_command(command, check=True):
    """Chạy lệnh và trả về kết quả"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            check=check
        )
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except subprocess.CalledProcessError as e:
        return e.stdout.strip(), e.stderr.strip(), e.returncode

def check_adb_installed():
    """Kiểm tra xem adb đã được cài đặt chưa"""
    stdout, stderr, code = run_command("adb version", check=False)
    if code != 0:
        print("❌ ADB chưa được cài đặt hoặc không có trong PATH")
        print("Vui lòng cài đặt Android SDK Platform Tools:")
        print("https://developer.android.com/studio/releases/platform-tools")
        return False
    print("✅ ADB đã được cài đặt")
    return True

def check_scrcpy_installed():
    """Kiểm tra xem scrcpy đã được cài đặt chưa"""
    stdout, stderr, code = run_command("scrcpy --version", check=False)
    if code != 0:
        print("❌ Scrcpy chưa được cài đặt hoặc không có trong PATH")
        print("Vui lòng cài đặt scrcpy:")
        print("Windows: choco install scrcpy hoặc tải từ https://github.com/Genymobile/scrcpy/releases")
        print("Linux: sudo apt install scrcpy")
        print("Mac: brew install scrcpy")
        return False
    print("✅ Scrcpy đã được cài đặt")
    return True

def get_connected_devices():
    """Lấy danh sách thiết bị đã kết nối"""
    stdout, stderr, code = run_command("adb devices", check=False)
    devices = []
    for line in stdout.split('\n')[1:]:
        if line.strip() and '\t' in line:
            device_id, status = line.strip().split('\t')
            if status == 'device':
                devices.append(device_id)
    return devices

def get_device_ip(device_id):
    """Lấy địa chỉ IP của thiết bị"""
    stdout, stderr, code = run_command(f"adb -s {device_id} shell ip route", check=False)
    if code == 0:
        # Tìm IP trong kết quả ip route
        match = re.search(r'(\d+\.\d+\.\d+\.\d+)', stdout)
        if match:
            return match.group(1)
    
    # Thử cách khác: dùng ifconfig hoặc ip addr
    stdout, stderr, code = run_command(f"adb -s {device_id} shell ifconfig wlan0", check=False)
    if code == 0:
        match = re.search(r'inet addr:(\d+\.\d+\.\d+\.\d+)', stdout)
        if match:
            return match.group(1)
        match = re.search(r'inet (\d+\.\d+\.\d+\.\d+)', stdout)
        if match:
            return match.group(1)
    
    # Thử ip addr show wlan0
    stdout, stderr, code = run_command(f"adb -s {device_id} shell ip addr show wlan0", check=False)
    if code == 0:
        match = re.search(r'inet (\d+\.\d+\.\d+\.\d+/\d+)', stdout)
        if match:
            return match.group(1).split('/')[0]
    
    return None

def enable_tcpip(device_id, port=5555):
    """Bật chế độ TCP/IP cho thiết bị"""
    print(f"📱 Đang bật chế độ TCP/IP trên cổng {port}...")
    stdout, stderr, code = run_command(f"adb -s {device_id} tcpip {port}", check=False)
    if code == 0:
        print(f"✅ Đã bật TCP/IP trên cổng {port}")
        time.sleep(2)  # Đợi một chút để thiết bị sẵn sàng
        return True
    else:
        print(f"❌ Không thể bật TCP/IP: {stderr}")
        return False

def connect_wireless(ip, port=5555):
    """Kết nối với thiết bị qua mạng"""
    print(f"🔌 Đang kết nối với {ip}:{port}...")
    stdout, stderr, code = run_command(f"adb connect {ip}:{port}", check=False)
    if code == 0 and "connected" in stdout.lower():
        print(f"✅ Đã kết nối với {ip}:{port}")
        return True
    else:
        print(f"❌ Không thể kết nối: {stderr or stdout}")
        return False

def disconnect_usb(device_id):
    """Ngắt kết nối USB"""
    print("🔌 Đang ngắt kết nối USB...")
    run_command(f"adb disconnect {device_id}", check=False)
    time.sleep(1)

def launch_scrcpy(ip=None, port=5555, options=None):
    """Khởi chạy scrcpy"""
    print("🚀 Đang khởi chạy scrcpy...")
    cmd = "scrcpy"
    if ip:
        cmd = f"scrcpy --tcpip={ip}:{port}"
    if options:
        cmd += f" {options}"
    
    print(f"Chạy lệnh: {cmd}")
    subprocess.run(cmd, shell=True)

def main():
    parser = argparse.ArgumentParser(
        description="Tool scrcpy để kết nối điện thoại Android qua mạng nội bộ"
    )
    parser.add_argument(
        "--ip",
        type=str,
        help="Địa chỉ IP của điện thoại (bỏ qua nếu muốn tự động phát hiện)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=5555,
        help="Cổng TCP/IP (mặc định: 5555)"
    )
    parser.add_argument(
        "--skip-usb",
        action="store_true",
        help="Bỏ qua bước kết nối USB (dùng khi đã bật TCP/IP trước đó)"
    )
    parser.add_argument(
        "--scrcpy-options",
        type=str,
        help="Các tùy chọn bổ sung cho scrcpy (ví dụ: --max-size 1024 --bit-rate 2M)"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("📱 Tool Scrcpy Wireless Connection")
    print("=" * 60)
    print()
    
    # Kiểm tra các công cụ cần thiết
    if not check_adb_installed():
        sys.exit(1)
    
    if not check_scrcpy_installed():
        sys.exit(1)
    
    print()
    
    # Nếu đã có IP, kết nối trực tiếp
    if args.ip:
        print(f"🔗 Kết nối trực tiếp với {args.ip}:{args.port}")
        if connect_wireless(args.ip, args.port):
            print()
            launch_scrcpy(args.ip, args.port, args.scrcpy_options)
        else:
            print("\n❌ Không thể kết nối. Vui lòng kiểm tra:")
            print("   1. Điện thoại và máy tính cùng mạng WiFi")
            print("   2. Đã bật TCP/IP trên điện thoại (chạy lại không có --skip-usb)")
            print("   3. Firewall không chặn cổng 5555")
            sys.exit(1)
        return
    
    # Nếu không có IP, cần kết nối USB trước
    if not args.skip_usb:
        print("📱 Bước 1: Kiểm tra thiết bị USB...")
        devices = get_connected_devices()
        
        if not devices:
            print("❌ Không tìm thấy thiết bị nào kết nối qua USB")
            print("Vui lòng:")
            print("   1. Kết nối điện thoại với máy tính qua USB")
            print("   2. Bật chế độ USB Debugging trên điện thoại")
            print("   3. Chấp nhận yêu cầu USB Debugging trên điện thoại")
            sys.exit(1)
        
        if len(devices) > 1:
            print(f"⚠️  Tìm thấy {len(devices)} thiết bị. Sử dụng thiết bị đầu tiên: {devices[0]}")
        
        device_id = devices[0]
        print(f"✅ Tìm thấy thiết bị: {device_id}")
        print()
        
        # Lấy IP của thiết bị
        print("📱 Bước 2: Lấy địa chỉ IP của thiết bị...")
        ip = get_device_ip(device_id)
        
        if not ip:
            print("❌ Không thể lấy địa chỉ IP của thiết bị")
            print("Vui lòng nhập IP thủ công bằng cách dùng --ip <địa_chỉ_ip>")
            sys.exit(1)
        
        print(f"✅ Địa chỉ IP: {ip}")
        print()
        
        # Bật TCP/IP
        if not enable_tcpip(device_id, args.port):
            sys.exit(1)
        print()
        
        # Kết nối qua mạng
        print("📱 Bước 3: Kết nối qua mạng...")
        if not connect_wireless(ip, args.port):
            sys.exit(1)
        print()
        
        # Ngắt USB
        print("📱 Bước 4: Ngắt kết nối USB...")
        disconnect_usb(device_id)
        print()
        
        # Đợi một chút để kết nối ổn định
        time.sleep(2)
        
        # Kiểm tra lại kết nối
        devices = get_connected_devices()
        if not any(ip in d for d in devices):
            print("⚠️  Cảnh báo: Thiết bị có thể chưa kết nối hoàn toàn")
        print()
    else:
        print("⏭️  Bỏ qua bước kết nối USB")
        print("Đảm bảo bạn đã kết nối qua mạng trước đó")
        print()
    
    # Khởi chạy scrcpy
    print("📱 Bước 5: Khởi chạy scrcpy...")
    launch_scrcpy(options=args.scrcpy_options)

if __name__ == "__main__":
    main()

