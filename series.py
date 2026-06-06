"""
TV Series Router — Cymor Movie Hub
Endpoints: search, details, episode download links
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import asyncio
import logging

from utils.cache import cache
from utils.serializers import serialize_search_item, serialize_details, serialize_download_files

logger = logging.getLogger("cymor.series")
router = APIRouter()


@router.get("/search")
async def search_series(
    q: str = Query(..., description="TV series title to search for", min_length=1),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=50, description="Results per page"),
):
    """
    Search for TV series by title.

    Example: GET /api/series/search?q=merlin&page=1
    """
    cache_key = f"series:search:{q.lower().strip()}:{page}:{per_page}"
    cached = await cache.get(cache_key)
    if cached:
        return cached

    try:
        from moviebox_api.v1.core import Search, Session, SubjectType

        session = Session()
        search = Search(
            session,
            query=q.strip(),
            subject_type=SubjectType.TV_SERIES,
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

        await cache.set(cache_key, response, ttl=600)
        return response

    except Exception as e:
        logger.error(f"Series search error for '{q}': {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/{item_id}")
async def get_series_details(item_id: str):
    """
    Get full details for a TV series including seasons and episode counts.

    Example: GET /api/series/%2Fdetail%2Fmerlin-sMxCiIO6fZ9%3Fid%3D8382755684005333552
    """
    import urllib.parse
    page_url = urllib.parse.unquote(item_id)

    cache_key = f"series:details:{page_url}"
    cached = await cache.get(cache_key)
    if cached:
        return cached

    try:
        from moviebox_api.v1 import TVSeriesDetails, Session

        session = Session()
        details_inst = TVSeriesDetails(page_url, session=session)
        details = await asyncio.to_thread(details_inst.get_content_model_sync)

        response = serialize_details(details)
        response["page_url"] = page_url

        await cache.set(cache_key, response, ttl=1800)
        return response

    except Exception as e:
        logger.error(f"Series details error for '{page_url}': {e}")
        raise HTTPException(status_code=500, detail=f"Could not fetch series details: {str(e)}")


@router.get("/{item_id}/downloads")
async def get_episode_downloads(
    item_id: str,
    season: int = Query(1, ge=1, description="Season number"),
    episode: int = Query(1, ge=1, description="Episode number"),
):
    """
    Get download links for a specific TV series episode.

    Example: GET /api/series/{item_id}/downloads?season=1&episode=3
    """
    import urllib.parse
    page_url = urllib.parse.unquote(item_id)

    cache_key = f"series:downloads:{page_url}:s{season}e{episode}"
    cached = await cache.get(cache_key)
    if cached:
        return cached

    try:
        from moviebox_api.v1 import (
            TVSeriesDetails,
            DownloadableTVSeriesFilesDetail,
            Session,
        )

        session = Session()

        # Step 1: Series details
        details_inst = TVSeriesDetails(page_url, session=session)
        details = await asyncio.to_thread(details_inst.get_content_model_sync)

        # Step 2: Downloadable files for this season/episode
        downloadable = DownloadableTVSeriesFilesDetail(session, details)
        files = await asyncio.to_thread(
            downloadable.get_content_model_sync, season=season, episode=episode
        )

        response = serialize_download_files(files)
        response["page_url"] = page_url
        response["season"] = season
        response["episode"] = episode

        await cache.set(cache_key, response, ttl=1800)
        return response

    except Exception as e:
        logger.error(f"Episode downloads error for '{page_url}' S{season}E{episode}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Could not fetch episode download links: {str(e)}",
        )
