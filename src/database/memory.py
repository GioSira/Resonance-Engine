import os
import threading
from typing import Dict, Optional

from .interface import IDatabase
from src.schemas.metrics import TelemetryPayload
from src.schemas.session import SessionState, SessionConfig
from src.shared.logger import get_logger

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


    def set_telemetry(self, payload: TelemetryPayload) -> None:
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


    def set_session(self, payload: SessionState) -> None:
        with self._lock:
            self._session_store[payload.config.session_id] = payload
            self._logger.info(f"🟢 Telemetry payload saved for session {payload.session_id}")


    def get_session(self, session_id: str) -> Optional[SessionState]:

        if not(session_id in self._session_store):
            self._logger.error(f"🔴 Session id {session_id} not in session_state db")
            raise ValueError(f"Session id {session_id} not in session_state db")

        with self._lock:
            payload = self._session_store.get(session_id)
            self._logger.info(f"🟢 Session state found with {session_id}")
            return payload
        

    def update_telemetry(self, payload):

        if not(payload.session_id in self._telemetry_store):
            self._logger.info(f"⚠️ Session id {payload.session_id} not in telemetry_store db")
            return False
        
        with self._lock:
            self._telemetry_store[payload.session_id] = payload

        return True

    
    def update_session(self, payload):
        
        if not(payload.config.session_id in self._session_store):
            self._logger.info(f"⚠️ Session id {payload.session_id} not in session_storer db")
            return False
        
        with self._lock:
            self._session_store[payload.session_id] = payload

        return True
    
    
    def delete_telemetry(self, session_id):
        
        with self._lock:
            if not(session_id in self._telemetry_store):
                self._logger.error(f"🔴 Session id {session_id} not in telemetry_store db")
                raise ValueError(f"Session id {session_id} not in telemetry_store db")
            
            self._telemetry_store.pop(session_id)


    def delete_session(self, session_id):
        
        with self._lock:
            if not(session_id in self._session_store):
                self._logger.error(f"🔴 Session id {session_id} not in session_store db")
                raise ValueError(f"Session id {session_id} not in session_store db")
            
            self._session_store.pop(session_id)

    
    def clear_all(self):
        
        if os.getenv("ENV") != "test" and os.getenv("ALLOW_CLEANUP") != "true":
            raise PermissionError(f"Operation Denied. Ambient not setted for testing")
        
        self._internal_clear_all()

    
    def _internal_clear_all(self):

        with self._lock:
            self._telemetry_store = {}
            self._session_store = {}
            self._initalized = False
