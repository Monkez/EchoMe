/* ============ EchoMe - App Logic ============ */
const API_URL = window.location.origin;
let state = {
  user: null,
  currentPage: 'landing',
  sessions: [],
  currentSession: null,
  analyticsData: null
};

// ==================== ROUTING ====================
function navigate(page, data) {
  document.querySelectorAll('.page').forEach(p => p.classList.add('hidden'));
  const el = document.getElementById(`page-${page}`);
  if (el) { el.classList.remove('hidden'); el.classList.add('fade-in'); }
  state.currentPage = page;
  
  // Update navbar
  const navbar = document.getElementById('navbar');
  const navUser = document.getElementById('nav-user-section');
  if (page === 'landing') { navbar.classList.add('hidden'); }
  else { navbar.classList.remove('hidden'); }
  
  if (state.user) {
    navUser.classList.remove('hidden');
    document.getElementById('nav-username').textContent = state.user.name;
    document.getElementById('nav-avatar').textContent = state.user.name.charAt(0).toUpperCase();
    document.getElementById('nav-avatar').style.background = state.user.avatar_color || '#6C5CE7';
  } else {
    navUser.classList.add('hidden');
  }
  
  // Page-specific init
  if (page === 'dashboard') loadDashboard();
  if (page === 'analytics' && data) loadAnalytics(data);
  
  window.scrollTo(0, 0);
}

// ==================== AUTH ====================
async function handleLogin(e) {
  e.preventDefault();
  const email = document.getElementById('login-email').value;
  const password = document.getElementById('login-password').value;
  const btn = e.target.querySelector('button[type=submit]');
  btn.disabled = true; btn.innerHTML = '<span class="spinner"></span> Đang đăng nhập...';
  
  try {
    const res = await fetch(`${API_URL}/api/auth/login`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    const data = await res.json();
    if (data.success) {
      state.user = data;
      localStorage.setItem('ttm_user', JSON.stringify(data));
      showToast('Đăng nhập thành công!', 'success');
      navigate('dashboard');
    } else {
      showToast(data.error || 'Đăng nhập thất bại', 'error');
    }
  } catch (err) { showToast('Không thể kết nối server', 'error'); }
  btn.disabled = false; btn.innerHTML = '🔐 Đăng nhập';
}

async function handleRegister(e) {
  e.preventDefault();
  const name = document.getElementById('reg-name').value;
  const email = document.getElementById('reg-email').value;
  const company = document.getElementById('reg-company').value;
  const password = document.getElementById('reg-password').value;
  const btn = e.target.querySelector('button[type=submit]');
  btn.disabled = true; btn.innerHTML = '<span class="spinner"></span> Đang tạo tài khoản...';
  
  try {
    const res = await fetch(`${API_URL}/api/auth/register`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, email, company, password })
    });
    const data = await res.json();
    if (data.success) {
      state.user = data;
      localStorage.setItem('ttm_user', JSON.stringify(data));
      showToast('Đăng ký thành công!', 'success');
      navigate('dashboard');
    } else {
      showToast(data.error || 'Đăng ký thất bại', 'error');
    }
  } catch (err) { showToast('Không thể kết nối server', 'error'); }
  btn.disabled = false; btn.innerHTML = '✨ Tạo tài khoản';
}

function logout() {
  state.user = null;
  localStorage.removeItem('ttm_user');
  navigate('landing');
  showToast('Đã đăng xuất', 'info');
}

// ==================== DASHBOARD ====================
async function loadDashboard() {
  if (!state.user) return navigate('login');
  
  const grid = document.getElementById('sessions-grid');
  grid.innerHTML = '<div style="text-align:center;padding:40px"><span class="spinner"></span></div>';
  
  try {
    const res = await fetch(`${API_URL}/api/sessions`, {
      headers: { 'X-Leader-ID': state.user.leader_id }
    });
    const data = await res.json();
    state.sessions = data.sessions || [];
    renderDashboard();
  } catch (err) {
    grid.innerHTML = '<div class="empty-state"><div class="empty-icon">⚠️</div><div class="empty-title">Không thể tải dữ liệu</div></div>';
  }
}

