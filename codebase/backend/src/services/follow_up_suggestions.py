"""Generate clickable follow-up prompts after each assistant reply."""

from __future__ import annotations

import json
import os
import random
import re
from typing import Any, Dict, List, Literal, Optional

from src.core.factory import get_llm_provider
from src.utils.request_limits import parse_requested_movie_count

FollowUpKind = Literal["continue", "explore", "detail"]

EXPLORE_PROMPTS: List[Dict[str, str]] = [
    {"text": "Phim Sci-Fi trending tuần này ở VN", "kind": "explore"},
    {"text": "Gợi ý phim hài nhẹ để xem tối nay", "kind": "explore"},
    {"text": "Phim lãng mạn hợp xem hẹn hò cuối tuần", "kind": "explore"},
    {"text": "So sánh Inception và Interstellar", "kind": "explore"},
]

FOLLOWUP_SYSTEM = (
    "Bạn tạo gợi ý câu hỏi tiếp theo cho app gợi ý phim tiếng Việt. "
    "Mỗi gợi ý là câu người dùng sẽ gửi chat (ngắn, tự nhiên). "
    "Với mỗi phim vừa gợi ý, ưu tiên chip dạng: Cho mình biết thêm về phim <Tên phim>. "
    "Không tạo chip '3 phim khác' nếu vừa trả lời chi tiết một phim. "
    'Trả về ĐÚNG JSON array: [{"text":"...","kind":"detail"|"continue"|"explore"}]'
)


def _dedupe(items: List[Dict[str, str]], limit: int = 4) -> List[Dict[str, str]]:
    seen: set[str] = set()
    out: List[Dict[str, str]] = []
    for item in items:
        text = (item.get("text") or "").strip()
        if not text or text.lower() in seen:
            continue
        seen.add(text.lower())
        kind = item.get("kind")
        if kind not in ("continue", "explore", "detail"):
            kind = "continue"
        out.append({"text": text, "kind": kind})
        if len(out) >= limit:
            break
    return out


def _primary_genre(movies: List[Dict[str, Any]]) -> str:
    for movie in movies:
        genres = movie.get("genres")
        if isinstance(genres, list) and genres:
            return str(genres[0])
        if isinstance(genres, str) and genres.strip():
            return genres.split(",")[0].strip()
    return "phim"


def _detail_chips(movies: List[Dict[str, Any]], *, max_titles: int = 3) -> List[Dict[str, str]]:
    chips: List[Dict[str, str]] = []
    for movie in movies[:max_titles]:
        title = movie.get("title")
        if not title:
            continue
        chips.append(
            {
                "text": f"Cho mình biết thêm về phim {title}",
                "kind": "detail",
            }
        )
    return chips


def _heuristic_follow_ups(
    user_message: str,
    answer: str,
    movies: List[Dict[str, Any]],
    *,
    limit: int = 4,
) -> List[Dict[str, str]]:
    suggestions: List[Dict[str, str]] = []
    titles = [str(m["title"]) for m in movies if m.get("title")][:3]
    genre = _primary_genre(movies)
    requested_n = parse_requested_movie_count(user_message)

    if movies:
        suggestions.extend(_detail_chips(movies))

        if titles:
            suggestions.append(
                {
                    "text": f"Phim {titles[0]} có trên Netflix VN không?",
                    "kind": "continue",
                }
            )
        if len(titles) >= 2:
            suggestions.append(
                {
                    "text": f"So sánh {titles[0]} và {titles[1]}",
                    "kind": "continue",
                }
            )
        elif titles:
            suggestions.append(
                {
                    "text": f"Gợi ý phim tương tự {titles[0]}",
                    "kind": "continue",
                }
            )

        if requested_n and requested_n >= 2 and len(movies) >= 2:
            suggestions.append(
                {
                    "text": f"Cho tôi {requested_n} phim {genre} khác nữa, không trùng danh sách trước",
                    "kind": "continue",
                }
            )

    normalized_user = user_message.lower()
    pool = [p for p in EXPLORE_PROMPTS if p["text"].lower() not in normalized_user]
    if not pool:
        pool = list(EXPLORE_PROMPTS)
    random.shuffle(pool)
    for item in pool:
        if len(suggestions) >= limit:
            break
        suggestions.append(item)

    if not movies:
        suggestions = list(EXPLORE_PROMPTS[:3])
        random.shuffle(suggestions)

    return _dedupe(suggestions, limit=limit)


def _parse_llm_json(content: str) -> Optional[List[Dict[str, str]]]:
    text = (content or "").strip()
    if not text:
        return None
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\[[\s\S]*\]", text)
        if not match:
            return None
        try:
            data = json.loads(match.group(0))
        except json.JSONDecodeError:
            return None
    if not isinstance(data, list):
        return None
    parsed: List[Dict[str, str]] = []
    for item in data:
        if isinstance(item, str) and item.strip():
            parsed.append({"text": item.strip(), "kind": "continue"})
        elif isinstance(item, dict) and (item.get("text") or "").strip():
            kind = item.get("kind")
            if kind not in ("continue", "explore", "detail"):
                kind = "continue"
            parsed.append({"text": str(item["text"]).strip(), "kind": kind})
    return parsed or None


async def generate_follow_up_suggestions(
    user_message: str,
    answer: str,
    movies: List[Dict[str, Any]],
    provider: str = "openai",
    model: str = "gpt-4o-mini",
    *,
    limit: int = 4,
) -> List[Dict[str, str]]:
    """Return up to `limit` follow-up chips (detail + continue + explore)."""
    fallback = _heuristic_follow_ups(user_message, answer, movies, limit=limit)
    use_llm = os.getenv("FOLLOWUP_USE_LLM", "true").lower() not in ("0", "false", "no")

    if not use_llm:
        return fallback

    movie_lines = []
    for m in movies[:6]:
        title = m.get("title") or "?"
        mid = m.get("id")
        genres = m.get("genres")
        g = ", ".join(genres[:3]) if isinstance(genres, list) else str(genres or "")
        movie_lines.append(f"- {title} (id {mid}, {g})")

    prompt = (
        f"Tạo đúng {limit} gợi ý câu hỏi tiếp theo.\n"
        f"- Với mỗi phim trong danh sách, có ít nhất một chip kind=detail: "
        f'"Cho mình biết thêm về phim <tên>".\n'
        f"- kind=continue: Netflix, phim tương tự, so sánh (không dùng '3 phim khác' trừ khi user đã xin nhiều phim).\n"
        f"- Ít nhất 1 kind=explore (chủ đề mới).\n"
        f"Câu hỏi người dùng: {user_message.strip()}\n"
        f"Câu trả lời trợ lý (tóm tắt): {(answer or '')[:800]}\n"
    )
    if movie_lines:
        prompt += "Phim trong kết quả:\n" + "\n".join(movie_lines)

    try:
        llm = get_llm_provider(provider=provider, model=model)
        result = await llm.generate(prompt, system_prompt=FOLLOWUP_SYSTEM)
        parsed = _parse_llm_json(result.get("content") or "")
        if parsed:
            merged = _dedupe(_detail_chips(movies) + parsed + fallback, limit=limit)
            if merged:
                return merged
    except Exception:
        pass

    return fallback
