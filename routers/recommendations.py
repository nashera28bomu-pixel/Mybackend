from fastapi import APIRouter
from utils.recommendations import get_movie_recommendations

# THIS IS THE MISSING PIECE
router = APIRouter()

@router.get("/{imdb_id}/recommendations")
async def get_recommendations(imdb_id: str):
    return await get_movie_recommendations(imdb_id)