function renderDashboard() {
  const sessions = state.sessions;
  // Stats
  const totalSessions = sessions.length;
  const activeSessions = sessions.filter(s => s.status === 'active').length;
  const totalFeedbacks = sessions.reduce((a, s) => a + (s.total_feedbacks || 0), 0);
  const totalPositive = sessions.reduce((a, s) => a + (s.positive_count || 0), 0);
  
  document.getElementById('stat-sessions').textContent = totalSessions;
  document.getElementById('stat-active').textContent = activeSessions;
  document.getElementById('stat-feedbacks').textContent = totalFeedbacks;
  document.getElementById('stat-positive').textContent = totalFeedbacks > 0 ? Math.round(totalPositive / totalFeedbacks * 100) + '%' : '—';
  
  // Sessions grid
  const grid = document.getElementById('sessions-grid');
  if (sessions.length === 0) {
    grid.innerHTML = `
      <div class="empty-state" style="grid-column:1/-1">
        <div class="empty-icon">📋</div>
        <div class="empty-title">Chưa có phiên góp ý nào</div>
        <div class="empty-desc">Tạo phiên góp ý đầu tiên để bắt đầu thu thập ý kiến ẩn danh từ các thành viên.</div>
        <button class="btn btn-primary" onclick="openCreateModal()">➕ Tạo phiên góp ý</button>
      </div>`;
    return;
  }
  
  grid.innerHTML = sessions.map((s, i) => `
    <div class="card session-card slide-up" style="animation-delay:${i * 0.05}s" onclick="navigate('analytics','${s.id}')">
      <div class="card-header">
        <div>
          <div class="card-title">${escHtml(s.title)}</div>
          <div class="session-uid">${s.uid}</div>
        </div>
        <span class="badge ${s.status === 'active' ? 'badge-success' : 'badge-warning'}">${s.status === 'active' ? '🟢 Đang mở' : '🔒 Đã đóng'}</span>
      </div>
      ${s.description ? `<p style="font-size:13px;color:var(--text-muted);margin-bottom:12px">${escHtml(s.description).substring(0, 100)}${s.description.length > 100 ? '...' : ''}</p>` : ''}
      <div class="session-meta">
        <span>💬 ${s.total_feedbacks || 0} góp ý</span>
        <span>👍 ${s.positive_count || 0}</span>
        <span>👎 ${s.negative_count || 0}</span>
        <span>📅 ${formatDate(s.created_at)}</span>
      </div>
    </div>
  `).join('');
}

// ==================== CREATE SESSION ====================
function openCreateModal() {
  document.getElementById('create-modal').classList.remove('hidden');
}
function closeCreateModal() {
  document.getElementById('create-modal').classList.add('hidden');
}

async function handleCreateSession(e) {
  e.preventDefault();
  const title = document.getElementById('cs-title').value;
  const desc = document.getElementById('cs-desc').value;
  const category = document.getElementById('cs-category').value;
  
  try {
    const res = await fetch(`${API_URL}/api/sessions`, {
      method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Leader-ID': state.user.leader_id },
      body: JSON.stringify({ title, description: desc, category })
    });
    const data = await res.json();
    if (data.success) {
      showToast(`Đã tạo phiên góp ý! Mã UID: ${data.uid}`, 'success');
      closeCreateModal();
      e.target.reset();
      loadDashboard();
    } else {
      showToast(data.error || 'Tạo thất bại', 'error');
    }
  } catch (err) { showToast('Lỗi kết nối', 'error'); }
}

async function seedDemo() {
  try {
    const res = await fetch(`${API_URL}/api/demo/seed`, {
      method: 'POST', headers: { 'X-Leader-ID': state.user.leader_id }
    });
    const data = await res.json();
    if (data.success) {
      showToast(`Demo data created! UID: ${data.uid}`, 'success');
      loadDashboard();
    }
  } catch (err) { showToast('Error creating demo', 'error'); }
}

