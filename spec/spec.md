# SPEC — AI Movie Recommendation Web App
# Nhóm · Batch 02 · Day 06

---

## 1. Bằng chứng

### Self-use evidence (tự dùng app Streamlit Day 03)

| Observation | File liên quan | Path | Điều học được |
|---|---|---|---|
| ReAct agent chạy 5-8 bước, spinner mơ hồ, user không biết đang chờ gì | `src/app.py:245` | Low-confidence | Guest UI phải hiện step-by-step: "đang tìm phim… đang kiểm tra Netflix VN…" |
| `check_streaming_availability` trả empty providers với nhiều phim phổ biến ở VN | `src/tools/movie_tools.py:116` | Low-confidence | Hiện badge "Chưa xác nhận platform VN" thay vì im lặng |
| Mood filter chỉ nhận 6 enum cứng — nhập "hồi hộp" → lỗi JSON | `src/tools/mood_config.py` | Failure | Agent phải map ngôn ngữ tự nhiên → enum trước khi gọi tool |
| App không có lịch sử phiên — refresh mất toàn bộ chat | `src/app.py:44` | Failure | Backend cần lưu session nếu muốn UX liên tục |

### User evidence (phỏng vấn nhanh 3 người trong lớp)

| Quote | User | Pain |
|---|---|---|
| "Gợi ý hay nhưng không biết xem trên đâu, cứ phải search thêm" | Người dùng 20-30 tuổi có Netflix | Streaming availability không đáng tin |
| "Không biết nên hỏi câu gì để app hiểu tôi muốn phim loại nào" | First-time user | Onboarding yếu, thiếu câu hỏi mẫu |
| "App trông xấu, không muốn chia sẻ link cho bạn" | Người dùng có ý kiến UX | Streamlit UI không đủ polished cho sản phẩm thật |

### Competitor/analog evidence

| App | Họ làm gì? | Pattern học được |
|---|---|---|
| Letterboxd | Visual grid poster + rating badge, không AI real-time | Layout card phim hiệu quả hơn danh sách text |
| Netflix "Because you watched X" | Black-box algo, không giải thích | Transparency (hiện reasoning) là differentiator |
| Perplexity AI | Hiển thị source + reasoning song song với answer | Trace panel tạo trust cho admin |

---

## 2. Lát cắt để build

```
Cho người dùng VN có Netflix/Disney+ đang muốn chọn phim tối nay,
prototype sẽ dùng AI ReAct agent (9 TMDB tools) để nhận câu hỏi tự nhiên
("tôi buồn muốn xem phim nhẹ nhàng", "phim Sci-Fi trending tuần này"),
tự chọn tool phù hợp (filter_by_mood / search_movies / get_trending_movies +
check_streaming_availability),
tạo ra poster grid 3-5 phim với streaming badge VN + 1-2 câu giải thích,
và xử lý failure mode "streaming không rõ VN" bằng badge "Chưa xác nhận platform VN"
kèm link JustWatch VN — không im lặng, không hallucinate.
```

---

## 3. AI Product Canvas

| Ô | Nội dung |
|---|---|
| **Value — Giá trị** | Dành cho người dùng VN 18–35 tuổi có subscription streaming, đang bị kẹt ở bước "chọn phim tối nay". Đau ở chỗ: app recommendation hiện tại không hiểu ngôn ngữ tự nhiên/tâm trạng, gợi ý phim không biết stream được ở VN không → mất thêm 10–15 phút tự tìm. AI giải được: nhận câu hỏi tự nhiên → tự gọi TMDB tools → trả gợi ý có poster, badge streaming VN, giải thích ngắn trong ≤ 15 giây. |
| **Trust — Niềm tin** | Khi AI gợi ý phim không stream được ở VN: hiện badge "Chưa xác nhận platform VN" + link JustWatch VN. Không để LLM khẳng định streaming info — 100% relay từ TMDB API. Khi agent không chắc mood: hỏi lại thay vì đoán sai. Admin có trace viewer để kiểm tra từng bước reasoning. |
| **Feasibility — Tính khả thi** | Chi phí: ~$0.005–0.02/query (gpt-4o-mini). Độ trễ mục tiêu: ≤ 15 giây. Dữ liệu: TMDB API v3 live. Rủi ro lớn nhất: TMDB watch-provider data thiếu cho VN → đã xử lý bằng badge "Chưa xác nhận". Ngưỡng dừng: nếu latency > 30 giây ổn định → đơn giản hóa chain tool. |
| **Tín hiệu học** | Khi user tinh chỉnh gợi ý ("phim này tôi xem rồi"), agent nhận context mới và chạy lại. Admin panel log trace + latency để phân tích sau. Chưa có feedback loop tự động trong Day 06 — đây là cải tiến tiếp theo. |

---

## 4. Tăng năng lực hay tự động hóa

**Quyết định: Augmentation — AI gợi ý, user quyết cuối.**

- TMDB data live — agent không tự sinh phim, chỉ search/filter từ database thật.
- User là người cuối cùng chọn xem phim nào (một thao tác chấp nhận).
- Automation toàn phần (tự play phim) nằm ngoài scope Day 06.
- **Human role:** Decider — đọc gợi ý và tự quyết định.

Lý do chọn augment chứ không automate: rủi ro sai (gợi ý phim không phù hợp mood) có thể hoàn tác dễ dàng — user chỉ cần nhập lại. Không có hậu quả không thể đảo ngược.

---

## 5. Bốn đường đi của trải nghiệm

