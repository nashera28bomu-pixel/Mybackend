"""
TMDB API helper for Cymor Movie Hub.
All metadata, search, trending, details come from here.
"""
import os
import httpx
import logging
from typing import Optional

logger = logging.getLogger("cymor.tmdb")

TMDB_BASE   = "https://api.themoviedb.org/3"
TMDB_IMG    = "https://image.tmdb.org/t/p"
TMDB_KEY    = os.environ.get("TMDB_API_KEY", "")

POSTER_SM   = f"{TMDB_IMG}/w342"
POSTER_LG   = f"{TMDB_IMG}/w500"
BACKDROP    = f"{TMDB_IMG}/w1280"


def poster_url(path: Optional[str], size: str = "w342") -> Optional[str]:
    if not path:
        return None
    return f"{TMDB_IMG}/{size}{path}"


async def tmdb_get(path: str, params: dict = {}) -> dict:
    if not TMDB_KEY:
        raise ValueError("TMDB_API_KEY not set in environment variables")
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            f"{TMDB_BASE}{path}",
            params={"api_key": TMDB_KEY, "language": "en-US", **params},
        )
        resp.raise_for_status()
        return resp.json()


def fmt_movie(m: dict) -> dict:
    """Normalize a TMDB movie result into Cymor's standard format."""
    return {
        "id":          m.get("id"),
        "tmdb_id":     m.get("id"),
        "title":       m.get("title") or m.get("original_title"),
        "poster":      poster_url(m.get("poster_path")),
        "backdrop":    poster_url(m.get("backdrop_path"), "w1280"),
        "year":        (m.get("release_date") or "")[:4],
        "rating":      round(m.get("vote_average", 0), 1),
        "description": m.get("overview"),
        "genres":      [g["name"] for g in m.get("genres", [])] or
                       _genre_ids_to_names(m.get("genre_ids", []), "movie"),
        "type":        "movie",
        "page_url":    str(m.get("id")),  # used as identifier in frontend
        "popularity":  m.get("popularity"),
        "adult":       m.get("adult", False),
    }


def fmt_series(s: dict) -> dict:
    """Normalize a TMDB TV series result into Cymor's standard format."""
    return {
        "id":           s.get("id"),
        "tmdb_id":      s.get("id"),
        "title":        s.get("name") or s.get("original_name"),
        "poster":       poster_url(s.get("poster_path")),
        "backdrop":     poster_url(s.get("backdrop_path"), "w1280"),
        "year":         (s.get("first_air_date") or "")[:4],
        "rating":       round(s.get("vote_average", 0), 1),
        "description":  s.get("overview"),
        "genres":       [g["name"] for g in s.get("genres", [])] or
                        _genre_ids_to_names(s.get("genre_ids", []), "tv"),
        "type":         "series",
        "page_url":     str(s.get("id")),
        "seasons":      s.get("number_of_seasons"),
        "episodes":     s.get("number_of_episodes"),
        "status":       s.get("status"),
        "popularity":   s.get("popularity"),
    }


def fmt_details(d: dict, media_type: str) -> dict:
    """Normalize full TMDB detail response (includes credits, videos)."""
    base = fmt_movie(d) if media_type == "movie" else fmt_series(d)

    # Cast
    credits = d.get("credits", {})
    cast = [c["name"] for c in credits.get("cast", [])[:12]]
    crew = credits.get("crew", [])
    directors = [c["name"] for c in crew if c.get("job") == "Director"]

    # Trailer
    videos = d.get("videos", {}).get("results", [])
    trailer = next((v for v in videos if v.get("type") == "Trailer" and v.get("site") == "YouTube"), None)
    trailer_url = f"https://www.youtube.com/watch?v={trailer['key']}" if trailer else None

    base.update({
        "cast":        cast,
        "director":    ", ".join(directors) if directors else None,
        "runtime":     d.get("runtime"),
        "tagline":     d.get("tagline"),
        "language":    d.get("original_language", "").upper(),
        "country":     (d.get("production_countries") or [{}])[0].get("name"),
        "trailer_url": trailer_url,
        "imdb_id":     d.get("imdb_id") or d.get("external_ids", {}).get("imdb_id"),
        "budget":      d.get("budget"),
        "revenue":     d.get("revenue"),
        "homepage":    d.get("homepage"),
    })
    return base


# Genre ID → name maps (for search results that only return IDs)
_MOVIE_GENRES = {
    28:"Action",12:"Adventure",16:"Animation",35:"Comedy",80:"Crime",
    99:"Documentary",18:"Drama",10751:"Family",14:"Fantasy",36:"History",
    27:"Horror",10402:"Music",9648:"Mystery",10749:"Romance",878:"Science Fiction",
    10770:"TV Movie",53:"Thriller",10752:"War",37:"Western",
}
_TV_GENRES = {
    10759:"Action & Adventure",16:"Animation",35:"Comedy",80:"Crime",
    99:"Documentary",18:"Drama",10751:"Family",10762:"Kids",9648:"Mystery",
    10763:"News",10764:"Reality",10765:"Sci-Fi & Fantasy",10766:"Soap",
    10767:"Talk",10768:"War & Politics",37:"Western",
}

def _genre_ids_to_names(ids: list, kind: str) -> list:
    gmap = _MOVIE_GENRES if kind == "movie" else _TV_GENRES
    return [gmap[i] for i in ids if i in gmap]
