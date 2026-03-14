@echo off
REM TalkToMe - Quick Start Script
REM Runs both backend and frontend

echo.
echo ========================================
echo TalkToMe - Starting Servers
echo ========================================
echo.

REM Kill existing processes
echo Cleaning up old processes...
taskkill /IM python.exe /F 2>nul
taskkill /IM node.exe /F 2>nul

echo.
echo ========================================
echo Starting Backend (Port 5000)...
echo ========================================
echo.

start cmd /k "cd C:\Users\Monkez-PC\.piepie\workspace\projects\TalkToMe\backend && python server.py"

echo.
echo Waiting 3 seconds...
timeout /t 3 /nobreak

echo.
echo ========================================
echo Starting Frontend (Port 3000)...
echo ========================================
echo.

start cmd /k "cd C:\Users\Monkez-PC\.piepie\workspace\projects\TalkToMe\frontend && python -m http.server 3000"

echo.
echo ========================================
echo Servers Starting...
echo ========================================
echo.
echo Frontend: http://localhost:3000
echo Backend:  http://localhost:5000/api/health
echo.
echo Opening browser in 2 seconds...
timeout /t 2 /nobreak

start http://localhost:3000

echo.
echo Done! Check the browser windows.
echo.
