# Frontend Admin — Movie Agent Dashboard

Next.js app dành cho quản trị / demo nội bộ (so sánh models, xem trace ReAct, metrics). Hiện mới khởi tạo scaffold — UI sẽ gọi API từ `backend/`.

## Yêu cầu

- Node.js 18.18+
- Backend chạy tại http://localhost:8000 (xem [backend/README.md](../backend/README.md))

## Cài đặt

```bash
cd frontend-admin
npm install
```

## Chạy dev

```bash
cd frontend-admin
npm run dev -- -p 3001
```

Mở http://localhost:3001 (port khác `frontend-user` để chạy song song).

## Biến môi trường (khi tích hợp API)

Tạo `.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Scripts

| Lệnh | Mô tả |
|------|--------|
| `npm run dev` | Dev server |
| `npm run build` | Production build |
| `npm run start` | Chạy bản build |
| `npm run lint` | ESLint |

## Cấu trúc

- `src/app/` — App Router (Next.js)
- Kết nối backend: `POST /api/compare`, `GET /api/tools`, trace/metrics từ response chat
