"""
Movies Router — Cymor Movie Hub
Endpoints: search, details, downloadable files
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import asyncio
import logging

from utils.cache import cache
from utils.serializers import serialize_search_item, serialize_details, serialize_download_files

logger = logging.getLogger("cymor.movies")
router = APIRouter()


@router.get("/search")
async def search_movies(
    q: str = Query(..., description="Movie title to search for", min_length=1),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=50, description="Results per page"),
):
    """
    Search for movies by title.

    Example: GET /api/movies/search?q=avatar&page=1
    """
    cache_key = f"movies:search:{q.lower().strip()}:{page}:{per_page}"
    cached = await cache.get(cache_key)
    if cached:
        return cached

    try:
        from moviebox_api.v1.core import Search, Session, SubjectType

        session = Session()
        search = Search(
            session,
            query=q.strip(),
            subject_type=SubjectType.MOVIES,
            page=page,
            per_page=per_page,
        )

        results = await asyncio.to_thread(search.get_content_model_sync)

        items = [serialize_search_item(item) for item in (results.items or [])]

        response = {
            "query": q,
            "page": page,
            "per_page": per_page,
            "total": len(items),
            "has_more": getattr(getattr(results, "pager", None), "hasMore", False),
            "results": items,
        }

        await cache.set(cache_key, response, ttl=600)  # 10 min cache
        return response

    except Exception as e:
        logger.error(f"Movie search error for '{q}': {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/{item_id}")
async def get_movie_details(item_id: str):
    """
    Get full details for a specific movie.

    `item_id` is the page_url value returned from search (e.g. /detail/avatar-WLDIi21IUBa?id=...)
    Pass it URL-encoded.

    Example: GET /api/movies/%2Fdetail%2Favatar-WLDIi21IUBa%3Fid%3D8906247916759695608
    """
    import urllib.parse
    page_url = urllib.parse.unquote(item_id)

    cache_key = f"movies:details:{page_url}"
    cached = await cache.get(cache_key)
    if cached:
        return cached

    try:
        from moviebox_api.v1 import MovieDetails, Session

        session = Session()
        md = MovieDetails(page_url, session=session)
        details = await asyncio.to_thread(md.get_content_model_sync)

        response = serialize_details(details)
        response["page_url"] = page_url

        await cache.set(cache_key, response, ttl=1800)  # 30 min cache
        return response

    except Exception as e:
        logger.error(f"Movie details error for '{page_url}': {e}")
        raise HTTPException(status_code=500, detail=f"Could not fetch movie details: {str(e)}")


@router.get("/{item_id}/downloads")
async def get_movie_downloads(item_id: str):
    """
    Get all downloadable video qualities and subtitle files for a movie.

    Returns a list of video URLs (by quality) and subtitle URLs (by language).

    Example: GET /api/movies/%2Fdetail%2Favatar-WLDIi21IUBa%3Fid%3D...%2Fdownloads
    """
    import urllib.parse
    page_url = urllib.parse.unquote(item_id)

    cache_key = f"movies:downloads:{page_url}"
    cached = await cache.get(cache_key)
    if cached:
        return cached

    try:
        from moviebox_api.v1 import MovieDetails, DownloadableMovieFilesDetail, Session

        session = Session()

        # Step 1: Get details
        md = MovieDetails(page_url, session=session)
        details = await asyncio.to_thread(md.get_content_model_sync)

        # Step 2: Get downloadable files metadata
        downloadable = DownloadableMovieFilesDetail(session, details)
        files = await asyncio.to_thread(downloadable.get_content_model_sync)

        response = serialize_download_files(files)
        response["page_url"] = page_url

        await cache.set(cache_key, response, ttl=1800)
        return response

    except Exception as e:
        logger.error(f"Movie downloads error for '{page_url}': {e}")
        raise HTTPException(status_code=500, detail=f"Could not fetch download links: {str(e)}")
