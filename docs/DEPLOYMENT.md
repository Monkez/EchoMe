# TalkToMe - Deployment Guide

## 📦 Production Deployment

### Prerequisites
- Python 3.8+
- Node.js 16+
- PostgreSQL 12+
- Redis 6+
- Docker (optional)

---

## 🚀 Backend Deployment

### 1. Environment Setup

```bash
# Create production environment file
cat > .env << EOF
ENVIRONMENT=production
DATABASE_URL=postgresql://user:pass@db-host:5432/talktome
SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))')
ANTHROPIC_API_KEY=your-api-key
REDIS_URL=redis://redis-host:6379/0
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
CORS_ORIGINS=https://yourdomain.com
JWT_SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))')
EOF
```

### 2. Database Setup

```bash
# Install PostgreSQL driver
pip install psycopg2-binary

# Initialize database
python -c "from app import db, app; app.app_context().push(); db.create_all()"

# Run migrations (if using Alembic)
flask db upgrade
```

### 3. Gunicorn Server

```bash
# Install Gunicorn
pip install gunicorn

# Run with multiple workers
gunicorn --workers 4 \
         --worker-class sync \
         --bind 0.0.0.0:5000 \
         --timeout 60 \
         --access-logfile - \
         --error-logfile - \
         app:app
```

### 4. Celery Worker

```bash
# Start Celery worker
celery -A tasks worker --loglevel=info

# Start Celery Beat (scheduler)
celery -A tasks beat --loglevel=info
```

### 5. Nginx Configuration

```nginx
upstream talktome_backend {
    server 127.0.0.1:5000;
}

server {
    listen 443 ssl http2;
    server_name api.talktome.com;
    
    ssl_certificate /etc/letsencrypt/live/api.talktome.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.talktome.com/privkey.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    location / {
        proxy_pass http://talktome_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
    limit_req zone=api_limit burst=20 nodelay;
}

# HTTP redirect
server {
    listen 80;
    server_name api.talktome.com;
    return 301 https://$server_name$request_uri;
}
```

### 6. Systemd Services

#### Gunicorn Service (`/etc/systemd/system/talktome.service`)

```ini
[Unit]
Description=TalkToMe Gunicorn Application
After=network.target postgresql.service

[Service]
User=www-data
WorkingDirectory=/var/www/talktome
ExecStart=/var/www/talktome/venv/bin/gunicorn \
    --workers 4 \
    --bind unix:/var/run/talktome.sock \
    app:app

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### Celery Worker Service (`/etc/systemd/system/talktome-celery.service`)

```ini
[Unit]
Description=TalkToMe Celery Worker
After=network.target redis.service

[Service]
User=www-data
WorkingDirectory=/var/www/talktome
ExecStart=/var/www/talktome/venv/bin/celery -A tasks worker --loglevel=info

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable talktome talktome-celery
sudo systemctl start talktome talktome-celery
sudo systemctl status talktome talktome-celery
```

---

## 🎨 Frontend Deployment

### 1. Build Optimization

```bash
# Install dependencies
npm install --production

# Build optimized bundle
npm run build

# Check bundle size
npm run analyze
```

### 2. Nginx Configuration

```nginx
upstream talktome_frontend {
    # Just serve static files
}

server {
    listen 443 ssl http2;
    server_name talktome.com;
    
    ssl_certificate /etc/letsencrypt/live/talktome.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/talktome.com/privkey.pem;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # Root directory
    root /var/www/talktome-frontend/build;
    index index.html;
    
    # Cache static assets
    location /static {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # SPA routing
    location / {
        try_files $uri $uri/ /index.html;
        add_header Cache-Control "no-cache";
    }
}

# HTTP redirect
server {
    listen 80;
    server_name talktome.com;
    return 301 https://$server_name$request_uri;
}
```

### 3. Environment Variables

```bash
# .env.production
REACT_APP_API_URL=https://api.talktome.com
REACT_APP_ENVIRONMENT=production
```

### 4. Deploy Command

```bash
# Build
npm run build

# Copy to server
scp -r build/* user@server:/var/www/talktome-frontend/build/

# Or with rsync
rsync -avz build/ user@server:/var/www/talktome-frontend/build/
```

---

## 🐳 Docker Deployment

### Docker Compose (`docker-compose.yml`)

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:14-alpine
    environment:
      POSTGRES_DB: talktome
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  backend:
    build: ./backend
    environment:
      DATABASE_URL: postgresql://postgres:${DB_PASSWORD}@postgres:5432/talktome
      REDIS_URL: redis://redis:6379/0
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
    ports:
      - "5000:5000"
    depends_on:
      - postgres
      - redis
    command: gunicorn --bind 0.0.0.0:5000 app:app

  celery-worker:
    build: ./backend
    environment:
      DATABASE_URL: postgresql://postgres:${DB_PASSWORD}@postgres:5432/talktome
      REDIS_URL: redis://redis:6379/0
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
    depends_on:
      - postgres
      - redis
    command: celery -A tasks worker --loglevel=info

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend

volumes:
  postgres_data:
```

Deploy:
```bash
docker-compose up -d
docker-compose logs -f
```

---

## 📊 Monitoring & Logging

### Prometheus Metrics

```python
# In app.py
from prometheus_client import Counter, Histogram, generate_latest

feedback_submissions = Counter(
    'talktome_feedbacks_submitted_total',
    'Total feedback submissions'
)

session_duration = Histogram(
    'talktome_session_duration_seconds',
    'Session duration'
)

@app.metrics
def metrics():
    return generate_latest()
```

### Logging

```python
import logging
from logging.handlers import RotatingFileHandler

if not app.debug:
    if not app.logger.handlers:
        file_handler = RotatingFileHandler(
            'logs/talktome.log',
            maxBytes=10240000,
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
```

---

## 🔒 Security Checklist

- [ ] HTTPS enabled with valid SSL certificate
- [ ] CORS properly configured
- [ ] CSRF protection enabled
- [ ] Input validation & sanitization
- [ ] SQL injection prevention (using ORM)
- [ ] XSS protection (Content-Security-Policy headers)
- [ ] Rate limiting enabled
- [ ] Database encryption enabled
- [ ] Regular backups scheduled
- [ ] Log rotation configured
- [ ] Firewall rules configured
- [ ] Secrets management (use environment variables)

---

## 📈 Performance Optimization

### Caching Strategy

```python
from flask_caching import Cache

cache = Cache(app, config={
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_URL': os.getenv('REDIS_URL'),
    'CACHE_DEFAULT_TIMEOUT': 300,
    'CACHE_KEY_PREFIX': 'talktome_'
})

@app.route('/api/sessions/<id>/analytics')
@cache.cached(timeout=300)
def get_analytics(id):
    # ...
```

### Database Optimization

```python
# Use connection pooling
from sqlalchemy.pool import QueuePool

app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'poolclass': QueuePool,
    'pool_size': 10,
    'max_overflow': 20,
    'pool_recycle': 3600,
    'pool_pre_ping': True,
}

# Add database indexes
class Feedback(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    session_id = db.Column(db.String(36), db.ForeignKey('feedback_sessions.id'), index=True)
    created_at = db.Column(db.DateTime, index=True)
```

---

## 🚨 Troubleshooting

### 502 Bad Gateway
- Check Gunicorn logs
- Verify database connection
- Check worker count

### Slow Analytics
- Check Redis connection
- Monitor Celery queue
- Consider caching

### High Memory Usage
- Check Celery task backlog
- Monitor query performance
- Adjust pool size

---

**Deployment successful! Monitor and scale as needed.** 🚀
