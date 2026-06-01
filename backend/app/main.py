from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import get_settings
from app.core.migrations import get_migration_status


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title='WorldSim-Writer API')
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_origin],
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )
    app.include_router(api_router)
    return app


app = create_app()


@app.get('/health')
def health_check() -> dict:
    settings = get_settings()
    return {'status': 'ok', 'migration': get_migration_status(), 'llm': {'mock': settings.llm_mock}}
