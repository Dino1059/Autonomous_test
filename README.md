# 🤖 AI Agent Tester Framework

AI Agent Tester là một hệ thống kiểm thử trình duyệt tự động (Autonomous Browser Testing Framework) tích hợp AI Agent. Hệ thống tự động khám phá luồng người dùng, tự tạo kịch bản kiểm thử (Test Plan), thực thi tự động qua trình duyệt Playwright và tự động thu thập bằng chứng kiểm thử (API validation, Screenshots, Logs, Visual Diff).

Hệ thống thống nhất sử dụng **1 Giao diện Duy nhất (React SPA Dashboard)** kết nối trực tiếp với **FastAPI Backend Server**:
- 🎨 **React SPA Dashboard Workspace**: Giao diện chính tích hợp Prompt-to-Test Generator, Live Playwright Viewport, Real-time Step Monitor, Evidence Inspector, và White/Dark Mode toggle.
- ⚡ **FastAPI Backend Service**: Hệ thống RESTful API điều phối các tác vụ kiểm thử, thực thi trình duyệt Playwright và lưu trữ dữ liệu vào CSDL SQLite (`autotester.db`).

---

## 🚀 Khởi chạy Nhanh (Quick Start)

### Cách 1: Khởi chạy Cục bộ (Python / Conda)

```bash
# 1. Khởi tạo & Kích hoạt môi trường Conda
conda create -n agent_tester python=3.11.11 -y
conda activate agent_tester

# 2. Cài đặt các thư viện phụ thuộc & Trình duyệt Playwright
pip install -r requirements.txt
playwright install

# 3. Tạo file cấu hình môi trường từ mẫu
cp .env.example .env
# (Chỉnh sửa file .env để điền các API Key của bạn)

# 4. Khởi chạy Dịch vụ
# - Chạy Backend FastAPI Server (Port 8081)
python app/main.py --port 8081 --host 0.0.0.0

# - Chạy React Dashboard SPA (Port 8088) - Mở tab terminal mới
python3 -m http.server 8088
```

---

### Cách 2: Khởi chạy bằng Docker & Docker Compose

#### Yêu cầu tiền đề:
- Docker & Docker Compose đã được cài đặt.
- File `.env` đã được cấu hình các API Key cần thiết.

#### Sử dụng Docker Compose trực tiếp:
```bash
# Xây dựng Docker Image và khởi chạy các container ở chế độ background
docker-compose up -d --build

# Xem log hoạt động theo thời gian thực
docker-compose logs -f

# Dừng các dịch vụ
docker-compose down
```

---

## 📍 Các Cổng Truy cập (Access Points)

| Dịch vụ | Địa chỉ Truy cập (URL) | Mô tả |
| :--- | :--- | :--- |
| 🎨 **React SPA Dashboard** | `http://localhost:8088` *(hoặc mở `frontend/index.html`)* | Giao diện điều khiển duy nhất của AI Agent Tester (Đăng nhập Demo: `admin123` / `123`). |
| 📚 **FastAPI Swagger Docs** | `http://localhost:8081/docs` | Tài liệu RESTful API công khai để kết nối trực tiếp. |
| 🟢 **API Health Check** | `http://localhost:8081/health` | Kiểm tra trạng thái sức khỏe của Backend Server. |

---

## 🔑 Đăng nhập Demo trên React Dashboard SPA
- **Địa chỉ**: `http://localhost:8088`
- **Username / Email**: `admin123`
- **Password**: `123`
- *(Trên Modal Sign In có sẵn nút 1-click **"Fill Demo: admin123 / 123"** để điền nhanh).*

---

## ⚙️ Cấu hình Biến Môi trường (Environment Variables)

Tạo file `.env` ở thư mục gốc của dự án với các thông số mẫu:

```env
# AI Model API Keys
OPENROUTER_API_KEY=
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
AZURE_ENDPOINT=
AZURE_OPENAI_API_KEY=
GOOGLE_API_KEY=
DEEPSEEK_API_KEY=

# Laminar Telemetry API Configuration (Optional)
LAMINAR_API_KEY=
LAMINAR_BASE_URL=
LAMINAR_HTTP_PORT=
LAMINAR_GRPC_PORT=

# Thư mục lưu trữ báo cáo kiểm thử & CSDL
REPORT_FOLDER=./demo_reports

# Cấu hình Server Backend
PORT=8081
HOST=0.0.0.0
```

---

## 📂 Cấu trúc Thư mục Dự án (Project Structure)

```
AI-Agent-Tester/
├── frontend/             # Giao diện React SPA Dashboard duy nhất (index.html, TRACE_LOG.md)
├── app/                  # FastAPI Backend Server & Database Core
│   ├── controllers/      # REST API Controllers (tasks.py, actions.py, settings.py)
│   ├── db/               # PostgreSQL & SQLite Persistence (`database.py`, `autotester.db`)
│   ├── utils/            # Execution & Browser Actions (task_execution.py, browser_actions.py)
│   └── main.py           # FastAPI Application Entry point
├── demo_reports/         # Thư mục chứa báo cáo kết quả test, ảnh screenshot & JSON traces
├── docker-compose.yml    # Cấu hình Docker Compose dịch vụ
├── Dockerfile            # Docker Image build specification
├── Makefile              # Lệnh tắt vận hành container
└── TRACE_LOG.md          # Nhật ký thay đổi hệ thống & bảng mã commit SHA
```

---

## 🛠️ Tính năng & Quy trình Kiểm thử (Core Features & Workflow)

1. **Prompt-to-Test Generator**: Nhập prompt ngôn ngữ tự nhiên (ví dụ: *"Kiểm tra tính năng quên mật khẩu trên trang test.com"*).
2. **Planner Agent**: Tự động sinh ra **Structured Test Plan** đầy đủ các bước qua `POST /tasks/generate-plan`.
3. **Interactive Step Editor**: Sửa, xóa, thêm bước hoặc thay đổi thứ tự kịch bản trước khi thực thi.
4. **Live Playwright Viewport**: Quan sát trực tiếp màn hình trình duyệt Playwright thao tác tự động (`1920x1080`, 60 FPS).
5. **Agent Step Monitor**: Giám sát từng bước theo thời gian thực (Step X/Y, Action, Observation, Next step).
6. **Timeline & Multi-Evidence Viewer**: Thu thập bằng chứng tự động gồm **API Validation** (Status Code, Latency, Response Payload), **Screenshots**, **Agent Logs**, **Console Logs** và **Visual Diff**.
7. **White / Dark Mode Toggle**: Chuyển đổi linh hoạt giữa giao diện Dark Mode và Light Mode (☀️/🌙).
8. **SQLite Database Sync**: Tự động lưu vết tất cả đợt test vào `autotester.db` và hiển thị trên bảng **Recent Test Runs**.

---

## 🔧 Troubleshooting (Xử lý sự cố thường gặp)

1. **Lỗi xung đột Cổng (Port conflicts)**:
   - Chỉnh sửa cổng trong file `.env`, `docker-compose.yml` hoặc tham số `--port` nếu cổng `8081` hoặc `8088` đã bị chiếm dụng.
2. **Lỗi thiếu Trình duyệt Playwright**:
   - Chạy lệnh `playwright install` để cài đặt binary của Chromium.

---

## 📜 Giấy phép & Đóng góp (License & Support)
- **Trace Log / Nhật ký phiên bản**: Tham khảo chi tiết tại [`frontend/TRACE_LOG.md`](frontend/TRACE_LOG.md).