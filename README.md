# 🤖 AI Agent Tester Framework

AI Agent Tester là một hệ thống kiểm thử trình duyệt tự động (Autonomous Browser Testing Framework) tích hợp AI Agent. Hệ thống tự động khám phá luồng người dùng, tự tạo kịch bản kiểm thử (Test Plan), thực thi tự động qua trình duyệt Playwright và tự động thu thập bằng chứng kiểm thử (API validation, Screenshots, Logs, Visual Diff).

Hệ thống hỗ trợ đa giao diện linh hoạt:
- 🎨 **React SPA Dashboard Workspace**: Giao diện hiện đại tích hợp Prompt Generator, Live Playwright Viewport, Step Timeline & Evidence Inspector, White/Dark Mode toggle (Khuyên dùng).
- 🎛️ **Gradio Web Interface**: Giao diện quản lý các mẫu test YAML (Templates).
- ⚡ **FastAPI Backend Service**: Hệ thống RESTful API điều phối các tác vụ kiểm thử và kết nối với các mô hình LLM.

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

# 4. Khởi chạy các Dịch vụ
# - Chạy Backend FastAPI Server (Port 8081)
python app/main.py --port 8081 --host 0.0.0.0

# - Chạy Gradio WebUI (Port 7860) - Mở tab terminal mới
python gradio_ui/webui.py

# - Chạy React Dashboard SPA (Port 8088) - Mở tab terminal mới
python3 -m http.server 8088
```

---

### Cách 2: Khởi chạy bằng Docker & Docker Compose (Khuyên dùng cho Production/DevOps)

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

#### Sử dụng Makefile (Nếu có cài Make):
```bash
make quick-start   # Xây dựng và khởi chạy ứng dụng
make dev-start     # Khởi chạy ở chế độ Development (hỗ trợ Hot Reload)
make stop          # Dừng toàn bộ các container
make logs          # Xem log hệ thống
make clean         # Dọn dẹp các container và image cũ
```

---

## 📍 Các Cổng Truy cập (Access Points)

| Dịch vụ | Địa chỉ Truy cập (URL) | Mô tả |
| :--- | :--- | :--- |
| 🎨 **React SPA Dashboard** | `http://localhost:8088` *(hoặc mở `frontend/index.html`)* | Giao diện điều khiển AI Agent Tester chính (Đăng nhập Demo: `admin123` / `123`). |
| 🎛️ **Gradio WebUI** | `http://localhost:7860` | Giao diện quản lý & chạy kịch bản test từ file mẫu YAML. |
| 📚 **FastAPI Swagger Docs** | `http://localhost:8081/docs` | Tài liệu API RESTful tương tác trực tiếp. |
| 🟢 **API Health Check** | `http://localhost:8081/health` | Kiểm tra trạng thái hoạt động của Backend Server. |

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

# Thư mục lưu trữ báo cáo kiểm thử
REPORT_FOLDER=./demo_reports

# Cấu hình Server Backend
PORT=8081
HOST=0.0.0.0
```

---

## 📂 Cấu trúc Thư mục Dự án (Project Structure)

```
AI-Agent-Tester/
├── frontend/             # Giao diện React SPA Dashboard (index.html, TRACE_LOG.md)
├── app/                  # FastAPI Backend Server (Controllers, Routers, Task Execution, Playwright integration)
│   ├── controllers/      # API Controllers (tasks.py, actions.py, settings.py)
│   ├── utils/            # Utility functions (task_execution.py, browser_actions.py, llm_utils.py)
│   └── main.py           # FastAPI Entry point
├── gradio_ui/            # Gradio Web Interface & YAML templates
│   ├── webui.py          # Gradio app launcher
│   └── templates_agent/  # Mẫu kịch bản YAML
├── demo_reports/         # Thư mục chứa báo cáo kết quả test, ảnh screenshot & logs
├── src/                  # Các gói phụ trợ LLM Workers
├── docker-compose.yml    # Cấu hình Docker Compose dịch vụ
├── Dockerfile            # Docker Image build specification
├── Makefile              # Các câu lệnh tắt vận hành Docker
└── TRACE_LOG.md          # Nhật ký thay đổi hệ thống & bảng mã commit SHA
```

---

## 🛠️ Tính năng & Quy trình Kiểm thử (Core Features & Workflow)

1. **Prompt-to-Test Generator**: Nhập prompt ngôn ngữ tự nhiên (ví dụ: *"Kiểm tra tính năng quên mật khẩu trên trang test.com"*).
2. **Planner Agent**: Tự động sinh ra **Structured Test Plan** đầy đủ các bước.
3. **Interactive Step Editor**: Cho phép sửa, xóa, thêm bước hoặc thay đổi thứ tự kịch bản trước khi chạy.
4. **Live Playwright Viewport**: Quan sát trực tiếp màn hình trình duyệt Playwright thao tác tự động (`1920x1080`, 60 FPS).
5. **Agent Step Monitor**: Giám sát từng bước theo thời gian thực (Step X/Y, Action, Observation, Next step).
6. **Timeline & Multi-Evidence Viewer**: Thu thập bằng chứng tự động gồm **API Validation** (Status Code, Latency, Response Payload), **Screenshots**, **Agent Logs**, **Console Logs** và **Visual Diff**.
7. **White / Dark Mode Toggle**: Chuyển đổi linh hoạt giữa giao diện Dark Mode và Light Mode (☀️/🌙).

---

## 🔧 Troubleshooting (Xử lý sự cố thường gặp)

1. **Lỗi xung đột Cổng (Port conflicts)**:
   - Nếu cổng `8081`, `7860` hoặc `8088` đã bị chiếm dụng, hãy chỉnh sửa cổng trong file `.env`, `docker-compose.yml` hoặc đổi tham số `--port` khi chạy lệnh python.
2. **Lỗi thiếu Trình duyệt Playwright**:
   - Chạy lệnh `playwright install` hoặc `python -m playwright install` để tải về binary của Chromium/Firefox/WebKit.
3. **Cơ chế Secret Protection trên GitHub**:
   - Không được commit API key thực vào file `.env.example` hoặc mã nguồn công khai.

---

## 📜 Giấy phép & Đóng góp (License & Support)
- **Trace Log / Nhật ký phiên bản**: Tham khảo chi tiết tại [`frontend/TRACE_LOG.md`](frontend/TRACE_LOG.md).