#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EchoMe Backend Server
Premium Anonymous Feedback Platform
"""

import os, sys, io, uuid, json, random, hashlib, re, threading
import requests as http_requests
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from collections import Counter

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app)

db_url = os.getenv('DATABASE_URL', 'sqlite:///echome.db')
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = db_url
if db_url.startswith("postgresql://"):
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_pre_ping': True, 'pool_recycle': 300}
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-echome-v1')

db = SQLAlchemy(app)

# ==================== Models ====================

class Leader(db.Model):
    __tablename__ = 'leaders'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    company = db.Column(db.String(200), default='')
    password_hash = db.Column(db.String(256), nullable=False)
    avatar_color = db.Column(db.String(7), default='#6C5CE7')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class FeedbackSession(db.Model):
    __tablename__ = 'feedback_sessions'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    uid = db.Column(db.String(8), unique=True, nullable=False)
    leader_id = db.Column(db.String(36), db.ForeignKey('leaders.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default='')
    category = db.Column(db.String(50), default='general')  # general, pulse, exit, project
    status = db.Column(db.String(20), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    closed_at = db.Column(db.DateTime, nullable=True)
    cached_analytics_json = db.Column(db.Text, nullable=True)
    last_analyzed_at = db.Column(db.DateTime, nullable=True)
    last_feedback_count = db.Column(db.Integer, default=0)

class Feedback(db.Model):
    __tablename__ = 'feedbacks'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = db.Column(db.String(36), db.ForeignKey('feedback_sessions.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    sentiment = db.Column(db.String(20), default='neutral')
    sentiment_score = db.Column(db.Float, default=0.0)
    topics = db.Column(db.Text, default='[]')
    is_filtered = db.Column(db.Boolean, default=False)
    filter_reason = db.Column(db.String(200), default='')
    ai_summary = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ==================== LLM-Powered Analysis ====================

LLM_API_KEY = "key_dd7f66cc2646195bbeeef14f413490d56030022ab9f24822b99f24a88f41de4e"
LLM_API_BASE = "https://aisieure.com/v1"
LLM_MODEL = "claude-haiku-4.5"

def call_llm(prompt, max_tokens=800):
    """Call the LLM API directly via HTTP (OpenAI-compatible)"""
    try:
        resp = http_requests.post(
            f"{LLM_API_BASE}/chat/completions",
            headers={
                "Authorization": f"Bearer {LLM_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": LLM_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": 0.3
            },
            timeout=60
        )
        if resp.status_code != 200:
            print(f"[LLM Error] Status {resp.status_code}: {resp.text[:300]}")
            return None
        data = resp.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"[LLM Error] {type(e).__name__}: {e}")
        return None

def analyze_feedback_llm(content):
    """Use LLM to analyze a single feedback submission"""
    prompt = f"""Phân tích góp ý ẩn danh sau. Trả về CHỈ JSON hợp lệ, không markdown, không giải thích thêm:

GÓP Ý: "{content}"

Trả về JSON:
{{"sentiment":"positive hoặc neutral hoặc negative","sentiment_score":-1.0 đến 1.0,"topics":["chủ đề 1","chủ đề 2"],"is_spam":true/false,"spam_reason":"lý do nếu spam","summary":"tóm tắt chi tiết nội dung chính"}}

