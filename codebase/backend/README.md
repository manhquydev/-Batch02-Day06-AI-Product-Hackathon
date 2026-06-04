# Backend — Movie ReAct Agent API

FastAPI server exposing the same agent logic as the former Streamlit demo (Chatbot baseline, ReAct v1/v2, multi-model comparison, TMDB tools).

## Yêu cầu

- Python 3.10+
- API keys trong file `.env` (xem `.env.example`)

## Cài đặt

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # chỉnh API keys
```

### (Tùy chọn) Model local GGUF

```bash
pip install -r requirements-local.txt
mkdir -p models
# Đặt file .gguf vào models/ và cấu hình LOCAL_MODEL_PATH trong .env
```

## Chạy server

```bash
cd backend
source .venv/bin/activate
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

- API docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

## Endpoints chính

| Method | Path | Mô tả |
|--------|------|--------|
| GET | `/api/models` | Danh sách `provider/model` khả dụng |
| GET | `/api/tools` | 9 TMDB tools |
| GET | `/api/example-prompts` | Câu hỏi mẫu |
| POST | `/api/chat` | Một model — chat / ReAct |
| POST | `/api/compare` | 2–4 models song song |

### Ví dụ `POST /api/chat`

```json
{
  "message": "Gợi ý phim sci-fi trending tuần này ở VN",
  "mode": "ReAct Agent v2",
  "provider": "openai",
  "model": "gpt-4o-mini",
  "max_steps": 5
}
```

### Ví dụ `POST /api/compare`

```json
{
  "query": "So sánh Inception và Interstellar",
  "models": ["openai/gpt-4o-mini", "deepseek/deepseek-chat"],
  "mode": "ReAct Agent v2",
  "max_steps": 5
}
```

## Cấu trúc mã nguồn

- `src/agent/` — Chatbot baseline, ReAct v1/v2
- `src/core/` — LLM providers (OpenAI, DeepSeek, Gemini, Ollama, local)
- `src/tools/` — TMDB tools
- `src/services/` — `run_query`, so sánh song song
- `src/api/main.py` — FastAPI app

## Test

```bash
cd backend
pytest tests/ -q
python tests/test_local.py   # kiểm tra local GGUF (nếu đã cài)
```