// ==================== ANALYTICS ====================
async function loadAnalytics(sessionId) {
  const content = document.getElementById('analytics-content');
  content.innerHTML = '<div style="text-align:center;padding:60px"><span class="spinner"></span><p style="margin-top:12px;color:var(--text-secondary)">Đang phân tích dữ liệu...</p></div>';
  
  try {
    const res = await fetch(`${API_URL}/api/sessions/${sessionId}/analytics`, {
      headers: { 'X-Leader-ID': state.user.leader_id }
    });
    const data = await res.json();
    if (data.success) {
      state.analyticsData = data;
      state.currentSession = sessionId;
      renderAnalytics(data);
    } else {
      content.innerHTML = '<div class="empty-state"><div class="empty-icon">❌</div><div class="empty-title">Không tìm thấy dữ liệu</div></div>';
    }
  } catch (err) {
    content.innerHTML = '<div class="empty-state"><div class="empty-icon">⚠️</div><div class="empty-title">Lỗi kết nối</div></div>';
  }
}

function renderAnalytics(data) {
  const d = data;
  const a = d.ai_analytics || {};
  const metrics = a.key_metrics || [];
  const highlights = a.highlights || [];
  const themes = a.top_themes || [];
  
  const colorMap = { success: 'var(--success)', warning: 'var(--warning)', danger: 'var(--danger)', info: 'var(--accent-light)' };
  
  const metricsHtml = metrics.map(m => {
    const color = colorMap[m.color] || 'var(--text-primary)';
    return `<div class="card stat-card">
      <div class="stat-label">${escHtml(m.label)}</div>
      <div class="stat-value" style="color:${color}">${escHtml(m.value)}</div>
    </div>`;
  }).join('');
  
  const highlightsHtml = highlights.map(h => {
    const barClass = h.type === 'positive' ? 'positive' : h.type === 'negative' ? 'negative' : 'neutral';
    return `<div class="sentiment-row">
      <div class="sentiment-label">${escHtml(h.label)}</div>
      <div class="sentiment-bar-bg"><div class="sentiment-bar ${barClass}" style="width:${Math.max(h.percentage, 2)}%">${h.percentage}%</div></div>
    </div>`;
  }).join('');
  
  const themesHtml = themes.length > 0 
    ? themes.map(t => `<div class="topic-chip">${escHtml(t.theme)} <span class="count">${t.count}</span></div>`).join('')
    : '<p style="color:var(--text-muted);font-size:13px">Chưa đủ dữ liệu</p>';
  
  document.getElementById('analytics-content').innerHTML = `
    <div class="analytics-header">
      <h2 style="font-size:24px;font-weight:800">${escHtml(d.session_title)}</h2>
      <div style="display:flex;gap:8px;align-items:center;margin-top:8px;flex-wrap:wrap">
        <span class="badge badge-accent">UID: ${d.session_uid}</span>
        <span class="badge ${d.status === 'active' ? 'badge-success' : 'badge-warning'}">${d.status === 'active' ? '🟢 Đang mở' : '🔒 Đã đóng'}</span>
        <span class="badge badge-info">💬 ${d.total_feedbacks} góp ý</span>
        ${d.filtered_feedbacks > 0 ? `<span class="badge badge-danger">🚫 ${d.filtered_feedbacks} bị lọc</span>` : ''}
      </div>
    </div>

    <div class="stats-grid">${metricsHtml}</div>

    <div class="ai-insight" style="margin-bottom:16px">
      <div class="ai-insight-header">🤖 Phân tích AI</div>
      <div class="ai-insight-body">${renderMarkdown(d.ai_insight || a.insight_report || '')}</div>
    </div>

    <div class="analytics-grid" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px;margin-bottom:16px">
      <div class="card chart-card">
        <div class="chart-title">📊 Phân bố đánh giá</div>
        <div class="sentiment-bars">${highlightsHtml}</div>
      </div>
      <div class="card chart-card">
        <div class="chart-title">🔍 Chủ đề nổi bật</div>
        <div class="topic-chips">${themesHtml}</div>
      </div>
    </div>

    ${(d.trends && d.trends.length > 0) ? `
    <div class="card chart-card">
      <div class="chart-title">📈 Xu hướng theo thời gian</div>
      <div class="trend-bars">
        ${d.trends.map(t => {
          const h = Math.max(t.satisfaction * 10, 5);
          const color = t.satisfaction >= 7 ? 'var(--success)' : t.satisfaction >= 4 ? 'var(--warning)' : 'var(--danger)';
          return `<div class="trend-bar-wrap">
            <div style="font-size:10px;font-weight:700;color:var(--text-secondary)">${t.satisfaction}</div>
            <div class="trend-bar" style="height:${h}%;background:${color}"></div>
            <div class="trend-date">${t.date.substring(5)}</div>
          </div>`;
        }).join('')}
      </div>
    </div>` : ''}

    <div style="display:flex;gap:8px;margin-top:16px;flex-wrap:wrap">
      <button class="btn btn-secondary" onclick="copyUID('${d.session_uid}')">📋 Sao chép mã UID</button>
      ${d.status === 'active' ?
        `<button class="btn btn-danger btn-sm" onclick="toggleSession('${state.currentSession}','close')">🔒 Đóng phiên</button>` :
        `<button class="btn btn-success btn-sm" onclick="toggleSession('${state.currentSession}','reopen')">🔓 Mở lại</button>`
      }
    </div>
  `;
}

