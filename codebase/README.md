# Codebase — AI Movie Recommendation Web App

Prototype ReAct Agent gợi ý phim cho người dùng VN, tích hợp FastAPI backend + 2 Next.js frontends.

## Cấu trúc

```
codebase/
├── backend/          FastAPI — ReAct agent, 9 TMDB tools, multi-model support
├── frontend-user/    Next.js — Guest UI (chat + poster grid + streaming badge)
└── frontend-admin/   Next.js — Admin UI (trace viewer + metrics dashboard)
```

## Chạy bằng Docker (cả 3 service)

**Yêu cầu:** Docker Desktop hoặc Docker Engine + Docker Compose v2.

```bash
cd codebase
cp backend/.env.example backend/.env    # bắt buộc: OPENAI_API_KEY, TMDB_API_KEY
# tùy chọn: cp .env.docker.example .env

docker compose up --build
```

**Lỗi `registry-1.docker.io ... connection refused` khi `--build`:** Docker không kết nối được Docker Hub (VPN, firewall, mạng công ty). Bạn vẫn chạy được stack nếu đã build trước đó:

```bash
docker compose up -d
```

Chỉ rebuild khi có mạng ổn định; `docker-compose.yml` đặt `pull: false` để ưu tiên image base (`node:20-alpine`, `python:3.12-slim`) đã có trên máy. Nếu vẫn lỗi: bật/tắt VPN, **Docker Desktop → Settings → Resources → Network**, hoặc cấu hình HTTP/HTTPS proxy cho Docker.

**Chat trả lời “không thể kết nối TMDB” / không có poster:** Container backend không gọi được `api.themoviedb.org` (cùng kiểu lỗi mạng Docker Hub). Agent vẫn trả text qua LLM nhưng tool TMDB trả `TMDB network error` nên không có dữ liệu phim. Thử: `docker compose restart backend`, tắt VPN, hoặc chạy backend ngoài Docker (`uvicorn` trong `backend/`) rồi trỏ frontend tới `http://localhost:8000`.

| Service | URL |
|---------|-----|
| Guest UI (`frontend-user`) | http://localhost:3000 |
| Admin UI (`frontend-admin`) | http://localhost:3001 |
| Backend API + Swagger | http://localhost:8000/docs |

Dừng stack: `docker compose down`

**Phiên chat (guest UI):** Mỗi lần mở/refresh trang hoặc bấm «Trò chuyện mới» → `session_id` mới. Backend lưu toàn bộ lượt (câu hỏi + câu trả lời + danh sách phim TMDB) trong RAM cho đến khi hết phiên. Câu tiếp theo như «Cho tôi 3 phim khác nữa» dùng ngữ cảnh phiên; TMDB tools **tự loại** các `movie_id` đã gợi ý và lấy trang discover/trending tiếp theo để tránh trùng poster. Sau >10 lượt, backend tóm tắt rồi tiếp tục.

Rebuild sau khi đổi code frontend (biến `NEXT_PUBLIC_*` bake lúc build):

```bash
docker compose build --no-cache frontend-user frontend-admin
docker compose up -d
```

---

## Cách chạy local

### Yêu cầu

- Python 3.10+
- Node.js 18+
- API keys: `OPENAI_API_KEY`, `TMDB_API_KEY` (xem `backend/.env.example`)

### 1. Backend

```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env   # điền API keys
uvicorn src.api.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

### 2. Frontend User (Guest)

```bash
cd frontend-user
npm install
npm run dev
```

→ http://localhost:3000

### 3. Frontend Admin

```bash
cd frontend-admin
npm install
npm run dev -- -p 3001
```

→ http://localhost:3001

## Biến môi trường

Xem `backend/.env.example`. Các biến bắt buộc:

| Biến | Mô tả |
|------|-------|
| `OPENAI_API_KEY` | OpenAI API key (dùng gpt-4o-mini mặc định) |
| `TMDB_API_KEY` | TMDB API v3 key (lấy tại themoviedb.org) |
| `DEEPSEEK_API_KEY` | Tùy chọn — nếu muốn dùng DeepSeek model |

## Công cụ và API đã dùng

| Layer | Công nghệ |
|-------|-----------|
| Backend framework | FastAPI + Uvicorn |
| AI model | OpenAI GPT-4o-mini (mặc định), DeepSeek, Ollama |
| Agent pattern | ReAct Agent v2 (tự chọn tool theo context) |
| Data | TMDB API v3 — 9 tools: search, trending, mood filter, streaming check, … |
| Frontend | Next.js 15 + TypeScript + Tailwind CSS |

## Endpoints chính

| Method | Path | Mô tả |
|--------|------|--------|
| POST | `/api/chat` | Gửi câu hỏi → agent chạy → trả movies + trace + metrics |
| GET | `/api/models` | Danh sách provider/model khả dụng |
| GET | `/api/tools` | 9 TMDB tools |
| POST | `/api/compare` | So sánh 2–4 models song song |

## Phân công

| Thành viên | Mã HV | Phần phụ trách |
|---|---|---|
| Trịnh Thị Lan Anh | 2A202600737 | Guest UI (`frontend-user/src/`) |
| Nguyễn Mạnh Quý | 2A202600643 | Admin UI (`frontend-admin/src/`) |
| Nguyễn Thanh Anh Quân | 2A202600892 | FastAPI endpoints (`backend/src/api/`) |
| Nguyễn Đình Bảo Long | 2A202600981 | FastAPI infra + config (`backend/src/core/`) |