| Đường đi | Thiết kế xử lý |
|---|---|
| **Đường thuận** | User nhập "tôi buồn muốn xem phim nhẹ nhàng" → agent gọi `filter_by_mood("sad")` + `check_streaming_availability` → trả 3-5 phim có poster, điểm TMDB, badge streaming VN, câu giải thích ngắn. Latency ≤ 15 giây. |
| **Khi AI không chắc** | User nhập câu mơ hồ ("xem gì đi") → agent hiển thị "Bạn đang cảm thấy thế nào?" + 3 mood suggestion (Buồn / Vui / Hồi hộp) để user chọn; không tự đoán sai. |
| **Khi AI sai** | TMDB trả empty result / API timeout → agent báo lỗi rõ ràng + gợi ý thay thế ("Thử mood khác?", "Xem trending tuần này?"); không crash silent. Streaming empty → badge "Chưa xác nhận" + link JustWatch VN. |
| **Khi người dùng sửa** | User nhập tinh chỉnh ("phim này tôi xem rồi, gợi ý khác đi") → agent chạy lại với context mới từ conversation history. Log trace để admin review. |

---

## 6. Những kiểu lỗi đáng lo nhất

### Lỗi 1: Hallucinate streaming availability

```
Xuất hiện khi: TMDB watch-provider data trống hoặc chỉ có global, không có VN.
Ai chịu thiệt: User mở Netflix tìm không thấy phim → mất tin hoàn toàn vào app.
Prototype xử lý: Không bao giờ để LLM khẳng định có/không — chỉ relay raw data từ
TMDB API. Nếu providers empty → hiện badge "Chưa xác nhận platform VN" + link
"Kiểm tra trên JustWatch VN".
```

### Lỗi 2: Mood mapping sai với ngôn ngữ tự nhiên VN

```
Xuất hiện khi: User nhập "hồi hộp", "mệt mỏi", "buồn cười" — không khớp 6 enum cứng.
Ai chịu thiệt: Agent trả lỗi JSON, user không nhận được gợi ý nào.
Prototype xử lý: Agent map ngôn ngữ tự nhiên → enum trước khi gọi tool
(ví dụ: "hồi hộp" → "excited"). Nếu không map được → hỏi lại với 3 lựa chọn.
```

### Lỗi 3: Latency vượt 15 giây

```
Xuất hiện khi: Agent chuỗi 5-8 tool calls, mỗi call có delay TMDB API.
Ai chịu thiệt: User bỏ chờ, nghĩ app bị treo.
Prototype xử lý: Hiển thị step-by-step progress ("Đang tìm phim... Đang kiểm tra
Netflix VN...") để user biết app đang hoạt động. Max_steps giới hạn ở 5 bước.
```

---

## 7. Kế hoạch kiểm thử và bằng chứng demo

### Test cases chuẩn bị sẵn

| Input | Expected output | Path |
|---|---|---|
| "tôi buồn muốn xem phim nhẹ nhàng" | 3-5 phim drama/comedy có poster + badge streaming | Happy |
| "xem gì đi" | Agent hỏi lại với 3 mood options | Low-confidence |
| "phim Sci-Fi trending VN tuần này" | Trending movies có badge streaming VN | Happy |
| Nhập mood "hồi hộp" | Map → "excited", trả gợi ý phim thriller/action | Happy |
| TMDB timeout (simulate) | Error message rõ + gợi ý thay thế | Failure |

### Bằng chứng giữ lại

- Screenshots từ self-use Streamlit Day 03 (trong `evidence/`)
- Nhật ký prompt gửi cho gpt-4o-mini (trace admin panel)
- .env.example ghi rõ biến môi trường cần thiết
- Test suite `backend/tests/`

---

## 8. Phân công

| Thành viên | Mã HV | Phần phụ trách |
|---|---|---|
| Trịnh Thị Lan Anh | 2A202600737 | **Guest UI (Next.js):** chat input, poster grid, streaming badge, mood selector, step-by-step progress. Files: `frontend-user/src/` |
| Nguyễn Mạnh Quý | 2A202600643 | **Admin UI (Next.js):** trace viewer panel, metrics dashboard (latency, tool calls, steps), model selector. Files: `frontend-admin/src/` |
| Nguyễn Thanh Anh Quân | 2A202600892 | **FastAPI endpoints:** `POST /api/chat`, `GET /api/models`, `GET /api/tools`, wrap ReAct agent. Files: `backend/src/api/` |
| Nguyễn Đình Bảo Long | 2A202600981 | **FastAPI infra:** project setup, CORS, .env config, Pydantic schemas, error handling. Files: `backend/src/core/`, `backend/src/api/main.py` |

---

## Tech stack

| Layer | Công nghệ | Ghi chú |
|---|---|---|
| Backend | Python 3.11 + FastAPI + Uvicorn | Giữ agent/tools từ Day 03 |
| LLM | OpenAI GPT-4o-mini (mặc định) / DeepSeek / Ollama | Factory pattern hiện có |
| Data | TMDB API v3 (live data) | `backend/src/tools/tmdb_client.py` |
| Frontend User | Next.js 15 + TypeScript + Tailwind CSS | Guest UI |
| Frontend Admin | Next.js 15 + TypeScript + Tailwind CSS | Trace viewer + metrics |

---

## Định nghĩa "done" cho Day 06 demo

- [ ] Guest nhập câu tự nhiên → nhận poster grid ≤ 15 giây
- [ ] Streaming badge hiện đúng hoặc "Chưa xác nhận" — không im lặng
- [ ] Failure path "không rõ mood" → agent hỏi lại thay vì crash
- [ ] Admin xem được trace và latency của request vừa chạy
- [ ] `POST /api/chat` trả JSON có `movies[]`, `trace[]`, `metrics{}`
- [ ] Repo có README với hướng dẫn chạy local và `.env.example`