async function toggleSession(id, action) {
  try {
    await fetch(`${API_URL}/api/sessions/${id}/${action}`, {
      method: 'POST', headers: { 'X-Leader-ID': state.user.leader_id }
    });
    showToast(action === 'close' ? 'Đã đóng phiên' : 'Đã mở lại phiên', 'success');
    loadAnalytics(id);
  } catch (err) { showToast('Lỗi', 'error'); }
}

// ==================== FEEDBACK SUBMISSION ====================
async function validateFeedbackCode() {
  const uid = document.getElementById('fb-uid').value.trim().toUpperCase();
  const infoEl = document.getElementById('fb-session-info');
  const formEl = document.getElementById('fb-form-section');
  
  if (uid.length < 4) { infoEl.innerHTML = ''; formEl.classList.add('hidden'); return; }
  
  try {
    const res = await fetch(`${API_URL}/api/feedback/validate`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ uid })
    });
    const data = await res.json();
    if (data.valid) {
      infoEl.innerHTML = `<div class="badge badge-success" style="padding:8px 16px;font-size:13px">✅ ${escHtml(data.title)}</div>`;
      formEl.classList.remove('hidden');
    } else {
      infoEl.innerHTML = `<div class="badge badge-danger" style="padding:8px 16px;font-size:13px">❌ ${data.reason}</div>`;
      formEl.classList.add('hidden');
    }
  } catch (err) {
    infoEl.innerHTML = '<div class="badge badge-danger" style="padding:8px 16px">⚠️ Lỗi kết nối</div>';
  }
}

async function handleSubmitFeedback(e) {
  e.preventDefault();
  const uid = document.getElementById('fb-uid').value.trim();
  const content = document.getElementById('fb-content').value.trim();
  const btn = e.target.querySelector('button[type=submit]');
  btn.disabled = true; btn.innerHTML = '<span class="spinner"></span> Đang gửi...';
  
  try {
    const res = await fetch(`${API_URL}/api/feedback/submit`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ uid, content })
    });
    const data = await res.json();
    if (data.success) {
      document.getElementById('fb-form-wrapper').innerHTML = `
        <div class="feedback-success slide-up">
          <div class="icon">🎉</div>
          <h3>Gửi góp ý thành công!</h3>
          <p>Cảm ơn bạn đã chia sẻ. Danh tính của bạn được bảo vệ hoàn toàn. Không ai có thể biết bạn là ai.</p>
          <button class="btn btn-primary" style="margin-top:20px" onclick="resetFeedbackForm()">📝 Gửi góp ý khác</button>
        </div>`;
    } else {
      showToast(data.error || 'Gửi thất bại', 'error');
    }
  } catch (err) { showToast('Lỗi kết nối', 'error'); }
  btn.disabled = false; btn.innerHTML = '📨 Gửi góp ý ẩn danh';
}

function resetFeedbackForm() {
  document.getElementById('fb-form-wrapper').innerHTML = buildFeedbackFormHTML();
  document.getElementById('fb-form-section').classList.add('hidden');
}

