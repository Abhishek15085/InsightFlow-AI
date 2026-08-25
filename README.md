# 🤖 InsightFlow AI

> **Intelligent Data Analysis & Agentic AI Platform**

InsightFlow AI is an end-to-end data intelligence platform that takes raw datasets and transforms them through automated cleaning, EDA, visualization, and an AI-powered chatbot assistant — all without any ML expertise required.

---

## 🚀 Development Phases

| Phase | Feature | Status |
|-------|---------|--------|
| Phase 0 | Project Setup | ✅ Complete |
| Phase 1 | File Upload | ✅ Complete |
| Phase 2 | Dataset Validation | ✅ Complete |
| Phase 3 | Automatic EDA | ✅ Complete |
| Phase 4 | Data Preprocessing | ✅ Complete |
| Phase 5 | Interactive Dashboard | ✅ Complete |
| Phase 6 | Agentic AI Chatbot | 🔄 In Progress |
| Phase 7 | Deployment | 🔜 Upcoming |

---

## 🤖 Phase 6 — Agentic AI Chatbot

InsightFlow AI integrates **NVIDIA Nemotron 3 Ultra** via **OpenRouter** as a dataset-aware AI assistant.

### Architecture

```
User
 ↓
Streamlit Chatbot UI
 ↓
FastAPI  POST /api/chat
 ↓
Nemotron Service  (OpenRouter OpenAI-compatible API)
 ↓
NVIDIA Nemotron 3 Ultra (nvidia/nemotron-3-ultra-550b-a55b:free)
 ↓
AI Response → Streamlit → User
```

### What the Chatbot Can Do

- Answer questions about the **uploaded dataset** (rows, columns, missing values, duplicates)
- Explain **EDA results** and visualizations
- Suggest **preprocessing strategies**
- Interpret **correlation matrices** and distributions
- Maintain **conversation history** for follow-up questions

### Agentic AI Sub-Phases

| Sub-Phase | Feature | Status |
|-----------|---------|--------|
| 6.1 | OpenRouter API key + `.env` setup | ✅ Done |
| 6.2 | Nemotron service (`nemotron_service.py`) | ✅ Done |
| 6.3 | FastAPI `/api/chat` endpoint | ✅ Done |
| 6.4 | React (Vite) chatbot UI | ✅ Done |
| 6.5 | Dataset-aware context injection (real data rows + column stats) | ✅ Done |
| 6.6 | Conversation history — multi-turn with token-safe trimming | ✅ Done |
| 6.7 | Streaming responses | 🔮 Future |
| 6.8 | RAG (ChromaDB Vector Search) | ✅ Done |

### Model Details

| Property | Value |
|----------|-------|
| Model | NVIDIA Nemotron 3 Ultra |
| Model ID | `nvidia/nemotron-3-ultra-550b-a55b:free` |
| Provider | OpenRouter (OpenAI-compatible API) |
| Endpoint | `https://openrouter.ai/api/v1` |
| Free Limit | ~50 requests/day |
| Privacy | Do NOT send personal/confidential data |

---

## 🗂️ Project Structure

```
InsightFlow-AI/
│
├── backend/                  # FastAPI backend
│   ├── api/                  # Route handlers
│   │   ├── chat.py           # 🆕 Agentic AI chat endpoint
│   │   ├── upload.py
│   │   ├── validate.py
│   │   ├── eda.py
│   │   ├── clean.py
│   │   ├── dashboard.py
│   │   └── health.py
│   ├── services/             # Service layer
│   │   ├── nemotron_service.py  # 🆕 NVIDIA Nemotron via OpenRouter
│   │   ├── cleaning_service.py
│   │   ├── eda_service.py
│   │   └── upload_service.py
│   ├── schemas/              # Pydantic request/response schemas
│   ├── config/               # App configuration & settings
│   └── main.py               # FastAPI app entry point
│
├── frontend/                 # Streamlit frontend
│   ├── pages/                # Multi-page app views
│   ├── components/           # Reusable UI components
│   └── app.py                # Streamlit entry point (includes chatbot)
│
├── datasets/                 # Uploaded datasets (gitignored)
├── reports/                  # Generated EDA reports
├── outputs/                  # Exported outputs
├── tests/                    # Unit & integration tests
├── docs/                     # Documentation & architecture
├── docker/                   # Docker-related configs
│
├── .env                      # 🔐 API keys (gitignored — never commit!)
├── requirements.txt          # Python dependencies
├── .gitignore
├── docker-compose.yml
└── Dockerfile
```

---

## ⚙️ Quick Start

### 1. Clone & Setup Environment

```bash
git clone <repo-url>
cd InsightFlow-AI

python -m venv venv
# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Configure API Key

Create a `.env` file at project root:

```env
OPENROUTER_API_KEY=your_openrouter_api_key_here
```

> ⚠️ **Never commit `.env` to GitHub.** It is already listed in `.gitignore`.

### 3. Run Backend (FastAPI)

```bash
uvicorn backend.main:app --reload --port 8000
```

API Docs: http://localhost:8000/docs

### 4. Run Frontend (Streamlit)

```bash
streamlit run frontend/app.py
```

UI: http://localhost:8501

### 5. Run with Docker

```bash
docker-compose up --build
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend API | FastAPI + Uvicorn |
| Frontend UI | Streamlit |
| Data Processing | Pandas, NumPy |
| Visualization | Plotly, Matplotlib |
| Agentic AI | NVIDIA Nemotron 3 Ultra via OpenRouter |
| AI Client | OpenAI Python SDK (OpenRouter-compatible) |
| Containerization | Docker |

---

## 🔐 Security Notes

- Store `OPENROUTER_API_KEY` in `.env` — **never hardcode it**
- `.env` is in `.gitignore` — **never commit it**
- Do not send personal/confidential data to the AI model
- Free tier: ~50 requests/day — plan accordingly

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.
