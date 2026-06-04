import ast
import inspect
import json
import re
from typing import Any, Callable, Dict, List, Tuple

from src.tools import movie_tools
from src.tools.session_context import get_excluded_ids, get_requested_movie_limit, is_movie_detail_mode

_LIMIT_ARG_INDEX: Dict[str, int] = {
    "search_movies": 1,
    "filter_by_mood": 1,
    "get_similar_movies": 1,
    "search_person": 1,
    "get_movies_by_person": 2,
}

ToolFn = Callable[..., str]


def _spec(name: str, description: str, fn: ToolFn, example: str) -> Dict[str, Any]:
    return {"name": name, "description": description, "fn": fn, "example": example}


TOOL_SPECS: List[Dict[str, Any]] = [
    _spec(
        "search_movies",
        "Search TMDB by title/keyword. Args: query (str), limit (int, default 5). Returns TMDB movie_id, title, year, genres, rating.",
        movie_tools.search_movies,
        'search_movies("Inception", 5)',
    ),
    _spec(
        "get_movie_details",
        "Get live TMDB details. Args: movie_id (int, TMDB id). Returns plot, runtime, director, cast, rating.",
        movie_tools.get_movie_details,
        "get_movie_details(27205)",
    ),
    _spec(
        "filter_by_mood",
        'Discover TMDB movies by mood via genre mapping. mood: happy, sad, relaxed, excited, romantic, scary. Args: mood (str), limit (int).',
        movie_tools.filter_by_mood,
        'filter_by_mood("romantic", 5)',
    ),
    _spec(
        "get_similar_movies",
        "TMDB similar movies. Args: movie_id (int), limit (int, default 5). Search first if you only know the title.",
        movie_tools.get_similar_movies,
        "get_similar_movies(27205, 5)",
    ),
    _spec(
        "check_streaming_availability",
        'TMDB watch/providers for a country. Args: movie_id (int), country (str ISO, default "VN"). Returns Netflix, Disney+, etc.',
        movie_tools.check_streaming_availability,
        'check_streaming_availability(27205, "VN")',
    ),
    _spec(
        "get_trending_movies",
        'Trending/popular TMDB movies. Args: region (str, default "VN"), genre (str optional, e.g. "Sci-Fi"), period ("day"|"week").',
        movie_tools.get_trending_movies,
        'get_trending_movies("VN", "Sci-Fi", "week")',
    ),
    _spec(
        "compare_movies",
        "Compare 2-3 TMDB movies by live rating/metadata. Args: movie_ids (list of int). Use search_movies to find ids first.",
        movie_tools.compare_movies,
        "compare_movies([27205, 157336, 1124])",
    ),
    _spec(
        "search_person",
        "Search TMDB for a person (actor/director) by name. Args: name (str), limit (int, default 5). Returns person_id, name, profile.",
        movie_tools.search_person,
        'search_person("Tom Hanks", 5)',
    ),
    _spec(
        "get_movies_by_person",
        "Get list of movies by a person. Args: person_id (int, from search_person), role ('director'|'actor', default 'director'), limit (int). Use search_person first to find person_id.",
        movie_tools.get_movies_by_person,
        'get_movies_by_person(2001, "director", 5)',
    ),
    _spec(
        "get_movie_trailer",
        "Get YouTube trailer URL for a movie. Args: movie_id (int, TMDB id). Returns trailer_url and embed_url, or null if unavailable. Use search_movies first if you only have a title.",
        movie_tools.get_movie_trailer,
        "get_movie_trailer(27205)",
    ),
]

TOOL_MAP: Dict[str, ToolFn] = {spec["name"]: spec["fn"] for spec in TOOL_SPECS}


def parse_action(action_line: str) -> Tuple[str, List[Any]]:
    """Parse tool_name(arg1, arg2) into name and Python args."""
    text = action_line.strip()
    try:
        node = ast.parse(text, mode="eval").body
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            args = [ast.literal_eval(ast.unparse(arg)) for arg in node.args]
            return node.func.id, args
    except (SyntaxError, ValueError):
        pass

    match = re.match(r"^(\w+)\((.*)\)\s*$", text, re.DOTALL)
    if not match:
        raise ValueError(f"Invalid action format: {action_line}")

    name = match.group(1)
    args_blob = match.group(2).strip()
    if not args_blob:
        return name, []

    return name, [args_blob.strip("\"'")]


def _apply_requested_limit_to_args(tool_name: str, args: List[Any]) -> List[Any]:
    """Force tool limit arg to match the count the user asked for this turn."""
    idx = _LIMIT_ARG_INDEX.get(tool_name)
    if idx is None:
        return args
    args = list(args)
    while len(args) <= idx:
        args.append(get_requested_movie_limit())
    args[idx] = get_requested_movie_limit()
    return args


def _finalize_tool_observation(observation: str) -> str:
    """Cap movie lists and drop session duplicates."""
    try:
        data = json.loads(observation)
    except (json.JSONDecodeError, TypeError):
        return observation
    if not isinstance(data, dict) or data.get("error"):
        return observation

    changed = False
    cap = get_requested_movie_limit()
    exclude = get_excluded_ids()

    for key in ("movies",):
        items = data.get(key)
        if not isinstance(items, list):
            continue
        filtered = [
            m for m in items if isinstance(m, dict) and (not exclude or m.get("id") not in exclude)
        ]
        if len(filtered) > cap:
            filtered = filtered[:cap]
        if filtered != items:
            data[key] = filtered
            changed = True

    comparison = data.get("comparison")
    if isinstance(comparison, list):
        filtered_cmp = [
            m for m in comparison if isinstance(m, dict) and (not exclude or m.get("id") not in exclude)
        ]
        if len(filtered_cmp) > cap:
            filtered_cmp = filtered_cmp[:cap]
        if filtered_cmp != comparison:
            data["comparison"] = filtered_cmp
            changed = True

    if isinstance(data.get("movies"), list):
        data["count"] = len(data["movies"])
    if changed:
        if exclude:
            data["session_exclusions_applied"] = True
            data["excluded_ids_in_session"] = sorted(exclude)
        data["requested_limit"] = cap
    return json.dumps(data, ensure_ascii=False)


_LIST_TOOLS_IN_DETAIL_MODE = frozenset({"get_trending_movies", "filter_by_mood"})


async def execute_tool(tool_name: str, args: List[Any]) -> str:
    """Execute a registered tool by name. Supports both sync and async tool functions."""
    fn = TOOL_MAP.get(tool_name)
    if not fn:
        available = ", ".join(TOOL_MAP.keys())
        return json.dumps({"error": f"Tool {tool_name} not found. Available: {available}"})

    if is_movie_detail_mode() and tool_name in _LIST_TOOLS_IN_DETAIL_MODE:
        return json.dumps(
            {
                "error": (
                    "Detail mode: user asked about one specific film. "
                    "Use search_movies(title, 1) then get_movie_details(movie_id) instead."
                )
            }
        )

    try:
        args = _apply_requested_limit_to_args(tool_name, args)
        result = fn(*args)
        # Await if the tool function is a coroutine
        if inspect.isawaitable(result):
            result = await result
        return _finalize_tool_observation(result)
    except TypeError as exc:
        return json.dumps({"error": f"Invalid arguments for {tool_name}: {exc}"})
    except Exception as exc:
        return json.dumps({"error": f"Tool execution failed: {exc}"})
