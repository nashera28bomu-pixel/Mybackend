"""
Trending Router — 100% TMDB powered
Cymor Movie Hub v2
"""
from fastapi import APIRouter, HTTPException, Query
import asyncio, logging
from utils.cache import cache
from utils.tmdb import tmdb_get, fmt_movie, fmt_series

logger = logging.getLogger("cymor.trending")
router = APIRouter()


@router.get("/")
async def trending(time_window: str = Query("week", regex="^(day|week)$")):
    key = f"trend:all:{time_window}"
    if cached := await cache.get(key): return cached
    try:
        mv, tv = await asyncio.gather(
            tmdb_get(f"/trending/movie/{time_window}"),
            tmdb_get(f"/trending/tv/{time_window}"),
        )
        response = {
            "movies": [fmt_movie(m) for m in mv.get("results", [])],
            "series": [fmt_series(s) for s in tv.get("results", [])],
        }
        await cache.set(key, response, ttl=1800)
        return response
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/movies")
async def trending_movies(time_window: str = Query("week", regex="^(day|week)$")):
    key = f"trend:movies:{time_window}"
    if cached := await cache.get(key): return cached
    try:
        data = await tmdb_get(f"/trending/movie/{time_window}")
        r = {"movies": [fmt_movie(m) for m in data.get("results", [])]}
        await cache.set(key, r, ttl=1800)
        return r
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/series")
async def trending_series(time_window: str = Query("week", regex="^(day|week)$")):
    key = f"trend:series:{time_window}"
    if cached := await cache.get(key): return cached
    try:
        data = await tmdb_get(f"/trending/tv/{time_window}")
        r = {"series": [fmt_series(s) for s in data.get("results", [])]}
        await cache.set(key, r, ttl=1800)
        return r
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/popular/movies")
async def popular_movies():
    key = "pop:movies"
    if cached := await cache.get(key): return cached
    try:
        data = await tmdb_get("/movie/popular")
        r = {"movies": [fmt_movie(m) for m in data.get("results", [])]}
        await cache.set(key, r, ttl=3600)
        return r
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/popular/series")
async def popular_series():
    key = "pop:series"
    if cached := await cache.get(key): return cached
    try:
        data = await tmdb_get("/tv/popular")
        r = {"series": [fmt_series(s) for s in data.get("results", [])]}
        await cache.set(key, r, ttl=3600)
        return r
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/top-rated/movies")
async def top_rated_movies():
    key = "top:movies"
    if cached := await cache.get(key): return cached
    try:
        data = await tmdb_get("/movie/top_rated")
        r = {"movies": [fmt_movie(m) for m in data.get("results", [])]}
        await cache.set(key, r, ttl=7200)
        return r
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/top-rated/series")
async def top_rated_series():
    key = "top:series"
    if cached := await cache.get(key): return cached
    try:
        data = await tmdb_get("/tv/top_rated")
        r = {"series": [fmt_series(s) for s in data.get("results", [])]}
        await cache.set(key, r, ttl=7200)
        return r
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/genres/movies")
async def by_genre(genre_id: int = Query(...), page: int = Query(1, ge=1)):
    key = f"genre:{genre_id}:{page}"
    if cached := await cache.get(key): return cached
    try:
        data = await tmdb_get("/discover/movie", {"with_genres": genre_id, "page": page, "sort_by": "popularity.desc"})
        r = {"genre_id": genre_id, "page": page, "total_pages": data.get("total_pages"), "movies": [fmt_movie(m) for m in data.get("results", [])]}
        await cache.set(key, r, ttl=3600)
        return r
    except Exception as e:
        raise HTTPException(500, str(e))
