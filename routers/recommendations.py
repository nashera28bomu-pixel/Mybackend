# utils/recommendations.py
import httpx
import logging
import os

# This pulls the variable you saved in the Render dashboard
TMDB_API_KEY = os.environ.get("TMDB_API_KEY")
TMDB_BASE = "https://api.themoviedb.org/3"

logger = logging.getLogger("cymor.recommendations")

async def get_movie_recommendations(imdb_id: str):
    if not TMDB_API_KEY:
        logger.error("TMDB_API_KEY is not set in environment variables!")
        return []

    try:
        async with httpx.AsyncClient() as client:
            # 1. Map IMDB ID to TMDB ID
            find_url = f"{TMDB_BASE}/find/{imdb_id}?api_key={TMDB_API_KEY}&external_source=imdb_id"
            find_res = await client.get(find_url)
            tmdb_data = find_res.json()
            
            movie_results = tmdb_data.get("movie_results", [])
            if not movie_results: 
                return []
            
            tmdb_id = movie_results[0]["id"]
            
            # 2. Fetch recommendations
            rec_url = f"{TMDB_BASE}/movie/{tmdb_id}/recommendations?api_key={TMDB_API_KEY}"
            rec_res = await client.get(rec_url)
            data = rec_res.json()
            
            # 3. Clean and format the list
            return [
                {
                    "id": m.get("id"),
                    "title": m.get("title"),
                    "poster": f"https://image.tmdb.org/t/p/w500{m.get('poster_path')}" if m.get("poster_path") else "",
                    "year": m.get("release_date", "")[:4],
                    "type": "movie"
                }
                for m in data.get("results", [])[:6]
            ]
    except Exception as e:
        logger.error(f"Recommendation service failed for {imdb_id}: {e}")
        return []