Quy tắc:
- topics: 1-3 chủ đề chính bằng tiếng Việt
- is_spam = true nếu: vô nghĩa, lặp ký tự, quá ngắn, xúc phạm/công kích cá nhân
- summary: TÓM TẮT CỤ THỂ nhưng PHẢI KHÁI QUÁT HÓA sự việc để hoàn toàn ẨN DANH người viết. TUYỆT ĐỐI QUAN TRỌNG: Không giữ lại tên riêng, thời gian cụ thể, sự kiện chi tiết khiến người nhận đoán ra ai viết. Vd: "Chủ nhật rồi m trễ 30p" -> "Có ý kiến nhắc nhở về việc chưa tuân thủ thời gian trong các cuộc hẹn". Vd công việc: "Sếp Minh hay mắng" -> "Góp ý về phong cách giao tiếp chưa phù hợp từ cấp quản lý". Tự động nhận diện bối cảnh công ty hay đời sống để dùng từ cho chuẩn.
- CHỈ trả về JSON"""

    result = call_llm(prompt, max_tokens=500)
    if result:
        try:
            cleaned = result.strip()
            if cleaned.startswith("```"):
                cleaned = re.sub(r'^```(?:json)?\s*', '', cleaned)
                cleaned = re.sub(r'\s*```$', '', cleaned)
            return json.loads(cleaned)
        except json.JSONDecodeError:
            print(f"[LLM Parse Error] {result[:200]}")
    return None

def generate_llm_analytics(feedbacks_data, session_title='', session_category='general'):
    """Generate comprehensive analytics using LLM - returns structured JSON"""
    if not feedbacks_data:
        return None
    
    total = len(feedbacks_data)
    # Use summary if available, otherwise fallback to raw content
    all_summaries = [f.get('summary') if f.get('summary') else f.get('content', '') for f in feedbacks_data]
    
    # Filter out empty strings
    all_summaries = [s for s in all_summaries if s.strip()]
    summary_list = '\n'.join([f"- {s}" for s in all_summaries[:20]])
    
    is_personal = session_category == 'personal' or 'nhận xét' in session_title.lower() or 'cá nhân' in session_title.lower()
    
    if is_personal:
        prompt = f"""Bạn là một người bạn thân thiết. Nhóm bạn vừa gom được {total} lời nhắn (khen, chê, khuyên nhủ) dành cho một người bạn chung.
Nhiệm vụ: Tổng hợp lại thành một bức thư/báo cáo nhỏ mang giọng điệu đời thường, quan tâm. 

TUYỆT ĐỐI KHÔNG DÙNG: "nhân viên", "đồng nghiệp", "công ty", "kỷ luật", "quy định", "nơi làm việc", "tuân thủ", "trách nhiệm công việc".
(Ví dụ: Đi trễ -> Trễ hẹn đi chơi. Cáu gắt -> Tâm trạng thất thường với bạn bè).

CÁC LỜI NHẮN:
{summary_list}

Trả về CHỈ JSON theo định dạng sau (KHÔNG thêm markdown bao quanh khối json):
{{"diem_tinh_cam": 0-10, "cam_xuc_chung": "positive/mixed/negative", "dac_diem": [{{"label": "Tính cách", "value": "Ngắn gọn", "color": "success/warning/danger/info"}}], "phan_loai": [{{"label": "nhóm ý kiến", "percentage": số, "type": "positive/neutral/negative"}}], "chu_de": [{{"theme": "Chủ đề", "count": số}}], "thu_gui_ban_be": "đoạn văn"}}

QUY TẮC CẦN NHỚ:
- dac_diem: 4 items, label là tính cách (vd "Sự quan tâm", "Đúng giờ").
- thu_gui_ban_be: Tiếng Việt. Dùng \n cho xuống dòng. Viết như một lời tóm tắt cho bạn bè đọc. Chia thành các phần: 📊 Nhận xét chung, 🌟 Điểm đáng yêu, 🤔 Điểm cần tém lại, 💡 Lời khuyên chân thành.
- Bắt buộc KHÁI QUÁT HÓA, không trích câu nguyên văn làm lộ danh tính người viết.
- QUAN TRỌNG: thu_gui_ban_be dùng \\n (escaped newline). KHÔNG dùng newline thật. CHỈ trả về JSON hợp lệ."""
    else:
        prompt = f"""Bạn là chuyên gia phân tích và tổng hợp thông tin. Dựa trên {total} ý kiến/góp ý ẩn danh, phân tích TOÀN DIỆN.

BỐI CẢNH: Phiên "{session_title}" (loại: {session_category})
LƯU Ý CỰC KỲ QUAN TRỌNG: Tự động nhận diện đây là công sở hay môi trường tổ chức để dùng từ ngữ (nhân viên/sinh viên/mọi người) cho phù hợp. Quán triệt việc bảo mật danh tính, tuyệt đối KHÁI QUÁT HÓA mọi ví dụ.

CÁC GÓP Ý (đã ẩn danh):
{summary_list}

