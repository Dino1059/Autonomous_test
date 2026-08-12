SYSTEM ARCHITECTURE & MAP (DO NOT REMOVE)

## 1. Tech Stack & Versions (Công nghệ & Phiên bản)
- **Core**: Python 3.11, FastAPI 0.115.12, Uvicorn 0.34.1, Pydantic 2.10.6
- **Agent Framework**: `browser-use[memory]==0.2.5` (LangChain-based browser automation agent)
- **LLM Framework**: LangChain (langchain-core 0.3.49, langchain-openai 0.3.11, langchain-google-genai 2.1.2)
- **Browser Automation**: Playwright 1.52.0 (chromium), Pillow 11.2.1, opencv-python 4.11.0.86
- **UI Layer**: Gradio 5.25.2 (Gradio UI), json-repair 0.42.0
- **Monitoring**: LMNR 0.5.2, Loguru 0.7.3
- **LLM Provider**: Google Gemini (gemini-2.0-flash), Hub1 API (unsloth/MiniMax-M2.7, OpenAI-compatible), OpenRouter

## 2. Agent Topology (Bản đồ Multi-Agent)
- **FastAPI Server** `app/main.py`: Khởi tạo ứng dụng FastAPI, CORS, logging, router. Entry point chạy server.
- **Task Controller** `app/controllers/tasks.py`: Nhận request chạy test từ API (`POST /tasks/run`), khởi tạo background task, quản lý trạng thái task (running/completed/failed).
- **Task Executor** `app/utils/task_execution.py`: Logic chính — tạo LLM worker, tạo browser session, chạy Agent `browser-use` với task prompt, sinh report.
- **LLM Factory** `app/utils/llm_utils.py`: Factory pattern — tạo instance LLM theo provider (`google`, `openai`, `openrouter`, `hub1`). Tích hợp `SanitizingChatOpenAI` cho Hub1.
- **Sanitizing LLM** `app/utils/sanitizing_llm.py`: Wrapper LangChain `ChatOpenAI`, tự động chuyển `role: "tool"` → `HumanMessage("[Tool result]: ...")` để tương thích với Hub1 API (không hỗ trợ tool role). Có env var `SANITIZE_LLM=false` để tắt.
- **Browser Config** `app/utils/browser_config.py`: Cấu hình browser profile, viewport, headless mode, user-data-dir.
- **Browser Actions** `app/utils/browser_actions.py`: Định nghĩa các action browser-use có thể gọi.
- **Prompts** `app/utils/prompts.py`: Template prompt cho report generation.
- **Globals** `app/utils/globals.py`: Lưu trạng thái task toàn cục (BACKGROUND_TASKS, CANCELLATION_FLAGS).
- **Actions Controller** `app/controllers/actions.py`: API CRUD cho custom actions (JSON file).
- **Settings Controller** `app/controllers/settings.py`: API cập nhật biến môi trường.
- **Serializers** `app/serializers/models.py`: Pydantic models cho request/response (RunTaskRequest, TaskConfig, ...).
- **Gradio UI** `gradio_ui/webui.py`: Giao diện người dùng, gọi API FastAPI, poll kết quả task, hiển thị report.
- **Mock LLM** `app/utils/mock_llm.py`: LLM giả lập dùng cho test.
- **Record API** `app/record_api.py`: API ghi log.

## 3. Data Flow & State Path (Luồng Dữ liệu & Trạng thái)
- **Luồng chính**: User Input (API/UI) → `app/controllers/tasks.py` (POST /tasks/run) → `app/utils/task_execution.py` (run_tasks_background) → `app/utils/llm_utils.py` (create_custom_llm) → `browser-use Agent` (step loop: LLM call → execute action) → `demo_reports/TEST_XXXXX/report_*.md` (kết quả).
- **Luồng LLM request**: Agent gọi LangChain `_generate()` → `SanitizingChatOpenAI._generate()` (nếu Hub1) → sanitize messages → gửi lên API Hub1/Google/OpenRouter → nhận response → agent parse output.
- **State lưu**: Background task state trong `BACKGROUND_TASKS` dict (in-memory). Report lưu file trong `demo_reports/`. Log server ghi vào `server.log`. Log UI ghi vào `ui.log`.
- **Log file**: `server.log` (server chính), `ui.log` (Gradio UI), `demo_reports/TEST_XXXXX/` (kết quả test).

