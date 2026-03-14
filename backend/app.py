"""
TalkToMe Backend - Main Application
Flask-based REST API for anonymous feedback platform
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import uuid
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    'DATABASE_URL', 
    'sqlite:///talktome.db'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')

db = SQLAlchemy(app)

# ==================== Database Models ====================

class Leader(db.Model):
    """Leader/Manager account"""
    __tablename__ = 'leaders'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    company = db.Column(db.String(120))
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    sessions = db.relationship('FeedbackSession', backref='leader', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Leader {self.email}>'


class FeedbackSession(db.Model):
    """Feedback collection session"""
    __tablename__ = 'feedback_sessions'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    uid = db.Column(db.String(8), unique=True, nullable=False)  # Short code for subordinates
    leader_id = db.Column(db.String(36), db.ForeignKey('leaders.id'), nullable=False)
    
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='active')  # active, closed, draft
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    deadline = db.Column(db.DateTime)
    
    # Settings
    allow_multiple_submissions = db.Column(db.Boolean, default=True)
    require_email = db.Column(db.Boolean, default=False)  # For follow-up
    
    # Relationships
    feedbacks = db.relationship('Feedback', backref='session', lazy=True, cascade='all, delete-orphan')
    analytics = db.relationship('SessionAnalytics', backref='session', uselist=False, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<FeedbackSession {self.uid}>'


class Feedback(db.Model):
    """Anonymous feedback submission"""
    __tablename__ = 'feedbacks'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = db.Column(db.String(36), db.ForeignKey('feedback_sessions.id'), nullable=False)
    
    content = db.Column(db.Text, nullable=False)
    
    # Processing fields
    sentiment = db.Column(db.String(20))  # positive, neutral, negative
    sentiment_score = db.Column(db.Float)  # -1 to 1
    is_filtered = db.Column(db.Boolean, default=False)  # Spam/inappropriate
    filter_reason = db.Column(db.String(200))
    
    # Categorization
    topics = db.Column(db.JSON)  # ["work-life-balance", "career", ...]
    summary = db.Column(db.Text)  # AI generated summary
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Feedback {self.id[:8]}>'


class SessionAnalytics(db.Model):
    """Pre-computed analytics for session"""
    __tablename__ = 'session_analytics'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = db.Column(db.String(36), db.ForeignKey('feedback_sessions.id'), unique=True, nullable=False)
    
    total_feedbacks = db.Column(db.Integer, default=0)
    satisfaction_score = db.Column(db.Float)  # 0-10
    
    sentiment_positive = db.Column(db.Float)  # percentage
    sentiment_neutral = db.Column(db.Float)
    sentiment_negative = db.Column(db.Float)
    
    top_issues = db.Column(db.JSON)  # [{"issue": "...", "percentage": 15}, ...]
    
    summary_text = db.Column(db.Text)  # Overall summary
    
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Analytics {self.session_id[:8]}>'


# ==================== API Routes ====================

# ---------- Leader Authentication ----------

@app.route('/api/auth/register', methods=['POST'])
def register():
    """Register new leader"""
    data = request.json
    
    # Validation
    if not all(k in data for k in ['email', 'name', 'password']):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Check if exists
    if Leader.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already registered'}), 409
    
    # Create leader
    from werkzeug.security import generate_password_hash
    leader = Leader(
        email=data['email'],
        name=data['name'],
        company=data.get('company', ''),
        password_hash=generate_password_hash(data['password'])
    )
    
    db.session.add(leader)
    db.session.commit()
    
    return jsonify({
        'message': 'Registration successful',
        'leader_id': leader.id
    }), 201


@app.route('/api/auth/login', methods=['POST'])
def login():
    """Login leader"""
    data = request.json
    
    leader = Leader.query.filter_by(email=data['email']).first()
    if not leader:
        return jsonify({'error': 'Invalid credentials'}), 401
    
    from werkzeug.security import check_password_hash
    if not check_password_hash(leader.password_hash, data['password']):
        return jsonify({'error': 'Invalid credentials'}), 401
    
    # TODO: Generate JWT token
    return jsonify({
        'message': 'Login successful',
        'leader_id': leader.id,
        'name': leader.name
    }), 200


# ---------- Feedback Session Management ----------

@app.route('/api/sessions', methods=['POST'])
def create_session():
    """Create new feedback session"""
    data = request.json
    leader_id = request.headers.get('X-Leader-ID')  # TODO: Use JWT
    
    if not leader_id:
        return jsonify({'error': 'Unauthorized'}), 401
    
    # Generate unique UID (8 chars alphanumeric)
    uid = str(uuid.uuid4())[:8].upper()
    
    session = FeedbackSession(
        uid=uid,
        leader_id=leader_id,
        title=data['title'],
        description=data.get('description', ''),
        deadline=datetime.fromisoformat(data['deadline']) if data.get('deadline') else None,
        allow_multiple_submissions=data.get('allow_multiple_submissions', True),
        require_email=data.get('require_email', False)
    )
    
    db.session.add(session)
    db.session.commit()
    
    return jsonify({
        'message': 'Session created',
        'uid': uid,
        'session_id': session.id
    }), 201


@app.route('/api/sessions/<session_id>', methods=['GET'])
def get_session(session_id):
    """Get session details (leader only)"""
    session = FeedbackSession.query.get(session_id)
    
    if not session:
        return jsonify({'error': 'Session not found'}), 404
    
    return jsonify({
        'id': session.id,
        'uid': session.uid,
        'title': session.title,
        'status': session.status,
        'created_at': session.created_at.isoformat(),
        'feedbacks_count': len(session.feedbacks)
    }), 200


@app.route('/api/sessions/<session_id>/close', methods=['POST'])
def close_session(session_id):
    """Close feedback session"""
    session = FeedbackSession.query.get(session_id)
    
    if not session:
        return jsonify({'error': 'Session not found'}), 404
    
    session.status = 'closed'
    db.session.commit()
    
    return jsonify({'message': 'Session closed'}), 200


# ---------- Feedback Submission ----------

@app.route('/api/feedback/submit', methods=['POST'])
def submit_feedback():
    """Submit anonymous feedback via UID"""
    data = request.json
    uid = data.get('uid')
    content = data.get('content')
    
    if not uid or not content:
        return jsonify({'error': 'Missing UID or content'}), 400
    
    # Find session by UID
    session = FeedbackSession.query.filter_by(uid=uid).first()
    
    if not session:
        return jsonify({'error': 'Invalid feedback code'}), 404
    
    if session.status == 'closed':
        return jsonify({'error': 'This feedback session is closed'}), 410
    
    # Create feedback
    feedback = Feedback(
        session_id=session.id,
        content=content
    )
    
    db.session.add(feedback)
    db.session.commit()
    
    # TODO: Queue for LLM processing
    
    return jsonify({
        'message': 'Feedback submitted successfully',
        'feedback_id': feedback.id
    }), 201


# ---------- Analytics ----------

@app.route('/api/sessions/<session_id>/analytics', methods=['GET'])
def get_analytics(session_id):
    """Get analytics for session (leader only)"""
    session = FeedbackSession.query.get(session_id)
    
    if not session:
        return jsonify({'error': 'Session not found'}), 404
    
    # Get or create analytics
    analytics = session.analytics
    if not analytics:
        analytics = SessionAnalytics(session_id=session.id)
        db.session.add(analytics)
        db.session.commit()
    
    return jsonify({
        'session_id': session.id,
        'total_feedbacks': analytics.total_feedbacks,
        'satisfaction_score': analytics.satisfaction_score,
        'sentiment': {
            'positive': analytics.sentiment_positive,
            'neutral': analytics.sentiment_neutral,
            'negative': analytics.sentiment_negative
        },
        'top_issues': analytics.top_issues,
        'summary': analytics.summary_text,
        'updated_at': analytics.updated_at.isoformat()
    }), 200


@app.route('/api/sessions/<session_id>/trends', methods=['GET'])
def get_trends(session_id):
    """Get satisfaction trends over time"""
    session = FeedbackSession.query.get(session_id)
    
    if not session:
        return jsonify({'error': 'Session not found'}), 404
    
    # Group feedbacks by day
    feedbacks = Feedback.query.filter_by(session_id=session_id).all()
    
    trends = {}
    for fb in feedbacks:
        day = fb.created_at.date().isoformat()
        if day not in trends:
            trends[day] = []
        if fb.sentiment_score:
            trends[day].append(fb.sentiment_score)
    
    # Calculate daily average
    daily_scores = {}
    for day, scores in trends.items():
        daily_scores[day] = sum(scores) / len(scores) if scores else 0
    
    return jsonify({
        'trends': daily_scores
    }), 200


# ---------- Health Check ----------

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok'}), 200


# ==================== Error Handlers ====================

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'Server error'}), 500


# ==================== Database Initialization ====================

def init_db():
    """Initialize database"""
    with app.app_context():
        db.create_all()
        print("Database initialized!")


if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
