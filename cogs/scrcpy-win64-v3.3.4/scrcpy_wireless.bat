@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ============================================================
echo 📱 Tool Scrcpy Wireless Connection (Windows Batch)
echo ============================================================
echo.

REM Kiểm tra ADB
adb version >nul 2>&1
if errorlevel 1 (
    echo ❌ ADB chưa được cài đặt hoặc không có trong PATH
    echo Vui lòng cài đặt Android SDK Platform Tools
    pause
    exit /b 1
)
echo ✅ ADB đã được cài đặt

REM Kiểm tra Scrcpy
scrcpy --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Scrcpy chưa được cài đặt hoặc không có trong PATH
    echo Vui lòng cài đặt scrcpy: choco install scrcpy
    pause
    exit /b 1
)
echo ✅ Scrcpy đã được cài đặt
echo.

REM Kiểm tra thiết bị USB
echo 📱 Bước 1: Kiểm tra thiết bị USB...
adb devices | findstr /C:"device" >nul
if errorlevel 1 (
    echo ❌ Không tìm thấy thiết bị nào kết nối qua USB
    echo Vui lòng:
    echo    1. Kết nối điện thoại với máy tính qua USB
    echo    2. Bật chế độ USB Debugging trên điện thoại
    echo    3. Chấp nhận yêu cầu USB Debugging trên điện thoại
    pause
    exit /b 1
)
echo ✅ Tìm thấy thiết bị USB
echo.

REM Lấy IP của thiết bị
echo 📱 Bước 2: Lấy địa chỉ IP của thiết bị...
for /f "tokens=*" %%i in ('adb shell ip route ^| findstr /R "[0-9][0-9]*\.[0-9][0-9]*\.[0-9][0-9]*\.[0-9][0-9]*"') do (
    for /f "tokens=*" %%j in ("%%i") do (
        set "line=%%j"
        for /f "tokens=1" %%k in ("!line!") do set "ip=%%k"
        goto :found_ip
    )
)

REM Thử cách khác
for /f "tokens=*" %%i in ('adb shell ifconfig wlan0 2^>nul ^| findstr "inet"') do (
    for /f "tokens=2 delims=:" %%j in ("%%i") do (
        for /f "tokens=1" %%k in ("%%j") do set "ip=%%k"
        goto :found_ip
    )
)

echo ❌ Không thể lấy địa chỉ IP tự động
echo Vui lòng nhập địa chỉ IP của điện thoại:
set /p ip="IP: "
if "!ip!"=="" (
    echo ❌ IP không hợp lệ
    pause
    exit /b 1
)

:found_ip
echo ✅ Địa chỉ IP: %ip%
echo.

REM Bật TCP/IP
echo 📱 Bước 3: Bật chế độ TCP/IP trên cổng 5555...
adb tcpip 5555
if errorlevel 1 (
    echo ❌ Không thể bật TCP/IP
    pause
    exit /b 1
)
echo ✅ Đã bật TCP/IP
timeout /t 2 /nobreak >nul
echo.

REM Kết nối qua mạng
echo 📱 Bước 4: Kết nối qua mạng...
adb connect %ip%:5555
if errorlevel 1 (
    echo ❌ Không thể kết nối
    pause
    exit /b 1
)
echo ✅ Đã kết nối qua mạng
timeout /t 2 /nobreak >nul
echo.

REM Ngắt USB
echo 📱 Bước 5: Ngắt kết nối USB...
adb disconnect
timeout /t 1 /nobreak >nul
echo.

REM Khởi chạy scrcpy
echo 📱 Bước 6: Khởi chạy scrcpy...
echo.
scrcpy

pause

