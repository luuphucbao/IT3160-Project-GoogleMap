@echo off
chcp 65001 >nul
TITLE IT3160 Project Launcher

echo ====================================================
echo      IT3160 Project - Google Map Clone Launcher
echo ====================================================

echo.
echo [1/3] Đang khởi động Backend Server (Port 8000)...
:: Mở cửa sổ mới chạy Backend
start "Backend API" cmd /k "cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

echo.
echo [2/3] Đang khởi động Frontend Server (Port 8080)...
:: Mở cửa sổ mới chạy Frontend
start "Frontend Static Server" cmd /k "cd frontend && python -m http.server 8080"

echo.
echo [3/3] Đang chờ server khởi động (3 giây)...
timeout /t 3 /nobreak >nul

echo.
echo Đang mở trình duyệt...
start http://localhost:8080/index.html
start http://localhost:8080/admin.html

echo.
echo ====================================================
echo      Đã khởi chạy thành công!
echo      Hãy đóng các cửa sổ cmd bật lên để tắt server.
echo ====================================================
pause
