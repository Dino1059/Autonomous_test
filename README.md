# 🤖 AI Agent Tester Framework (Autonomous Browser Testing)

AI Agent Tester là một hệ thống kiểm thử trình duyệt tự động (Autonomous Browser Testing Framework) tích hợp AI Multi-Agent. Hệ thống tự động khám phá luồng người dùng, tự tạo kịch bản kiểm thử (Test Plan), thực thi tự động qua trình duyệt Playwright và thu thập bằng chứng kiểm thử toàn diện (API validation, Screenshots, Logs, Visual Diff).

Hệ thống được thiết kế với kiến trúc hiện đại, tập trung vào trải nghiệm điều khiển tập trung:
- 🎨 **React SPA Dashboard Workspace**: Giao diện điều khiển duy nhất tích hợp Prompt Generator, Live Playwright Viewport, Step Timeline & Evidence Inspector, White/Dark Mode toggle (Khuyên dùng).
- ⚡ **FastAPI Backend Service**: Hệ thống RESTful API điều phối các tác vụ kiểm thử, quản lý Multi-Agent Orchestrator và kết nối đa dạng các mô hình LLM (Gemini, OpenAI, OpenRouter, Anthropic, DeepSeek, Azure OpenAI, Hub1).

---

## 📂 Cấu trúc Thư mục Dự án (Project Structure)

```
UI-test/
├── frontend/             # Giao diện React SPA Dashboard
│   ├── index.html        # Single Page Application (React 18 CDN, Tailwind, Framer Motion)
│   └── TRACE_LOG.md      # Nhật ký thay đổi giao diện & frontend commit trace
├── app/                  # FastAPI Backend Server & Core Engine
│   ├── main.py           # FastAPI Entry Point (CORS, Health Check, Port binding)
│   ├── record_api.py     # Recording & Action Logger API
│   ├── agents/           # Multi-Agent Framework (Orchestrator, Planner, Browser Exec, Evaluator)
│   ├── controllers/      # API Controllers (tasks.py, actions.py, settings.py)
│   ├── db/               # SQLite / PostgreSQL Database Integration (autotester.db)
│   ├── routers/          # FastAPI Routes Definition (tasks_router, actions_router, settings_router)
│   ├── schemas/          # Input/Output Schemas & Validation Models
│   ├── serializers/      # Pydantic Serialization Models (RunTaskRequest, TaskConfig)
│   ├── templates/        # Default Test Templates / Actions
│   └── utils/            # Core Utility Functions
│       ├── browser_config.py   # Browser Auto-detect (Headless Docker / Headful Local)
│       ├── browser_actions.py  # Playwright & browser-use custom actions
│       ├── task_execution.py   # Background Task Loop Execution
│       ├── llm_utils.py        # LLM Factory & Provider Resolver
│       ├── sanitizing_llm.py   # LangChain LLM Wrapper (Fix tool role for Hub1/OpenAI compat)
│       ├── globals.py          # Shared Task States & Cancellation Flags
│       ├── mock_llm.py         # Mock LLM provider for isolated testing
│       └── prompts.py          # Prompt templates for plan & report generation
├── src/                  # Các gói mở rộng phụ trợ LLM Workers
│   ├── llms/             # Base LLM Workers & Custom Providers
│   └── tests/            # Test scripts & Integration test cases
├── demo_reports/         # Thư mục lưu trữ báo cáo kết quả kiểm thử (MD, Screenshots, Logs)
├── browser_profiles/     # Lưu trữ User Data Profile của Browser Playwright
├── autotester.db         # Cơ sở dữ liệu SQLite lưu trữ lịch sử kiểm thử & cấu hình
├── Dockerfile            # Cấu hình Build Docker Image
├── docker-compose.yml    # Cấu hình Docker Compose đa dịch vụ (FastAPI + Frontend)
├── .env.example          # Mẫu cấu hình biến môi trường
├── requirements.txt      # Danh sách các thư viện Python phụ thuộc
├── start.sh              # Script hỗ trợ khởi chạy nhanh hệ thống
├── DEV_CONTEXT.md        # Tài liệu Kiến trúc Hệ thống & Luồng xử lý chi tiết (System Architecture)
└── TRACE_LOG.md          # Nhật ký phiên bản hệ thống & Bảng vết Commit SHA
```

---

## 🚀 Hướng dẫn Khởi chạy Nhanh (Quick Start)

### Cách 1: Khởi chạy Cục bộ (Python / Conda)

```bash
# 1. Tạo & Kích hoạt môi trường Python (Khuyên dùng Python 3.11)
conda create -n agent_tester python=3.11.11 -y
conda activate agent_tester

# 2. Cài đặt thư viện phụ thuộc & Trình duyệt Playwright Chromium
pip install -r requirements.txt
playwright install chromium

# 3. Cấu hình file môi trường
cp .env.example .env
# (Mở file .env và điền API Key cho LLM provider bạn sử dụng)

# 4. Khởi chạy các dịch vụ:
# - Bước 4a: Khởi chạy Backend FastAPI (Port 8081)
python app/main.py --port 8081 --host 0.0.0.0

# - Bước 4b: Khởi chạy Frontend React SPA (Port 8088) - Mở tab terminal mới
python3 -m http.server 8088 --directory frontend
# Hoặc chạy script tự động: bash start.sh
```

