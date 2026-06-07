"""
Cymor Movie Hub - Clean Source Scraper v2
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Movies  → YTS API  (official, free, no ads) → magnet links + .torrent files
TV      → EZTV API (official, free, no ads) → magnet links + .torrent files

Frontend streams using WebTorrent.js directly in the browser.
Zero ads. Zero iframes. Zero redirects.
"""
import httpx
import re
import logging
from typing import Optional

logger = logging.getLogger("cymor.scraper")

YTS_API   = "https://yts.mx/api/v2"
EZTV_API  = "https://eztvx.to/api/get-torrents"

TRACKERS = "&".join([
    "tr=udp%3A%2F%2Fopen.demonii.com%3A1337%2Fannounce",
    "tr=udp%3A%2F%2Ftracker.openbittorrent.com%3A80",
    "tr=udp%3A%2F%2Ftracker.coppersurfer.tk%3A6969",
    "tr=udp%3A%2F%2Fglotorrents.pw%3A6969%2Fannounce",
    "tr=udp%3A%2F%2Ftracker.opentrackr.org%3A1337%2Fannounce",
    "tr=udp%3A%2F%2Ftorrent.gresille.org%3A80%2Fannounce",
    "tr=udp%3A%2F%2Fp4p.arenabg.ch%3A1337",
    "tr=udp%3A%2F%2Ftracker.leechers-paradise.org%3A6969",
])

def build_magnet(hash: str, title: str) -> str:
    dn = re.sub(r"\s+", "+", title.strip())
    return f"magnet:?xt=urn:btih:{hash}&dn={dn}&{TRACKERS}"


# ─────────────────────────────────────────
# MOVIES via YTS API
# ─────────────────────────────────────────

async def get_movie_sources(imdb_id: Optional[str], title: str, year: str) -> dict:
    """
    Fetch clean torrent/magnet sources for a movie from YTS.
    Returns 720p, 1080p, 2160p options with magnets + .torrent URLs.
    No ads. No iframes. Direct links.
    """
    result = {
        "sources":  [],
        "provider": "YTS",
        "note":     "Stream in browser with WebTorrent or download .torrent file",
        "found":    False,
    }

    try:
        async with httpx.AsyncClient(timeout=12) as client:
            # Try by IMDB ID first (most accurate)
            params = {"query_term": imdb_id} if imdb_id else {"query_term": f"{title} {year}".strip()}
            params["limit"] = 5

            resp = await client.get(f"{YTS_API}/list_movies.json", params=params)
            resp.raise_for_status()
            data = resp.json()

        movies = data.get("data", {}).get("movies") or []
        if not movies:
            # fallback: search by title only
            async with httpx.AsyncClient(timeout=12) as client:
                resp2 = await client.get(f"{YTS_API}/list_movies.json", params={"query_term": title, "limit": 5})
                data2 = resp2.json()
            movies = data2.get("data", {}).get("movies") or []

        if not movies:
            result["note"] = "Not found on YTS yet — try again later or check download links below"
            return result

        movie = movies[0]
        torrents = movie.get("torrents") or []

        for t in torrents:
            quality  = t.get("quality", "")
            if quality == "3D":
                continue
            codec    = t.get("video_codec", "")
            size     = t.get("size", "")
            seeds    = t.get("seeds", 0)
            peers    = t.get("peers", 0)
            hash_    = t.get("hash", "")
            torrent_url = t.get("url", "")
            magnet   = build_magnet(hash_, f"{movie.get('title', title)} {year} {quality}")

            result["sources"].append({
                "quality":     quality,
                "codec":       codec,
                "size":        size,
                "seeds":       seeds,
                "peers":       peers,
                "hash":        hash_,
                "magnet":      magnet,
                "torrent_url": torrent_url,
                "type":        "torrent",
                "streamable":  True,   # WebTorrent can stream this in-browser
                "ads":         False,
            })

        # Sort by quality: 2160p > 1080p > 720p
        order = {"2160p": 0, "1080p": 1, "720p": 2}
        result["sources"].sort(key=lambda x: order.get(x["quality"], 99))
        result["found"] = len(result["sources"]) > 0
        result["yts_title"] = movie.get("title")
        result["yts_cover"]  = movie.get("large_cover_image")

    except Exception as e:
        logger.error(f"YTS error for {imdb_id or title}: {e}")
        result["error"] = str(e)

    return result


