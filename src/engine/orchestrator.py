import os
from typing import Optional, List

from cache.interface import ICache
from database.interface import IDatabase

from schemas.session import SessionState, TriggerRule
from schemas.metrics import TelemetryPayload

from .interface import IOrchestrator
from .strategies import RuleEvaluator
from shared.logger import get_logger


class Orchestrator(IOrchestrator):

    def __init__(self, cache: ICache, db: IDatabase):
        self._cache = cache
        self._db = db
        self._logger = get_logger("ORCHESTRATOR")


    def process_telemetry(self, payload: TelemetryPayload) -> bool:
        
        try:
            
            # 1) update or insert into cache
            self._cache.set_telemetry(payload)

            # 2) update or insert into db
            self._db.set_telemetry(payload)

            self._logger.debug(f"🟢 Telemetry with session id {payload.session_id} correctly processed")

            return True
        
        except Exception as e:
            
            self.log.error(f"🔴 Error while saving telemetry with session id {payload.session_id}: {e}")
            return False


    def process_session(self, payload: SessionState) -> bool:

        try:
        
            # 1) update or insert into cache
            self._cache.set_session(payload)

            # 2) update or insert into db
            self._db.set_session(payload)

            self._logger.debug(f"🟢 Session state with session id {payload.config.session_id} correctly processed")

            return True
        
        except Exception as e:
            
            self.log.error(f"🔴 Error while saving session with session id {payload.config.session_id}: {e}")
            return False


    def get_telemetry(self, session_id) -> Optional[TelemetryPayload]:
        
        # check if present into cache
        data_cache = self._cache.get_telemetry(session_id)
        if data_cache:
            self._logger.debug(f"🟢 Telemetry data present with session id {session_id} present in cache")
            return data_cache
        
        # session_id not in cache, searching db
        data_db = self._db.get_telemetry(session_id)
        if data_db:
            self._logger.debug(f"🟢 Telemetry data present with session id {session_id} present in db")
            # data present into db, save it in cache
            self._cache.set_telemetry(data_db)
            return data_db
        
        # not present into db or cache, return None
        self._logger.error(f"🔴 Telemetry data with session id {session_id} present neither in cache nor db")
        return None


    def get_session(self, session_id) -> Optional[SessionState]:
        
        # check if present into cache
        data_cache = self._cache.get_session(session_id)
        if data_cache:
            self._logger.debug(f"🟢 Session data present with session id {session_id} present in cache")
            return data_cache
        
        # session_id not in cache, searching db
        data_db = self._db.get_session(session_id)
        if data_db:
            self._logger.debug(f"🟢 Session data present with session id {session_id} present in db")
            # data present into db, save it in cache
            self._cache.set_session(data_db)
            return data_db
        
        # not present into db or cache, return None
        self._logger.error(f"🔴 Session data with session id {session_id} present neither in cache nor db")
        return None
