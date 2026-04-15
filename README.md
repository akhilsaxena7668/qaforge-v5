# QAForge — AI-Powered Testing Suite (Gemini Edition)

> Generate, execute, and export comprehensive test cases using 4 specialized Google Gemini AI models.

## 🤖 Gemini Models Used

| Model | Use Case |
|-------|----------|
| `gemini-2.0-flash` | Fast URL/text test generation |
| `gemini-1.5-pro` | Deep analysis & complex suites |
| `gemini-1.5-flash` | Image/screenshot analysis (vision) |
| `gemini-2.0-flash-exp` | Video/screen recording analysis |

## ✅ Features

- **Test Web Apps** — Paste any URL, Gemini analyzes your UI
- **Test Mobile Apps** — Upload iOS/Android screenshots
- **Test Desktop Apps** — Screenshot any Windows/Mac/Linux app
- **Generate from Video** — Drop a screen recording walkthrough
- **Generate from Text** — Describe your app in plain English
- **Execute Tests** — Live test feed with pass/fail tracking
- **Download Reports** — HTML, Excel (with charts!), and JSON formats
- **4 AI Models** — Select the right model for each task

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Google Gemini API key (free at https://aistudio.google.com/app/apikey)

### Install & Run

```bash
# 1. Unzip and enter the project folder
cd qaforge-gemini

# 2. Install dependencies
pip install -r requirements.txt

# 3. (Optional) Set API key as environment variable
export GEMINI_API_KEY=AIzaSy...

# 4. Start the server
python run.py

# 5. Open in browser
open http://localhost:8000
```

### Configure in UI
1. Open http://localhost:8000
2. Click **CONFIG** in the navbar
3. Paste your Gemini API key → **SAVE & CONNECT**
4. Go to **GENERATE** → choose URL, Image, Video, or Text
5. Click **EXECUTE** to run tests
6. **Download** HTML, Excel, or JSON reports

## 📁 Project Structure

```
qaforge-gemini/
├── backend/
│   ├── main.py           # FastAPI routes
│   ├── ai_engine.py      # Gemini AI integration (4 models)
│   ├── test_executor.py  # Test execution engine
│   ├── report_gen.py     # HTML + Excel + JSON reports
│   └── models.py         # Pydantic data models
├── frontend/
│   ├── index.html        # Landing page (with animations)
│   ├── app.html          # Main QA tool application
│   ├── css/app.css       # App styles
│   └── js/
│       ├── landing.js    # Particle/animation engine
│       └── app.js        # App frontend logic
├── reports/              # Generated report files
├── requirements.txt
└── run.py                # Entry point
```

## 📊 Export Formats

| Format | Contents |
|--------|----------|
| **HTML** | Styled test report with KPIs, full test table |
| **Excel** | 3 sheets: Summary, Detailed Results, Charts (bar + pie) |
| **JSON** | Raw data for CI/CD pipelines |

## 🔧 Production Extension

The test executor currently uses realistic simulation. To run real browser tests:

```python
# In backend/test_executor.py, replace run_test() with:
# - Playwright for web testing
# - Selenium for cross-browser
# - Appium for mobile
# - PyAutoGUI for desktop
```

## 📄 License
MIT License