function buildFeedbackFormHTML() {
  return `
    <div class="form-group">
      <label class="form-label">Mã góp ý (UID)</label>
      <input class="form-input" id="fb-uid" type="text" placeholder="Nhập mã UID bạn nhận được..." oninput="validateFeedbackCode()" maxlength="12" style="text-transform:uppercase;letter-spacing:3px;font-weight:700;font-size:18px;text-align:center">
    </div>
    <div id="fb-session-info" style="margin-bottom:16px"></div>
    <div id="fb-form-section" class="hidden">
      <form onsubmit="handleSubmitFeedback(event)">
        <div class="form-group">
          <label class="form-label">Nội dung góp ý</label>
          <textarea class="form-textarea" id="fb-content" placeholder="Hãy chia sẻ thẳng thắn suy nghĩ của bạn...\n\nGóp ý của bạn hoàn toàn ẩn danh. Không ai biết bạn là ai." required minlength="10" rows="6"></textarea>
        </div>
        <div style="background:var(--bg-glass);padding:12px;border-radius:var(--radius-sm);margin-bottom:20px;font-size:12px;color:var(--text-muted);display:flex;align-items:center;gap:8px">
          🔒 Góp ý hoàn toàn ẩn danh • Không lưu IP • Không theo dõi • Người tạo không đọc trực tiếp
        </div>
        <button type="submit" class="btn btn-primary btn-block btn-lg">📨 Gửi góp ý ẩn danh</button>
      </form>
    </div>`;
}

// ==================== HELPERS ====================
function escHtml(str) {
  if (!str) return '';
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

function renderMarkdown(str) {
  if (!str) return '';
  let html = escHtml(str);
  // Bold: **text** - use softer contrast
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong class="md-bold">$1</strong>');
  // Headings: # ## ###
  html = html.replace(/^#{1,3}\s+(.*)$/gm, '<div class="md-heading">$1</div>');
  // Horizontal rules: ---
  html = html.replace(/^-{3,}$/gm, '<hr class="md-hr">');
  // Numbered lists: 1. 2. 3.
  html = html.replace(/^(\d+)\.\s+(.*)$/gm, '<div class="md-list-item"><span class="md-list-num">$1.</span> $2</div>');
  // Bullet points: • or -
  html = html.replace(/^[•\-]\s+(.*)$/gm, '<div class="md-list-item"><span class="md-list-num">•</span> $1</div>');
  // Preserve newlines
  html = html.replace(/\n/g, '<br>');
  // Clean up double <br> from block elements
  html = html.replace(/<br>\s*(<div|<hr)/g, '$1');
  html = html.replace(/(<\/div>)\s*<br>/g, '$1');
  return html;
}

function formatDate(iso) {
  if (!iso) return '';
  const d = new Date(iso);
  return d.toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit', year: 'numeric' });
}

function copyUID(uid) {
  navigator.clipboard.writeText(uid).then(() => showToast(`Đã sao chép mã: ${uid}`, 'success'));
}

function showToast(msg, type = 'info') {
  const container = document.getElementById('toast-container');
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = msg;
  container.appendChild(toast);
  setTimeout(() => { toast.style.opacity = '0'; setTimeout(() => toast.remove(), 300); }, 3000);
}

// ==================== INIT ====================
document.addEventListener('DOMContentLoaded', () => {
  // Check saved session
  const saved = localStorage.getItem('ttm_user');
  if (saved) {
    try {
      state.user = JSON.parse(saved);
    } catch (e) { localStorage.removeItem('ttm_user'); }
  }
  
  // Initialize theme
  const savedTheme = localStorage.getItem('ttm_theme') || 'dark';
  document.documentElement.setAttribute('data-theme', savedTheme);
  const themeBtn = document.getElementById('theme-btn');
  if (themeBtn) themeBtn.textContent = savedTheme === 'dark' ? '🌙' : '☀️';
  
  // Check URL for feedback code
  const params = new URLSearchParams(window.location.search);
  const feedbackCode = params.get('code') || params.get('uid');
  
  if (feedbackCode) {
    navigate('feedback');
    setTimeout(() => {
      const input = document.getElementById('fb-uid');
      if (input) { input.value = feedbackCode.toUpperCase(); validateFeedbackCode(); }
    }, 100);
  } else if (state.user) {
    navigate('dashboard');
  } else {
    navigate('landing');
  }
});

function toggleTheme() {
  const current = document.documentElement.getAttribute('data-theme') || 'dark';
  const next = current === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem('ttm_theme', next);
  const btn = document.getElementById('theme-btn');
  if (btn) btn.textContent = next === 'dark' ? '🌙' : '☀️';
}
