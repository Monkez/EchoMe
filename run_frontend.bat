@echo off
REM Start TalkToMe Frontend Server
REM Frontend chạy trên port 3000

cd C:\Users\Monkez-PC\.piepie\workspace\projects\TalkToMe\frontend

REM Cài dependencies
call npm install --legacy-peer-deps

REM Set environment variables
set REACT_APP_API_URL=http://localhost:5000
set REACT_APP_ENVIRONMENT=development

REM Chạy React development server
echo ========================================
echo Starting TalkToMe Frontend Server...
echo Port: 3000
echo URL: http://localhost:3000
echo ========================================
call npm start
