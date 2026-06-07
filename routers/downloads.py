"""
Downloads Router — proxy for .torrent files only
Cymor Movie Hub v2
"""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse, RedirectResponse
import httpx, logging

logger = logging.getLogger("cymor.downloads")
router = APIRouter()

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}


@router.get("/proxy")
async def proxy_torrent(
    url:      str = Query(...),
    filename: str = Query("cymor.torrent"),
):
    """Proxy a .torrent file download through the backend."""
    if not url.startswith("http"):
        raise HTTPException(400, "Invalid URL")
    try:
        async def stream():
            async with httpx.AsyncClient(follow_redirects=True, timeout=15, headers=HEADERS) as c:
                async with c.stream("GET", url) as r:
                    async for chunk in r.aiter_bytes(65536):
                        yield chunk

        async with httpx.AsyncClient(follow_redirects=True, timeout=10, headers=HEADERS) as c:
            head = await c.head(url)

        ct = head.headers.get("content-type", "application/x-bittorrent")
        hdrs = {
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Access-Control-Allow-Origin": "*",
        }
        if cl := head.headers.get("content-length"):
            hdrs["Content-Length"] = cl

        return StreamingResponse(stream(), media_type=ct, headers=hdrs)
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/redirect")
async def redirect(url: str = Query(...)):
    if not url.startswith("http"):
        raise HTTPException(400, "Invalid URL")
    return RedirectResponse(url, 302)


@router.get("/check")
async def check_url(url: str = Query(...)):
    """Check if a URL is reachable — frontend uses this before showing sources."""
    if not url.startswith("http"):
        raise HTTPException(400, "Invalid URL")
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=8, headers=HEADERS) as c:
            r = await c.head(url)
        return {"url": url, "reachable": r.status_code < 400, "status": r.status_code}
    except Exception as e:
        return {"url": url, "reachable": False, "error": str(e)}
