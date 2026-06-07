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

# Import your routers
from routers import movies, series, downloads, trending, recommendations

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

# Include routers
app.include_router(movies.router,         prefix="/api/movies",         tags=["Movies"])
app.include_router(series.router,         prefix="/api/series",         tags=["TV Series"])
app.include_router(downloads.router,      prefix="/api/downloads",      tags=["Downloads"])
app.include_router(trending.router,       prefix="/api/trending",       tags=["Trending"])
app.include_router(recommendations.router, prefix="/api/movies",         tags=["Recommendations"])

@app.get("/", tags=["Health"])
async def root():
    return {
        "name": "Cymor Movie Hub API",
        "status": "running",
        "version": "2.0.0",
        "author": "Legendary Smiley Cymor",
        "endpoints": {
            "trending":            "/api/trending",
            "movies_search":       "/api/movies/search?q=avatar",
            "movie_details":       "/api/movies/{id}",
            "recommendations":     "/api/movies/{id}/recommendations",
            "docs":                "/docs",
        },
    }

@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "service": "cymor-movie-hub"}