## 4. Error Routing Rules (Quy tắc Định tuyến Lỗi để Fix Bug)
- IF error contains `"role": "tool"` hoặc `"Input should be 'system', 'user' or 'assistant'"` (422 from Hub1 API) → Go to `app/utils/sanitizing_llm.py` (sanitize_messages chuyển tool → human). Kiểm tra `SANITIZE_LLM` env var.
- IF error contains `"Error 401: LLM API call failed"` hoặc `"Failed to invoke model"` → Go to `app/utils/llm_utils.py` (check API key, base URL, model name). Kiểm tra `.env` (HUB1_API_KEY, HUB1_API_BASE_URL, HUB1_MODEL_NAME).
- IF error contains `"Could not parse response"` hoặc `"Expecting ',' delimiter"` hoặc `finish_reason: 'length'` → Go to `app/utils/llm_utils.py` hoặc `app/utils/sanitizing_llm.py` (model output bị truncate, cần tăng max_tokens hoặc đổi model).
- IF error contains `ModuleNotFoundError` (import lỗi) → Go to `requirements.txt` (version mismatch, thiếu dependency).
- IF error contains `TypeError: BrowserType.launch_persistent_context()` → Go to `requirements.txt` (playwright version mismatch với browser-use 0.2.5, cần 1.52.0).
- IF error contains `"Result failed"` hoặc `"Stopping due to consecutive failures"` → Go to `app/utils/task_execution.py` và `app/utils/llm_utils.py` (model không đáp ứng được browser-use agent).
- IF error contains `"No module named 'browser_use.agent.memory'"` → Go to `requirements.txt` (cần `browser-use[memory]==0.2.5`, không phải `browser-use==0.2.5`).
- IF error contains `"Failed to parse model output"` → Go to `app/utils/sanitizing_llm.py` (có thể sanitize làm mất tool_calls của AIMessage).
- IF error contains `"posthog"` hoặc `"capture"` (Python 3.14 warning) → Go to `requirements.txt` hoặc environment (non-critical, có thể ignore).




