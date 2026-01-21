from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException

from src.schemas.metrics import TelemetryPayload
from src.schemas.session import SessionConfig, SessionState
from src.engine.interface import IOrchestrator
from src.music.interface import IMusicProvider
from src.shared.logger import get_logger

log = get_logger("ROUTES")



router = APIRouter(prefix='/v0.1')


# --- GLOBAL STATE CONTAINER ---
class AppState:
    orchestrator: IOrchestrator = None
    music_provider = None

state = AppState()


# --- DEPENDENCIES ---

def get_orchestrator():
    if not state.orchestrator:
        raise HTTPException(status_code=503, detail="System not initialized")
    return state.orchestrator

def get_music():
    if not state.music_provider:
        raise HTTPException(status_code=503, detail="Music system offline")
    return state.music_provider


# --- BACKGROUND WORKERS ---

def process_music_change(genre: str, provider):
    """Questa funzione gira in un thread separato"""
    if genre:
        provider.play_genre(genre)


# --- ENDPOINTS ---

@router.get("/health")
async def health_check():
    """Ping per vedere se il server è vivo"""
    return {"status": "active", "version": "0.1.0"}


@router.post("/session/setup")
async def setup_session(config: SessionConfig, orchestrator: IOrchestrator = Depends(get_orchestrator)):
    try:
        # Salviamo la config su DB e Cache
        orchestrator.db.save_config(config)
        orchestrator.cache.set_session_state(
            # Costruiamo uno stato iniziale pulito
            # (Nota: importare SessionState se serve ricostruirlo qui)
            pass 
        )
        return {"message": f"Session {config.session_id} initialized"}
    except Exception as e:
        log.error(f"Setup error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    

@router.post("/telemetry")
async def ingest_telemetry(
    payload: TelemetryPayload, 
    background_tasks: BackgroundTasks,
    orchestrator: IOrchestrator = Depends(get_orchestrator),
    music: IMusicProvider = Depends(get_music)
):
    """
    Endpoint ad alta frequenza (riceve dati ogni secondo).
    Deve essere velocissimo.
    """
    # 1. Process Logic (Veloce: Redis + CPU Rules)
    target_genre = orchestrator.process_telemetry(payload)
    
    # 2. Action (Lenta: Chiamata API Spotify) -> Background
    if target_genre:
        # Non aspettiamo Spotify qui! Lo mandiamo in coda.
        background_tasks.add_task(process_music_change, target_genre, music)
    
    return {"status": "processed", "triggered_genre": target_genre}