---

### Cách 2: Khởi chạy bằng Docker & Docker Compose (Khuyên dùng cho DevOps/CI-CD)

```bash
# Xây dựng Docker Image và chạy Container ẩn ở chế độ background
docker-compose up -d --build

# Kiểm tra log hoạt động theo thời gian thực
docker-compose logs -f

# Dừng toàn bộ các dịch vụ container
docker-compose down
```

---

## 📍 Các Cổng Truy cập (Access Points)

| Dịch vụ | Địa chỉ Truy cập (URL) | Mô tả |
| :--- | :--- | :--- |
| 🎨 **React SPA Dashboard** | `http://localhost:8088` | Giao diện chính điều khiển AI Agent Tester (Đăng nhập Demo: `admin123` / `123`). |
| 📚 **FastAPI Swagger Docs** | `http://localhost:8081/docs` | Tài liệu API RESTful tương tác & thử nghiệm trực tiếp. |
| 🟢 **API Health Check** | `http://localhost:8081/health` | Kiểm tra trạng thái hệ thống Backend. |

---

## 🔑 Đăng nhập Demo trên React Dashboard SPA
- **Địa chỉ**: `http://localhost:8088`
- **Username / Email**: `admin123`
- **Password**: `123`
- *(Trên Modal Sign In có sẵn nút 1-click **"Fill Demo: admin123 / 123"** để điền nhanh credentials).*

---

## ⚙️ Cấu hình Biến Môi trường (Environment Variables)

Tạo file `.env` ở thư mục gốc của dự án với các thông số cấu hình:

```env
# AI Model API Keys
OPENROUTER_API_KEY=
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
AZURE_ENDPOINT=
AZURE_OPENAI_API_KEY=
GOOGLE_API_KEY=
DEEPSEEK_API_KEY=

# Hub1 API Key (Nếu sử dụng Hub1 LLM Model)
HUB1_API_KEY=
HUB1_API_BASE_URL=
HUB1_MODEL_NAME=

# Cấu hình Telemetry (Tùy chọn)
LAMINAR_API_KEY=
LAMINAR_BASE_URL=

# Thư mục lưu trữ báo cáo & cấu hình Server
REPORT_FOLDER=./demo_reports
PORT=8081
HOST=0.0.0.0
```

---

## 🛠️ Tính năng & Quy trình Kiểm thử (Core Features & Workflow)

1. **Prompt-to-Test Generator**: Nhập yêu cầu bằng ngôn ngữ tự nhiên (ví dụ: *"Kiểm tra tính năng đăng nhập và chuyển hướng sang Dashboard trên site target.com"*).
2. **Planner Agent**: Tự động phân tích và sinh ra **Structured Test Plan** đầy đủ các bước thực hiện.
3. **Interactive Step Editor**: Cho phép chỉnh sửa, thêm, xóa bước hoặc điều chỉnh tham số trước khi bấm thực thi.
4. **Live Playwright Viewport**: Quan sát trực quan màn hình trình duyệt Playwright thao tác tự động theo thời gian thực (Headful khi chạy local, Headless trong Docker).
5. **Agent Step Monitor**: Giám sát từng bước theo thời gian thực (Action, Observation, Next step, Execution Status).
6. **Timeline & Multi-Evidence Viewer**: Tự động thu thập bằng chứng kiểm thử gồm **API Validation**, **Screenshots**, **Agent Logs**, **Console Logs** và **Visual Diff**.
7. **White / Dark Mode Toggle**: Chuyển đổi linh hoạt giao diện sáng/tối (☀️/🌙).

---

## 🔧 Troubleshooting (Xử lý sự cố thường gặp)

1. **Trình duyệt không bật lên khi chạy Local**:
   - Kiểm tra `app/utils/browser_config.py`. Hệ thống tự động nhận diện chế độ: Local sẽ mở cửa sổ Playwright Chromium (`headless=False`), Docker sẽ chạy chế độ ẩn (`headless=True`).
2. **Lỗi xung đột Cổng (Port Conflicts)**:
   - Thay đổi tham số `--port` khi khởi chạy Backend (`python app/main.py --port 8082`) hoặc đổi port trong `docker-compose.yml`.
3. **Lỗi kết quả LLM hoặc API Key**:
   - Đảm bảo ít nhất một API Key hợp lệ đã được cung cấp trong file `.env` (Gemini `GOOGLE_API_KEY` hoặc OpenAI `OPENAI_API_KEY`).

---

## 📜 Tài liệu Tham khảo thêm (Documentation)
- **Tài liệu Kiến trúc & Flow Chi tiết**: [`DEV_CONTEXT.md`](DEV_CONTEXT.md)
- **Nhật ký Phiên bản & Commit Trace**: [`TRACE_LOG.md`](TRACE_LOG.md) & [`frontend/TRACE_LOG.md`](frontend/TRACE_LOG.md)