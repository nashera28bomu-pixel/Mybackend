"""
Downloads Router — Cymor Movie Hub
Proxies file downloads so users get a clean experience
without exposing raw upstream URLs in the frontend.
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse, RedirectResponse
import httpx
import logging

logger = logging.getLogger("cymor.downloads")
router = APIRouter()

# Max redirect hops before we give up
MAX_REDIRECTS = 5


@router.get("/proxy")
async def proxy_download(
    url: str = Query(..., description="The direct file URL to proxy"),
    filename: str = Query("cymor_download", description="Suggested filename for the download"),
):
    """
    Proxy a movie or subtitle file download.
    Frontend calls this endpoint; backend streams the file to the user.

    Example: GET /api/downloads/proxy?url=https://...&filename=Avatar_1080p.mp4
    """
    if not url.startswith("http"):
        raise HTTPException(status_code=400, detail="Invalid URL.")

    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=30) as client:
            # HEAD request to get content type and size
            head = await client.head(url)
            content_type = head.headers.get("content-type", "application/octet-stream")
            content_length = head.headers.get("content-length")

        async def stream_file():
            async with httpx.AsyncClient(follow_redirects=True, timeout=None) as client:
                async with client.stream("GET", url) as response:
                    async for chunk in response.aiter_bytes(chunk_size=65536):
                        yield chunk

        headers = {
            "Content-Disposition": f'attachment; filename="{filename}"',
        }
        if content_length:
            headers["Content-Length"] = content_length

        return StreamingResponse(
            stream_file(),
            media_type=content_type,
            headers=headers,
        )

    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Download source timed out.")
    except Exception as e:
        logger.error(f"Proxy download error: {e}")
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")


@router.get("/redirect")
async def redirect_download(
    url: str = Query(..., description="Direct file URL to redirect to"),
):
    """
    Lightweight redirect to a direct download URL.
    Use this when you don't need streaming (e.g. subtitles).

    Example: GET /api/downloads/redirect?url=https://...
    """
    if not url.startswith("http"):
        raise HTTPException(status_code=400, detail="Invalid URL.")
    return RedirectResponse(url=url, status_code=302)
