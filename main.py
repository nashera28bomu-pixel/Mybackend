"""
Cymor Movie Hub - FastAPI Backend v2
TMDB for metadata | Custom scraper for downloads
By Legendary Smiley Cymor | Cymor Tech Services
Always a winner.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from routers import movies, series, downloads, trending

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cymor")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🎬 Cymor Movie Hub v2 starting — TMDB powered")
    yield
    logger.info("🎬 Cymor Movie Hub shutting down")


app = FastAPI(
    title="Cymor Movie Hub API",
    description="TMDB-powered movie & series API with download scraping. By Legendary Smiley Cymor.",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(movies.router,    prefix="/api/movies",    tags=["Movies"])
app.include_router(series.router,    prefix="/api/series",    tags=["TV Series"])
app.include_router(downloads.router, prefix="/api/downloads", tags=["Downloads"])
app.include_router(trending.router,  prefix="/api/trending",  tags=["Trending"])


@app.get("/", tags=["Health"])
async def root():
    return {
        "name": "Cymor Movie Hub API",
        "status": "running",
        "version": "2.0.0",
        "author": "Legendary Smiley Cymor",
        "motto": "Always a winner.",
        "powered_by": "TMDB + Custom Scraper",
        "endpoints": {
            "trending":            "/api/trending",
            "movies_search":       "/api/movies/search?q=avatar",
            "movie_details":       "/api/movies/{tmdb_id}",
            "movie_downloads":     "/api/movies/{tmdb_id}/downloads",
            "series_search":       "/api/series/search?q=breaking+bad",
            "series_details":      "/api/series/{tmdb_id}",
            "episode_downloads":   "/api/series/{tmdb_id}/downloads?season=1&episode=1",
            "docs":                "/docs",
        },
    }


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "service": "cymor-movie-hub"}
