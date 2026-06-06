"""
Serializer helpers — converts moviebox_api Pydantic models
into clean, frontend-friendly dicts for Cymor Movie Hub.
"""

from typing import Any


def serialize_search_item(item: Any) -> dict:
    """Convert a search result item into a clean dict."""
    try:
        return {
            "id": getattr(item, "id", None),
            "title": getattr(item, "title", None) or getattr(item, "name", None),
            "poster": getattr(item, "poster", None) or getattr(item, "poster_url", None),
            "year": getattr(item, "year", None),
            "rating": getattr(item, "rating", None) or getattr(item, "score", None),
            "type": getattr(item, "type", None),
            "page_url": getattr(item, "page_url", None),
            "description": getattr(item, "description", None) or getattr(item, "intro", None),
            "genres": _safe_list(getattr(item, "genres", None) or getattr(item, "category", None)),
        }
    except Exception:
        # Fallback — dump whatever attributes we can
        return _safe_dict(item)


def serialize_details(details: Any) -> dict:
    """Convert movie/series detail model into a clean dict."""
    try:
        raw = {}

        for attr in [
            "id", "title", "name", "poster", "poster_url", "backdrop",
            "year", "rating", "score", "description", "intro",
            "genres", "category", "cast", "director", "duration",
            "country", "language", "type", "seasons", "episodes",
            "page_url", "trailer_url",
        ]:
            val = getattr(details, attr, None)
            if val is not None:
                raw[attr] = val

        return {
            "id": raw.get("id"),
            "title": raw.get("title") or raw.get("name"),
            "poster": raw.get("poster") or raw.get("poster_url"),
            "backdrop": raw.get("backdrop"),
            "year": raw.get("year"),
            "rating": raw.get("rating") or raw.get("score"),
            "description": raw.get("description") or raw.get("intro"),
            "genres": _safe_list(raw.get("genres") or raw.get("category")),
            "cast": _safe_list(raw.get("cast")),
            "director": raw.get("director"),
            "duration": raw.get("duration"),
            "country": raw.get("country"),
            "language": raw.get("language"),
            "type": raw.get("type"),
            "seasons": raw.get("seasons"),
            "episodes": raw.get("episodes"),
            "trailer_url": raw.get("trailer_url"),
        }
    except Exception:
        return _safe_dict(details)


def serialize_download_files(files_detail: Any) -> dict:
    """Convert DownloadableFilesMetadata into clean video + subtitle lists."""
    try:
        videos = []
        subtitles = []

        downloads = getattr(files_detail, "downloads", []) or []
        captions = getattr(files_detail, "captions", []) or []

        for v in downloads:
            videos.append({
                "quality": str(getattr(v, "quality", None) or getattr(v, "resolution", "Unknown")),
                "url": getattr(v, "url", None) or getattr(v, "download_url", None),
                "size": getattr(v, "size", None) or getattr(v, "file_size", None),
                "format": getattr(v, "format", "mp4"),
            })

        for s in captions:
            subtitles.append({
                "language": getattr(s, "language", None) or getattr(s, "lang", "Unknown"),
                "url": getattr(s, "url", None) or getattr(s, "download_url", None),
                "format": getattr(s, "format", "srt"),
            })

        return {
            "videos": videos,
            "subtitles": subtitles,
            "best_quality": videos[0] if videos else None,
        }
    except Exception as e:
        return {"error": str(e), "videos": [], "subtitles": []}


def _safe_list(val: Any) -> list:
    if val is None:
        return []
    if isinstance(val, list):
        return val
    if isinstance(val, str):
        return [v.strip() for v in val.split(",") if v.strip()]
    return [val]


def _safe_dict(obj: Any) -> dict:
    """Last-resort serializer using __dict__."""
    try:
        if hasattr(obj, "__dict__"):
            return {k: str(v) for k, v in obj.__dict__.items() if not k.startswith("_")}
        if hasattr(obj, "dict"):
            return obj.dict()
        return {"raw": str(obj)}
    except Exception:
        return {}
