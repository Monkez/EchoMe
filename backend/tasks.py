"""
TalkToMe Celery Tasks - Async Processing
Handle LLM analysis & analytics updates asynchronously
"""

from celery import Celery, shared_task
from datetime import datetime
from models import db, Feedback, FeedbackSession, SessionAnalytics
from llm_service import FeedbackAnalyzer
import json

# Initialize Celery
celery_app = Celery('talktome', broker='redis://localhost:6379/0')
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)


@shared_task
def process_feedback_task(feedback_id):
    """
    Process single feedback with LLM
    Analyze sentiment, extract topics, filter spam
    """
    try:
        feedback = Feedback.query.get(feedback_id)
        if not feedback:
            return {'error': 'Feedback not found'}
        
        # Analyze feedback
        result = FeedbackAnalyzer.analyze_feedback(feedback.content)
        
        if not result['success']:
            feedback.is_filtered = True
            feedback.filter_reason = 'LLM analysis failed'
        else:
            data = result['data']
            
            # Update feedback
            feedback.sentiment = data.get('sentiment', 'neutral')
            feedback.sentiment_score = data.get('sentiment_score', 0)
            feedback.topics = data.get('topics', [])
            feedback.summary = data.get('summary', '')
            
            # Filter spam/inappropriate
            feedback.is_filtered = data.get('is_spam', False) or data.get('is_inappropriate', False)
            if feedback.is_filtered:
                feedback.filter_reason = 'Spam' if data.get('is_spam') else 'Inappropriate content'
        
        db.session.commit()
        
        # Queue analytics recalculation
        recalculate_analytics.delay(feedback.session_id)
        
        return {'success': True, 'feedback_id': feedback_id}
        
    except Exception as e:
        print(f"Error processing feedback: {e}")
        return {'error': str(e)}


@shared_task
def recalculate_analytics(session_id):
    """
    Recalculate analytics for entire session
    Called after new feedbacks are processed
    """
    try:
        session = FeedbackSession.query.get(session_id)
        if not session:
            return {'error': 'Session not found'}
        
        # Get valid feedbacks (not filtered)
        feedbacks = Feedback.query.filter_by(
            session_id=session_id,
            is_filtered=False
        ).all()
        
        if not feedbacks:
            return {'message': 'No valid feedbacks'}
        
        # Extract feedback texts for batch analysis
        feedback_texts = [fb.content for fb in feedbacks]
        
        # Batch analyze
        batch_result = FeedbackAnalyzer.batch_analyze_feedbacks(feedback_texts)
        
        if not batch_result['success']:
            return {'error': batch_result['error']}
        
        analytics_data = batch_result['data']
        
        # Get or create analytics
        analytics = session.analytics
        if not analytics:
            analytics = SessionAnalytics(session_id=session_id)
        
        # Update metrics
        analytics.total_feedbacks = analytics_data['total_feedbacks']
        analytics.satisfaction_score = analytics_data['satisfaction_score']
        analytics.sentiment_positive = analytics_data['sentiments']['positive_pct']
        analytics.sentiment_neutral = analytics_data['sentiments']['neutral_pct']
        analytics.sentiment_negative = analytics_data['sentiments']['negative_pct']
        analytics.top_issues = json.dumps(analytics_data['top_topics'])
        analytics.updated_at = datetime.utcnow()
        
        # Generate summary
        summary = FeedbackAnalyzer.generate_summary(
            feedback_texts,
            analytics_data
        )
        analytics.summary_text = summary
        
        db.session.add(analytics)
        db.session.commit()
        
        return {
            'success': True,
            'session_id': session_id,
            'feedbacks_processed': analytics_data['total_feedbacks']
        }
        
    except Exception as e:
        print(f"Error recalculating analytics: {e}")
        return {'error': str(e)}


@shared_task
def close_expired_sessions():
    """
    Close sessions with passed deadline
    Run periodically (hourly)
    """
    try:
        from datetime import datetime, timedelta
        
        now = datetime.utcnow()
        expired = FeedbackSession.query.filter(
            FeedbackSession.deadline <= now,
            FeedbackSession.status == 'active'
        ).all()
        
        for session in expired:
            session.status = 'closed'
        
        db.session.commit()
        
        return {
            'success': True,
            'sessions_closed': len(expired)
        }
        
    except Exception as e:
        print(f"Error closing expired sessions: {e}")
        return {'error': str(e)}


@shared_task
def send_reminders():
    """
    Send reminder notifications
    Run periodically (daily)
    """
    try:
        # Find active sessions with deadline in 24 hours
        from datetime import datetime, timedelta
        
        now = datetime.utcnow()
        tomorrow = now + timedelta(days=1)
        
        sessions = FeedbackSession.query.filter(
            FeedbackSession.deadline.between(now, tomorrow),
            FeedbackSession.status == 'active'
        ).all()
        
        notifications_sent = 0
        
        for session in sessions:
            # Send notification to leader
            # TODO: Implement notification service
            notifications_sent += 1
        
        return {
            'success': True,
            'notifications_sent': notifications_sent
        }
        
    except Exception as e:
        print(f"Error sending reminders: {e}")
        return {'error': str(e)}


@shared_task
def cleanup_old_data():
    """
    Clean up old closed sessions & logs
    Run weekly
    """
    try:
        from datetime import datetime, timedelta
        
        # Delete closed sessions older than 1 year
        cutoff = datetime.utcnow() - timedelta(days=365)
        
        old_sessions = FeedbackSession.query.filter(
            FeedbackSession.status == 'closed',
            FeedbackSession.created_at < cutoff
        ).all()
        
        for session in old_sessions:
            # Delete associated feedbacks & analytics
            Feedback.query.filter_by(session_id=session.id).delete()
            SessionAnalytics.query.filter_by(session_id=session.id).delete()
            db.session.delete(session)
        
        db.session.commit()
        
        return {
            'success': True,
            'sessions_deleted': len(old_sessions)
        }
        
    except Exception as e:
        print(f"Error cleaning up old data: {e}")
        return {'error': str(e)}


# Periodic tasks configuration
from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    'close-expired-sessions': {
        'task': 'tasks.close_expired_sessions',
        'schedule': crontab(minute=0),  # Every hour
    },
    'send-reminders': {
        'task': 'tasks.send_reminders',
        'schedule': crontab(hour=9, minute=0),  # Daily at 9 AM
    },
    'cleanup-old-data': {
        'task': 'tasks.cleanup_old_data',
        'schedule': crontab(day_of_week=0, hour=2, minute=0),  # Weekly Sunday 2 AM
    },
}
