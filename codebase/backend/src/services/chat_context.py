"""Build agent input from session history + optional summary."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from src.services.session_store import RECENT_TURNS_AFTER_SUMMARY, TURN_LIMIT, ChatSession, ChatTurn
from src.utils.request_intent import (
    extract_target_movie_title,
    is_movie_detail_request,
    is_movie_review_request,
)
from src.utils.request_limits import parse_requested_movie_count


def format_turn(turn: ChatTurn) -> str:
    lines = [f"Người dùng: {turn.user}", f"Trợ lý: {turn.assistant}"]
    if turn.movies:
        labels = []
        for movie in turn.movies[:12]:
            title = movie.get("title") or "?"
            mid = movie.get("id")
            genres = movie.get("genres")
            genre_text = ""
            if isinstance(genres, list) and genres:
                genre_text = f", thể loại: {', '.join(str(g) for g in genres[:3])}"
            labels.append(f"{title} (TMDB id {mid}{genre_text})" if mid else str(title))
        lines.append(f"Phim đã gợi ý trong lượt này: {'; '.join(labels)}")
    return "\n".join(lines)


def format_turns(turns: List[ChatTurn]) -> str:
    if not turns:
        return ""
    return "\n\n".join(format_turn(t) for t in turns)


def build_context_prefix(session: ChatSession) -> str:
    """Context from completed turns (not including the new user message)."""
    parts = []

    if session.turn_count > 0:
        if session.turn_count < TURN_LIMIT:
            block = format_turns(session.turns)
            if block:
                parts.append(f"[Ngữ cảnh cuộc trò chuyện]\n{block}")
        else:
            if session.summary:
                parts.append(f"[Tóm tắt các lượt trước]\n{session.summary}")
            recent = session.turns[-RECENT_TURNS_AFTER_SUMMARY:]
            if recent:
                parts.append(f"[Vài lượt gần nhất]\n{format_turns(recent)}")

    if session.rejected_movie_ids:
        ids_str = ", ".join(str(mid) for mid in sorted(session.rejected_movie_ids))
        parts.append(f"[Phim đã từ chối - KHÔNG GỢI Ý LẠI]\nID TMDB: {ids_str}")

    return "\n\n".join(parts)


def is_follow_up_message(message: str) -> bool:
    normalized = message.strip().lower()
    cues = (
        "khác",
        "khac",
        "nữa",
        "nua",
        "thêm",
        "them",
        "tiếp",
        "tiep",
        "còn",
        "con ",
        "nữa đi",
        "other",
        "more",
        "another",
    )
    return any(cue in normalized for cue in cues)


def build_agent_input(context_prefix: str, message: str, session: Optional[ChatSession] = None) -> str:
    if not context_prefix.strip():
        return message

    exclude_ids: List[int] = session.suggested_movie_ids() if session else []
    requested_n = parse_requested_movie_count(message)
    rules = [
        "Trả lời dựa trên ngữ cảnh phiên chat và câu hỏi mới nhất.",
        "Nếu người dùng nói 'phim khác', 'thêm', 'nữa' — giữ cùng thể loại/mood như lượt trước nhưng gợi ý phim TMDB khác.",
    ]
    if is_movie_review_request(message):
        rules.append(
            "Đây là câu hỏi về REVIEW người dùng TMDB: dùng get_reviews(movie_id), không dùng get_movie_details hay danh sách phim mới."
        )
    elif is_movie_detail_request(message):
        rules.append(
            "Đây là câu hỏi chi tiết về MỘT phim: không trả về carousel nhiều phim; chỉ một phim trong Final Answer."
        )
    elif requested_n is not None:
        rules.append(
            f"Người dùng yêu cầu đúng {requested_n} phim: mọi tool có tham số limit phải dùng limit={requested_n}, "
            f"Final Answer chỉ liệt kê đúng {requested_n} phim (không thêm)."
        )
    if exclude_ids:
        rules.append(
            f"Không gợi ý lại các TMDB id đã đưa trong phiên: {', '.join(str(i) for i in exclude_ids)}. "
            "Dùng search/discover/trending với từ khóa hoặc page khác để lấy kết quả mới."
        )
    if is_follow_up_message(message):
        rules.append(
            "Đây là câu hỏi tiếp theo trong cùng phiên: ưu tiên cùng chủ đề/thể loại với các lượt trước, "
            "chỉ đổi danh sách phim."
        )

    return (
        f"{context_prefix.strip()}\n\n"
        f"[Câu hỏi mới nhất của người dùng]\n{message.strip()}\n\n"
        + " ".join(rules)
    )


def _review_instruction_block(message: str, session: Optional[ChatSession]) -> str:
    if not is_movie_review_request(message):
        return ""

    title = extract_target_movie_title(message)
    movie = session.find_movie_by_title(title) if session and title else None

    lines = [
        "[Yêu cầu: review / nhận xét người dùng TMDB cho MỘT phim — không gợi ý danh sách phim khác]",
        "Dùng get_reviews(movie_id, 2) sau khi đã có id; Final Answer dịch đầy đủ nội dung review sang tiếng Việt (tên tác giả + toàn bộ ý kiến).",
        "Không gọi get_trending_movies, filter_by_mood hay get_movie_details thay cho review.",
    ]
    if movie and movie.get("id"):
        lines.append(
            f'Phim người dùng đang hỏi review: "{movie.get("title")}" — TMDB id {movie["id"]}. '
            f"Ưu tiên: Action: get_reviews({movie['id']}, 2)"
        )
    elif title:
        lines.append(
            f'Phim người dùng đang hỏi review (theo tên): "{title}". '
            f'Ưu tiên: Action: search_movies("{title}", 1) rồi get_reviews(id, 2).'
        )
    return "\n".join(lines) + "\n\n"


def _detail_instruction_block(message: str, session: Optional[ChatSession]) -> str:
    if not is_movie_detail_request(message):
        return ""

    title = extract_target_movie_title(message)
    movie = session.find_movie_by_title(title) if session and title else None

    lines = [
        "[Yêu cầu: mô tả chi tiết MỘT bộ phim — không gợi ý danh sách 3–5 phim khác]",
        "Dùng get_movie_details(movie_id) sau khi đã có id; Final Answer chỉ nói về một phim (nội dung, đạo diễn, diễn viên, điểm TMDB).",
        "Không gọi get_trending_movies hay filter_by_mood cho câu này.",
    ]
    if movie and movie.get("id"):
        lines.append(
            f'Phim người dùng đang hỏi: "{movie.get("title")}" — TMDB id {movie["id"]}. '
            f"Ưu tiên: Action: get_movie_details({movie['id']})"
        )
    elif title:
        lines.append(
            f'Phim người dùng đang hỏi (theo tên): "{title}". '
            f'Ưu tiên: Action: search_movies("{title}", 1) rồi get_movie_details(id).'
        )
    return "\n".join(lines) + "\n\n"


async def prepare_session_turn(
    session: ChatSession,
    message: str,
    provider: str,
    model: str,
    summarize_fn,
) -> Tuple[str, str, bool]:
    """
    Returns (agent_input, latest_user_message_for_guard, did_summarize).
    """
    summarized = False
    if session.turn_count >= TURN_LIMIT and (
        session.summary is None or session.turn_count % TURN_LIMIT == 0
    ):
        session.summary = await summarize_fn(session.turns, provider, model)
        summarized = True

    prefix = build_context_prefix(session)
    agent_input = build_agent_input(prefix, message, session)
    review_block = _review_instruction_block(message, session)
    if review_block:
        agent_input = review_block + agent_input
    else:
        detail_block = _detail_instruction_block(message, session)
        if detail_block:
            agent_input = detail_block + agent_input
    return agent_input, message, summarized