# ─────────────────────────────────────────
# TV SERIES via EZTV API
# ─────────────────────────────────────────

async def get_episode_sources(imdb_id: str, season: int, episode: int, title: str) -> dict:
    """
    Fetch clean torrent/magnet sources for a TV episode from EZTV.
    Returns all available quality options with magnets.
    No ads. No iframes. Direct links.
    """
    result = {
        "sources":  [],
        "provider": "EZTV",
        "season":   season,
        "episode":  episode,
        "note":     "Stream in browser with WebTorrent or download .torrent file",
        "found":    False,
    }

    if not imdb_id:
        result["note"] = "IMDB ID required for TV episode lookup"
        return result

    # EZTV expects numeric IMDB ID (strip 'tt' prefix)
    imdb_numeric = imdb_id.replace("tt", "").lstrip("0") if imdb_id else ""

    try:
        async with httpx.AsyncClient(timeout=12) as client:
            resp = await client.get(EZTV_API, params={
                "imdb_id": imdb_numeric,
                "limit":   100,
            })
            resp.raise_for_status()
            data = resp.json()

        all_torrents = data.get("torrents") or []

        # Filter to matching season + episode
        ep_str  = f"S{str(season).zfill(2)}E{str(episode).zfill(2)}"
        matched = [
            t for t in all_torrents
            if (
                str(t.get("season", ""))  == str(season) and
                str(t.get("episode", "")) == str(episode)
            ) or ep_str.lower() in t.get("filename", "").lower()
        ]

        # Detect quality from filename
        def detect_quality(filename: str) -> str:
            fn = filename.upper()
            if "2160P" in fn or "4K" in fn: return "2160p"
            if "1080P" in fn: return "1080p"
            if "720P"  in fn: return "720p"
            if "480P"  in fn: return "480p"
            return "SD"

        seen_hashes = set()
        for t in matched:
            h = t.get("hash", "")
            if h in seen_hashes:
                continue
            seen_hashes.add(h)

            filename = t.get("filename", "")
            quality  = detect_quality(filename)
            magnet   = t.get("magnet_url") or build_magnet(h, filename)
            size_bytes = int(t.get("size_bytes") or 0)
            size_str   = _fmt_size(size_bytes)

            result["sources"].append({
                "quality":     quality,
                "filename":    filename,
                "size":        size_str,
                "size_bytes":  size_bytes,
                "seeds":       t.get("seeds", 0),
                "peers":       t.get("peers", 0),
                "hash":        h,
                "magnet":      magnet,
                "torrent_url": t.get("torrent_url", ""),
                "type":        "torrent",
                "streamable":  True,
                "ads":         False,
            })

        # Sort: highest seeds first, then by quality
        order = {"2160p": 0, "1080p": 1, "720p": 2, "480p": 3, "SD": 4}
        result["sources"].sort(key=lambda x: (order.get(x["quality"], 5), -x["seeds"]))

        result["found"] = len(result["sources"]) > 0
        if not result["found"]:
            result["note"] = f"Episode {ep_str} not yet on EZTV — may not be released yet"

    except Exception as e:
        logger.error(f"EZTV error {imdb_id} S{season}E{episode}: {e}")
        result["error"] = str(e)

    return result


def _fmt_size(b: int) -> str:
    if not b: return ""
    if b > 1_000_000_000: return f"{b/1_000_000_000:.1f} GB"
    if b > 1_000_000:     return f"{b/1_000_000:.0f} MB"
    return f"{b} B"
