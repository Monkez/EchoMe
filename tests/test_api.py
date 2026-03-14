"""
TalkToMe Testing Suite - Unit & Integration Tests
pytest + fixtures for comprehensive testing
"""

import pytest
import json
from datetime import datetime, timedelta
from app import app, db
from models import Leader, FeedbackSession, Feedback, SessionAnalytics
from werkzeug.security import generate_password_hash
import uuid

# ==================== Fixtures ====================

@pytest.fixture
def client():
    """Test client"""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()


@pytest.fixture
def leader(client):
    """Create test leader"""
    with app.app_context():
        leader = Leader(
            id=str(uuid.uuid4()),
            email='test@example.com',
            name='Test Leader',
            password_hash=generate_password_hash('password123')
        )
        db.session.add(leader)
        db.session.commit()
        return leader


@pytest.fixture
def session(leader):
    """Create test feedback session"""
    with app.app_context():
        session = FeedbackSession(
            id=str(uuid.uuid4()),
            uid='TEST1234',
            leader_id=leader.id,
            title='Test Feedback Session',
            description='Testing feedback collection',
            status='active'
        )
        db.session.add(session)
        db.session.commit()
        return session


# ==================== Authentication Tests ====================

class TestAuthentication:
    
    def test_register_success(self, client):
        """Test successful registration"""
        response = client.post('/api/auth/register', 
            json={
                'email': 'newleader@example.com',
                'name': 'New Leader',
                'password': 'secure_password123'
            }
        )
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert 'leader_id' in data
    
    
    def test_register_duplicate_email(self, client, leader):
        """Test registration with existing email"""
        response = client.post('/api/auth/register',
            json={
                'email': 'test@example.com',  # Already exists
                'name': 'Duplicate',
                'password': 'password'
            }
        )
        
        assert response.status_code == 409
        assert 'already registered' in response.json['error']
    
    
    def test_register_missing_fields(self, client):
        """Test registration with missing fields"""
        response = client.post('/api/auth/register',
            json={
                'email': 'test@test.com'
                # Missing name and password
            }
        )
        
        assert response.status_code == 400
        assert 'Missing required fields' in response.json['error']
    
    
    def test_login_success(self, client, leader):
        """Test successful login"""
        response = client.post('/api/auth/login',
            json={
                'email': 'test@example.com',
                'password': 'password123'
            }
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'leader_id' in data
        assert data['name'] == 'Test Leader'
    
    
    def test_login_invalid_password(self, client, leader):
        """Test login with wrong password"""
        response = client.post('/api/auth/login',
            json={
                'email': 'test@example.com',
                'password': 'wrongpassword'
            }
        )
        
        assert response.status_code == 401
        assert 'Invalid credentials' in response.json['error']
    
    
    def test_login_nonexistent_user(self, client):
        """Test login for non-existent user"""
        response = client.post('/api/auth/login',
            json={
                'email': 'notexist@example.com',
                'password': 'password'
            }
        )
        
        assert response.status_code == 401


# ==================== Session Management Tests ====================

class TestSessionManagement:
    
    def test_create_session_success(self, client, leader):
        """Test creating feedback session"""
        response = client.post('/api/sessions',
            json={
                'title': 'Q1 Feedback',
                'description': 'Quarterly review',
                'allow_multiple_submissions': True
            },
            headers={'X-Leader-ID': leader.id}
        )
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert 'uid' in data
        assert len(data['uid']) == 8
        assert data['session']['title'] == 'Q1 Feedback'
    
    
    def test_create_session_without_auth(self, client):
        """Test creating session without authentication"""
        response = client.post('/api/sessions',
            json={'title': 'Test'}
        )
        
        assert response.status_code == 401
    
    
    def test_create_session_missing_title(self, client, leader):
        """Test creating session without title"""
        response = client.post('/api/sessions',
            json={'description': 'No title'},
            headers={'X-Leader-ID': leader.id}
        )
        
        assert response.status_code == 400
    
    
    def test_list_sessions(self, client, leader, session):
        """Test listing leader's sessions"""
        response = client.get('/api/sessions',
            headers={'X-Leader-ID': leader.id}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['sessions']) == 1
        assert data['sessions'][0]['title'] == 'Test Feedback Session'
    
    
    def test_get_session_detail(self, client, leader, session):
        """Test getting session details"""
        response = client.get(f'/api/sessions/{session.id}',
            headers={'X-Leader-ID': leader.id}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['session']['uid'] == 'TEST1234'
        assert data['session']['status'] == 'active'
    
    
    def test_get_nonexistent_session(self, client, leader):
        """Test getting non-existent session"""
        fake_id = str(uuid.uuid4())
        response = client.get(f'/api/sessions/{fake_id}',
            headers={'X-Leader-ID': leader.id}
        )
        
        assert response.status_code == 404
    
    
    def test_close_session(self, client, leader, session):
        """Test closing session"""
        response = client.post(f'/api/sessions/{session.id}/close',
            headers={'X-Leader-ID': leader.id}
        )
        
        assert response.status_code == 200
        
        # Verify session is closed
        with app.app_context():
            s = FeedbackSession.query.get(session.id)
            assert s.status == 'closed'


# ==================== Feedback Submission Tests ====================

class TestFeedbackSubmission:
    
    def test_submit_feedback_success(self, client, session):
        """Test successful feedback submission"""
        response = client.post('/api/feedback/submit',
            json={
                'uid': 'TEST1234',
                'content': 'This is constructive feedback about our work environment.'
            }
        )
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert 'feedback_id' in data
    
    
    def test_submit_feedback_invalid_uid(self, client):
        """Test submission with invalid UID"""
        response = client.post('/api/feedback/submit',
            json={
                'uid': 'INVALID',
                'content': 'Some feedback'
            }
        )
        
        assert response.status_code == 404
        assert 'Invalid feedback code' in response.json['error']
    
    
    def test_submit_feedback_closed_session(self, client, leader, session):
        """Test submission to closed session"""
        # Close session
        with app.app_context():
            s = FeedbackSession.query.get(session.id)
            s.status = 'closed'
            db.session.commit()
        
        response = client.post('/api/feedback/submit',
            json={
                'uid': 'TEST1234',
                'content': 'Feedback'
            }
        )
        
        assert response.status_code == 410
        assert 'closed' in response.json['error']
    
    
    def test_submit_feedback_too_short(self, client, session):
        """Test feedback too short"""
        response = client.post('/api/feedback/submit',
            json={
                'uid': 'TEST1234',
                'content': 'short'
            }
        )
        
        assert response.status_code == 400
        assert 'at least 10 characters' in response.json['error']
    
    
    def test_submit_feedback_too_long(self, client, session):
        """Test feedback too long"""
        long_text = 'x' * 5001
        response = client.post('/api/feedback/submit',
            json={
                'uid': 'TEST1234',
                'content': long_text
            }
        )
        
        assert response.status_code == 400
        assert 'less than 5000 characters' in response.json['error']
    
    
    def test_validate_uid_valid(self, client, session):
        """Test UID validation - valid"""
        response = client.post('/api/feedback/validate-uid',
            json={'uid': 'TEST1234'}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['valid'] == True
        assert data['session_title'] == 'Test Feedback Session'
    
    
    def test_validate_uid_invalid(self, client):
        """Test UID validation - invalid"""
        response = client.post('/api/feedback/validate-uid',
            json={'uid': 'FAKECODE'}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['valid'] == False


# ==================== Analytics Tests ====================

class TestAnalytics:
    
    def test_get_analytics_no_data(self, client, leader, session):
        """Test analytics before processing"""
        response = client.get(f'/api/sessions/{session.id}/analytics',
            headers={'X-Leader-ID': leader.id}
        )
        
        assert response.status_code == 202  # Processing
        assert response.json['status'] == 'processing'
    
    
    def test_get_analytics_with_data(self, client, leader, session):
        """Test analytics with processed feedbacks"""
        with app.app_context():
            # Add analytics
            analytics = SessionAnalytics(
                session_id=session.id,
                total_feedbacks=10,
                satisfaction_score=7.5,
                sentiment_positive=60.0,
                sentiment_neutral=25.0,
                sentiment_negative=15.0,
                top_issues=json.dumps([
                    {'topic': 'work-life-balance', 'percentage': 30},
                    {'topic': 'career-growth', 'percentage': 20}
                ]),
                summary_text='Team is satisfied but needs work-life balance improvements'
            )
            db.session.add(analytics)
            db.session.commit()
        
        response = client.get(f'/api/sessions/{session.id}/analytics',
            headers={'X-Leader-ID': leader.id}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['analytics']['satisfaction_score'] == 7.5
        assert data['analytics']['sentiments']['positive_pct'] == 60.0
    
    
    def test_get_trends(self, client, leader, session):
        """Test satisfaction trends"""
        with app.app_context():
            # Add feedbacks with different dates
            for i in range(5):
                fb = Feedback(
                    session_id=session.id,
                    content=f'Feedback {i}',
                    sentiment='positive',
                    sentiment_score=0.8,
                    is_filtered=False,
                    created_at=datetime.utcnow() - timedelta(days=i)
                )
                db.session.add(fb)
            db.session.commit()
        
        response = client.get(f'/api/sessions/{session.id}/trends',
            headers={'X-Leader-ID': leader.id}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'trends' in data
        assert len(data['trends']) >= 1


# ==================== Health Check Tests ====================

class TestHealthCheck:
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get('/api/health')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'ok'
        assert 'timestamp' in data


# ==================== Integration Tests ====================

class TestIntegration:
    
    def test_full_workflow(self, client, leader):
        """Test complete feedback flow"""
        
        # 1. Create session
        create_response = client.post('/api/sessions',
            json={
                'title': 'Integration Test Session',
                'description': 'Full workflow test'
            },
            headers={'X-Leader-ID': leader.id}
        )
        assert create_response.status_code == 201
        uid = json.loads(create_response.data)['uid']
        session_id = json.loads(create_response.data)['session']['id']
        
        # 2. Submit multiple feedbacks
        for i in range(3):
            submit_response = client.post('/api/feedback/submit',
                json={
                    'uid': uid,
                    'content': f'Feedback number {i+1} - Great team work and communication!'
                }
            )
            assert submit_response.status_code == 201
        
        # 3. Validate UID still works
        validate_response = client.post('/api/feedback/validate-uid',
            json={'uid': uid}
        )
        assert validate_response.status_code == 200
        assert json.loads(validate_response.data)['valid'] == True
        
        # 4. Close session
        close_response = client.post(f'/api/sessions/{session_id}/close',
            headers={'X-Leader-ID': leader.id}
        )
        assert close_response.status_code == 200
        
        # 5. Verify session is closed
        list_response = client.get('/api/sessions',
            headers={'X-Leader-ID': leader.id}
        )
        assert list_response.status_code == 200
        sessions = json.loads(list_response.data)['sessions']
        assert sessions[0]['status'] == 'closed'


# ==================== Run Tests ====================

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
