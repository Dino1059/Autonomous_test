# NHẬT KÝ HỆ THỐNG & TẢI TRẠNG THAY ĐỔI (TRACE LOG)
## AI Agent Tester — Bản thiết kế v1

**Repository**: [https://github.com/Dino1059/Autonomous_test.git](https://github.com/Dino1059/Autonomous_test.git)  
**Phiên bản (Version)**: v1.0.0  
**Ngày khởi tạo**: 08/08/2026  
**Môi trường (Tech Stack)**: HTML5, React 18 (UMD CDN), Babel Standalone 7.29, Framer Motion 11.11, Tailwind CSS.

---

### 📊 BẢNG TỔNG HỢP COMMIT & LỆNH REVERT (COMMIT TRACE TABLE)

| STT | Comment (Commit Message) | SHA | Nội dung tóm tắt thay đổi | Lệnh Revert về bản đó |
| :-: | :--- | :-: | :--- | :--- |
| **5** | `Remove demo_reports` | `b6fc36e` | Remove demo_reports | `git checkout b6fc36e`<br/>*(hoặc `git reset --hard b6fc36e`)* |
| **4** | `gộp tài liệu README.md và README-Docker.md` | `059ee6b` | gộp tài liệu README.md và README-Docker.md | `git checkout 059ee6b`<br/>*(hoặc `git reset --hard 059ee6b`)* |
| **3** | `bản thiết kế v1 của dự án` | `f1c79f2` | bản thiết kế v1 của dự án | `git checkout f1c79f2`<br/>*(hoặc `git reset --hard f1c79f2`)* |
| **1** | `bản thiết kế v1 của dự án` | `c343fc2` | Khởi tạo giao diện Landing Page Space Travel, bổ sung Auth Modal trượt 2 ô, đăng nhập `admin123/123`, chế độ White Mode (☀️/🌙) và toàn bộ AI Agent Tester Dashboard Workspace. | `git checkout c343fc2` <br/>*(hoặc `git reset --hard c343fc2`)* |
| **2** | `Initial commit` | `807f60a` | Khởi tạo dự án gốc backend & cấu trúc ban đầu. | `git checkout 807f60a` <br/>*(hoặc `git reset --hard 807f60a`)* |

---

### 📜 LỊCH SỬ THAY ĐỔI CHI TIẾT THEO PHIÊN BẢN (DETAILED CHANGELOG)

#### 📌 [v1.7.0] - Thêm Nút bấm Chuyển đổi Giao diện White Mode / Light Mode
- Thêm icon Mặt trời (☀️) / Mặt trăng (🌙) trên thanh Navigation.
- Chuyển đổi linh hoạt toàn bộ hệ thống sang **White / Light Mode** với bộ theme kính mờ nền sáng (`bg-slate-50`, `liquid-glass` viền mờ tối, chữ `text-slate-900` sắc nét).

#### 📌 [v1.6.0] - Xây dựng Toàn bộ AI Agent Tester Dashboard Workspace
Cấu trúc và triển khai 8 khu vực chức năng cốt lõi của Dashboard:
1. **Top Navigation Bar**: Thanh menu điều hướng module (`Dashboard`, `New Test`, `Test Runs`, `Test Cases`, `Comparisons`, `Reports`, `Environments`, `Settings`) + Đèn báo kết nối Real-time (`Agent Online`, `Playwright Connected`).
2. **Test Overview Metrics**: Thống kê chỉ số `Total Test Runs (1,284)`, `Passed (1,192)`, `Failed (64)`, `In Progress`, `Avg Duration (42.5s)`.
3. **Prompt-to-Test Generator**: Nhập prompt ngôn ngữ tự nhiên (ví dụ: *"Kiểm tra tính năng quên mật khẩu trên trang test.com"*) + các gợi ý sample prompt 1-click.
4. **Planner Agent Structured Test Plan**: Tự động sinh ra Kịch bản dạng JSON cấu trúc + Bộ công cụ chỉnh sửa kịch bản trực tiếp (Add, Edit, Delete, Reorder Steps).
5. **Playwright Live Browser Viewport Simulator**: Màn hình mô phỏng thao tác trình duyệt Playwright thời gian thực (`1920x1080`, 60 FPS, highlight DOM selector active) + Bộ điều khiển `Pause`, `Resume`, `Stop`.
6. **Agent Step Monitor**: Giám sát hành động của AI Agent theo thời gian thực (Step X/Y, Current Action, Observation, Next Step).
7. **Execution Timeline & Evidence Inspection**: Dòng thời gian các bước + Trình soi bằng chứng đa dạng (🌐 API Validation: POST endpoint, Status 200, 342ms latency, JSON Schema, 📸 Screenshot, 🤖 Agent Logs, 💻 Console Logs, 👁️ Visual Diff 0.01%).
8. **Recent Test Runs Table & System Footer**: Bảng lịch sử các đợt test gần nhất + Chân trang giám sát trạng thái hệ thống.

#### 📌 [v1.5.0] - Phân quyền Đăng nhập & Tích hợp Tài khoản Test (`admin123` / `123`)
- Cấu hình logic xác thực cho Modal Đăng nhập:
  - **Tài khoản**: `admin123`
  - **Mật khẩu**: `123`
- Bổ sung nút 1-click **"Fill Demo: admin123 / 123"** giúp đăng nhập thử nghiệm nhanh chóng.
- Kết nối thành công luồng Đăng nhập chuyển hướng trực tiếp vào **AI Agent Tester Dashboard Workspace**.

#### 📌 [v1.4.0] - Thiết kế Modal Đăng nhập / Đăng ký Trượt 2 Ô (Sliding Card Auth Modal)
- Xây dựng Modal Đăng nhập dạng thẻ kính mờ 2 nửa màn hình.
- Ứng dụng Framer Motion với vật lý lò xo (`spring physics stiffness: 220, damping: 26`): Khi ấn sang *Create Account*, thẻ hình ảnh bên phải trượt mượt mà sang trái che ô cũ và hiện form Đăng ký mới.
- Đổi nút bấm trên thanh Menu từ *Claim a Spot* thành **Sign In**.

#### 📌 [v1.3.0] - Định hình Nội dung Autonomous AI Testing Engine
- Cập nhật toàn bộ nội dung Hero Section sang thương hiệu **Autonomous AI Testing Platform**.
- Thay đổi thanh đối tác sang hệ sinh thái tích hợp DevOps / Testing chuyên nghiệp: **GitHub**, **GitLab**, **Playwright**, **Cypress**, **Jira**, **Jenkins**.
- Bổ sung các chỉ số ấn tượng: **99.8% Test Coverage** và **10x Release Velocity**.

#### 📌 [v1.2.0] - Khắc phục lỗi UMD Global Scope trên trình duyệt
- Phát hiện và xử lý xung đột tên biến toàn cục trong bản UMD của Framer Motion (`window.Motion` vs `window.FramerMotion`).
- Bổ sung cơ chế fallback tự động `window.Motion = window.Motion || window.FramerMotion` để tránh lỗi màn hình đen trên mọi trình duyệt.

#### 📌 [v1.1.0] - Xử lý Video lặp & Hiệu ứng Chữ BlurText
- Phát triển component `FadingVideo` xử lý mượt mà việc chuyển màu video nền tự động lặp (looping crossfade) bằng `requestAnimationFrame` (rAF) mà không dùng CSS transitions.
- Phát triển component `BlurText` kết hợp `IntersectionObserver` tự động hiện hiệu ứng làm mượt từng từ (word-by-word blur-in animation) khi cuộn tới màn hình.

#### 📌 [v1.0.0] - Khởi tạo Giao diện & Hệ thống Kính mờ (Liquid Glass System)
- Thiết lập cấu trúc Single Page Application (SPA) trên `index.html`.
- Cài đặt Font chữ Google Fonts: `Instrument Serif` (Headline nghiêng nghệ thuật) và `Barlow` (Nội dung chính) & `JetBrains Mono` (Mã nguồn / Log).
- Cấu hình Tailwind CSS tùy chỉnh bán kính bo tròn pill (`borderRadius.DEFAULT: "9999px"`).
- Xây dựng hệ thống class CSS kính mờ cao cấp: `.liquid-glass` (blur 4px, viền sáng mảnh) và `.liquid-glass-strong` (blur 50px, hiệu ứng đổ bóng mượt).

---

### 📂 CẤU TRÚC THƯ MỤC THƯỜNG TRỰC (FRONTEND FOLDER STRUCTURE)

```
frontend/
├── index.html        # Ứng dụng Single Page Application React (Landing Page + Sliding Auth Modal + Dashboard Workspace)
└── TRACE_LOG.md      # Nhật ký lưu trữ lịch sử thay đổi, bảng commit SHA và lệnh Revert
```
