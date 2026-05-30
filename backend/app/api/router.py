from fastapi import APIRouter

from app.auth.router import router as auth_router
from app.character.relation_router import router as relation_router
from app.character.router import router as character_router
from app.foreshadow.router import router as foreshadow_router
from app.narrative.router import router as narrative_router
from app.narrative_control_center.router import router as narrative_control_center_router
from app.snapshot_export.router import router as snapshot_export_router
from app.world.router import router as world_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(world_router)
api_router.include_router(character_router)
api_router.include_router(relation_router)
api_router.include_router(foreshadow_router)
api_router.include_router(narrative_router)
api_router.include_router(narrative_control_center_router)
api_router.include_router(snapshot_export_router)
