# TalkToMe - Project Documentation

## 📱 Project Overview

**TalkToMe** is an anonymous feedback platform that enables organizations to collect honest, constructive feedback from employees while protecting their privacy. Leaders cannot identify who provided specific feedback, but receive valuable AI-synthesized insights.

### 🎯 Core Value Proposition

```
Problem:
  - Employees fear retaliation for honest feedback
  - Leaders miss critical insights due to self-censorship
  - Negative feedback often filtered out naturally
  - No structured way to collect and analyze feedback

Solution:
  - Complete anonymity for feedback submitters
  - AI-powered filtering and synthesis
  - Leaders see insights, not raw feedback
  - Structured analytics and trend analysis
```

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    TALKTOME PLATFORM                    │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Frontend (React)          Backend (Flask)             │
│  ├─ Login/Register         ├─ User Auth               │
│  ├─ Create Session         ├─ Session Management      │
│  ├─ Submit Feedback        ├─ Feedback Storage        │
│  └─ View Analytics         └─ API Layer               │
│                                                         │
│                    ┌─────────────┐                     │
│                    │   Database  │                     │
│                    │  (SQLite)   │                     │
│                    └─────────────┘                     │
│                                                         │
│        LLM Service (Claude API)                        │
│        ├─ Sentiment Analysis                          │
│        ├─ Topic Extraction                            │
│        ├─ Spam Filtering                              │
│        └─ Summary Generation                          │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 🗄️ Database Schema

### Leaders Table
```sql
CREATE TABLE leaders (
  id VARCHAR(36) PRIMARY KEY,
  email VARCHAR(120) UNIQUE NOT NULL,
  name VARCHAR(120),
  company VARCHAR(120),
  password_hash VARCHAR(256),
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### FeedbackSessions Table
```sql
CREATE TABLE feedback_sessions (
  id VARCHAR(36) PRIMARY KEY,
  uid VARCHAR(8) UNIQUE NOT NULL,  -- Short code for employees
  leader_id VARCHAR(36) FOREIGN KEY,
  title VARCHAR(200),
  description TEXT,
  status VARCHAR(20) DEFAULT 'active',  -- active, closed, draft
  created_at DATETIME,
  deadline DATETIME,
  allow_multiple_submissions BOOLEAN DEFAULT TRUE,
  require_email BOOLEAN DEFAULT FALSE
);
```

### Feedbacks Table
```sql
CREATE TABLE feedbacks (
  id VARCHAR(36) PRIMARY KEY,
  session_id VARCHAR(36) FOREIGN KEY,
  content TEXT NOT NULL,
  sentiment VARCHAR(20),  -- positive, neutral, negative
  sentiment_score FLOAT,  -- -1 to 1
  is_filtered BOOLEAN DEFAULT FALSE,
  filter_reason VARCHAR(200),
  topics JSON,  -- ["topic1", "topic2"]
  summary TEXT,
  created_at DATETIME
);
```

### SessionAnalytics Table
```sql
CREATE TABLE session_analytics (
  id VARCHAR(36) PRIMARY KEY,
  session_id VARCHAR(36) UNIQUE FOREIGN KEY,
  total_feedbacks INTEGER,
  satisfaction_score FLOAT,  -- 0-10
  sentiment_positive FLOAT,
  sentiment_neutral FLOAT,
  sentiment_negative FLOAT,
  top_issues JSON,
  summary_text TEXT,
  updated_at DATETIME
);
```

---

## 🔌 API Endpoints

### Authentication
```
POST   /api/auth/register       - Register new leader
POST   /api/auth/login          - Login leader
POST   /api/auth/logout         - Logout
```

### Sessions
```
POST   /api/sessions            - Create new feedback session
GET    /api/sessions/<id>       - Get session details
GET    /api/sessions            - List leader's sessions
POST   /api/sessions/<id>/close - Close session
```

### Feedback Submission
```
POST   /api/feedback/submit     - Submit feedback (via UID)
GET    /api/feedback/validate   - Validate UID
```

### Analytics
```
GET    /api/sessions/<id>/analytics  - Get session analytics
GET    /api/sessions/<id>/trends     - Get satisfaction trends
GET    /api/sessions/<id>/summary    - Get AI summary
```

---

## 🤖 LLM Processing Pipeline

### Single Feedback Analysis

```
Input: "I love the team but communication could be better"

↓ Claude API

Output:
{
  "sentiment": "positive",
  "sentiment_score": 0.6,
  "topics": ["communication", "team-dynamics"],
  "summary": "Employee values team but sees room for improvement in internal communication.",
  "key_concerns": ["Communication clarity"],
  "suggestions": ["Implement communication protocol", "Regular sync meetings"]
}
```

### Batch Processing

```
50 feedbacks → Analyze each → Aggregate results

