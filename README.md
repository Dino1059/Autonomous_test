# AI Agent Tester

An automated browser testing framework with AI-powered test execution and user simulation. The system consists of a FastAPI backend for test orchestration and a Gradio web interface for test management.

## 🚀 Quick Start

### Installation
```bash
conda create -n agent_tester python=3.11.11
conda activate agent_tester
cd ai-agent-tester
pip install -r requirements.txt
playwright install
```


### Env
See `.env.example`

### 🏃‍♂️ Running the Applications

```bash
## run tester api
python app/main.py --port 8081 --host 0.0.0.0

## run gradio webui
python gradio_ui/webui.py
```


## 📋 Usage

### Access Points

- **API Documentation**: http://localhost:8081/docs (Swagger UI)
- **API Health Check**: http://localhost:8081/health
- **Gradio Web Interface**: http://localhost:7860

### Using the Gradio Interface

1. **Select a Test Template**: Choose from available YAML-based test templates
2. **Fill Required Inputs**: The interface dynamically shows input fields based on the selected template
3. **Run Test**: Click "🚀 Run Test" to execute the automated browser test
4. **View Results**: Monitor real-time progress and view detailed reports

### API Endpoints

The FastAPI backend provides the following main endpoints:

- `GET /` - Welcome message
- `GET /health` - Health check
- `POST /tasks` - Create and execute test tasks
- `GET /tasks/{task_id}` - Get task status and results
- Additional endpoints for settings, actions, and task management



### Test Templates
- **Location**: `gradio_ui/templates_agent/`
- **Format**: YAML files with placeholder definitions
- **Features**:
  - Configurable test scenarios
  - Dynamic input field generation
  - Support for custom actions and browser configurations

## 📊 Reports

Test reports are automatically generated and stored in:
- **Default Location**: `gradio_ui/reports/{case_id}/`
- **Formats**: 
  - Markdown reports with test results
  - Screenshots for each test step
  - JSON data with detailed execution logs



### Adding New Templates

1. Create a new YAML file in `gradio_ui/templates_agent/`
2. Define placeholders and test steps
3. The template will automatically appear in the Gradio interface