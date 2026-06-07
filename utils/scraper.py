"""
Cymor Movie Hub - Source Scraper v3
Multi-provider + detailed diagnostics
By Legendary Smiley Cymor
"""

import re
import httpx
import logging
from typing import Optional

logger = logging.getLogger("cymor.scraper")

#Multiple movie provider mirrors

YTS_PROVIDERS = [
"https://yts.mx/api/v2",
"https://yts.rs/api/v2",
"https://yts.lt/api/v2",
]

Multiple TV providers

EZTV_PROVIDERS = [
"https://eztvx.to/api/get-torrents",
"https://eztv.re/api/get-torrents",
]

HEADERS = {
"User-Agent": "CymorMovieHub/3.0",
"Accept": "application/json",
}

TRACKERS = "&".join([
"tr=udp%3A%2F%2Fopen.demonii.com%3A1337%2Fannounce",
"tr=udp%3A%2F%2Ftracker.openbittorrent.com%3A80",
"tr=udp%3A%2F%2Ftracker.opentrackr.org%3A1337%2Fannounce",
"tr=udp%3A%2F%2Ftracker.coppersurfer.tk%3A6969",
])

QUALITY_ORDER = {
"2160p": 0,
"1080p": 1,
"720p": 2,
"480p": 3,
"SD": 4,
}

def build_magnet(hash_: str, title: str) -> str:
dn = re.sub(r"\s+", "+", title.strip())
return f"magnet:?xt=urn:btih:{hash_}&dn={dn}&{TRACKERS}"

def fmt_size(b: int) -> str:
if not b:
return ""
if b > 1_000_000_000:
return f"{b/1_000_000_000:.1f} GB"
if b > 1_000_000:
return f"{b/1_000_000:.0f} MB"
return f"{b} B"

async def fetch_json(url: str, params=None):
async with httpx.AsyncClient(
timeout=httpx.Timeout(15.0),
follow_redirects=True,
headers=HEADERS,
) as client:
response = await client.get(url, params=params)
response.raise_for_status()
return response.json()

==========================================================

MOVIES

==========================================================

async def get_movie_sources(
imdb_id: Optional[str],
title: str,
year: str,
) -> dict:

result = {
    "sources": [],
    "provider": None,
    "found": False,
    "note": "Stream in browser with WebTorrent",
    "providers": {},
}

query = imdb_id or f"{title} {year}".strip()

for provider in YTS_PROVIDERS:

    try:
        logger.info(
            f"Movie lookup provider={provider} imdb={imdb_id} title={title}"
        )

        data = await fetch_json(
            f"{provider}/list_movies.json",
            {
                "query_term": query,
                "limit": 5,
            },
        )

        movies = data.get("data", {}).get("movies") or []

        if not movies:
            data = await fetch_json(
                f"{provider}/list_movies.json",
                {
                    "query_term": title,
                    "limit": 5,
                },
            )
            movies = data.get("data", {}).get("movies") or []

        if not movies:
            result["providers"][provider] = {
                "success": False,
                "error": "No movie match",
            }
            continue

        movie = movies[0]

        seen_hashes = set()

        for torrent in movie.get("torrents", []):

            hash_ = torrent.get("hash")
            if not hash_ or hash_ in seen_hashes:
                continue

            seen_hashes.add(hash_)

            quality = torrent.get("quality", "")

            if quality == "3D":
                continue

            result["sources"].append({
                "quality": quality,
                "codec": torrent.get("video_codec"),
                "size": torrent.get("size"),
                "seeds": torrent.get("seeds", 0),
                "peers": torrent.get("peers", 0),
                "hash": hash_,
                "magnet": build_magnet(
                    hash_,
                    f"{movie.get('title', title)} {quality}",
                ),
                "torrent_url": torrent.get("url"),
                "type": "torrent",
                "streamable": True,
                "ads": False,
            })

        result["provider"] = provider
        result["found"] = len(result["sources"]) > 0

        result["providers"][provider] = {
            "success": True,
            "sources": len(result["sources"]),
        }

        if result["found"]:
            result["sources"].sort(
                key=lambda x: QUALITY_ORDER.get(
                    x["quality"],
                    99,
                )
            )
            return result

    except Exception:
        logger.exception(
            f"Movie provider failed: {provider} "
            f"imdb={imdb_id} title={title}"
        )

        result["providers"][provider] = {
            "success": False,
            "error": "Provider request failed",
        }

result["note"] = "All movie providers failed"
return result

==========================================================

TV EPISODES

==========================================================

async def get_episode_sources(
imdb_id: str,
season: int,
episode: int,
title: str,
) -> dict:

result = {
    "sources": [],
    "provider": None,
    "season": season,
    "episode": episode,
    "found": False,
    "providers": {},
    "note": "Stream in browser with WebTorrent",
}

if not imdb_id:
    result["note"] = "IMDB ID required"
    return result

imdb_numeric = imdb_id.replace("tt", "").lstrip("0")
ep_tag = f"S{season:02d}E{episode:02d}"

for provider in EZTV_PROVIDERS:

    try:
        logger.info(
            f"TV lookup provider={provider} "
            f"imdb={imdb_numeric} "
            f"{ep_tag}"
        )

        data = await fetch_json(
            provider,
            {
                "imdb_id": imdb_numeric,
                "limit": 100,
            },
        )

        torrents = data.get("torrents") or []

        seen = set()

        for t in torrents:

            filename = t.get("filename", "")

            matches = (
                (
                    str(t.get("season")) == str(season)
                    and
                    str(t.get("episode")) == str(episode)
                )
                or
                ep_tag.lower() in filename.lower()
            )

            if not matches:
                continue

            hash_ = t.get("hash")

            if not hash_ or hash_ in seen:
                continue

            seen.add(hash_)

            fn = filename.upper()

            if "2160P" in fn or "4K" in fn:
                quality = "2160p"
            elif "1080P" in fn:
                quality = "1080p"
            elif "720P" in fn:
                quality = "720p"
            elif "480P" in fn:
                quality = "480p"
            else:
                quality = "SD"

            result["sources"].append({
                "quality": quality,
                "filename": filename,
                "size": fmt_size(
                    int(t.get("size_bytes") or 0)
                ),
                "size_bytes": int(
                    t.get("size_bytes") or 0
                ),
                "seeds": t.get("seeds", 0),
                "peers": t.get("peers", 0),
                "hash": hash_,
                "magnet": (
                    t.get("magnet_url")
                    or build_magnet(hash_, filename)
                ),
                "torrent_url": t.get("torrent_url"),
                "type": "torrent",
                "streamable": True,
                "ads": False,
            })

        result["provider"] = provider
        result["found"] = len(result["sources"]) > 0

        result["providers"][provider] = {
            "success": True,
            "sources": len(result["sources"]),
        }

        if result["found"]:
            result["sources"].sort(
                key=lambda x: (
                    QUALITY_ORDER.get(
                        x["quality"],
                        99,
                    ),
                    -x["seeds"],
                )
            )
            return result

    except Exception:
        logger.exception(
            f"TV provider failed: {provider} "
            f"imdb={imdb_id} "
            f"{ep_tag}"
        )

        result["providers"][provider] = {
            "success": False,
            "error": "Provider request failed",
        }

result["note"] = f"No sources found for {ep_tag}"
return result