Aggregation:
- Sentiment distribution (60% positive, 25% neutral, 15% negative)
- Topic clustering (communication: 28%, career: 18%, work-life: 15%)
- Top issues extraction
- Executive summary generation
- Satisfaction score calculation
```

### Filtering

Automatic filtering removes:
- Spam/off-topic feedback
- Offensive/discriminatory content
- Extremely negative feedback with no constructive suggestions
- Duplicate submissions

---

## 🔐 Privacy & Security

### Privacy Guarantees
1. **No Identity Storage**: Feedback never linked to submitter ID
2. **No IP Tracking**: IP addresses not logged with feedback
3. **No Device Fingerprinting**: Device info not collected
4. **Encrypted Storage**: All feedbacks encrypted at rest
5. **Limited Access**: Leader cannot access raw feedback
6. **No Follow-up**: Cannot reply to individual feedback

### Security Measures
1. HTTPS only communication
2. JWT token authentication
3. Database encryption
4. CORS protection
5. Rate limiting on submissions
6. Input validation & sanitization

---

## 📊 Analytics & Insights

### Satisfaction Score (0-10)
```
Calculated from:
- Sentiment analysis of all feedbacks
- Normalized to 0-10 scale
- Updated real-time as new feedback arrives
```

### Sentiment Distribution
```
Positive:  60%  (feedback with positive sentiment)
Neutral:   25%  (objective, balanced feedback)
Negative:  15%  (concerns, complaints)
```

### Top Issues/Themes
```
1. Work-life balance    (28% of feedbacks)
2. Career development   (18% of feedbacks)
3. Communication        (15% of feedbacks)
...
```

### Satisfaction Trends
```
Daily average satisfaction scores over time
- Shows improvement/decline patterns
- Identifies when issues emerged
- Correlate with company events/changes
```

---

## 🚀 Setup & Deployment

### Backend Setup

```bash
# Install dependencies
pip install -r backend/requirements.txt

# Set environment variables
export DATABASE_URL="sqlite:///talktome.db"
export SECRET_KEY="your-secret-key"
export ANTHROPIC_API_KEY="your-api-key"

# Initialize database
python backend/app.py

# Run server
flask run --port 5000
```

### Frontend Setup

```bash
# Install dependencies
cd frontend
npm install

# Set API endpoint
echo "REACT_APP_API_URL=http://localhost:5000" > .env

# Start development server
npm start
```

### Deployment (Production)

```bash
# Backend: Use Gunicorn + Nginx
gunicorn --workers 4 --bind 0.0.0.0:5000 backend.app:app

# Frontend: Build & serve
npm run build
# Serve /build folder with Nginx

# Database: Use PostgreSQL
# Encryption: Enable at-rest encryption
# HTTPS: Use Let's Encrypt SSL certs
```

---

## 📈 Usage Workflow

### For Leaders

1. **Create Session**
   - Click "New Feedback Session"
   - Set title, description, deadline
   - Generate UID code
   - Share UID with team

2. **Monitor Progress**
   - See real-time feedback count
   - View satisfaction score
   - Check submission trends

3. **Review Analytics**
   - View sentiment distribution
   - Read top issues
   - Read AI summary
   - Export report

4. **Take Action**
   - Address top concerns
   - Communicate changes
   - Create action items
   - Follow up later

### For Employees

1. **Receive UID**
   - Get code from leader
   - Join session via code

2. **Submit Feedback**
   - Write honest feedback
   - No identity visible
   - Can submit multiple times

3. **Trust Process**
   - Know identity protected
   - Leader sees insights not raw feedback
   - Help improve team/company

---

## 📋 Example Analytics Output

```json
{
  "session_id": "uid-abc123",
  "total_feedbacks": 47,
  "satisfaction_score": 7.2,
  "sentiments": {
    "positive_pct": 62,
    "neutral_pct": 24,
    "negative_pct": 14
  },
  "top_topics": [
    {"topic": "work-life-balance", "count": 18, "percentage": 38},
    {"topic": "career-growth", "count": 12, "percentage": 26},
    {"topic": "communication", "count": 9, "percentage": 19},
    {"topic": "management", "count": 7, "percentage": 15},
    {"topic": "compensation", "count": 5, "percentage": 11}
  ],
  "top_concerns": [
    {"item": "Long working hours during peak seasons", "count": 12},
    {"item": "Lack of clear career path", "count": 8},
    {"item": "Poor internal communication", "count": 6}
  ],
  "summary": "Overall team satisfaction is good at 7.2/10. Main concerns revolve around work-life balance during busy periods and clarity on career development paths. Communication between departments could be improved. Team values the company culture but wants more transparency on growth opportunities."
}
```

---

## 🎯 Future Enhancements

1. **Multi-language Support**
   - Auto-detect language
   - Translate feedback to leader's language
   
2. **Department-Level Analytics**
   - Compare satisfaction across departments
   - Identify teams with issues
   
3. **Action Tracking**
   - Leader creates action items from feedback
   - Track completion
   - Communicate back to team
   
4. **Predictive Analytics**
   - Predict turnover risk
   - Identify burnout indicators
   - Alert leaders to issues early
   
5. **Integration**
   - Slack notifications
   - Calendar integration
   - HRIS sync

---

## 🐛 Troubleshooting

### Issue: "Invalid UID"
- Check UID spelling (case-sensitive)
- Verify session is still active
- Session may have been closed

### Issue: "Submission failed"
- Check internet connection
- Verify UID is correct
- Browser cookies may need clearing

### Issue: "No analytics available"
- Wait for LLM processing (1-2 minutes)
- Refresh page
- Check if sufficient feedbacks submitted

---

**Con sẵn sàng phát triển TalkToMe cho ba!** 🚀
