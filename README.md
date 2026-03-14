<div align="center">
  <img src="frontend/assets/logo.png" alt="EchoMe Logo" width="120" />
  <h1>EchoMe</h1>
  <p><strong>Lắng nghe tiếng nói thật - Nền tảng thu thập và phân tích góp ý ẩn danh bằng AI</strong></p>
</div>

---

## 🌟 Giới thiệu
**EchoMe** (trước đây là TalkToMe) là giải pháp giúp các cá nhân, tổ chức, trường học, hay doanh nghiệp thiết lập một hòm thư góp ý **hoàn toàn ẩn danh**. Khác với các hệ thống biểu mẫu (Google Forms, Typeform) thông thường, EchoMe kết hợp sức mạnh của AI thế hệ mới (Claude Haiku 4.5) để tự động đọc, lọc nội dung rác, đánh giá sắc thái tình cảm và tổng hợp báo cáo chuyên sâu chỉ trong vài giây.

![EchoMe Dashboard](https://via.placeholder.com/800x400.png?text=EchoMe+Analytics+Dashboard)

## ✨ Tính năng nổi bật
- 🔒 **Ẩn danh tuyệt đối**: Không cần đăng nhập để gửi góp ý, không lưu IP, không có bất kỳ cookie theo dõi nào.
- 🤖 **Phân tích siêu tốc bằng AI**: Trí tuệ nhân tạo đọc từng lời nhắn, hiểu từ lóng tiếng Việt, phân loại theo chủ đề và đưa ra Insight (Nhận xét) sát thực tế.
- 🛡️ **Bảo vệ người đọc (Anti-Toxic)**: AI tự động phân biệt và chặn các lời lẽ công kích cá nhân, thù hằn, spam mà không cần bộ lọc từ ngữ thủ công dài dòng.
- ⚡ **Khóa Cache thông minh**: Cơ chế Cache tại Backend giúp tiết kiệm tối đa lượng Token API của AI. Chỉ phân tích lại khi có đủ dữ liệu mới, đem đến tốc độ hiển thị Dashboard mượt mà.
- 🌓 **Giao diện hiện đại**: Hỗ trợ đầy đủ Dark Mode / Light Mode, thiết kế Responsive hiển thị hoàn hảo từ PC đến Mobile.

## 🛠 Công nghệ sử dụng
Dự án được cố tình xây dựng bằng hệ sinh thái tối giản nhất, giúp bất kì ai cũng có thể đọc hiểu source code hoặc đem lên triển khai ở các nền tảng miễn phí.
- **Frontend**: HTML5, Vanilla CSS3, Vanilla JavaScript (Không framework cồng kềnh, tải trang cực nhanh).
- **Backend**: Python 3, Flask framework.
- **Cơ sở dữ liệu**: SQLite (bản Local) hoặc PostgreSQL (bản Production/Supabase). Trình ánh xạ SQLAlchemy tích hợp cơ chế chống đứt gãy kết nối (pool_pre_ping).
- **Trí tuệ Nhân tạo**: Anthropic LLM (Claude-3-Haiku) thông qua chuẩn REST API.

## 🚀 Hướng dẫn Cài đặt & Chạy dưới Máy tính (Local)

**1. Copy mã nguồn**
```bash
git clone https://github.com/Monkez/EchoMe.git
cd EchoMe
```

**2. Khởi tạo Backend**
Cài đặt thư viện (yêu cầu Python 3.8+):
```bash
pip install -r backend/requirements.txt
```

Sao chép file biến môi trường và điền Key AI của bạn:
```bash
cp .env.example .env
# Mở file .env và điền ANTHROPIC_API_KEY của bạn vào
```

Chạy máy chủ:
```bash
cd backend
python server.py
# Server sẽ chạy tại http://localhost:5000
```
Tài khoản Test có sẵn: `test@example.com` / `password123`

**3. Khởi tạo Frontend**
Mở thêm một Terminal mới, khởi chạy môi trường giả lập Server cho thư mục `frontend/`
```bash
cd frontend
python -m http.server 3000
# Vào trình duyệt http://localhost:3000 để dùng web
```

## ☁️ Hướng dẫn Đưa ứng dụng lên mạng (Deploy Public)
Dự án đã được thiết lập sẵn các file để đưa lên Cloud nền tảng miễn phí với 0 đồng chi phí duy trì.

**1. Backend (Lên thẳng Render.com)**
- Tạo Web Service trên Render, trỏ link Github của bạn.
- Nhập *Start Command*: `gunicorn server:app`
- Nhập *Environment Variables*: `DATABASE_URL` (link SQL miễn phí của Render hoặc Supabase), `SECRET_KEY` (chuỗi dài ngẫu nhiên), `ANTHROPIC_API_KEY`.

**2. Frontend (Lên Vercel.com)**
- Đăng nhập Vercel, *Add New Project* và dẫn Github của bạn vào.
- Chọn thư mục gốc (Root Directory) là `frontend/`. Không cần lệnh Build nào cả.
- Trỏ lại file định tuyến API: Mở GitHub sửa file `frontend/vercel.json`, thay dòng `<your-render-app-url>` thành đường dẫn thư mục Backend Render của bạn để chặn lỗi CORS.
- Bấm Deploy vĩnh viễn.

## 📜 Giấy phép
- Dự án này mở theo giấy phép MIT. Thoải mái phát triển thêm các tính năng phù hợp với tổ chức của bạn.
