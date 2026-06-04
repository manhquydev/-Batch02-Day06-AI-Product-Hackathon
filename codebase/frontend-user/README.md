# Frontend User — Movie Recommendation Demo

Next.js app dành cho người dùng cuối (chat, gợi ý phim). Hiện mới khởi tạo scaffold — UI sẽ gọi API từ `backend/`.

## Yêu cầu

- Node.js 18.18+
- Backend chạy tại http://localhost:8000 (xem [backend/README.md](../backend/README.md))

## Cài đặt

```bash
cd frontend-user
npm install
```

## Chạy dev

```bash
cd frontend-user
npm run dev
```

Mở http://localhost:3000

## Kết nối backend

1. Chạy FastAPI (terminal 1):

```bash
cd ../backend
# Cấu hình .env với OPENAI_API_KEY, TMDB_API_KEY (xem .env.example)
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

2. Tạo `frontend-user/.env.local` (copy từ `.env.local.example`):

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_USE_REAL_API=true
NEXT_PUBLIC_DEFAULT_MODEL=openai/gpt-4o-mini
```

3. Chạy lại `npm run dev`. Chat sẽ gọi `POST http://localhost:8000/api/chat`.

Để dùng dữ liệu mẫu offline (không cần backend): `NEXT_PUBLIC_USE_REAL_API=false`.

## Scripts

| Lệnh | Mô tả |
|------|--------|
| `npm run dev` | Dev server (Turbopack) |
| `npm run build` | Production build |
| `npm run start` | Chạy bản build |
| `npm run lint` | ESLint |

## Cấu trúc

- `src/app/` — App Router (Next.js)
- Kết nối backend: `POST /api/chat`, `GET /api/models`, …
