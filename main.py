"""
Cymor Movie Hub - FastAPI Backend
By Legendary Smiley Cymor | Cymor Tech Services
Always a winner.
"""

from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
import asyncio
import httpx
import logging
from typing import Optional
from contextlib import asynccontextmanager

from routers import movies, series, downloads, trending
from utils.cache import cache

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cymor-movie-hub")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🎬 Cymor Movie Hub Backend starting up...")
    yield
    logger.info("🎬 Cymor Movie Hub Backend shutting down...")


app = FastAPI(
    title="Cymor Movie Hub API",
    description="Backend API for Cymor Movie Hub — powering movies & TV series search, details, and downloads.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow your frontend (Vercel, localhost) to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8080",
        "https://*.vercel.app",
        "https://*.netlify.app",
        # Add your actual frontend domain here:
        # "https://cymormovies.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(movies.router, prefix="/api/movies", tags=["Movies"])
app.include_router(series.router, prefix="/api/series", tags=["TV Series"])
app.include_router(downloads.router, prefix="/api/downloads", tags=["Downloads"])
app.include_router(trending.router, prefix="/api/trending", tags=["Trending"])


@app.get("/", tags=["Health"])
async def root():
    return {
        "name": "Cymor Movie Hub API",
        "status": "running",
        "version": "1.0.0",
        "author": "Legendary Smiley Cymor",
        "motto": "Always a winner.",
        "endpoints": {
            "movies_search": "/api/movies/search?q=avatar",
            "movie_details": "/api/movies/{item_id}",
            "movie_downloads": "/api/movies/{item_id}/downloads",
            "series_search": "/api/series/search?q=merlin",
            "series_details": "/api/series/{item_id}",
            "series_episode_downloads": "/api/series/{item_id}/downloads?season=1&episode=1",
            "trending": "/api/trending",
            "docs": "/docs",
        },
    }


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "service": "cymor-movie-hub"}