Luồng Flow API cực kì chi tiết
GIAI ĐOẠN 1: FRONTEND (Gradio UI) → Tạo Payload
Bước 1: User chọn template từ dropdown (webui.py:576) → get_available_templates() đọc file .yaml trong templates_agent/
Bước 2: User điền các placeholder fields: title, step_action, step_expected_result, max_retry, url_test
Bước 3: User click "Run Test" → run_test_with_report() (webui.py:626) → run_test_case() (webui.py:436)
Bước 4: run_test_case() gọi create_payload_from_template(template_name, placeholder_dict, case_id) (webui.py:134)
- Substitutes ${variable} trong YAML template bằng string.Template.substitute()
- Đọc custom action từ file custom_actions/gather_evidence.py (nếu có)
- Tạo case_id = f"TEST_{hash(...):04d}"
- Trả về payload dict gồm: tasks, custom_actions, simulator_task, browser_config, v.v.
GIAI ĐOẠN 2: FRONTEND → HTTP → BACKEND
Bước 5: requests.post("http://localhost:8081/tasks/run", json=payload) (webui.py:485)
GIAI ĐOẠN 3: BACKEND RECEPTION (FastAPI)
Bước 6: FastAPI router (tasks_router.py) → run_tasks_endpoint() (tasks.py:15)
- Pydantic validate request body → RunTaskRequest model (models.py:77)
- Bottleneck #A: Pydantic validation + serialization của tasks, custom_actions, browser_config
Bước 7: Sinh task_id = uuid.uuid4(), khởi tạo BACKGROUND_TASKS[task_id] = {"status": "running"}
Bước 8: Convert CustomAction objects → dicts: custom_actions_dict = [action.model_dump() for action in request.custom_actions]
Bước 9: background_tasks.add_task(run_tasks_background, ...) → dispatch async background task (tasks.py:27)
Bước 10: Trả về response ngay lập tức cho frontend: DataResponse(data=MessageResponse(message=f"Task started with ID: {task_id}"))
GIAI ĐOẠN 4: FRONTEND POLLING
Bước 11: Frontend trích xuất task_id từ response
Bước 12: poll_results_streaming(task_id, case_id) (webui.py:508) → loop mỗi 5 giây gọi GET /tasks/{task_id}
Bước 13: get_task_status() (tasks.py:47) đọc BACKGROUND_TASKS[task_id] → trả về status "running" → frontend tiếp tục poll
GIAI ĐOẠN 5: BACKEND BACKGROUND EXECUTION
Bước 14: run_tasks_background() (task_execution.py:565) khởi chạy:
- CANCELLATION_FLAGS[task_id] = False
- Gọi run_tasks() (task_execution.py:136)
GIAI ĐOẠN 6: INITIALIZATION
Bước 15: Update SETTINGS globals: laminar keys, session_id, simulator config, browser_config
Bước 16: get_or_initialize_llm_worker(sim_provider, sim_model, sim_temperature) (globals.py:38)
- Tạo BaseLLMWorker (src/llms/base.py:46) → khởi tạo langchain LLM theo provider (Google/OpenAI/Hub1/OpenRouter)
- Bottleneck #B: Lazy singleton pattern nhưng lần đầu gọi có thể mất 1-2s tùy provider
Bước 17: Optional: Laminar.initialize() cho telemetry (task_execution.py:188)
Bước 18: update_browser_config_for_docker(final_browser_config) (browser_config.py)
Bước 19: browser_session = BrowserSession(**final_browser_config) + browser_session.start() (task_execution.py:232-236)
- Bottleneck #C: Launch Chromium (Playwright) → mất 2-10 giây tùy môi trường
GIAI ĐOẠN 7: PER-TASK EXECUTION LOOP (task_execution.py:239)
CHO MỖI TASK trong danh sách tasks (chạy tuần tự, KHÔNG song song):
Bước 20: Validate lại task config: TaskConfig.model_validate(task) (task_execution.py:246)
Bước 21: Nếu output_model_fields tồn tại → create_model_from_schema() (llm_utils.py:150) → tạo dynamic Pydantic model bằng create_model() (recursive, mỗi field, nested object)
- Bottleneck #D: Dynamic model creation chạy mỗi task, không cached
Bước 22: Controller(output_model=output_model, exclude_actions=...) (task_execution.py:255)
Bước 23: register_controller_actions(controller) (task_execution.py:506):
- registry.action(...)(paste_from_clipboard)
- registry.action(...)(call_user_simulator)
- registry.action(...)(get_system_message)
Bước 24: Với mỗi custom_action → register_custom_action(controller, action) (task_execution.py:516):
- Bottleneck #E: exec(action_code, context) → compile runtime Python code mỗi lần task chạy. Chậm + nguy hiểm
Bước 25: create_llm_for_task(task_config) (llm_utils.py:56) → Tạo LLM instance cho task agent
Bước 26: Xử lý config: planner_llm, memory_config, report_config
Bước 27: Agent(**kwargs) (task_execution.py:348) → tạo browser-use Agent với:
- task = prompt (có ${title}, ${step_action}, ... đã được thay thế)
- llm = task-specific LLM instance
- controller = controller đã register actions
- browser_session = browser session

