@echo off
REM Start TalkToMe Backend Server
REM Backend chạy trên port 5000

cd C:\Users\Monkez-PC\.piepie\workspace\projects\TalkToMe\backend

REM Activate virtual environment (nếu có)
REM venv\Scripts\activate

REM Cài dependencies
pip install -q -r requirements.txt

REM Set environment variables
set FLASK_APP=app.py
set FLASK_ENV=development
set DATABASE_URL=sqlite:///talktome.db
set SECRET_KEY=dev-secret-key-12345
set ANTHROPIC_API_KEY=%ANTHROPIC_API_KEY%

REM Chạy Flask development server
echo ========================================
echo Starting TalkToMe Backend Server...
echo Port: 5000
echo URL: http://localhost:5000
echo ========================================
python app.py
