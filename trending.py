"""
Trending Router — Cymor Movie Hub
Returns trending movies and series by running searches
on popular titles and caching the results aggressively.
"""

from fastapi import APIRouter, HTTPException
import asyncio
import logging

from utils.cache import cache
from utils.serializers import serialize_search_item

logger = logging.getLogger("cymor.trending")
router = APIRouter()

# Curated popular titles used to build a trending list
TRENDING_MOVIES = [
    "avengers endgame",
    "black panther",
    "inception",
    "interstellar",
    "the dark knight",
]

TRENDING_SERIES = [
    "breaking bad",
    "game of thrones",
    "stranger things",
    "the witcher",
    "money heist",
]


async def _fetch_first_result(query: str, subject_type) -> dict | None:
    """Fetch the top result for a given query."""
    try:
        from moviebox_api.v1.core import Search, Session

        session = Session()
        search = Search(session, query=query, subject_type=subject_type, per_page=1)
        results = await asyncio.to_thread(search.get_content_model_sync)
        if results.items:
            item = serialize_search_item(results.first_item)
            item["trending_query"] = query
            return item
    except Exception as e:
        logger.warning(f"Trending fetch failed for '{query}': {e}")
    return None


@router.get("/")
async def get_trending():
    """
    Get trending movies and TV series.
    Results are cached for 1 hour to keep the free tier happy.

    Example: GET /api/trending
    """
    cache_key = "trending:all"
    cached = await cache.get(cache_key)
    if cached:
        return cached

    try:
        from moviebox_api.v1.core import SubjectType

        # Fetch movies and series in parallel
        movie_tasks = [_fetch_first_result(q, SubjectType.MOVIES) for q in TRENDING_MOVIES]
        series_tasks = [_fetch_first_result(q, SubjectType.TV_SERIES) for q in TRENDING_SERIES]

        movie_results, series_results = await asyncio.gather(
            asyncio.gather(*movie_tasks),
            asyncio.gather(*series_tasks),
        )

        response = {
            "movies": [r for r in movie_results if r],
            "series": [r for r in series_results if r],
        }

        await cache.set(cache_key, response, ttl=3600)  # 1 hour cache
        return response

    except Exception as e:
        logger.error(f"Trending endpoint error: {e}")
        raise HTTPException(status_code=500, detail=f"Could not load trending content: {str(e)}")


@router.get("/movies")
async def get_trending_movies():
    """Trending movies only."""
    all_trending = await get_trending()
    return {"movies": all_trending.get("movies", [])}


@router.get("/series")
async def get_trending_series():
    """Trending TV series only."""
    all_trending = await get_trending()
    return {"series": all_trending.get("series", [])}
