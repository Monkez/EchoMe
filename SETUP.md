# 🚀 TalkToMe - Quick Setup For Testing

## ⚡ Quick Start (3 Steps)

### Step 1: Setup Backend (Terminal 1)

```bash
cd C:\Users\Monkez-PC\.piepie\workspace\projects\TalkToMe\backend
pip install -r requirements.txt
python app.py
```

Expected output:
```
 * Running on http://127.0.0.1:5000
 * Press CTRL+C to quit
```

### Step 2: Setup Frontend (Terminal 2)

```bash
cd C:\Users\Monkez-PC\.piepie\workspace\projects\TalkToMe\frontend
npm install --legacy-peer-deps
npm start
```

Expected output:
```
Compiled successfully!
webpack compiled with 0 warnings
Open http://localhost:3000 to view it in your browser.
```

### Step 3: Open Browser

```
Frontend: http://localhost:3000
Backend:  http://localhost:5000/api/health
```

---

## 🎯 Test Workflow

### 1️⃣ Login (http://localhost:3000)
- Email: `test@example.com`
- Password: `password123`
- Click "Login"

### 2️⃣ Create Session
- Click "New Session"
- Title: `Test Feedback`
- Click "Create"
- **Copy the UID code** (e.g., `ABC12345`)

### 3️⃣ Submit Feedback (Anonymous)
- Open new tab: `http://localhost:3000/feedback/ABC12345`
- Paste UID: `ABC12345`
- Write feedback: `Great team! Love working here but need better work-life balance`
- Click "Submit"

### 4️⃣ Check Analytics
- Go back to dashboard
- Click "View Analytics"
- See:
  - ✅ Satisfaction score
  - ✅ Sentiment (Positive/Neutral/Negative)
  - ✅ Top issues
  - ✅ AI summary

---

## 🧪 Test Multiple Feedbacks

Open multiple tabs and submit different feedbacks:

**Feedback 1:**
```
Great team culture and supportive managers!
→ Should show: Positive sentiment
```

**Feedback 2:**
```
Work hours are too long, affecting health and family time
→ Should show: Negative sentiment, work-life-balance flagged
```

**Feedback 3:**
```
Good company but career path is unclear, need better development opportunities
→ Should show: Mixed sentiment, career-growth issue
```

Then view analytics to see:
- Average satisfaction score
- Sentiment distribution (pie chart)
- Top issues extracted by AI
- Trends over time

---

## ✅ Checklist

Backend:
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Server running (`python app.py`)
- [ ] Health check works (`curl http://localhost:5000/api/health`)

Frontend:
- [ ] Dependencies installed (`npm install --legacy-peer-deps`)
- [ ] Server running (`npm start`)
- [ ] Page loads (`http://localhost:3000`)

Testing:
- [ ] Can login with test account
- [ ] Can create session and get UID
- [ ] Can submit feedback via UID
- [ ] Can view analytics dashboard
- [ ] Sentiment analysis working
- [ ] Multiple feedbacks aggregated

---

## 🔗 Direct Links

```
Frontend Dashboard: http://localhost:3000
Backend API:       http://localhost:5000/api/health
Feedback Form:     http://localhost:3000/feedback/[UID]
```

---

## 🐛 Troubleshooting

### "Port 3000 already in use"
```bash
# Kill the process
netstat -ano | findstr :3000
taskkill /PID {PID} /F
```

### "npm command not found"
```bash
# Install Node.js first
# Download from nodejs.org
# Then: npm install --legacy-peer-deps
```

### "ModuleNotFoundError: No module named 'flask'"
```bash
# Install dependencies
pip install -r backend/requirements.txt
```

### "Cannot connect to API"
- Check backend is running on port 5000
- Check REACT_APP_API_URL is correct
- Check browser console for CORS errors

---

## 📊 What Gets Tested

✅ **User Management**
- Register and login
- Password hashing

✅ **Session Management**
- Create sessions with unique UID
- List user's sessions
- Close sessions

✅ **Anonymous Feedback**
- Submit via UID (no tracking)
- Content validation
- Multiple submissions

✅ **AI Processing**
- Sentiment analysis (positive/negative/neutral)
- Topic extraction
- Summary generation
- Spam filtering

✅ **Analytics**
- Satisfaction score calculation
- Sentiment distribution
- Top issues identification
- Trend visualization

✅ **Privacy**
- Leader cannot see raw feedback
- No IP tracking
- No user identification
- Encrypted storage

---

**Ready? Start servers and test!** 🎯🐈
