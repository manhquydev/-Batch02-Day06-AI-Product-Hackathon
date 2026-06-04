"""Extract movie data from ReAct trace observations."""
import json
from typing import Any, Dict, List


def extract_movies_from_trace(trace: List[Dict[str, Any]] | None) -> List[Dict[str, Any]]:
    movies: List[Dict[str, Any]] = []
    seen_ids: set = set()
    if not trace:
        return movies
    for step in trace:
        obs_raw = step.get("observation")
        if not obs_raw:
            continue
        try:
            obs = json.loads(obs_raw)
        except (json.JSONDecodeError, TypeError):
            continue
        if obs.get("poster_url") and obs.get("id") not in seen_ids:
            movies.append(obs)
            seen_ids.add(obs["id"])
        for key in ("movies", "comparison"):
            for m in obs.get(key, []):
                if isinstance(m, dict) and m.get("poster_url") and m.get("id") not in seen_ids:
                    movies.append(m)
                    seen_ids.add(m["id"])
    return movies