GIAI ĐOẠN 8: AGENT EXECUTION (CORE - BOTTLENECK LỚN NHẤT)
Bước 28: agent_run_task = asyncio.create_task(agent.run(max_steps=task_config.max_steps)) (task_execution.py:385)
Bước 29: Vòng lặp monitor cancellation: while not agent_run_task.done(): asyncio.sleep(0.5) (task_execution.py:391) → poll mỗi 0.5s kiểm tra cancel flag
Bước 30: Agent bắt đầu chạy, mỗi step gồm:
1. Capture page state: screenshot (base64), HTML, URL → IO mất ~0.5-2s
2. Gửi state đến LLM → Bottleneck #1 (QUAN TRỌNG NHẤT): LLM Inference → mất 2-30s mỗi call tùy provider
3. LLM trả về action decision (click, type, navigate, ...)
4. Agent thực thi action bằng Playwright → mất 0.5-3s
5. Lặp lại đến khi task hoàn thành hoặc hết max_steps
Mỗi step = 1 LLM call (chậm nhất) + 1 Playwright action (nhanh hơn)
Với max_steps=20 + LLM chậm → tối thiểu 20 * (2s + 10s) = 240 giây (4 phút)

GIAI ĐOẠN 9: USER SIMULATOR INTERACTIONS (browser_actions.py:49)
Khi Agent gọi action call_user_simulator:
Bước 31: get_system_message() (browser_actions.py:178): extract page HTML + dùng Gemini LLM để parse system message từ page → mất 3-8s
Bước 32: Clipboard pyperclip.paste() lấy system message
Bước 33: llm_worker.get_response(question, session_id, image_urls) (base.py:116):
- Nếu có images: download từng URL (HTTP request) → encode base64 → Bottleneck #F: Image download + base64 encode
- Gọi LLM chain với history → Bottleneck #1: LLM inference (again)
Bước 34: json_repair.loads(response) parse JSON response, lưu USER_SIMULATOR_INTERACTIONS[session_id]
Bước 35: Sanitize + pyperclip.copy() → trả về ActionResult 

GIAI ĐOẠN 10: CUSTOM ACTION (gather_evidence)
Khi Agent gọi action gather_evidence: Chụp screenshot và lưu xuống filesystem
GIAI ĐOẠN 11: TASK COMPLETION
Bước 36: Agent hoàn thành → trả về history object
Bước 37: history.final_result() lấy structured output → Bottleneck #G: json_repair.loads() (nếu result là string/bytes)
Bước 38: Serialize history → json.dumps(history_dict['history'], default=str) (task_execution.py:462)
Bước 39: Nếu report_config tồn tại → generate_report() (llm_utils.py:258):
- Thu thập: URLs, screenshots, errors, tokens, duration (llm_utils.py:287-295)
- Build history_summary text (có thể rất lớn nếu nhiều steps)
- Bottleneck #1 (LLM Inference): Gọi reporter LLM .ainvoke(report_messages) với summary + optional screenshots
- Bottleneck #H: Ghi file xuống disk (report .md + history .txt)
- Bottleneck #I: os.makedirs mỗi lần + path join → small overhead nhưng tích lũy
Bước 40: Accumulate results: all_results.append({task_name, result, report_folder})
GIAI ĐOẠN 12: CLEANUP
Bước 41: browser_session.browser_context.close() → mất ~1-2s
Bước 42: browser_session.stop() + browser_session.close()
Bước 43: Trả về all_results, all_history đến run_tasks_background()
GIAI ĐOẠN 13: LƯU RESULTS VÀO GLOBAL STATE
Bước 44: run_tasks_background() (task_execution.py:603-630):
BACKGROUND_TASKS[task_id] = {
    "status": "completed",
    "results": results,
    "history": history,
    "simulator_interactions": simulator_interactions
}
GIAI ĐOẠN 14: FRONTEND NHẬN KẾT QUẢ
Bước 45: Lần poll tiếp theo thấy status = "completed" → hiển thị:
- Results (feature, feature_status, detail_reason)
- 3 simulator interactions gần nhất
- Report path
Bước 46: read_markdown_report(case_id) (webui.py:385): đọc file .md từ disk → IO read → sửa image paths
Bước 47: Hiển thị markdown report trong gr.Markdown