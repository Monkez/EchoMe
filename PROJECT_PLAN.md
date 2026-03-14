# TalkToMe - Anonymous Feedback Platform

## 📋 Project Structure

```
TalkToMe/
├── backend/
│   ├── app.py                 # Flask/FastAPI main
│   ├── config.py              # Config
│   ├── models.py              # Database models
│   ├── api/
│   │   ├── feedback.py        # Feedback endpoints
│   │   ├── analytics.py       # Analytics endpoints
│   │   └── auth.py            # Leader authentication
│   ├── services/
│   │   ├── llm_service.py     # LLM processing
│   │   ├── feedback_service.py # Feedback logic
│   │   └── analytics_service.py # Analytics logic
│   ├── database.py            # DB connection
│   └── requirements.txt
│
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── LeaderDashboard.jsx
│   │   │   ├── FeedbackForm.jsx
│   │   │   └── Analytics.jsx
│   │   ├── components/
│   │   ├── App.jsx
│   │   └── index.js
│   ├── package.json
│   └── .env
│
├── docs/
│   ├── API.md                 # API documentation
│   ├── DATABASE.md            # Schema design
│   └── ARCHITECTURE.md        # System design
│
└── README.md
```

## 🎯 Core Features

### 1. Leader Side
- ✅ Create feedback request session
- ✅ Get unique UID code
- ✅ View analytics dashboard (never see raw feedback)
- ✅ Set session parameters (deadline, anonymity level)
- ✅ Export reports

### 2. Subordinate Side
- ✅ Enter UID to join feedback session
- ✅ Submit anonymous feedback
- ✅ Multiple submissions allowed
- ✅ Real-time confirmation

### 3. AI Processing
- ✅ Sentiment analysis (positive/negative/neutral)
- ✅ Topic extraction (issues, concerns, suggestions)
- ✅ Spam/inappropriate filtering
- ✅ Duplicate detection
- ✅ Summary generation
- ✅ Trend analysis over time

### 4. Analytics
- ✅ Overall satisfaction score
- ✅ Sentiment distribution
- ✅ Top issues/themes
- ✅ Word cloud
- ✅ Time-series trends
- ✅ Anonymous demographic insights

## 🔐 Privacy & Security

- No IP tracking of feedbacks
- No user identification stored with feedback
- All feedback encrypted in database
- Leader cannot reverse-engineer identity
- HTTPS only
- Database audit logs

## 📊 Analytics Output Example

```json
{
  "session_id": "uid-12345",
  "total_feedbacks": 45,
  "summary": {
    "satisfaction_score": 7.2,
    "sentiment": {
      "positive": 60%,
      "neutral": 25%,
      "negative": 15%
    }
  },
  "top_issues": [
    "Work-life balance concerns (18%)",
    "Career development opportunities (12%)",
    "Communication clarity (10%)"
  ],
  "trends": {
    "week_1": 6.8,
    "week_2": 7.2,
    "week_3": 7.5
  }
}
```

---

**Con sẵn sàng code từng phần!** 🚀
