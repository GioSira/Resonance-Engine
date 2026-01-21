import os
from typing import Optional

from .interface import IDatabase
from schemas.metrics import TelemetryPayload
from schemas.session import SessionConfig, SessionState
from shared.decorator import retry_on_failure
from shared.logger import get_logger
from shared.config import settings

import firebase_admin
from firebase_admin import credentials, firestore


class FirebaseService(IDatabase):

    _instance = None

    
    def __init__(self):
        self._logger = get_logger("FIREBASE_SVC")
        self._initalized = False

    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FirebaseService, cls).__new__(cls)

        return cls._instance
        
    
    @retry_on_failure(max_retries=5, base_delay=2.0)
    def connect(self) -> None:
        
        if self._initialized: return

        self._logger.info("⚪ Connecting to Firebase DB")

        cred_path = settings.FIRESTORE_KEY_FILE
        
        if (not cred_path) and (not os.path.exists(cred_path)):
            self._logger.error(f"🔴 Credential not found in {cred_path}")
            raise FileNotFoundError(f"Credential not found in {cred_path}")

        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
        self._db = firestore.client()

        self._initialized = True

        self._logger.info("🟢 Connection to Firebase estabilished.")

    
    @retry_on_failure(max_retries=3, base_delay=0.5)
    def set_telemetry(self, payload: TelemetryPayload) -> None:
        
        path = settings.FIRESTORE_COLLECTION

        # get or create collection
        doc_ref = self._db.collection(path).document('metrics')

        # update data
        doc_ref.update(payload.metrics)

        self._logger.debug(f"🟢 Valid update for {payload.session_id}")


    @retry_on_failure(max_retries=3, base_delay=0.5)
    def set_session(self, payload: SessionState) -> None:
        
        path = settings.FIRESTORE_COLLECTION
        
        doc_ref = self._db.collection(path).document("state")

        doc_ref.update(payload)

        self._logger.debug(f"🟢 Valid update for {payload.config.session_id}")

    
    @retry_on_failure(max_retries=3, base_delay=0.5)
    def get_telemetry(self, session_id: str) -> Optional[SessionState]:
        
        path = settings.FIRESTORE_COLLECTION

        self.log.debug(f"🔍 Search session {session_id} from Firebase...")

        state_ref = self._db.collection(path).document("telemetry")
        if not state_ref:
            self._logger.warning(f"⚠️ Telemetry for session id {session_id} not present in Redis")
            return None
        
        return state_ref.get()


    @retry_on_failure(max_retries=3, base_delay=0.5)
    def get_session(self, session_id: str) -> Optional[TelemetryPayload]:
        
        path = settings.FIRESTORE_COLLECTION

        self.log.debug(f"🔍 Search session {session_id} from Firebase...")

        state_ref = self._db.collection(path).document("state")
        if not state_ref:
            self._logger.warning(f"⚠️ Session state for session id {session_id} not present in Redis")
            return None
        
        return state_ref.get()
        