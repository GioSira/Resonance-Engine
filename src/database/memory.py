import os
import threading
from typing import Dict, Optional
from pydantic import validate_call

from .interface import IDatabase
from schemas.metrics import TelemetryPayload
from schemas.session import SessionState
from shared.logger import get_logger

class MemoryService(IDatabase):

    _instance = None

    def __init__(self):
        self._logger = get_logger("MEMORY_SVC")
        self._initalized = False

        self._telemetry_store: Dict[str, TelemetryPayload] = {}
        self._session_store: Dict[str, SessionState] = {}
        self._lock = threading.Lock() # Mutex per thread safety

    def __new__(cls):
        
        if cls._instance is None:
            cls._instance = super(MemoryService, cls).__new__(cls)
        
        return cls._instance
    
    
    def connect(self):
       self._logger.info("💾 MemoryService created (Thread-Safe).")
       self._initalized = True


    def update_telemetry(self, payload: TelemetryPayload) -> None:
        with self._lock:
            self._telemetry_store[payload.session_id] = payload
            self._logger.info(f"🟢 Telemetry payload saved for session {payload.session_id}")
    

    def get_telemetry(self, session_id: str) -> Optional[TelemetryPayload]:

        if not(session_id in self._telemetry_store):
            self._logger.error(f"🔴 Session id {session_id} not in telemetry_store db")
            raise ValueError(f"Session id {session_id} not in telemetry_store db")

        with self._lock:
            payload =  self._telemetry_store.get(session_id)
            self._logger.info(f"🟢 Telemetry found with {session_id}")
            return payload


    def update_session(self, payload: SessionState) -> None:
        with self._lock:
            self._session_store[payload.config.session_id] = payload
            self._logger.info(f"🟢 Telemetry payload saved for session {payload.session_id}")


    def get_session_state(self, session_id: str) -> Optional[SessionState]:

        if not(session_id in self._session_store):
            self._logger.error(f"🔴 Session id {session_id} not in session_state db")
            raise ValueError(f"Session id {session_id} not in session_state db")

        with self._lock:
            payload = self._session_store.get(session_id)
            self._logger.info(f"🟢 Session state found with {session_id}")
            return payload
