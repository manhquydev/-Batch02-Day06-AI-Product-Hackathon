"""Async movie tool wrappers for the ReAct agent — all functions are async."""

import asyncio
import json
from typing import Any, Dict, List, Optional

from src.tools.mood_config import ALLOWED_MOODS, MOOD_GENRE_IDS
from src.tools.session_context import get_requested_movie_limit
from src.tools.tmdb_client import TMDbClientError, get_client


def _effective_limit(limit: int) -> int:
    """Honor explicit tool arg, but cap to user-requested count for this turn."""
    requested = get_requested_movie_limit()
    try:
        explicit = max(1, min(int(limit), 10))
    except (TypeError, ValueError):
        explicit = requested
    return min(explicit, requested)


def _json_ok(payload: Dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False)


def _json_error(message: str, **extra: Any) -> str:
    payload = {"error": message}
    payload.update(extra)
    return json.dumps(payload, ensure_ascii=False)


def _handle_errors(fn):
    """Async-aware decorator that catches TMDbClientError and ValueError."""
    async def wrapper(*args, **kwargs):
        try:
            return await fn(*args, **kwargs)
        except TMDbClientError as exc:
            return _json_error(str(exc))
        except ValueError as exc:
            return _json_error(str(exc))

    wrapper.__name__ = fn.__name__
    wrapper.__doc__ = fn.__doc__
    return wrapper


def _pros_cons(detail: Dict[str, Any]) -> Dict[str, List[str]]:
    pros: List[str] = []
    cons: List[str] = []

    rating = detail.get("rating") or 0
    runtime = detail.get("runtime_min") or 0
    vote_count = detail.get("vote_count") or 0

    if rating >= 7.5:
        pros.append(f"Điểm TMDB cao ({rating}/10)")
    elif rating < 6.0 and vote_count > 50:
        cons.append(f"Điểm TMDB thấp ({rating}/10)")

    if vote_count >= 1000:
        pros.append(f"Được {vote_count:,} lượt đánh giá trên TMDB")

    if runtime and runtime <= 100:
        pros.append(f"Thời lượng gọn ({runtime} phút)")
    elif runtime and runtime >= 150:
        cons.append(f"Phim dài ({runtime} phút)")

    if detail.get("plot"):
        pros.append("Có mô tả nội dung từ TMDB")

    if not pros:
        pros.append("Cân nhắc theo sở thích cá nhân")

    return {"pros": pros, "cons": cons}


@_handle_errors
async def search_movies(query: str, limit: int = 5) -> str:
    """Search movies on TMDB by title or keyword."""
    if not query.strip():
        return _json_error("query must not be empty")

    limit = _effective_limit(limit)
    client = get_client()
    movies = await client.search_movies(query, limit=limit)
    return _json_ok({"query": query, "source": "TMDB", "count": len(movies), "movies": movies})


@_handle_errors
async def get_movie_details(movie_id: int) -> str:
    """Return TMDB details for one movie_id."""
    detail = await get_client().get_movie_details(int(movie_id))
    detail["source"] = "TMDB"
    return _json_ok(detail)


@_handle_errors
async def filter_by_mood(mood: str, limit: int = 5) -> str:
    """Discover popular TMDB movies matching a mood via genre mapping."""
    mood_key = mood.strip().lower()
    if mood_key not in ALLOWED_MOODS:
        return _json_error(f"mood must be one of {ALLOWED_MOODS}", received=mood)

    limit = _effective_limit(limit)
    genre_ids = MOOD_GENRE_IDS[mood_key]
    client = get_client()
    movies = await client.discover_by_genres(genre_ids, limit=limit)
    return _json_ok(
        {
            "mood": mood_key,
            "source": "TMDB",
            "genre_ids": genre_ids,
            "count": len(movies),
            "movies": movies,
        }
    )


@_handle_errors
async def get_similar_movies(movie_id: int, limit: int = 5) -> str:
    """Suggest TMDB similar movies for a movie_id."""
    limit = _effective_limit(limit)
    payload = await get_client().similar_movies(int(movie_id), limit=limit)
    payload["source"] = "TMDB"
    payload["count"] = len(payload["movies"])
    return _json_ok(payload)


