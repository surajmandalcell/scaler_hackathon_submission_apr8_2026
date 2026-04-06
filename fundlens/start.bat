@echo off
title FundLens Server

echo Stopping any existing server on port 8000...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000" ^| findstr "LISTENING"') do (
    taskkill /PID %%a /F >nul 2>&1
)

echo Reinstalling package...
pip install -e . -q

echo.
echo Starting FundLens server...
start "FundLens Server" cmd /k "cd /d %~dp0 && python server/app.py"

echo Waiting for server to start...
timeout /t 4 /nobreak >nul

echo Starting public tunnel (ngrok)...
start "FundLens Public URL" cmd /k "ngrok http 8000"

echo.
echo ============================================================
echo  FundLens is running!
echo  Local:   http://localhost:8000/admin
echo  Public:  check the ngrok window for your public URL
echo           (share that URL to access from office / anywhere)
echo ============================================================
echo.
pause
