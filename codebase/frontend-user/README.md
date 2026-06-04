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

## Biến môi trường (khi tích hợp API)

Tạo `.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

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
