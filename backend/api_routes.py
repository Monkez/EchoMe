"""
TalkToMe API Routes - Detailed Implementation
Enhanced endpoints with error handling & validation
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
import uuid
from functools import wraps
from llm_service import FeedbackAnalyzer
from models import db, Leader, FeedbackSession, Feedback, SessionAnalytics

api_bp = Blueprint('api', __name__, url_prefix='/api')

# ==================== Middleware ====================

def require_auth(f):
    """Check JWT token"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return jsonify({'error': 'Unauthorized'}), 401
        
        # TODO: Verify JWT token
        leader_id = request.headers.get('X-Leader-ID')
        if not leader_id:
            return jsonify({'error': 'Missing leader ID'}), 401
        
        return f(*args, **kwargs)
    return decorated


def validate_json(*keys):
    """Validate required JSON fields"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            data = request.get_json()
            if not data:
                return jsonify({'error': 'Request body must be JSON'}), 400
            
            missing = [k for k in keys if k not in data or not data[k]]
            if missing:
                return jsonify({'error': f'Missing fields: {", ".join(missing)}'}), 400
            
            return f(*args, **kwargs)
        return decorated
    return decorator


# ==================== Leader Sessions API ====================

@api_bp.route('/sessions', methods=['POST'])
@require_auth
@validate_json('title')
def create_feedback_session():
    """Create new feedback session"""
    data = request.get_json()
    leader_id = request.headers.get('X-Leader-ID')
    
    try:
        # Generate unique UID
        uid = str(uuid.uuid4())[:8].upper()
        while FeedbackSession.query.filter_by(uid=uid).first():
            uid = str(uuid.uuid4())[:8].upper()
        
        # Parse deadline if provided
        deadline = None
        if data.get('deadline'):
            try:
                deadline = datetime.fromisoformat(data['deadline'])
            except ValueError:
                return jsonify({'error': 'Invalid deadline format'}), 400
        
        # Create session
        session = FeedbackSession(
            uid=uid,
            leader_id=leader_id,
            title=data['title'],
            description=data.get('description', ''),
            deadline=deadline,
            allow_multiple_submissions=data.get('allow_multiple_submissions', True),
            require_email=data.get('require_email', False)
        )
        
        db.session.add(session)
        db.session.commit()
        
        return jsonify({
            'message': 'Feedback session created successfully',
            'session': {
                'id': session.id,
                'uid': session.uid,
                'title': session.title,
                'created_at': session.created_at.isoformat(),
                'status': session.status
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@api_bp.route('/sessions', methods=['GET'])
@require_auth
def list_sessions():
    """List all sessions for leader"""
    leader_id = request.headers.get('X-Leader-ID')
    
    try:
        sessions = FeedbackSession.query.filter_by(leader_id=leader_id).all()
        
        return jsonify({
            'sessions': [
                {
                    'id': s.id,
                    'uid': s.uid,
                    'title': s.title,
                    'status': s.status,
                    'feedbacks_count': len(s.feedbacks),
                    'satisfaction_score': s.analytics.satisfaction_score if s.analytics else None,
                    'created_at': s.created_at.isoformat(),
                    'deadline': s.deadline.isoformat() if s.deadline else None
                }
                for s in sessions
            ]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/sessions/<session_id>', methods=['GET'])
@require_auth
def get_session_detail(session_id):
    """Get session details"""
    leader_id = request.headers.get('X-Leader-ID')
    
    try:
        session = FeedbackSession.query.filter_by(
            id=session_id,
            leader_id=leader_id
        ).first()
        
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        return jsonify({
            'session': {
                'id': session.id,
                'uid': session.uid,
                'title': session.title,
                'description': session.description,
                'status': session.status,
                'feedbacks_count': len(session.feedbacks),
                'filtered_count': sum(1 for f in session.feedbacks if f.is_filtered),
                'created_at': session.created_at.isoformat(),
                'deadline': session.deadline.isoformat() if session.deadline else None,
                'allow_multiple_submissions': session.allow_multiple_submissions,
                'require_email': session.require_email
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/sessions/<session_id>/close', methods=['POST'])
@require_auth
def close_session(session_id):
    """Close feedback session"""
    leader_id = request.headers.get('X-Leader-ID')
    
    try:
        session = FeedbackSession.query.filter_by(
            id=session_id,
            leader_id=leader_id
        ).first()
        
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        session.status = 'closed'
        db.session.commit()
        
        return jsonify({
            'message': 'Session closed successfully',
            'session_id': session.id
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ==================== Feedback Submission API ====================

@api_bp.route('/feedback/submit', methods=['POST'])
@validate_json('uid', 'content')
def submit_feedback():
    """Submit anonymous feedback"""
    data = request.get_json()
    uid = data['uid'].strip().upper()
    content = data['content'].strip()
    
    try:
        # Validate content length
        if len(content) < 10:
            return jsonify({'error': 'Feedback must be at least 10 characters'}), 400
        
        if len(content) > 5000:
            return jsonify({'error': 'Feedback must be less than 5000 characters'}), 400
        
        # Find session by UID
        session = FeedbackSession.query.filter_by(uid=uid).first()
        
        if not session:
            return jsonify({'error': 'Invalid feedback code'}), 404
        
        if session.status == 'closed':
            return jsonify({'error': 'This feedback session is closed'}), 410
        
        if session.deadline and datetime.utcnow() > session.deadline:
            return jsonify({'error': 'Feedback deadline has passed'}), 410
        
        # Create feedback
        feedback = Feedback(
            session_id=session.id,
            content=content
        )
        
        db.session.add(feedback)
        db.session.commit()
        
        # Queue for LLM processing (async)
        from celery import current_app as celery_app
        process_feedback_task.delay(feedback.id)
        
        return jsonify({
            'message': 'Feedback submitted successfully',
            'feedback_id': feedback.id
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@api_bp.route('/feedback/validate-uid', methods=['POST'])
@validate_json('uid')
def validate_uid():
    """Validate feedback UID exists and is active"""
    data = request.get_json()
    uid = data['uid'].strip().upper()
    
    try:
        session = FeedbackSession.query.filter_by(uid=uid).first()
        
        if not session:
            return jsonify({
                'valid': False,
                'reason': 'Invalid feedback code'
            }), 200
        
        if session.status == 'closed':
            return jsonify({
                'valid': False,
                'reason': 'Feedback session has been closed'
            }), 200
        
        if session.deadline and datetime.utcnow() > session.deadline:
            return jsonify({
                'valid': False,
                'reason': 'Feedback deadline has passed'
            }), 200
        
        return jsonify({
            'valid': True,
            'session_title': session.title,
            'allow_multiple': session.allow_multiple_submissions
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== Analytics API ====================

@api_bp.route('/sessions/<session_id>/analytics', methods=['GET'])
@require_auth
def get_analytics(session_id):
    """Get session analytics"""
    leader_id = request.headers.get('X-Leader-ID')
    
    try:
        session = FeedbackSession.query.filter_by(
            id=session_id,
            leader_id=leader_id
        ).first()
        
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        # Get or create analytics
        analytics = session.analytics
        if not analytics:
            # Trigger analytics recalculation
            recalculate_analytics.delay(session_id)
            return jsonify({
                'message': 'Analytics processing...',
                'status': 'processing'
            }), 202
        
        return jsonify({
            'analytics': {
                'session_id': session.id,
                'total_feedbacks': analytics.total_feedbacks,
                'satisfaction_score': analytics.satisfaction_score,
                'sentiments': {
                    'positive_pct': analytics.sentiment_positive,
                    'neutral_pct': analytics.sentiment_neutral,
                    'negative_pct': analytics.sentiment_negative
                },
                'top_issues': analytics.top_issues,
                'summary': analytics.summary_text,
                'updated_at': analytics.updated_at.isoformat()
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/sessions/<session_id>/trends', methods=['GET'])
@require_auth
def get_trends(session_id):
    """Get satisfaction trends over time"""
    leader_id = request.headers.get('X-Leader-ID')
    
    try:
        session = FeedbackSession.query.filter_by(
            id=session_id,
            leader_id=leader_id
        ).first()
        
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        # Get feedbacks grouped by day
        feedbacks = Feedback.query.filter_by(
            session_id=session_id,
            is_filtered=False
        ).all()
        
        # Calculate daily trends
        trends = {}
        for fb in feedbacks:
            day = fb.created_at.date().isoformat()
            if day not in trends:
                trends[day] = []
            
            # Convert sentiment score to 0-10 scale
            if fb.sentiment_score is not None:
                score = (fb.sentiment_score + 1) / 2 * 10
                trends[day].append(score)
        
        # Calculate daily averages
        daily_avg = {
            day: round(sum(scores) / len(scores), 1) 
            for day, scores in trends.items()
        }
        
        return jsonify({
            'trends': daily_avg
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/sessions/<session_id>/word-cloud', methods=['GET'])
@require_auth
def get_word_cloud(session_id):
    """Get word frequency for word cloud"""
    leader_id = request.headers.get('X-Leader-ID')
    
    try:
        session = FeedbackSession.query.filter_by(
            id=session_id,
            leader_id=leader_id
        ).first()
        
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        # Get all topics from feedbacks
        feedbacks = Feedback.query.filter_by(
            session_id=session_id,
            is_filtered=False
        ).all()
        
        from collections import Counter
        topics = []
        for fb in feedbacks:
            if fb.topics:
                topics.extend(fb.topics)
        
        topic_freq = Counter(topics)
        top_topics = topic_freq.most_common(20)
        
        return jsonify({
            'word_cloud': [
                {'topic': topic, 'frequency': freq}
                for topic, freq in top_topics
            ]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== Export API ====================

@api_bp.route('/sessions/<session_id>/export-pdf', methods=['GET'])
@require_auth
def export_pdf(session_id):
    """Export analytics as PDF"""
    leader_id = request.headers.get('X-Leader-ID')
    
    try:
        session = FeedbackSession.query.filter_by(
            id=session_id,
            leader_id=leader_id
        ).first()
        
        if not session or not session.analytics:
            return jsonify({'error': 'Session not found or not ready'}), 404
        
        # Generate PDF (using reportlab)
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        from io import BytesIO
        
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        
        # Add title
        c.setFont("Helvetica-Bold", 24)
        c.drawString(50, 750, f"Feedback Analytics Report")
        
        # Add session info
        c.setFont("Helvetica", 12)
        c.drawString(50, 720, f"Session: {session.title}")
        c.drawString(50, 700, f"Generated: {datetime.utcnow().isoformat()}")
        
        # Add metrics
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, 660, "Key Metrics:")
        
        c.setFont("Helvetica", 12)
        c.drawString(70, 640, f"Total Feedbacks: {session.analytics.total_feedbacks}")
        c.drawString(70, 620, f"Satisfaction Score: {session.analytics.satisfaction_score}/10")
        c.drawString(70, 600, f"Positive: {session.analytics.sentiment_positive}%")
        c.drawString(70, 580, f"Neutral: {session.analytics.sentiment_neutral}%")
        c.drawString(70, 560, f"Negative: {session.analytics.sentiment_negative}%")
        
        # Add summary
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, 520, "Summary:")
        
        c.setFont("Helvetica", 11)
        y = 500
        for line in session.analytics.summary_text.split('\n'):
            c.drawString(70, y, line[:80])
            y -= 20
        
        c.save()
        buffer.seek(0)
        
        return {
            'pdf': buffer.getvalue(),
            'filename': f"feedback-report-{session_id}.pdf"
        }, 200, {'Content-Disposition': f'attachment; filename="feedback-report-{session_id}.pdf"'}
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== Health Check ====================

@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.utcnow().isoformat()
    }), 200


# Register blueprint
def register_api(app):
    app.register_blueprint(api_bp)
