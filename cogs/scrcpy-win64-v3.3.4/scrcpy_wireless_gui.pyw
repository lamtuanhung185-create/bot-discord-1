#!/usr/bin/env python3
"""
Tool scrcpy với giao diện đồ họa để kết nối điện thoại Android với máy tính qua mạng nội bộ
"""

import subprocess
import sys
import re
import time
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from datetime import datetime
import json
import os

class ScrcpyWirelessGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Scrcpy Wireless Connection")
        self.root.geometry("700x650")
        self.root.resizable(True, True)
        
        # File lưu cấu hình
        self.config_file = "scrcpy_wireless_config.json"
        
        # Biến
        self.selected_device = tk.StringVar()
        self.device_ip = tk.StringVar()
        self.port = tk.StringVar(value="5555")
        self.turn_off_screen = tk.BooleanVar(value=False)
        self.is_connecting = False
        
        # Style
        style = ttk.Style()
        style.theme_use('clam')
        
        # Load IP đã lưu
        self.load_saved_ip()
        
        self.setup_ui()
        self.check_tools()
        
    def setup_ui(self):
        # Header
        header_frame = tk.Frame(self.root, bg="#2c3e50", pady=15)
        header_frame.pack(fill=tk.X)
        
        title_label = tk.Label(
            header_frame,
            text="📱 Scrcpy Wireless Connection",
            font=("Arial", 18, "bold"),
            bg="#2c3e50",
            fg="white"
        )
        title_label.pack()
        
        # Main container
        main_frame = tk.Frame(self.root, padx=20, pady=15)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Section 1: Device Selection
        device_frame = tk.LabelFrame(
            main_frame,
            text="Thiết bị",
            font=("Arial", 11, "bold"),
            padx=10,
            pady=10
        )
        device_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Device list
        device_list_frame = tk.Frame(device_frame)
        device_list_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(device_list_frame, text="Thiết bị USB:", font=("Arial", 9)).pack(anchor=tk.W)
        
        device_combo_frame = tk.Frame(device_list_frame)
        device_combo_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.device_combo = ttk.Combobox(
            device_combo_frame,
            textvariable=self.selected_device,
            state="readonly",
            width=40
        )
        self.device_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        refresh_btn = tk.Button(
            device_combo_frame,
            text="🔄 Quét",
            command=self.scan_devices,
            bg="#3498db",
            fg="white",
            font=("Arial", 9),
            relief=tk.FLAT,
            padx=15,
            cursor="hand2"
        )
        refresh_btn.pack(side=tk.LEFT)
        
        # IP Input
        ip_frame = tk.Frame(device_frame)
        ip_frame.pack(fill=tk.X, pady=(10, 0))
        
        tk.Label(ip_frame, text="Địa chỉ IP (tùy chọn):", font=("Arial", 9)).pack(anchor=tk.W)
        
        ip_input_frame = tk.Frame(ip_frame)
        ip_input_frame.pack(fill=tk.X, pady=(5, 0))
        
        # Combobox cho IP với danh sách IP đã lưu
        self.ip_combo = ttk.Combobox(
            ip_input_frame,
            textvariable=self.device_ip,
            font=("Arial", 10),
            width=18,
            state="normal"  # Cho phép nhập mới hoặc chọn từ danh sách
        )
        self.ip_combo.pack(side=tk.LEFT, padx=(0, 10))
        # Bind event khi chọn IP từ danh sách
        self.ip_combo.bind("<<ComboboxSelected>>", self.on_ip_selected)
        
        tk.Label(ip_input_frame, text="Cổng:", font=("Arial", 9)).pack(side=tk.LEFT, padx=(0, 5))
        port_entry = tk.Entry(
            ip_input_frame,
            textvariable=self.port,
            font=("Arial", 10),
            width=8
        )
        port_entry.pack(side=tk.LEFT)
        
        # Nút xóa IP đã lưu
        clear_ip_btn = tk.Button(
            ip_input_frame,
            text="🗑️ Xóa",
            command=self.clear_current_ip,
            bg="#95a5a6",
            fg="white",
            font=("Arial", 8),
            relief=tk.FLAT,
            padx=10,
            cursor="hand2"
        )
        clear_ip_btn.pack(side=tk.LEFT, padx=(10, 0))
        
        # Section 2: Actions
        action_frame = tk.LabelFrame(
            main_frame,
            text="Thao tác",
            font=("Arial", 11, "bold"),
            padx=10,
            pady=10
        )
        action_frame.pack(fill=tk.X, pady=(0, 10))
        
        button_frame = tk.Frame(action_frame)
        button_frame.pack(fill=tk.X)
        
        self.connect_btn = tk.Button(
            button_frame,
            text="🔌 Kết nối Wireless",
            command=self.connect_wireless_thread,
            bg="#27ae60",
            fg="white",
            font=("Arial", 10, "bold"),
            relief=tk.FLAT,
            padx=20,
            pady=10,
            cursor="hand2"
        )
        self.connect_btn.pack(side=tk.LEFT, padx=(0, 10), fill=tk.X, expand=True)
        
        self.launch_btn = tk.Button(
            button_frame,
            text="🚀 Khởi chạy Scrcpy",
            command=self.launch_scrcpy_thread,
            bg="#e74c3c",
            fg="white",
            font=("Arial", 10, "bold"),
            relief=tk.FLAT,
            padx=20,
            pady=10,
            cursor="hand2"
        )
        self.launch_btn.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Section 3: Log
        log_frame = tk.LabelFrame(
            main_frame,
            text="Nhật ký",
            font=("Arial", 11, "bold"),
            padx=10,
            pady=10
        )
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=12,
            font=("Consolas", 9),
            bg="#2c3e50",
            fg="#ecf0f1",
            insertbackground="white"
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Status bar
        self.status_bar = tk.Label(
            self.root,
            text="Sẵn sàng",
            bd=1,
            relief=tk.SUNKEN,
            anchor=tk.W,
            bg="#34495e",
            fg="white",
            font=("Arial", 9)
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Initial scan
        self.scan_devices()
        
        # Cập nhật danh sách IP trong combobox
        self.update_ip_combo()
        
    def load_saved_ip(self):
        """Tải danh sách IP và port đã lưu từ file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # Load danh sách IP
                    if 'ip_list' in config and isinstance(config['ip_list'], list):
                        ip_list = config['ip_list']
                        if ip_list:
                            # Lấy IP cuối cùng (mới nhất) làm mặc định
                            last_ip = ip_list[-1]
                            if isinstance(last_ip, dict):
                                self.device_ip.set(last_ip.get('ip', ''))
                                self.port.set(last_ip.get('port', '5555'))
                            else:
                                # Format cũ: chỉ là string
                                self.device_ip.set(last_ip)
                    # Load IP đơn lẻ (format cũ - để tương thích)
                    elif 'ip' in config:
                        self.device_ip.set(config['ip'])
                        if 'port' in config:
                            self.port.set(config['port'])
                    # Load preference tắt màn hình
                    if 'turn_off_screen' in config:
                        self.turn_off_screen.set(config['turn_off_screen'])
        except Exception as e:
            # Nếu có lỗi khi đọc file, bỏ qua
            pass
    
    def get_ip_list(self):
        """Lấy danh sách IP từ file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    if 'ip_list' in config and isinstance(config['ip_list'], list):
                        return config['ip_list']
            return []
        except Exception:
            return []
    
    def update_ip_combo(self):
        """Cập nhật danh sách IP trong combobox"""
        ip_list = self.get_ip_list()
        ip_values = []
        for item in ip_list:
            if isinstance(item, dict):
                ip_values.append(item['ip'])
            else:
                ip_values.append(item)
        self.ip_combo['values'] = ip_values
    
    def save_ip(self, ip, port):
        """Lưu IP và port vào danh sách"""
        try:
            ip_list = self.get_ip_list()
            
            # Tìm xem IP đã tồn tại chưa
            found = False
            for i, item in enumerate(ip_list):
                if isinstance(item, dict):
                    if item['ip'] == ip:
                        # Cập nhật port nếu khác
                        ip_list[i]['port'] = port
                        found = True
                        break
                else:
                    # Format cũ: chuyển sang format mới
                    if item == ip:
                        ip_list[i] = {'ip': ip, 'port': port}
                        found = True
                        break
            
            # Nếu chưa có, thêm mới
            if not found:
                ip_list.append({'ip': ip, 'port': port})
            
            # Giới hạn số lượng IP (giữ 10 IP gần nhất)
            if len(ip_list) > 10:
                ip_list = ip_list[-10:]
            
            # Load config hiện tại để giữ các setting khác
            config = {}
            if os.path.exists(self.config_file):
                try:
                    with open(self.config_file, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                except:
                    pass
            
            config['ip_list'] = ip_list
            # Lưu preference tắt màn hình
            config['turn_off_screen'] = self.turn_off_screen.get()
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            # Cập nhật combobox
            self.update_ip_combo()
        except Exception as e:
            self.log(f"Không thể lưu IP: {str(e)}", "WARNING")
    
    def on_ip_selected(self, event=None):
        """Khi chọn IP từ combobox, tự động điền port"""
        selected_ip = self.device_ip.get()
        if selected_ip:
            ip_list = self.get_ip_list()
            for item in ip_list:
                if isinstance(item, dict):
                    if item['ip'] == selected_ip:
                        self.port.set(item.get('port', '5555'))
                        break
    
    def clear_current_ip(self):
        """Xóa IP hiện tại khỏi danh sách"""
        current_ip = self.device_ip.get().strip()
        if not current_ip:
            self.log("Không có IP để xóa", "INFO")
            return
        
        try:
            ip_list = self.get_ip_list()
            new_list = []
            removed = False
            
            for item in ip_list:
                if isinstance(item, dict):
                    if item['ip'] != current_ip:
                        new_list.append(item)
                    else:
                        removed = True
                else:
                    if item != current_ip:
                        new_list.append(item)
                    else:
                        removed = True
            
            if removed:
                # Load config hiện tại để giữ các setting khác
                config = {}
                if os.path.exists(self.config_file):
                    try:
                        with open(self.config_file, 'r', encoding='utf-8') as f:
                            config = json.load(f)
                    except:
                        pass
                
                config['ip_list'] = new_list
                config['turn_off_screen'] = self.turn_off_screen.get()
                
                with open(self.config_file, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)
                
                self.device_ip.set("")
                self.port.set("5555")
                self.update_ip_combo()
                self.log(f"Đã xóa IP {current_ip} khỏi danh sách", "INFO")
            else:
                self.log("IP không có trong danh sách", "INFO")
        except Exception as e:
            self.log(f"Không thể xóa IP: {str(e)}", "ERROR")
    
    def save_screen_preference(self):
        """Lưu preference tắt màn hình"""
        try:
            config = {}
            if os.path.exists(self.config_file):
                try:
                    with open(self.config_file, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                except:
                    pass
            
            config['turn_off_screen'] = self.turn_off_screen.get()
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            pass  # Không cần log lỗi nhỏ này
        
    def log(self, message, level="INFO"):
        """Ghi log vào text widget"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        color_map = {
            "INFO": "#3498db",
            "SUCCESS": "#27ae60",
            "ERROR": "#e74c3c",
            "WARNING": "#f39c12"
        }
        color = color_map.get(level, "#ecf0f1")
        
        self.log_text.insert(tk.END, f"[{timestamp}] ", "timestamp")
        self.log_text.insert(tk.END, f"{message}\n", level)
        self.log_text.see(tk.END)
        self.root.update()
        
        # Tag colors
        self.log_text.tag_config("timestamp", foreground="#95a5a6")
        self.log_text.tag_config(level, foreground=color)
        
    def update_status(self, message):
        """Cập nhật thanh trạng thái"""
        self.status_bar.config(text=message)
        self.root.update()
        
    def check_tools(self):
        """Kiểm tra ADB và Scrcpy"""
        self.log("Đang kiểm tra công cụ...", "INFO")
        
        # Check ADB
        stdout, stderr, code = self.run_command("adb version", check=False)
        if code != 0:
            self.log("❌ ADB chưa được cài đặt", "ERROR")
            self.update_status("Lỗi: ADB chưa được cài đặt")
            messagebox.showerror(
                "Lỗi",
                "ADB chưa được cài đặt hoặc không có trong PATH.\n\n"
                "Vui lòng cài đặt Android SDK Platform Tools:\n"
                "https://developer.android.com/studio/releases/platform-tools"
            )
            return False
        self.log("✅ ADB đã được cài đặt", "SUCCESS")
        
        # Check Scrcpy
        stdout, stderr, code = self.run_command("scrcpy --version", check=False)
        if code != 0:
            self.log("❌ Scrcpy chưa được cài đặt", "ERROR")
            self.update_status("Lỗi: Scrcpy chưa được cài đặt")
            messagebox.showerror(
                "Lỗi",
                "Scrcpy chưa được cài đặt hoặc không có trong PATH.\n\n"
                "Vui lòng cài đặt scrcpy:\n"
                "Windows: choco install scrcpy\n"
                "Hoặc tải từ: https://github.com/Genymobile/scrcpy/releases"
            )
            return False
        self.log("✅ Scrcpy đã được cài đặt", "SUCCESS")
        
        self.update_status("Sẵn sàng")
        return True
        
    def run_command(self, command, check=True):
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
            
    def scan_devices(self):
        """Quét thiết bị USB"""
        self.log("Đang quét thiết bị USB...", "INFO")
        self.update_status("Đang quét thiết bị...")
        
        stdout, stderr, code = self.run_command("adb devices", check=False)
        devices = []
        
        for line in stdout.split('\n')[1:]:
            if line.strip() and '\t' in line:
                device_id, status = line.strip().split('\t')
                if status == 'device':
                    devices.append(device_id)
        
        if devices:
            self.device_combo['values'] = devices
            if devices:
                self.selected_device.set(devices[0])
            self.log(f"✅ Tìm thấy {len(devices)} thiết bị", "SUCCESS")
            self.update_status(f"Tìm thấy {len(devices)} thiết bị")
        else:
            self.device_combo['values'] = []
            self.selected_device.set("")
            self.log("❌ Không tìm thấy thiết bị USB", "WARNING")
            self.update_status("Không tìm thấy thiết bị USB")
            
    def get_device_ip(self, device_id):
        """Lấy địa chỉ IP của thiết bị"""
        self.log(f"Đang lấy IP của thiết bị {device_id}...", "INFO")
        
        # Thử ip route
        stdout, stderr, code = self.run_command(f"adb -s {device_id} shell ip route", check=False)
        if code == 0:
            match = re.search(r'(\d+\.\d+\.\d+\.\d+)', stdout)
            if match:
                ip = match.group(1)
                self.log(f"✅ Tìm thấy IP: {ip}", "SUCCESS")
                return ip
        
        # Thử ifconfig
        stdout, stderr, code = self.run_command(f"adb -s {device_id} shell ifconfig wlan0", check=False)
        if code == 0:
            match = re.search(r'inet addr:(\d+\.\d+\.\d+\.\d+)', stdout)
            if match:
                ip = match.group(1)
                self.log(f"✅ Tìm thấy IP: {ip}", "SUCCESS")
                return ip
            match = re.search(r'inet (\d+\.\d+\.\d+\.\d+)', stdout)
            if match:
                ip = match.group(1)
                self.log(f"✅ Tìm thấy IP: {ip}", "SUCCESS")
                return ip
        
        # Thử ip addr
        stdout, stderr, code = self.run_command(f"adb -s {device_id} shell ip addr show wlan0", check=False)
        if code == 0:
            match = re.search(r'inet (\d+\.\d+\.\d+\.\d+/\d+)', stdout)
            if match:
                ip = match.group(1).split('/')[0]
                self.log(f"✅ Tìm thấy IP: {ip}", "SUCCESS")
                return ip
        
        self.log("❌ Không thể lấy IP tự động", "ERROR")
        return None
        
    def enable_tcpip(self, device_id, port):
        """Bật chế độ TCP/IP"""
        self.log(f"Đang bật TCP/IP trên cổng {port}...", "INFO")
        stdout, stderr, code = self.run_command(f"adb -s {device_id} tcpip {port}", check=False)
        
        if code == 0:
            self.log(f"✅ Đã bật TCP/IP trên cổng {port}", "SUCCESS")
            time.sleep(2)
            return True
        else:
            self.log(f"❌ Không thể bật TCP/IP: {stderr}", "ERROR")
            return False
            
    def connect_wireless(self, ip, port):
        """Kết nối wireless"""
        self.log(f"Đang kết nối với {ip}:{port}...", "INFO")
        stdout, stderr, code = self.run_command(f"adb connect {ip}:{port}", check=False)
        
        if code == 0 and "connected" in stdout.lower():
            self.log(f"✅ Đã kết nối với {ip}:{port}", "SUCCESS")
            return True
        else:
            self.log(f"❌ Không thể kết nối: {stderr or stdout}", "ERROR")
            return False
    
    def turn_off_device_screen(self, device_id=None):
        """Tắt màn hình điện thoại - thử nhiều phương pháp"""
        try:
            self.log("Đang tắt màn hình điện thoại...", "INFO")
            
            # Xác định device ID
            if not device_id:
                # Lấy device từ IP đã kết nối
                ip = self.device_ip.get().strip()
                if ip:
                    device_id = f"{ip}:{self.port.get().strip() or '5555'}"
                else:
                    # Lấy device USB
                    device_id = self.selected_device.get()
            
            if not device_id:
                self.log("❌ Không tìm thấy thiết bị để tắt màn hình", "WARNING")
                return False
            
            # Phương pháp 1: input keyevent 26 (KEYCODE_POWER)
            self.log("Thử phương pháp 1: input keyevent 26...", "INFO")
            cmd = f"adb -s {device_id} shell input keyevent 26"
            stdout, stderr, code = self.run_command(cmd, check=False)
            if code == 0:
                time.sleep(0.5)  # Đợi màn hình tắt
                self.log("✅ Đã tắt màn hình điện thoại (phương pháp 1)", "SUCCESS")
                return True
            
            # Phương pháp 2: input keyevent KEYCODE_POWER
            self.log("Thử phương pháp 2: input keyevent KEYCODE_POWER...", "INFO")
            cmd = f"adb -s {device_id} shell input keyevent KEYCODE_POWER"
            stdout, stderr, code = self.run_command(cmd, check=False)
            if code == 0:
                time.sleep(0.5)
                self.log("✅ Đã tắt màn hình điện thoại (phương pháp 2)", "SUCCESS")
                return True
            
            # Phương pháp 3: Thử unlock screen trước rồi tắt
            self.log("Thử phương pháp 3: unlock rồi tắt màn hình...", "INFO")
            # Unlock (swipe up)
            cmd = f"adb -s {device_id} shell input swipe 500 1500 500 500"
            self.run_command(cmd, check=False)
            time.sleep(0.3)
            # Tắt màn hình
            cmd = f"adb -s {device_id} shell input keyevent 26"
            stdout, stderr, code = self.run_command(cmd, check=False)
            if code == 0:
                time.sleep(0.5)
                self.log("✅ Đã tắt màn hình điện thoại (phương pháp 3)", "SUCCESS")
                return True
            
            # Phương pháp 4: dumpsys power và set screen off
            self.log("Thử phương pháp 4: dumpsys power...", "INFO")
            cmd = f"adb -s {device_id} shell dumpsys power"
            stdout, stderr, code = self.run_command(cmd, check=False)
            if code == 0 and "mScreenOn=true" in stdout:
                # Màn hình đang bật, thử tắt bằng cách khác
                cmd = f"adb -s {device_id} shell input keyevent 26"
                self.run_command(cmd, check=False)
                time.sleep(0.5)
            
            # Phương pháp 5: Thử dùng service call (cần root trên một số thiết bị)
            self.log("Thử phương pháp 5: service call...", "INFO")
            cmd = f"adb -s {device_id} shell service call power 16 i32 0"
            stdout, stderr, code = self.run_command(cmd, check=False)
            if code == 0:
                time.sleep(0.5)
                self.log("✅ Đã tắt màn hình điện thoại (phương pháp 5)", "SUCCESS")
                return True
            
            # Nếu tất cả đều thất bại, thử lại phương pháp 1 với delay
            self.log("Thử lại với delay...", "INFO")
            time.sleep(1)
            cmd = f"adb -s {device_id} shell input keyevent 26"
            stdout, stderr, code = self.run_command(cmd, check=False)
            if code == 0:
                time.sleep(0.5)
                self.log("✅ Đã tắt màn hình điện thoại (thử lại)", "SUCCESS")
                return True
            
            self.log("⚠️ Không thể tắt màn hình. Có thể thiết bị không hỗ trợ hoặc cần quyền root", "WARNING")
            self.log("💡 Gợi ý: Bạn có thể dùng tùy chọn --turn-screen-off của scrcpy khi khởi chạy", "INFO")
            return False
            
        except Exception as e:
            self.log(f"⚠️ Lỗi khi tắt màn hình: {str(e)}", "WARNING")
            return False
            
    def connect_wireless_thread(self):
        """Thread để kết nối wireless"""
        if self.is_connecting:
            return
            
        self.is_connecting = True
        self.connect_btn.config(state=tk.DISABLED)
        
        def worker():
            try:
                ip = self.device_ip.get().strip()
                port = self.port.get().strip() or "5555"
                
                # Nếu có IP nhập thủ công
                if ip:
                    self.log(f"Kết nối trực tiếp với {ip}:{port}", "INFO")
                    if self.connect_wireless(ip, port):
                        self.update_status(f"Đã kết nối với {ip}:{port}")
                        # Lưu IP khi kết nối thành công
                        self.save_ip(ip, port)
                    else:
                        self.update_status("Kết nối thất bại")
                        messagebox.showerror(
                            "Lỗi",
                            "Không thể kết nối. Vui lòng kiểm tra:\n"
                            "1. Điện thoại và máy tính cùng mạng WiFi\n"
                            "2. Đã bật TCP/IP trên điện thoại\n"
                            "3. Firewall không chặn cổng 5555"
                        )
                else:
                    # Lấy IP từ thiết bị USB
                    device_id = self.selected_device.get()
                    if not device_id:
                        self.log("❌ Vui lòng chọn thiết bị hoặc nhập IP", "ERROR")
                        self.update_status("Vui lòng chọn thiết bị")
                        messagebox.showwarning("Cảnh báo", "Vui lòng chọn thiết bị USB hoặc nhập IP thủ công")
                        return
                    
                    # Lấy IP
                    ip = self.get_device_ip(device_id)
                    if not ip:
                        self.log("❌ Không thể lấy IP. Vui lòng nhập IP thủ công", "ERROR")
                        self.update_status("Không thể lấy IP")
                        messagebox.showwarning("Cảnh báo", "Không thể lấy IP tự động. Vui lòng nhập IP thủ công")
                        return
                    
                    # Bật TCP/IP
                    if not self.enable_tcpip(device_id, port):
                        self.update_status("Không thể bật TCP/IP")
                        return
                    
                    # Kết nối
                    if not self.connect_wireless(ip, port):
                        self.update_status("Kết nối thất bại")
                        return
                    
                    # Ngắt USB
                    self.log("Đang ngắt kết nối USB...", "INFO")
                    self.run_command(f"adb disconnect {device_id}", check=False)
                    time.sleep(2)
                    
                    self.update_status(f"Đã kết nối với {ip}:{port}")
                    self.device_ip.set(ip)  # Lưu IP để dùng sau
                    # Lưu IP khi kết nối thành công
                    self.save_ip(ip, port)
                    # Tắt màn hình nếu được bật
                    if self.turn_off_screen.get():
                        time.sleep(1)  # Đợi kết nối ổn định
                        self.turn_off_device_screen(f"{ip}:{port}")
                    
            except Exception as e:
                self.log(f"❌ Lỗi: {str(e)}", "ERROR")
                self.update_status("Lỗi kết nối")
            finally:
                self.is_connecting = False
                self.connect_btn.config(state=tk.NORMAL)
                
        threading.Thread(target=worker, daemon=True).start()
        
    def launch_scrcpy_thread(self):
        """Thread để khởi chạy scrcpy"""
        def worker():
            try:
                ip = self.device_ip.get().strip()
                port = self.port.get().strip() or "5555"
                
                self.log("Đang khởi chạy scrcpy...", "INFO")
                self.update_status("Đang khởi chạy scrcpy...")
                
                cmd = "scrcpy"
                if ip:
                    cmd = f"scrcpy --tcpip={ip}:{port}"
                
                # Thêm tùy chọn tắt màn hình nếu được bật
                if self.turn_off_screen.get():
                    cmd += " --turn-screen-off"
                    self.log("Tùy chọn tắt màn hình đã được bật", "INFO")
                
                self.log(f"Chạy lệnh: {cmd}", "INFO")
                subprocess.run(cmd, shell=True)
                
                self.log("Scrcpy đã đóng", "INFO")
                self.update_status("Sẵn sàng")
                
            except Exception as e:
                self.log(f"❌ Lỗi: {str(e)}", "ERROR")
                self.update_status("Lỗi khởi chạy scrcpy")
                messagebox.showerror("Lỗi", f"Không thể khởi chạy scrcpy:\n{str(e)}")
                
        threading.Thread(target=worker, daemon=True).start()

def main():
    root = tk.Tk()
    app = ScrcpyWirelessGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