@_handle_errors
async def check_streaming_availability(movie_id: int, country: str = "VN") -> str:
    """Check TMDB watch/providers for streaming/rent/buy in a country."""
    client = get_client()
    detail = await client.get_movie_details(int(movie_id))
    providers = await client.watch_providers(int(movie_id), country=country)
    providers["title"] = detail["title"]
    providers["source"] = "TMDB"
    return _json_ok(providers)


@_handle_errors
async def get_trending_movies(
    region: str = "VN",
    genre: Optional[str] = None,
    period: str = "week",
) -> str:
    """Fetch trending or popular TMDB movies, optionally filtered by genre."""
    limit = get_requested_movie_limit()
    movies = await get_client().trending_movies(
        region=region,
        genre=genre,
        period=period,
        limit=limit,
    )
    return _json_ok(
        {
            "region": region.upper(),
            "period": period,
            "genre_filter": genre,
            "source": "TMDB",
            "count": len(movies),
            "movies": movies,
        }
    )


@_handle_errors
async def compare_movies(movie_ids: List[int]) -> str:
    """Compare 2-3 TMDB movies using live ratings and metadata (parallel fetch)."""
    if not movie_ids or len(movie_ids) < 2:
        return _json_error("provide 2 or 3 TMDB movie_ids")

    movie_ids = [int(mid) for mid in movie_ids[:3]]
    client = get_client()

    # Parallel fetching of movie details
    details = await asyncio.gather(*[client.get_movie_details(mid) for mid in movie_ids])

    rows = []
    for detail in details:
        extras = _pros_cons(detail)
        rows.append(
            {
                "id": detail["id"],
                "title": detail["title"],
                "rating": detail["rating"],
                "genres": detail["genres"],
                "runtime_min": detail["runtime_min"],
                "vote_count": detail.get("vote_count", 0),
                "pros": extras["pros"],
                "cons": extras["cons"],
            }
        )

    winner = max(rows, key=lambda row: row["rating"])["title"]
    return _json_ok({"source": "TMDB", "comparison": rows, "winner_by_rating": winner})


@_handle_errors
async def search_person(name: str, limit: int = 5) -> str:
    """Search for a person (actor/director) on TMDB by name. Returns person_id, name, and profile."""
    if not name.strip():
        return _json_error("name must not be empty")

    limit = _effective_limit(limit)
    client = get_client()
    people = await client.search_person(name.strip(), limit=limit)
    return _json_ok(
        {
            "query": name,
            "source": "TMDB",
            "count": len(people),
            "people": people,
        }
    )


@_handle_errors
async def get_movie_trailer(movie_id: int) -> str:
    """Fetch YouTube trailer URL for a movie from TMDB."""
    client = get_client()
    videos, detail = await asyncio.gather(
        client.get_movie_videos(int(movie_id)),
        client.get_movie_details(int(movie_id)),
    )

    if not videos["trailer_url"]:
        return _json_ok({
            "movie_id": movie_id,
            "title": detail["title"],
            "source": "TMDB",
            "trailer_url": None,
            "message": "Không tìm thấy trailer YouTube cho phim này.",
        })

    return _json_ok({
        "movie_id": movie_id,
        "title": detail["title"],
        "source": "TMDB",
        "trailer_key": videos["trailer_key"],
        "trailer_url": videos["trailer_url"],
        "trailer_embed_url": videos["trailer_embed_url"],
        "trailer_name": videos["name"],
    })


@_handle_errors
async def get_movies_by_person(person_id: int, role: str = "director", limit: int = 5) -> str:
    """Get list of movies by a person (director or actor). Args: person_id (int), role ('director'|'actor'), limit (int)."""
    role_lower = role.strip().lower()
    if role_lower not in {"director", "actor"}:
        return _json_error("role must be 'director' or 'actor'", received=role)

    limit = _effective_limit(limit)
    client = get_client()
    movies = await client.get_movies_by_person(int(person_id), role=role_lower, limit=limit)
    return _json_ok(
        {
            "person_id": int(person_id),
            "role": role_lower,
            "source": "TMDB",
            "count": len(movies),
            "movies": movies,
        }
    )
