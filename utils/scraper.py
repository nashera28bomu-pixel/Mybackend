"""
Cymor Movie Hub - Source Scraper v3 (Stabilized)
Includes error handling and provider fallback logic
"""

import re
import httpx
import logging
from typing import Optional

logger = logging.getLogger("cymor.scraper")

YTS_PROVIDERS = [
    "https://yts.mx/api/v2",
    "https://yts.rs/api/v2",
    "https://yts.lt/api/v2",
]

EZTV_PROVIDERS = [
    "https://eztvx.to/api/get-torrents",
    "https://eztv.re/api/get-torrents",
]

HEADERS = {"User-Agent": "CymorMovieHub/3.0", "Accept": "application/json"}
TRACKERS = "&".join([
    "tr=udp%3A%2F%2Fopen.demonii.com%3A1337%2Fannounce",
    "tr=udp%3A%2F%2Ftracker.openbittorrent.com%3A80",
    "tr=udp%3A%2F%2Ftracker.opentrackr.org%3A1337%2Fannounce",
])

QUALITY_ORDER = {"2160p": 0, "1080p": 1, "720p": 2, "480p": 3, "SD": 4}

def build_magnet(hash_: str, title: str) -> str:
    dn = re.sub(r"\s+", "+", title.strip())
    return f"magnet:?xt=urn:btih:{hash_}&dn={dn}&{TRACKERS}"

def fmt_size(b: int) -> str:
    if not b: return ""
    if b > 1_000_000_000: return f"{b/1_000_000_000:.1f} GB"
    if b > 1_000_000: return f"{b/1_000_000:.0f} MB"
    return f"{b} B"

async def fetch_json(url: str, params=None):
    """Fetch JSON with error handling instead of raising exceptions."""
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True, headers=HEADERS) as client:
            response = await client.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                # Validate that API actually returned valid success status
                if isinstance(data, dict) and data.get("status") == "ok":
                    return data
            logger.warning(f"Provider {url} returned status {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"Failed to fetch from {url}: {e}")
        return None

# ==========================================================
# MOVIES (Stabilized)
# ==========================================================

async def get_movie_sources(imdb_id: Optional[str], title: str, year: str) -> dict:
    result = {"sources": [], "provider": None, "found": False, "providers": {}}
    query = imdb_id or f"{title} {year}".strip()

    for provider in YTS_PROVIDERS:
        logger.info(f"Trying provider: {provider}")
        data = await fetch_json(f"{provider}/list_movies.json", {"query_term": query, "limit": 5})
        
        # Ensure 'data' and 'movies' exist before processing
        movies = data.get("data", {}).get("movies") if data else []

        if movies:
            movie = movies[0]
            for torrent in movie.get("torrents", []):
                result["sources"].append({
                    "quality": torrent.get("quality"),
                    "hash": torrent.get("hash"),
                    "magnet": build_magnet(torrent.get("hash"), f"{movie.get('title')} {torrent.get('quality')}"),
                    "seeds": torrent.get("seeds", 0),
                    "size": torrent.get("size"),
                })
            result["provider"] = provider
            result["found"] = True
            result["sources"].sort(key=lambda x: QUALITY_ORDER.get(x["quality"], 99))
            return result
        
        result["providers"][provider] = "Failed"

    return result

# ==========================================================
# TV EPISODES (Stabilized)
# ==========================================================

async def get_episode_sources(imdb_id: str, season: int, episode: int, title: str) -> dict:
    result = {"sources": [], "provider": None, "found": False, "providers": {}}
    if not imdb_id: return result
    
    imdb_numeric = imdb_id.replace("tt", "").lstrip("0")
    ep_tag = f"S{season:02d}E{episode:02d}"

    for provider in EZTV_PROVIDERS:
        data = await fetch_json(provider, {"imdb_id": imdb_numeric, "limit": 100})
        torrents = data.get("torrents") if data else []

        if torrents:
            for t in torrents:
                if ep_tag.lower() in t.get("filename", "").lower():
                    result["sources"].append({
                        "quality": "1080p" if "1080" in t.get("filename") else "720p",
                        "magnet": t.get("magnet_url"),
                        "seeds": t.get("seeds", 0),
                    })
            
            if result["sources"]:
                result["provider"] = provider
                result["found"] = True
                return result

    return result
