import os
from typing import Optional, List
from concurrent.futures import ThreadPoolExecutor

from cache.interface import ICache
from database.interface import IDatabase

from schemas.session import SessionState, TriggerRule
from schemas.metrics import TelemetryPayload

from .interface import IOrchestrator
from .strategies import RuleEvaluator
from shared.logger import get_logger

import time
import hashlib


class Orchestrator(IOrchestrator):

    def __init__(self, cache: ICache, db: IDatabase):
        self._cache = cache
        self._db = db
        self._logger = get_logger("ORCHESTRATOR")
        self._executor = ThreadPoolExecutor(max_workers=5)


    def _hash_payload(self, session_id: str, metric: str, delta: float) -> str:
        fingerprint = hashlib.sha256(f"{session_id}:{metric}:{delta}".encode()).hexdigest()
        return fingerprint
    

    # =====================================
    # Section 1: Fast calls 
    # =====================================
    
    def update_metric(self, session_id: str, metric: str, delta: float) -> float:

        if self._cache.check_and_set_dedup(self._hash_payload(session_id, metric, delta)):
            self._logger.debug(f"🟢 Metric {metric} for session {session_id} already processed")
            return self._cache.get_metric(session_id, metric)

        try:
            value = self._cache.update_metric(session_id, metric, delta)
            return value
        except Exception as e:
            self._logger.error(f"🔴 Error while updating metric {metric} for session {session_id}: {e}")
            raise e


    def process_telemetry(self, payload: TelemetryPayload) -> bool:
        
        try:
            
            # 1) update or insert into cache
            self._cache.set_telemetry(payload)

            # 2) update or insert into db (async)
            self._executor.submit(self._safe_db_sync, "telemetry", payload)

            self._logger.debug(f"🟢 Telemetry with session id {payload.session_id} correctly processed")

            return True
        
        except Exception as e:
            
            self._logger.error(f"🔴 Error while saving telemetry with session id {payload.session_id}: {e}")
            return False

    def process_session(self, payload: SessionState) -> bool:

        try:
        
            # 1) update or insert into cache
            self._cache.set_session(payload)

            # 2) update or insert into db (async)
            self._executor.submit(self._safe_db_sync, "session", payload)

            self._logger.debug(f"🟢 Session state with session id {payload.config.session_id} correctly processed")

            return True
        
        except Exception as e:
            
            self._logger.error(f"🔴 Error while saving session with session id {payload.config.session_id}: {e}")
            return False


    # =====================================
    # Section 2: Slow calls 
    # =====================================


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
            self._cache.set_all_metrics(session_id, data_db.metrics)
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

    def flush_into_db(self, session_id: str) -> bool:
        """
        Flush all data from cache into database.
        """
        try:
            
            current_metrics = self._cache.get_all_metrics(session_id)
            telemetry_state = self._cache.get_telemetry(session_id)
            session_state = self._cache.get_session(session_id)

            if not session_state:
                self._logger.warning(f"Session {session_id} not found in cache")
                return False
            
            if not current_metrics:
                self._logger.warning(f"Current metrics {session_id} not found in cache")
                return False
            
            if not telemetry_state:
                self._logger.warning(f"Telemetry {session_id} not found in cache")
                return False

            telemetry_state.metrics = current_metrics
            session_state.last_metrics = current_metrics

            self._executor.submit(self._safe_db_sync, "telemetry", telemetry_state)
            self._executor.submit(self._safe_db_sync, "session", session_state)

            self._logger.debug(f"🟢 Session data with session id {session_id} correctly flushed into database")
            return True

        except Exception as e:
            self._logger.error(f"🔴 Error while flushing cache into database: {e}")
            return False


    # =====================================
    # Section 3: Metrics 
    # =====================================

    def set_metric(self, session_id: str, metric: str, value: float) -> None:
        self._cache.set_metric(session_id, metric, value)

    def get_metric(self, session_id: str, metric: str) -> float:
        return self._cache.get_metric(session_id, metric)

    def delete_metric(self, session_id: str, metric: str) -> bool:
        return self._cache.delete_metric(session_id, metric)

    def get_all_metrics(self, session_id: str) -> dict[str, float]:
        return self._cache.get_all_metrics(session_id)

    def clear_all_metrics(self, session_id: str) -> bool:
        return self._cache.clear_all_metrics(session_id)


    # =====================================
    # Section 4: Internal methods 
    # =====================================
    
    def _safe_db_sync(self, table: str, payload: Union[SessionState, TelemetryPayload]) -> None:
        
        """
        Safe database sync method.
        """
        try:
            if table == "session":
                self._db.set_session(payload)
            elif table == "telemetry":
                self._db.set_telemetry(payload)
            else:
                raise ValueError(f"Invalid table name: {table}")
        except Exception as e:
            self._logger.error(f"🔴 Error while saving {table} with session id {payload.config.session_id}: {e}")
