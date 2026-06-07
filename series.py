"""
TV Series Router — TMDB metadata + EZTV clean torrent sources
Cymor Movie Hub v2 | No ads. No iframes. Always a winner.
"""
from fastapi import APIRouter, HTTPException, Query
import logging

from utils.cache import cache
from utils.tmdb import tmdb_get, fmt_series, fmt_details
from utils.scraper import get_episode_sources

logger = logging.getLogger("cymor.series")
router = APIRouter()


@router.get("/search")
async def search_series(
    q:    str = Query(..., min_length=1),
    page: int = Query(1, ge=1, le=500),
):
    """Search TV series via TMDB."""
    key = f"tv:search:{q.lower().strip()}:{page}"
    if cached := await cache.get(key): return cached
    try:
        data = await tmdb_get("/search/tv", {"query": q.strip(), "page": page})
        response = {
            "query":       q,
            "page":        page,
            "total_pages": data.get("total_pages", 1),
            "total":       data.get("total_results", 0),
            "has_more":    page < data.get("total_pages", 1),
            "results":     [fmt_series(s) for s in data.get("results", [])],
        }
        await cache.set(key, response, ttl=600)
        return response
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/{tmdb_id}")
async def series_details(tmdb_id: int):
    """Full series details — seasons, cast, trailer."""
    key = f"tv:detail:{tmdb_id}"
    if cached := await cache.get(key): return cached
    try:
        data = await tmdb_get(f"/tv/{tmdb_id}", {"append_to_response": "credits,videos,external_ids"})
        response = fmt_details(data, "series")
        response["season_list"] = [
            {
                "season_number": s.get("season_number"),
                "name":          s.get("name"),
                "episode_count": s.get("episode_count"),
                "poster":        f"https://image.tmdb.org/t/p/w342{s['poster_path']}" if s.get("poster_path") else None,
                "air_date":      s.get("air_date"),
            }
            for s in data.get("seasons", []) if s.get("season_number", 0) > 0
        ]
        await cache.set(key, response, ttl=1800)
        return response
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/{tmdb_id}/season/{season_number}")
async def season_episodes(tmdb_id: int, season_number: int):
    """All episodes for a season with stills, runtimes, ratings."""
    key = f"tv:season:{tmdb_id}:{season_number}"
    if cached := await cache.get(key): return cached
    try:
        data = await tmdb_get(f"/tv/{tmdb_id}/season/{season_number}")
        episodes = [
            {
                "episode_number": e.get("episode_number"),
                "name":           e.get("name"),
                "overview":       e.get("overview"),
                "still":          f"https://image.tmdb.org/t/p/w300{e['still_path']}" if e.get("still_path") else None,
                "air_date":       e.get("air_date"),
                "runtime":        e.get("runtime"),
                "rating":         round(e.get("vote_average", 0), 1),
            }
            for e in data.get("episodes", [])
        ]
        response = {
            "tmdb_id":       tmdb_id,
            "season_number": season_number,
            "name":          data.get("name"),
            "episodes":      episodes,
            "total":         len(episodes),
        }
        await cache.set(key, response, ttl=3600)
        return response
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/{tmdb_id}/sources")
async def episode_sources(
    tmdb_id: int,
    season:  int = Query(1, ge=1),
    episode: int = Query(1, ge=1),
):
    """
    Get clean torrent/magnet sources for a TV episode via EZTV API.
    Returns magnet links by quality — stream with WebTorrent in browser.
    Zero ads. Zero iframes. Zero redirects.
    """
    key = f"tv:sources:{tmdb_id}:s{season}e{episode}"
    if cached := await cache.get(key): return cached
    try:
        detail  = await tmdb_get(f"/tv/{tmdb_id}", {"append_to_response": "external_ids"})
        imdb_id = detail.get("external_ids", {}).get("imdb_id") or ""
        title   = detail.get("name", "")

        sources = await get_episode_sources(imdb_id, season, episode, title)
        response = {
            "tmdb_id": tmdb_id,
            "imdb_id": imdb_id,
            "title":   title,
            "season":  season,
            "episode": episode,
            **sources,
        }
        ttl = 3600 if sources["found"] else 300
        await cache.set(key, response, ttl=ttl)
        return response
    except Exception as e:
        raise HTTPException(500, str(e))


# Aliases
@router.get("/{tmdb_id}/downloads")
async def episode_downloads(tmdb_id: int, season: int = Query(1), episode: int = Query(1)):
    return await episode_sources(tmdb_id, season, episode)

@router.get("/{tmdb_id}/stream")
async def episode_stream(tmdb_id: int, season: int = Query(1), episode: int = Query(1)):
    return await episode_sources(tmdb_id, season, episode)