Trả về CHỈ JSON theo định dạng sau:
{{"satisfaction_score": 0-10, "overall_sentiment": "positive/mixed/negative", "key_metrics": [{{"label": "tên metric linh hoạt", "value": "giá trị", "color": "success/warning/danger/info"}}], "highlights": [{{"label": "nhóm ý", "percentage": số, "type": "positive/neutral/negative"}}], "top_themes": [{{"theme": "chủ đề", "count": số}}], "insight_report": "đoạn văn"}}

QUY TẮC CẦN NHỚ:
- key_metrics: 4 items (linh hoạt theo nội dung).
- insight_report: Tiếng Việt. Dùng \n cho xuống dòng. Cấu trúc: 📊 Tổng quan, 🔍 Vấn đề, ✅ Điểm tích cực, 💡 Khuyến nghị.
- QUAN TRỌNG: insight_report dùng \\n (escaped newline). KHÔNG dùng newline thật. CHỈ trả về JSON hợp lệ."""

    print(f"[LLM Analytics] Calling LLM with {total} feedbacks...")
    result = call_llm(prompt, max_tokens=2500)
    if result:
        # Write debug log to file
        with open('/tmp/llm_analytics_debug.txt', 'w', encoding='utf-8') as f:
            f.write(f"=== RAW RESPONSE ({len(result)} chars) ===\n")
            f.write(result)
            f.write("\n=== END RAW ===\n")
        
        # Try multiple extraction strategies
        text = result.strip()
        
        # Strategy 1: Remove code fences aggressively
        text = re.sub(r'```\w*\s*', '', text)
        text = text.replace('```', '')
        text = text.strip()
        
        # Strategy 2: Find the outermost JSON object
        start = text.find('{')
        end = text.rfind('}')
        if start >= 0 and end > start:
            json_str = text[start:end+1]
            try:
                parsed = json.loads(json_str)
                print(f"[LLM Analytics] Parsed OK! Keys: {list(parsed.keys())}")
                
                # Map personal keys back to standard schema if needed
                if "thu_gui_ban_be" in parsed:
                    return {
                        "satisfaction_score": parsed.get("diem_tinh_cam", 0),
                        "overall_sentiment": parsed.get("cam_xuc_chung", "neutral"),
                        "key_metrics": parsed.get("dac_diem", []),
                        "highlights": parsed.get("phan_loai", []),
                        "top_themes": parsed.get("chu_de", []),
                        "insight_report": parsed.get("thu_gui_ban_be", "")
                    }
                return parsed
            except json.JSONDecodeError as e:
                with open('/tmp/llm_analytics_debug.txt', 'a', encoding='utf-8') as f:
                    f.write(f"\n=== PARSE ERROR ===\n{e}\n")
                    f.write(f"\n=== CLEANED JSON ===\n{json_str}\n")
                print(f"[LLM Analytics] Parse error: {e}")
        else:
            print(f"[LLM Analytics] No JSON object found")
    else:
        print("[LLM Analytics] No response from LLM")
    return None

def fallback_analytics(feedbacks_data):
    """Fallback when LLM is unavailable"""
    total = len(feedbacks_data)
    pos = sum(1 for f in feedbacks_data if f.get('sentiment') == 'positive')
    neg = sum(1 for f in feedbacks_data if f.get('sentiment') == 'negative')
    pos_pct = round(pos / total * 100, 1)
    neg_pct = round(neg / total * 100, 1)
    neu_pct = round(100 - pos_pct - neg_pct, 1)
    avg_score = sum(f.get('score', 0) for f in feedbacks_data) / total
    satisfaction = round((avg_score + 1) / 2 * 10, 1)
    all_topics = []
    for f in feedbacks_data:
        all_topics.extend(f.get('topics', []))
    topic_counts = Counter(all_topics)
    return {
        'satisfaction_score': max(0, min(10, satisfaction)),
        'overall_sentiment': 'positive' if pos_pct > 50 else 'negative' if neg_pct > 50 else 'mixed',
        'key_metrics': [
            {'label': 'Tổng góp ý', 'value': str(total), 'color': 'info'},
            {'label': 'Điểm đánh giá', 'value': f'{satisfaction}/10', 'color': 'success' if satisfaction >= 7 else 'warning'},
            {'label': 'Tích cực', 'value': f'{pos_pct}%', 'color': 'success'},
            {'label': 'Cần cải thiện', 'value': f'{neg_pct}%', 'color': 'danger'}
        ],
        'highlights': [
            {'label': 'Tích cực', 'percentage': pos_pct, 'type': 'positive'},
            {'label': 'Trung lập', 'percentage': neu_pct, 'type': 'neutral'},
            {'label': 'Cần cải thiện', 'percentage': neg_pct, 'type': 'negative'}
        ],
        'top_themes': [{'theme': t, 'count': c} for t, c in topic_counts.most_common(6)],
        'insight_report': f'📊 {total} góp ý, {pos_pct}% tích cực. (Phân tích AI không khả dụng, đang dùng phân tích cơ bản)'
    }

# ==================== Routes ====================

@app.route('/')
def serve_frontend():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'version': '1.0', 'name': 'EchoMe'}), 200

# ----- Auth -----

@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email', '').strip()
    name = data.get('name', '').strip()
    password = data.get('password', '')
    company = data.get('company', '').strip()
    
    if not email or not name or not password:
        return jsonify({'error': 'Vui lòng điền đầy đủ thông tin'}), 400
    
    if len(password) < 6:
        return jsonify({'error': 'Mật khẩu phải có ít nhất 6 ký tự'}), 400
    
    if Leader.query.filter_by(email=email).first():
        return jsonify({'error': 'Email đã được đăng ký'}), 409
    
    # Generate a consistent avatar color from email
    color_hash = hashlib.md5(email.encode()).hexdigest()[:6]
    avatar_color = f'#{color_hash}'
    
    from werkzeug.security import generate_password_hash
    leader = Leader(
        email=email, name=name, company=company,
        password_hash=generate_password_hash(password),
        avatar_color=avatar_color
    )
    db.session.add(leader)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'leader_id': leader.id,
        'name': leader.name,
        'email': leader.email,
        'company': leader.company,
        'avatar_color': leader.avatar_color
    }), 201

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    
    leader = Leader.query.filter_by(email=email).first()
    if not leader:
        return jsonify({'error': 'Thông tin đăng nhập không đúng'}), 401
    
    from werkzeug.security import check_password_hash
    if not check_password_hash(leader.password_hash, password):
        return jsonify({'error': 'Thông tin đăng nhập không đúng'}), 401
    
    return jsonify({
        'success': True,
        'leader_id': leader.id,
        'name': leader.name,
        'email': leader.email,
        'company': leader.company,
        'avatar_color': leader.avatar_color
    }), 200

# ----- Sessions -----

@app.route('/api/sessions', methods=['GET'])
def list_sessions():
    leader_id = request.headers.get('X-Leader-ID')
    if not leader_id:
        return jsonify({'error': 'Unauthorized'}), 401
    
    sessions = FeedbackSession.query.filter_by(leader_id=leader_id)\
        .order_by(FeedbackSession.created_at.desc()).all()
    
    result = []
    for s in sessions:
        fb_count = Feedback.query.filter_by(session_id=s.id).count()
        valid_count = Feedback.query.filter_by(session_id=s.id, is_filtered=False).count()
        
        # Quick sentiment summary
        feedbacks = Feedback.query.filter_by(session_id=s.id, is_filtered=False).all()
        pos = sum(1 for f in feedbacks if f.sentiment == 'positive')
        neg = sum(1 for f in feedbacks if f.sentiment == 'negative')
        
        result.append({
            'id': s.id,
            'uid': s.uid,
            'title': s.title,
            'description': s.description,
            'category': s.category,
            'status': s.status,
            'total_feedbacks': fb_count,
            'valid_feedbacks': valid_count,
            'positive_count': pos,
            'negative_count': neg,
            'created_at': s.created_at.isoformat(),
            'closed_at': s.closed_at.isoformat() if s.closed_at else None
        })
    
    return jsonify({'success': True, 'sessions': result}), 200

@app.route('/api/sessions', methods=['POST'])
def create_session():
    data = request.get_json()
    leader_id = request.headers.get('X-Leader-ID')
    
    if not leader_id or not data or not data.get('title'):
        return jsonify({'error': 'Thiếu thông tin'}), 400
    
    # Generate unique readable UID
    uid = str(uuid.uuid4()).replace('-', '')[:8].upper()
    while FeedbackSession.query.filter_by(uid=uid).first():
        uid = str(uuid.uuid4()).replace('-', '')[:8].upper()
    
    session = FeedbackSession(
        uid=uid,
        leader_id=leader_id,
        title=data['title'],
        description=data.get('description', ''),
        category=data.get('category', 'general')
    )
    db.session.add(session)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'uid': uid,
        'session_id': session.id,
        'title': session.title
    }), 201

@app.route('/api/sessions/<identifier>/close', methods=['POST'])
def close_session(identifier):
    session = FeedbackSession.query.get(identifier)
    if not session:
        session = FeedbackSession.query.filter_by(uid=identifier.upper()).first()
    if not session:
        return jsonify({'error': 'Không tìm thấy phiên góp ý'}), 404
    
    session.status = 'closed'
    session.closed_at = datetime.utcnow()
    db.session.commit()
    return jsonify({'success': True}), 200

@app.route('/api/sessions/<identifier>/reopen', methods=['POST'])
def reopen_session(identifier):
    session = FeedbackSession.query.get(identifier)
    if not session:
        session = FeedbackSession.query.filter_by(uid=identifier.upper()).first()
    if not session:
        return jsonify({'error': 'Không tìm thấy phiên góp ý'}), 404
    
    session.status = 'active'
    session.closed_at = None
    db.session.commit()
    return jsonify({'success': True}), 200

# ----- Feedback -----

@app.route('/api/feedback/validate', methods=['POST'])
def validate_uid():
    data = request.get_json()
    uid = data.get('uid', '').strip().upper()
    
    session = FeedbackSession.query.filter_by(uid=uid).first()
    if not session:
        return jsonify({'valid': False, 'reason': 'Mã góp ý không tồn tại'}), 200
    if session.status == 'closed':
        return jsonify({'valid': False, 'reason': 'Phiên góp ý đã đóng'}), 200
    
    return jsonify({
        'valid': True,
        'title': session.title,
        'description': session.description,
        'category': session.category
    }), 200

@app.route('/api/feedback/submit', methods=['POST'])
def submit_feedback():
    data = request.get_json()
    uid = data.get('uid', '').strip().upper()
    content = data.get('content', '').strip()
    
    if not uid or not content:
        return jsonify({'error': 'Vui lòng nhập đầy đủ thông tin'}), 400
    
    session = FeedbackSession.query.filter_by(uid=uid).first()
    if not session:
        return jsonify({'error': 'Mã góp ý không hợp lệ'}), 404
    if session.status == 'closed':
        return jsonify({'error': 'Phiên góp ý đã đóng'}), 410
    
    # Save feedback immediately with default values
    is_filtered_init = len(content.strip()) < 5
    filter_reason_init = 'Nội dung quá ngắn' if is_filtered_init else ''
    
    feedback = Feedback(
        session_id=session.id,
        content=content,
        sentiment='neutral',
        sentiment_score=0.0,
        topics=json.dumps(['Góp ý chung'], ensure_ascii=False),
        is_filtered=is_filtered_init,
        filter_reason=filter_reason_init,
        ai_summary=''
    )
    db.session.add(feedback)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Góp ý đã được gửi thành công! Danh tính của bạn được bảo vệ hoàn toàn.'
    }), 201

# ----- Analytics -----

@app.route('/api/sessions/<identifier>/analytics', methods=['GET'])
def get_analytics(identifier):
    session = FeedbackSession.query.get(identifier)
    if not session:
        session = FeedbackSession.query.filter_by(uid=identifier.upper()).first()
    if not session:
        return jsonify({'error': 'Không tìm thấy phiên góp ý'}), 404
    
    feedbacks = Feedback.query.filter_by(session_id=session.id)\
        .order_by(Feedback.created_at.asc()).all()
    
    total = len(feedbacks)
    valid_feedbacks = [f for f in feedbacks if not f.is_filtered]
    filtered_count = total - len(valid_feedbacks)
    valid_total = len(valid_feedbacks)
    
    if valid_total == 0:
        return jsonify({
            'success': True,
            'session_title': session.title,
            'session_uid': session.uid,
            'session_category': session.category,
            'status': session.status,
            'total_feedbacks': total,
            'valid_feedbacks': 0,
            'filtered_feedbacks': filtered_count,
            'ai_analytics': None,
            'trends': [],
            'ai_insight': 'Chưa có góp ý hợp lệ nào. Hãy chia sẻ mã UID để thu thập góp ý.',
            'recent_activity': []
        }), 200
    
    # CACHE CHECK
    now = datetime.utcnow()
    use_cache = False
    
    if session.cached_analytics_json and session.last_analyzed_at:
        # Giữ cache nếu số lượng feedback không đổi
        if session.last_feedback_count == valid_total:
            use_cache = True
        # HOẶC Giữ cache nếu có feedback mới nhưng chưa qua 1 giờ (đỡ tốn phí)
        elif (now - session.last_analyzed_at).total_seconds() < 3600:
            use_cache = True
            
    if use_cache:
        try:
            llm_analytics = json.loads(session.cached_analytics_json)
            print("[Analytics] Serving from cache.")
        except:
            use_cache = False

    if not use_cache and valid_total > 0:
        # Gather feedback data for LLM
        feedbacks_data = []
        for f in valid_feedbacks:
            try:
                topics = json.loads(f.topics) if f.topics else []
            except:
                topics = []
            feedbacks_data.append({
                'sentiment': f.sentiment,
                'score': f.sentiment_score,
                'topics': topics,
                'summary': f.ai_summary or '',
                'content': f.content
            })
        
        # LLM-powered comprehensive analytics
        print("[Analytics] Generating fresh LLM analytics")
        llm_analytics = generate_llm_analytics(
            feedbacks_data, 
            session_title=session.title, 
            session_category=session.category
        )
        
        # Fall back if LLM unavailable
        if not llm_analytics:
            llm_analytics = fallback_analytics(feedbacks_data)
        else:
            # Save generated analytics to cache
            session.cached_analytics_json = json.dumps(llm_analytics, ensure_ascii=False)
            session.last_analyzed_at = now
            session.last_feedback_count = valid_total
            db.session.commit()
    
    # Trends by day (kept for time-series chart - simple counting is OK here)
    daily = {}
    for f in valid_feedbacks:
        day = f.created_at.strftime('%Y-%m-%d')
        if day not in daily:
            daily[day] = {'scores': [], 'count': 0}
        daily[day]['scores'].append(f.sentiment_score)
        daily[day]['count'] += 1
    
    trends = [
        {
            'date': day,
            'satisfaction': round((sum(d['scores']) / len(d['scores']) + 1) / 2 * 10, 1),
            'count': d['count']
        }
        for day, d in sorted(daily.items())
    ]
    
    return jsonify({
        'success': True,
        'session_title': session.title,
        'session_uid': session.uid,
        'session_category': session.category,
        'status': session.status,
        'total_feedbacks': total,
        'valid_feedbacks': valid_total,
        'filtered_feedbacks': filtered_count,
        'ai_analytics': llm_analytics,
        'trends': trends,
        'ai_insight': llm_analytics.get('insight_report', ''),
        'recent_activity': {
            'total_7days': valid_total
        }
    }), 200

# ----- Demo Data -----

@app.route('/api/demo/seed', methods=['POST'])
def seed_demo_data():
    """Create demo data for testing"""
    leader_id = request.headers.get('X-Leader-ID')
    if not leader_id:
        return jsonify({'error': 'Unauthorized'}), 401
    
    # Create a demo session
    uid = 'DEMO' + str(random.randint(1000, 9999))
    session = FeedbackSession(
        uid=uid,
        leader_id=leader_id,
        title='Khảo sát góp ý Q1/2026',
        description='Thu thập góp ý ẩn danh từ các thành viên về hoạt động, tổ chức, và đề xuất cải tiến.',
        category='pulse'
    )
    db.session.add(session)
    db.session.flush()
    
    # Demo feedbacks spanning multiple days
    demo_feedbacks = [
        ("Tôi rất hài lòng với bầu không khí hiện tại. Mọi người rất đoàn kết và hỗ trợ lẫn nhau. Người phụ trách lắng nghe và tôn trọng ý kiến mọi người.", -5),
        ("Cần cải thiện việc phân bổ thời gian. Hiện tại nhiều thành viên phải dành quá nhiều thời gian mà không được ghi nhận đầy đủ. Cần cân bằng hơn.", -4),
        ("Cảm ơn ban tổ chức đã tạo nhiều hoạt động gắn kết. Điều này giúp tăng tinh thần đội nhóm rất nhiều. Rất hài lòng!", -4),
        ("Tôi lo lắng về lộ trình phát triển ở đây. Không rõ ràng tiêu chí đánh giá. Cần có chương trình hỗ trợ cho thành viên mới.", -3),
        ("Quyền lợi và đãi ngộ chưa tương xứng với đóng góp. Nhiều thành viên đã rời đi vì lý do này. Đề xuất xem xét lại.", -3),
        ("Rất thích văn hóa ở đây, mọi người thân thiện và chuyên nghiệp. Đặc biệt ấn tượng với cách xử lý vấn đề, luôn bình tĩnh và công bằng.", -2),
        ("Cần cải thiện cơ sở vật chất. Phòng họp thường xuyên kẹt, thiết bị cũ. Không gian hoạt động hơi chật.", -2),
        ("Giao tiếp giữa các nhóm còn yếu. Thông tin thường bị thiếu hoặc truyền đạt không rõ ràng. Cần có kênh trao đổi chính thức hơn.", -1),
        ("Chương trình đào tạo rất bổ ích. Nhờ tổ chức mà tôi đã phát triển rất nhiều kỹ năng mới. Cảm ơn đã đầu tư vào con người.", -1),
        ("Áp lực quá lớn, deadline liên tục. Nhiều thành viên trong nhóm đang kiệt sức. Cần phân bổ công việc hợp lý hơn.", 0),
        ("Tôi đánh giá cao sự minh bạch trong quyết định gần đây. Thông tin đã được chia sẻ rõ ràng hơn trước. Tiếp tục phát huy!", 0),
        ("Cần có phương thức làm việc linh hoạt hơn. Nhiều tổ chức khác đã áp dụng rất hiệu quả.", 0),
    ]
    
    now = datetime.utcnow()
    for content, day_offset in demo_feedbacks:
        # Use LLM for analysis
        analysis = analyze_feedback_llm(content)
        
        if analysis:
            sentiment = analysis.get('sentiment', 'neutral')
            score = float(analysis.get('sentiment_score', 0.0))
            topics = analysis.get('topics', ['Góp ý chung'])
            is_filtered = analysis.get('is_spam', False)
            filter_reason = analysis.get('spam_reason', '')
            ai_summary = analysis.get('summary', '')
        else:
            sentiment = 'neutral'
            score = 0.0
            topics = ['Góp ý chung']
            is_filtered = False
            filter_reason = ''
            ai_summary = ''
        
        fb = Feedback(
            session_id=session.id,
            content=content,
            sentiment=sentiment,
            sentiment_score=score,
            topics=json.dumps(topics, ensure_ascii=False),
            is_filtered=is_filtered,
            filter_reason=filter_reason,
            ai_summary=ai_summary,
            created_at=now + timedelta(days=day_offset)
        )
        db.session.add(fb)
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'session_id': session.id,
        'uid': uid,
        'message': f'Demo data created with {len(demo_feedbacks)} feedbacks'
    }), 201

# ==================== Main ====================

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # Create test user if not exists
        if not Leader.query.filter_by(email='test@example.com').first():
            from werkzeug.security import generate_password_hash
            leader = Leader(
                email='test@example.com',
                name='Nguyễn Văn An',
                company='Nhóm của tôi',
                password_hash=generate_password_hash('password123'),
                avatar_color='#6C5CE7'
            )
            db.session.add(leader)
            db.session.commit()
            print("✅ Test user: test@example.com / password123")
    
    print("=" * 60)
    print("🚀 EchoMe - Lắng nghe tiếng nói thật")
    print("📍 Backend: http://localhost:5000")
    print("📍 Frontend: http://localhost:5000 (served by Flask)")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
