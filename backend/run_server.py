#!/usr/bin/env python3
"""
TalkToMe Backend Server - Simple Startup
Chạy Flask development server
"""

import os
import sys
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid

# Initialize Flask
app = Flask(__name__)
CORS(app, origins=["http://localhost:3000", "http://127.0.0.1:3000"])

# Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///talktome.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'dev-key-12345'

db = SQLAlchemy(app)

# ==================== Database Models ====================

class Leader(db.Model):
    __tablename__ = 'leaders'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class FeedbackSession(db.Model):
    __tablename__ = 'feedback_sessions'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    uid = db.Column(db.String(8), unique=True, nullable=False)
    leader_id = db.Column(db.String(36), db.ForeignKey('leaders.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Feedback(db.Model):
    __tablename__ = 'feedbacks'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = db.Column(db.String(36), db.ForeignKey('feedback_sessions.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    sentiment = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ==================== API Routes ====================

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'message': 'TalkToMe Backend Running',
        'timestamp': datetime.utcnow().isoformat()
    }), 200

@app.route('/api/test', methods=['GET'])
def test():
    """Test endpoint"""
    return jsonify({
        'message': 'Backend is working!',
        'frontend_url': 'http://localhost:3000'
    }), 200

@app.route('/api/sessions', methods=['POST'])
def create_session():
    """Create feedback session"""
    data = request.get_json()
    leader_id = request.headers.get('X-Leader-ID')
    
    if not leader_id or not data or 'title' not in data:
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Generate UID
    uid = str(uuid.uuid4())[:8].upper()
    
    session = FeedbackSession(
        uid=uid,
        leader_id=leader_id,
        title=data['title'],
        description=data.get('description', '')
    )
    
    db.session.add(session)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'uid': uid,
        'session_id': session.id,
        'message': 'Session created'
    }), 201

@app.route('/api/feedback/submit', methods=['POST'])
def submit_feedback():
    """Submit anonymous feedback"""
    data = request.get_json()
    uid = data.get('uid', '').upper()
    content = data.get('content', '')
    
    if not uid or not content:
        return jsonify({'error': 'Missing UID or content'}), 400
    
    # Find session
    session = FeedbackSession.query.filter_by(uid=uid).first()
    
    if not session:
        return jsonify({'error': 'Invalid feedback code'}), 404
    
    if session.status == 'closed':
        return jsonify({'error': 'Session is closed'}), 410
    
    # Create feedback
    feedback = Feedback(
        session_id=session.id,
        content=content,
        sentiment='positive'  # Simulate AI analysis
    )
    
    db.session.add(feedback)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Feedback submitted',
        'feedback_id': feedback.id
    }), 201

@app.route('/api/sessions/<session_id>/analytics', methods=['GET'])
def get_analytics(session_id):
    """Get session analytics"""
    session = FeedbackSession.query.get(session_id)
    
    if not session:
        return jsonify({'error': 'Session not found'}), 404
    
    feedbacks = Feedback.query.filter_by(session_id=session_id).all()
    
    return jsonify({
        'success': True,
        'session_id': session.id,
        'total_feedbacks': len(feedbacks),
        'satisfaction_score': 7.5,
        'sentiments': {
            'positive_pct': 60,
            'neutral_pct': 25,
            'negative_pct': 15
        },
        'top_issues': [
            {'issue': 'Work-life balance', 'percentage': 30},
            {'issue': 'Career development', 'percentage': 25}
        ],
        'summary': 'Team is satisfied but needs work-life balance improvements'
    }), 200

@app.route('/', methods=['GET'])
def index():
    """Welcome message"""
    return jsonify({
        'app': 'TalkToMe',
        'status': 'running',
        'version': '1.0.0',
        'endpoints': {
            'health': '/api/health',
            'create_session': 'POST /api/sessions',
            'submit_feedback': 'POST /api/feedback/submit',
            'analytics': 'GET /api/sessions/{id}/analytics'
        }
    }), 200

# ==================== Main ====================

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # Create test data
        test_leader = Leader.query.filter_by(email='test@example.com').first()
        if not test_leader:
            from werkzeug.security import generate_password_hash
            test_leader = Leader(
                email='test@example.com',
                name='Test Leader',
                password_hash=generate_password_hash('password123')
            )
            db.session.add(test_leader)
            db.session.commit()
    
    print("\n" + "="*60)
    print("🚀 TalkToMe Backend Server Starting...")
    print("="*60)
    print("\n📍 Backend Running:")
    print("   URL: http://localhost:5000")
    print("   Health: http://localhost:5000/api/health")
    print("   Test: http://localhost:5000/api/test")
    print("\n🌐 Frontend URL:")
    print("   http://localhost:3000")
    print("\n✨ Test Account:")
    print("   Email: test@example.com")
    print("   Password: password123")
    print("\n" + "="*60 + "\n")
    
    app.run(host='127.0.0.1', port=5000, debug=True, use_reloader=False)
