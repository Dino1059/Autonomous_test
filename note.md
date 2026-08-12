## Tóm tắt các nội dung vừa bổ sung theo yêu cầu của bạn:                                                                                            
                                                                                                                                                        
  • Sơ đồ Sequence Diagram: Quy định rõ thứ tự truyền tin giữa Orchestrator ↔ Planner Agent ↔ Browser Execution Agent ↔ User Simulator Agent ↔ Report   
  Evaluator Agent.                                                                                                                                      
                                                                                                                                                        
  #### 2. Con người sẽ kiểm soát ra sao? (Human-in-the-Loop Control)                                                                                    
                                                                                                                                                        
  • 3 Chế độ điều khiển:                                                                                                                                
      1. Fully Autonomous: Chạy tự động 100% (User Simulator tự trả lời form/câu hỏi).                                                                  
      2. Semi-Autonomous (Approval Gate): Tạm dừng trước các hành động quan trọng (xoá dữ liệu, thanh toán) để chờ người dùng bấm Approve / Reject.     
      3. Live Intervention (Manual Takeover): Khi phát hiện CAPTCHA / Form lạ, hệ thống gửi cảnh báo HUMAN_INTERVENTION_NEEDED, hiển thị màn hình trình 
  #### 1. Các Agent giao tiếp với nhau như thế nào? (Inter-Agent Communication Protocol)                                                                
                                                                                                                                                        
  • Chuẩn giao tiếp AgentMessage: Sử dụng pydantic model định nghĩa rõ sender, recipient, message_type (TASK_PLAN, ACTION_REQUEST, SIMULATION_QUERY,    
  HUMAN_INTERVENTION_NEEDED, EVALUATION_REQUEST, v.v.) và payload dữ liệu.                                                                              
  • Bộ nhớ dùng chung (SharedExecutionContext): Chứa danh sách sub_goals, ảnh screenshot mới nhất, lịch sử tương tác và log hoạt động realtime.         
      duyệt hiện tại và chờ con người nhập liệu từ Gradio UI.
  • Các API điều khiển thời gian thực: Thêm các endpoint /pause, /resume, /human-input, và /cancel.
  
  #### 3. Lộ trình triển khai Step-by-Step
  
  • Bước 1: Định nghĩa Data Models & Message Protocol (app/schemas/agent_messages.py, app/schemas/context.py).
  • Bước 2: Khởi tạo BaseAgent và AgentEventBus (app/agents/base.py).
  • Bước 3: Triển khai 4 Agent chuyên biệt (planner.py, browser_executor.py, user_simulator.py, evaluator.py).
  • Bước 4: Triển khai Orchestrator (app/agents/orchestrator.py) quản lý luồng & chờ Human Input.
  • Bước 5: Tích hợp Controller & Bảng điều khiển Gradio UI.
  • Bước 6: Kiểm thử tự động & xác minh thủ công.