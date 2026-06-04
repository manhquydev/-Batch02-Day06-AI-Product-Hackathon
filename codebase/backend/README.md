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
| POST | `/api/chat` | Một model — chat / ReAct (hỗ trợ `session_id` đa lượt) |
| POST | `/api/sessions` | Tạo phiên chat mới |
| POST | `/api/sessions/{id}/reset` | Xóa lịch sử phiên |
| POST | `/api/summary` | Tóm tắt lịch sử (tự gọi khi >10 lượt) |
| POST | `/api/compare` | 2–4 models song song |

### Ví dụ `POST /api/chat`

```json
{
  "message": "Gợi ý phim sci-fi trending tuần này ở VN",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "mode": "ReAct Agent v2",
  "provider": "openai",
  "model": "gpt-4o-mini",
  "max_steps": 8
}
```

### `max_steps` (tỉ lệ hoàn thành cao hơn)

| Cách | Giá trị |
|------|---------|
| Mặc định API | `8` (env `AGENT_DEFAULT_MAX_STEPS`) |
| Tối đa API | `12` (env `AGENT_MAX_MAX_STEPS`) |
| Guest UI | `NEXT_PUBLIC_MAX_STEPS=8` lúc build frontend-user |
| Admin UI | Slider **Max steps** trên dashboard (2–12) |

Trong `backend/.env`:

```env
AGENT_DEFAULT_MAX_STEPS=8
AGENT_MAX_MAX_STEPS=12
```

Câu hỏi phức tạp (nhiều tool + session dài): thử `max_steps: 10` hoặc `12`. Agent còn **ép Final Answer** khi sắp hết bước và **gọi thêm 1 lần LLM** tổng hợp nếu vẫn thiếu đáp án.

Sau **10 lượt** hội thoại trong cùng `session_id`, lượt thứ 11+ tự gọi tóm tắt (`/api/summary` nội bộ) rồi dùng bản tóm tắt + vài lượt gần nhất làm ngữ cảnh.

### Ví dụ `POST /api/compare`

```json
{
  "query": "So sánh Inception và Interstellar",
  "models": ["openai/gpt-4o-mini", "deepseek/deepseek-chat"],
  "mode": "ReAct Agent v2",
  "max_steps": 8
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
