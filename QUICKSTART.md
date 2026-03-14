# 🚀 TalkToMe - Quick Start Guide

## ⚡ Start Server (2 Terminals)

### Terminal 1 - Backend (Port 5000)

```bash
cd C:\Users\Monkez-PC\.piepie\workspace\projects\TalkToMe
run_backend.bat
```

Expected output:
```
========================================
Starting TalkToMe Backend Server...
Port: 5000
URL: http://localhost:5000
========================================
 * Running on http://127.0.0.1:5000
 * Press CTRL+C to quit
```

### Terminal 2 - Frontend (Port 3000)

```bash
cd C:\Users\Monkez-PC\.piepie\workspace\projects\TalkToMe
run_frontend.bat
```

Expected output:
```
========================================
Starting TalkToMe Frontend Server...
Port: 3000
URL: http://localhost:3000
========================================
Compiled successfully!
```

---

## 🌐 Access Application

### Frontend (User Interface)
```
http://localhost:3000
```

### Backend API (REST Endpoints)
```
http://localhost:5000/api/health
```

---

## 📋 Test User Account

For testing, use:
```
Email: test@example.com
Password: password123
```

---

## 🎯 Test Workflow

### 1. Leader Flow
1. Navigate to http://localhost:3000
2. Click "Login" (or Register if new)
3. Enter test credentials
4. Create new feedback session
5. Copy UID code
6. View generated link

### 2. Employee Flow
1. Visit http://localhost:3000/feedback/[UID]
2. Enter feedback code (e.g., ABC12345)
3. Write anonymous feedback
4. Submit

### 3. Leader Analytics
1. Go back to dashboard
2. Click "View Analytics"
3. See sentiment distribution
4. Check top issues
5. Read AI summary

---

## 🔗 API Endpoints (For Testing)

### Health Check
```
GET http://localhost:5000/api/health
```

### Create Session
```
POST http://localhost:5000/api/sessions
Headers: X-Leader-ID: {leader_id}
Body: {"title": "Test", "description": "..."}
```

### Submit Feedback
```
POST http://localhost:5000/api/feedback/submit
Body: {"uid": "ABC12345", "content": "feedback text"}
```

### Get Analytics
```
GET http://localhost:5000/api/sessions/{session_id}/analytics
Headers: X-Leader-ID: {leader_id}
```

---

## 🛠️ Troubleshooting

### Issue: Port 3000/5000 already in use
```bash
# Find process using port 5000
netstat -ano | findstr :5000

# Kill process (replace PID)
taskkill /PID {PID} /F
```

### Issue: Module not found
```bash
# Backend
pip install -r backend/requirements.txt

# Frontend
npm install --legacy-peer-deps
```

### Issue: Cannot connect to API
- Check backend is running on port 5000
- Check REACT_APP_API_URL environment variable
- Check browser console for CORS errors

### Issue: Feedback form not working
- Verify UID is correct (8 characters)
- Check session is still active
- Check browser console for errors

---

## 📊 Database

SQLite database created automatically:
```
backend/talktome.db
```

To reset database:
```bash
# Delete the file
del backend/talktome.db

# Restart backend (will create new)
```

---

## 🔐 Security Note

This is development mode with:
- CORS enabled
- Debug mode ON
- SQLite in-memory DB

For production, use:
- PostgreSQL
- Environment variables for secrets
- Gunicorn + Nginx
- HTTPS enabled

---

## 📞 Support

If issues occur:
1. Check console logs
2. Verify both servers running
3. Check environment variables
4. Restart services

---

**Ready to test! Start servers and visit links above.** 🎯🐈
