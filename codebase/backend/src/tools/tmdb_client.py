"""Async TMDB API client using httpx with in-memory TTL caching."""

import asyncio
import hashlib
import json
import os
from typing import Any, Dict, List, Optional, Set, Tuple

from src.utils.title_match import rank_search_results

import httpx
from cachetools import TTLCache

TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p"
DEFAULT_LANGUAGE = os.getenv("TMDB_LANGUAGE", "vi-VN")
DEFAULT_REGION = os.getenv("TMDB_REGION", "VN")
TMDB_MAX_RETRIES = max(1, int(os.getenv("TMDB_MAX_RETRIES", "3")))
TMDB_RETRY_BACKOFF_SEC = float(os.getenv("TMDB_RETRY_BACKOFF_SEC", "0.6"))

# In-memory TTL caches — shared across requests within the same process
_details_cache: TTLCache = TTLCache(maxsize=512, ttl=3600)       # movie details: 1 hour
_search_cache: TTLCache = TTLCache(maxsize=256, ttl=1800)        # search results: 30 min
_trending_cache: TTLCache = TTLCache(maxsize=64, ttl=1800)       # trending: 30 min
_providers_cache: TTLCache = TTLCache(maxsize=256, ttl=3600)     # watch providers: 1 hour
_videos_cache: TTLCache = TTLCache(maxsize=256, ttl=3600)        # movie videos: 1 hour


def _cache_key(path: str, params: Dict[str, Any]) -> str:
    """Generate a deterministic cache key from path + sorted query params."""
    raw = f"{path}|{json.dumps(params, sort_keys=True)}"
    return hashlib.md5(raw.encode()).hexdigest()


class TMDbClientError(Exception):
    """Raised when TMDB API calls fail."""


class TMDbClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        language: str = DEFAULT_LANGUAGE,
        region: str = DEFAULT_REGION,
        timeout: int = 15,
    ):
        self.api_key = api_key or os.getenv("TMDB_API_KEY")
        self.language = language
        self.region = region
        self.timeout = timeout
        self._genre_names: Dict[int, str] = {}
        self._http_client: Optional[httpx.AsyncClient] = None

    def _require_api_key(self) -> str:
        if not self.api_key:
            raise TMDbClientError(
                "TMDB_API_KEY chưa được cấu hình. "
                "Đăng ký miễn phí tại https://www.themoviedb.org/settings/api "
                "và thêm vào file .env."
            )
        return self.api_key

    def _get_http_client(self) -> httpx.AsyncClient:
        """Lazy-create a shared async HTTP client for connection pooling."""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(
                base_url=TMDB_BASE_URL,
                timeout=self.timeout,
            )
        return self._http_client

    async def _get(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        cache: Optional[TTLCache] = None,
    ) -> Dict[str, Any]:
        query = dict(params or {})
        query["api_key"] = self._require_api_key()
        query.setdefault("language", self.language)

        # Check cache first
        if cache is not None:
            key = _cache_key(path, query)
            if key in cache:
                return cache[key]

        client = self._get_http_client()
        last_request_error: Optional[httpx.RequestError] = None
        for attempt in range(1, TMDB_MAX_RETRIES + 1):
            try:
                response = await client.get(path, params=query)
                response.raise_for_status()
                break
            except httpx.HTTPStatusError as exc:
                msg = str(exc)
                try:
                    payload = exc.response.json()
                    if isinstance(payload, dict):
                        msg = payload.get("status_message") or payload.get("errors") or msg
                except Exception:
                    pass
                raise TMDbClientError(f"TMDB request failed ({exc.response.status_code}): {msg}") from exc
            except httpx.RequestError as exc:
                last_request_error = exc
                if attempt < TMDB_MAX_RETRIES:
                    await asyncio.sleep(TMDB_RETRY_BACKOFF_SEC * attempt)
                    continue
        else:
            exc = last_request_error
            assert exc is not None
            err_msg = str(exc) or "Không thể kết nối (Connection blocked/reset)"
            raise TMDbClientError(f"TMDB network error: {type(exc).__name__} - {err_msg}") from exc

        payload = response.json()
        if isinstance(payload, dict) and payload.get("success") is False:
            message = payload.get("status_message") or payload.get("errors") or "Unknown TMDB error"
            raise TMDbClientError(str(message))

        # Store in cache
        if cache is not None:
            cache[key] = payload

        return payload

    async def load_genre_names(self) -> Dict[int, str]:
        if self._genre_names:
            return self._genre_names
        data = await self._get("/genre/movie/list", cache=_details_cache)
        self._genre_names = {g["id"]: g["name"] for g in data.get("genres", [])}
        return self._genre_names

    async def genre_names(self, genre_ids: List[int]) -> List[str]:
        names = await self.load_genre_names()
        return [names.get(gid, str(gid)) for gid in genre_ids]

    @staticmethod
    def _year(release_date: str) -> Optional[int]:
        if release_date and len(release_date) >= 4:
            return int(release_date[:4])
        return None

    def _session_exclude(self) -> tuple[Set[int], int]:
        try:
            from src.tools.session_context import get_discover_start_page, get_excluded_ids

            return get_excluded_ids(), get_discover_start_page()
        except Exception:
            return set(), 1

    async def _pick_unique_summaries(
        self,
        raw_movies: List[Dict[str, Any]],
        limit: int,
        exclude: Set[int],
    ) -> List[Dict[str, Any]]:
        picked: List[Dict[str, Any]] = []
        for movie in raw_movies:
            mid = movie.get("id")
            if mid is not None and int(mid) in exclude:
                continue
            picked.append(await self.summarize(movie))
            if len(picked) >= limit:
                break
        return picked

    async def summarize(self, movie: Dict[str, Any]) -> Dict[str, Any]:
        raw_genre_ids = movie.get("genre_ids") or []
        if raw_genre_ids:
            # Search/discover endpoints return genre_ids as [28, 12, ...]
            genre_ids = raw_genre_ids if isinstance(raw_genre_ids[0], int) else [g["id"] for g in raw_genre_ids]
        elif movie.get("genres"):
            genre_ids = [g["id"] for g in movie["genres"]]
        else:
            genre_ids = []

        genres = await self.genre_names(genre_ids) if genre_ids else []
        if not genres and movie.get("genres"):
            genres = [g["name"] for g in movie["genres"]]

        return {
            "id": movie["id"],
            "title": movie.get("title") or movie.get("original_title"),
            "year": self._year(movie.get("release_date", "")),
            "genres": genres,
            "rating": round(float(movie.get("vote_average") or 0), 1),
            "poster_url": f"{TMDB_IMAGE_BASE}/w500{movie['poster_path']}" if movie.get("poster_path") else None,
            "backdrop_url": f"{TMDB_IMAGE_BASE}/w1280{movie['backdrop_path']}" if movie.get("backdrop_path") else None,
        }

    async def search_movies(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        exclude, start_page = self._session_exclude()
        limit = max(1, min(int(limit), 10))
        query = query.strip()
        ranked_pool: List[Tuple[float, Dict[str, Any]]] = []
        seen_ids: Set[int] = set()

        for page in range(start_page, start_page + 5):
            data = await self._get(
                "/search/movie",
                {"query": query, "include_adult": "false", "page": page},
                cache=_search_cache,
            )
            for score, movie in rank_search_results(data.get("results", []), query):
                mid = movie.get("id")
                if mid is None or mid in seen_ids or mid in exclude:
                    continue
                seen_ids.add(mid)
                ranked_pool.append((score, movie))

            if page >= data.get("total_pages", page):
                break

        ranked_pool.sort(key=lambda pair: pair[0], reverse=True)

        picked: List[Dict[str, Any]] = []
        for _score, movie in ranked_pool[: limit * 2]:
            if movie.get("id") in exclude:
                continue
            picked.append(await self.summarize(movie))
            if len(picked) >= limit:
                break
        return picked

    async def get_movie_details(self, movie_id: int) -> Dict[str, Any]:
        data = await self._get(
            f"/movie/{int(movie_id)}",
            {"append_to_response": "credits"},
            cache=_details_cache,
        )

        director = next(
            (
                person["name"]
                for person in data.get("credits", {}).get("crew", [])
                if person.get("job") == "Director"
            ),
            None,
        )
        cast = [
            person["name"]
            for person in data.get("credits", {}).get("cast", [])[:5]
        ]

        return {
            "id": data["id"],
            "title": data.get("title") or data.get("original_title"),
            "year": self._year(data.get("release_date", "")),
            "genres": [g["name"] for g in data.get("genres", [])],
            "runtime_min": data.get("runtime"),
            "rating": round(float(data.get("vote_average") or 0), 1),
            "vote_count": data.get("vote_count", 0),
            "director": director,
            "cast": cast,
            "plot": data.get("overview") or "",
            "original_language": data.get("original_language"),
            "poster_url": f"{TMDB_IMAGE_BASE}/w500{data['poster_path']}" if data.get("poster_path") else None,
            "backdrop_url": f"{TMDB_IMAGE_BASE}/w1280{data['backdrop_path']}" if data.get("backdrop_path") else None,
        }

    async def discover_by_genres(
        self,
        genre_ids: List[int],
        limit: int = 5,
        region: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        exclude, start_page = self._session_exclude()
        limit = max(1, min(int(limit), 10))
        picked: List[Dict[str, Any]] = []
        base_params = {
            "with_genres": ",".join(str(g) for g in genre_ids),
            "sort_by": "popularity.desc",
            "include_adult": "false",
            "vote_count.gte": 100,
            "region": (region or self.region).upper(),
        }
        for page in range(start_page, start_page + 5):
            data = await self._get(
                "/discover/movie",
                {**base_params, "page": page},
                cache=_trending_cache,
            )
            batch = await self._pick_unique_summaries(
                data.get("results", []),
                limit - len(picked),
                exclude,
            )
            picked.extend(batch)
            if len(picked) >= limit:
                return picked[:limit]
            if page >= data.get("total_pages", page):
                break
        return picked

    async def similar_movies(self, movie_id: int, limit: int = 5) -> Dict[str, Any]:
        exclude, start_page = self._session_exclude()
        limit = max(1, min(int(limit), 10))
        source = await self.get_movie_details(movie_id)
        exclude = set(exclude) | {int(movie_id)}
        picked: List[Dict[str, Any]] = []
        for page in range(start_page, start_page + 5):
            data = await self._get(
                f"/movie/{int(movie_id)}/similar",
                {"page": page},
                cache=_search_cache,
            )
            batch = await self._pick_unique_summaries(
                data.get("results", []),
                limit - len(picked),
                exclude,
            )
            picked.extend(batch)
            if len(picked) >= limit:
                break
            if page >= data.get("total_pages", page):
                break
        return {"source": source["title"], "movies": picked[:limit]}

    async def watch_providers(self, movie_id: int, country: str = DEFAULT_REGION) -> Dict[str, Any]:
        data = await self._get(f"/movie/{int(movie_id)}/watch/providers", cache=_providers_cache)
        country_key = country.upper()
        country_data = data.get("results", {}).get(country_key, {})
        providers: Dict[str, List[str]] = {
            "flatrate": [],
            "rent": [],
            "buy": [],
        }

        for bucket in providers:
            for item in country_data.get(bucket, []) or []:
                name = item.get("provider_name")
                if name and name not in providers[bucket]:
                    providers[bucket].append(name)

        available = providers["flatrate"] + providers["rent"]
        return {
            "movie_id": movie_id,
            "country": country_key,
            "link": country_data.get("link"),
            "streaming": providers["flatrate"],
            "rent": providers["rent"],
            "buy": providers["buy"],
            "available_on": available,
        }

    async def trending_movies(
        self,
        region: str = DEFAULT_REGION,
        genre: Optional[str] = None,
        period: str = "week",
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        period_key = period if period in {"day", "week"} else "week"

        if genre:
            from src.tools.mood_config import GENRE_NAME_TO_ID

            genre_id = GENRE_NAME_TO_ID.get(genre.strip().lower())
            if not genre_id:
                raise TMDbClientError(
                    f"Unknown genre '{genre}'. Examples: Sci-Fi, Action, Romance, Horror."
                )
            return await self.discover_by_genres([genre_id], limit=limit, region=region)

        exclude, start_page = self._session_exclude()
        picked: List[Dict[str, Any]] = []
        for page in range(start_page, start_page + 3):
            data = await self._get(
                f"/trending/movie/{period_key}",
                {"region": region.upper(), "page": page},
                cache=_trending_cache,
            )
            batch = await self._pick_unique_summaries(
                data.get("results", []),
                limit - len(picked),
                exclude,
            )
            picked.extend(batch)
            if len(picked) >= limit:
                return picked[:limit]

        if region.upper() != "US":
            for page in range(start_page, start_page + 5):
                regional = await self._get(
                    "/discover/movie",
                    {
                        "sort_by": "popularity.desc",
                        "region": region.upper(),
                        "include_adult": "false",
                        "page": page,
                    },
                    cache=_trending_cache,
                )
                batch = await self._pick_unique_summaries(
                    regional.get("results", []),
                    limit - len(picked),
                    exclude,
                )
                picked.extend(batch)
                if len(picked) >= limit:
                    return picked[:limit]
                if page >= regional.get("total_pages", page):
                    break

        return picked[:limit]

    async def search_person(self, name: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for a person (actor/director) on TMDB by name."""
        data = await self._get(
            "/search/person",
            {"query": name.strip(), "include_adult": "false", "page": 1},
            cache=_search_cache,
        )
        results = data.get("results", [])[:limit]
        return [
            {
                "id": person["id"],
                "name": person.get("name", ""),
                "known_for_department": person.get("known_for_department", ""),
                "profile_path": f"{TMDB_IMAGE_BASE}/w500{person['profile_path']}"
                if person.get("profile_path")
                else None,
                "popularity": person.get("popularity", 0),
            }
            for person in results
        ]

    async def get_movie_videos(self, movie_id: int) -> Dict[str, Any]:
        """Fetch movie videos from TMDB, returning the best YouTube trailer."""
        data = await self._get(f"/movie/{int(movie_id)}/videos", cache=_videos_cache)
        results = data.get("results", [])

        # Priority: official YouTube trailers → any YouTube trailers → any YouTube video
        trailers = [v for v in results if v.get("site") == "YouTube" and v.get("type") == "Trailer" and v.get("official")]
        if not trailers:
            trailers = [v for v in results if v.get("site") == "YouTube" and v.get("type") == "Trailer"]
        if not trailers:
            trailers = [v for v in results if v.get("site") == "YouTube"]

        best = trailers[0] if trailers else None
        best_key = best.get("key") if best else None
        return {
            "movie_id": movie_id,
            "trailer_key": best_key,
            "trailer_url": f"https://www.youtube.com/watch?v={best_key}" if best_key else None,
            "trailer_embed_url": f"https://www.youtube.com/embed/{best_key}" if best_key else None,
            "name": best.get("name") if best else None,
        }

    async def get_movies_by_person(
        self, person_id: int, role: str = "director", limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Get movies for a person by role (director or actor)."""
        role_lower = role.strip().lower()
        if role_lower not in {"director", "actor"}:
            raise TMDbClientError(f"role must be 'director' or 'actor', got '{role}'")

        data = await self._get(
            f"/person/{int(person_id)}",
            {"append_to_response": "movie_credits"},
            cache=_details_cache,
        )

        movie_credits = data.get("movie_credits", {})

        if role_lower == "director":
            # Get crew entries where job is "Director"
            crew = movie_credits.get("crew", [])
            movie_ids = [
                m["id"]
                for m in crew
                if m.get("job") == "Director" and m.get("id")
            ]
        else:  # actor
            # Get cast entries
            cast = movie_credits.get("cast", [])
            movie_ids = [m["id"] for m in cast if m.get("id")]

        # Fetch details for each movie in parallel
        async def _safe_detail(mid: int) -> Optional[Dict[str, Any]]:
            try:
                return await self.get_movie_details(mid)
            except TMDbClientError:
                return None

        exclude, _ = self._session_exclude()
        results = await asyncio.gather(*[_safe_detail(mid) for mid in movie_ids[:limit]])
        return [r for r in results if r is not None and r.get("id") not in exclude]


_client: Optional[TMDbClient] = None


def get_client(language: Optional[str] = None) -> TMDbClient:
    """Get or create a singleton TMDbClient. Pass language to override locale."""
    global _client
    if _client is None:
        _client = TMDbClient(language=language or DEFAULT_LANGUAGE)
    elif language and _client.language != language:
        _client = TMDbClient(language=language)
    return _client
