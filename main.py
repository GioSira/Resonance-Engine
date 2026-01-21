import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

# internal imports
from src.cache.factory import CacheFactory
from src.database.factory import DatabaseFactory
from src.music.factory import MusicFactory
from src.engine.orchestrator import Orchestrator
from src.shared.logger import get_logger
from src.shared.config import settings
from src.api.routes import router, state


log = get_logger("API_MAIN")



# --- LIFESPAN ---
@asynccontextmanager
async def lifespan(app: FastAPI):

    """
    Executed on server start. Initialize all connections.
    """

    log.info("🚀 Server Starting...")

    try:

        cache = CacheFactory.get_cache(settings.CHACHE_TYPE)
        db = DatabaseFactory.get_database(settings.DB_TYPE)
        music = MusicFactory.get_music_provider(settings.MUSIC_PROVIDER)

        state.orchestrator = Orchestrator(cache=cache, database=db)
        state.music_provider = music

        log.info("✅ All systems go.")
        yield # Server starting accepting requests

    except Exception as e:
        log.critical(f"🔥 Startup Failed: {e}")
        raise e
    
    finally:
        log.info("🛑 Server shutting down.")



# --- APP DEFINITION ---
def create_app() -> FastAPI:
    app = FastAPI(
        title="DSO Neural Orchestrator",
        version="0.1.0",
        lifespan=lifespan
    )
    app.include_router(router)

    return app



# --- ENTRY POINT (Per debug locale) ---
if __name__ == "__main__":
    import uvicorn
    # Lancia il server su localhost:8000
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
