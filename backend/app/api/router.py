from fastapi import APIRouter

from app.auth.router import router as auth_router
from app.character.router import router as character_router
from app.foreshadow.router import router as foreshadow_router
from app.narrative.router import router as narrative_router
from app.world.router import router as world_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(world_router)
api_router.include_router(character_router)
api_router.include_router(foreshadow_router)
api_router.include_router(narrative_router)
