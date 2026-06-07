"""
Movies Router — TMDB metadata + YTS clean torrent sources
Cymor Movie Hub v2 | No ads. No iframes. Always a winner.
"""
from fastapi import APIRouter, HTTPException, Query
import logging

from utils.cache import cache
from utils.tmdb import tmdb_get, fmt_movie, fmt_details
from utils.scraper import get_movie_sources

logger = logging.getLogger("cymor.movies")
router = APIRouter()


@router.get("/search")
async def search_movies(
    q:    str = Query(..., min_length=1),
    page: int = Query(1, ge=1, le=500),
):
    """Search movies via TMDB — instant, reliable, full posters & metadata."""
    key = f"mv:search:{q.lower().strip()}:{page}"
    if cached := await cache.get(key): return cached
    try:
        data = await tmdb_get("/search/movie", {"query": q.strip(), "page": page, "include_adult": False})
        response = {
            "query":       q,
            "page":        page,
            "total_pages": data.get("total_pages", 1),
            "total":       data.get("total_results", 0),
            "has_more":    page < data.get("total_pages", 1),
            "results":     [fmt_movie(m) for m in data.get("results", [])],
        }
        await cache.set(key, response, ttl=600)
        return response
    except Exception as e:
        logger.error(f"Movie search: {e}")
        raise HTTPException(500, str(e))


@router.get("/{tmdb_id}")
async def movie_details(tmdb_id: int):
    """Full movie details from TMDB — cast, trailer, genres, runtime."""
    key = f"mv:detail:{tmdb_id}"
    if cached := await cache.get(key): return cached
    try:
        data = await tmdb_get(f"/movie/{tmdb_id}", {"append_to_response": "credits,videos,external_ids"})
        response = fmt_details(data, "movie")
        await cache.set(key, response, ttl=1800)
        return response
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/{tmdb_id}/sources")
async def movie_sources(tmdb_id: int):
    """
    Get clean torrent/magnet sources for a movie via YTS API.
    Returns 720p / 1080p / 2160p magnet links — stream with WebTorrent
    or download the .torrent file. Zero ads. Zero iframes.
    """
    key = f"mv:sources:{tmdb_id}"
    if cached := await cache.get(key): return cached
    try:
        # Get IMDB ID from TMDB
        detail = await tmdb_get(f"/movie/{tmdb_id}", {"append_to_response": "external_ids"})
        imdb_id = detail.get("imdb_id") or detail.get("external_ids", {}).get("imdb_id")
        title   = detail.get("title", "")
        year    = (detail.get("release_date") or "")[:4]

        sources = await get_movie_sources(imdb_id, title, year)
        response = {
            "tmdb_id": tmdb_id,
            "imdb_id": imdb_id,
            "title":   title,
            "year":    year,
            **sources,
        }
        ttl = 3600 if sources["found"] else 300
        await cache.set(key, response, ttl=ttl)
        return response
    except Exception as e:
        raise HTTPException(500, str(e))


# Alias so old frontend calls still work
@router.get("/{tmdb_id}/downloads")
async def movie_downloads(tmdb_id: int):
    return await movie_sources(tmdb_id)

@router.get("/{tmdb_id}/stream")
async def movie_stream(tmdb_id: int):
    return await movie_sources(tmdb_id)
