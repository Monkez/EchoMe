# TalkToMe Testing Guide

## 📋 Test Coverage

```
Backend Tests:
├── Authentication (5 tests)
│   ├─ Register success
│   ├─ Register duplicate email
│   ├─ Login success
│   ├─ Login invalid password
│   └─ Login nonexistent user
│
├── Session Management (7 tests)
│   ├─ Create session
│   ├─ List sessions
│   ├─ Get session detail
│   ├─ Close session
│   └─ ...
│
├── Feedback Submission (7 tests)
│   ├─ Submit feedback
│   ├─ Validate UID
│   ├─ Invalid UID
│   ├─ Too short/long content
│   └─ ...
│
├── Analytics (3 tests)
│   ├─ Get analytics
│   ├─ Trends data
│   └─ ...
│
└── Integration Tests (1 test)
    └─ Full workflow

LLM Service Tests:
├── Sentiment Analysis (4 tests)
│   ├─ Positive feedback
│   ├─ Negative feedback
│   ├─ Neutral feedback
│   └─ Topic extraction
│
├── Quality Checks (2 tests)
│   ├─ Spam detection
│   └─ Inappropriate content
│
└── Batch Processing (4 tests)
    ├─ Batch analysis
    ├─ Satisfaction score
    ├─ Summary generation
    └─ Multilingual support

Total: 29+ Test Cases
```

---

## 🚀 Running Tests

### Prerequisites

```bash
pip install pytest pytest-cov python-dotenv
```

### Run All Tests

```bash
# Run all tests with verbose output
pytest -v

# Run with coverage report
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_api.py -v

# Run specific test class
pytest tests/test_api.py::TestAuthentication -v

# Run specific test
pytest tests/test_api.py::TestAuthentication::test_login_success -v
```

### Run by Category

```bash
# Unit tests only
pytest -m unit -v

# Integration tests only
pytest -m integration -v

# Exclude integration tests
pytest -m "not integration" -v
```

### Run with Coverage

```bash
# Generate HTML coverage report
pytest --cov=. --cov-report=html

# View report
open htmlcov/index.html

# Show coverage percentage
pytest --cov=. --cov-report=term-missing
```

---

## ✅ Test Categories

### Authentication Tests
```python
# Test cases
✓ Register new leader
✓ Register duplicate email (fails)
✓ Login success
✓ Login wrong password (fails)
✓ Login nonexistent user (fails)
```

### Session Management Tests
```python
# Test cases
✓ Create session (new UID)
✓ Create without auth (fails)
✓ List all sessions
✓ Get session details
✓ Get nonexistent session (fails)
✓ Close session
```

### Feedback Submission Tests
```python
# Test cases
✓ Submit feedback successfully
✓ Submit to invalid UID (fails)
✓ Submit to closed session (fails)
✓ Content too short (fails)
✓ Content too long (fails)
✓ Validate UID valid
✓ Validate UID invalid
```

### Analytics Tests
```python
# Test cases
✓ Get analytics (processing)
✓ Get analytics with data
✓ Get satisfaction trends
✓ Export PDF
```

### LLM Service Tests
```python
# Test cases
✓ Analyze positive feedback
✓ Analyze negative feedback
✓ Analyze neutral feedback
✓ Extract topics
✓ Detect spam
✓ Batch analysis
✓ Satisfaction score (0-10)
✓ Summary generation
✓ Multilingual support
```

---

## 📊 Expected Test Results

### Sample Output

```
tests/test_api.py::TestAuthentication::test_register_success PASSED
tests/test_api.py::TestAuthentication::test_register_duplicate_email PASSED
tests/test_api.py::TestAuthentication::test_login_success PASSED
tests/test_api.py::TestSessionManagement::test_create_session_success PASSED
tests/test_api.py::TestFeedbackSubmission::test_submit_feedback_success PASSED
tests/test_api.py::TestIntegration::test_full_workflow PASSED
tests/test_llm.py::TestFeedbackAnalyzer::test_analyze_positive_feedback PASSED
tests/test_llm.py::TestFeedbackAnalyzer::test_batch_analysis PASSED

======================== 29 passed in 2.34s ========================
```

### Coverage Report

```
Name                  Stmts   Miss  Cover
------------------------------------------
app.py               120      5    96%
models.py            80       2    97%
api_routes.py        200      10   95%
llm_service.py       150      8    94%
tasks.py             100      5    95%
------------------------------------------
TOTAL                650      30   95%
```

---

## 🔧 Fixtures

### Database Fixtures

```python
@pytest.fixture
def client():
    """In-memory SQLite test database"""
    # Creates fresh DB for each test
    # Cleans up after test
    
@pytest.fixture
def leader(client):
    """Create test leader account"""
    
@pytest.fixture
def session(leader):
    """Create test feedback session"""
```

### Usage

```python
def test_something(client, leader, session):
    # All fixtures automatically provided
    # Database state reset after test
    pass
```

---

## 🐛 Common Issues

### Issue: "No module named 'app'"
```bash
# Solution: Run from project root
cd /path/to/TalkToMe
pytest tests/
```

### Issue: Database locked
```bash
# Solution: Using in-memory SQLite, shouldn't happen
# If it does, restart pytest
```

### Issue: LLM tests fail (API key)
```bash
# Solution: Set ANTHROPIC_API_KEY
export ANTHROPIC_API_KEY="your-key"
pytest tests/test_llm.py
```

### Issue: Slow tests
```bash
# Solution: Mock external API calls
# Update test_llm.py to use mock responses
```

---

## 📈 Test Performance

### Expected Times

```
Unit Tests:      ~2-3 seconds
Integration:     ~5-10 seconds
LLM Tests:       ~10-30 seconds (depends on API)
Full Suite:      ~15-30 seconds
With Coverage:   ~20-40 seconds
```

---

## 🔒 Testing Best Practices

1. **Isolation**: Each test runs independently
2. **Cleanup**: Database reset after each test
3. **Mocking**: External APIs can be mocked
4. **Fixtures**: Reusable test data setup
5. **Assertions**: Clear expected behavior
6. **Names**: Descriptive test method names

---

## 📝 Adding New Tests

### Template

```python
class TestNewFeature:
    
    def test_happy_path(self, client, leader):
        """Test successful scenario"""
        response = client.post('/api/new-endpoint',
            json={'data': 'value'},
            headers={'X-Leader-ID': leader.id}
        )
        
        assert response.status_code == 200
        assert 'expected_key' in response.json
    
    
    def test_error_case(self, client):
        """Test error scenario"""
        response = client.post('/api/new-endpoint',
            json={'bad': 'data'}
        )
        
        assert response.status_code == 400
        assert 'error' in response.json
```

---

## 🚀 CI/CD Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Run tests
      run: pytest --cov=. --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v2
```

---

**Ready to test! Run: `pytest -v`** 🎯🐈
