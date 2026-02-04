import os
from typing import Optional
from pydantic import ValidationError

from .interface import ICache
from src.schemas.metrics import TelemetryPayload
from src.schemas.session import SessionState

from src.shared.logger import get_logger
from src.shared.decorator import retry_on_failure
from src.shared.config import settings

import redis


class RedisCache(ICache):

    _instance = None

    def __init__(self):
        self._client = None
        # define TTL i.e. life of data
        self._ttl = 3600 # 1 hour
        self._logger = get_logger("REDIS_CACHE")
        self._initialized = False


    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RedisCache, cls).__new__(cls)

        return cls._instance
    

    @retry_on_failure(max_retries=5, base_delay=2.0)
    def connect(self):

        if self._initialized: return

        host = settings.REDIS_HOST or 'localhost'
        port = int(settings.REDIS_PORT) or 6379
        user = settings.REDIS_USER
        password = settings.REDIS_PASSWORD

        self._logger.info(f"⚪ Connecting Redis to {host}:{port}...")

        self._client = r = redis.Redis(
            host=host,
            port=port,
            decode_responses=True,
            username=user,
            password=password,
        )

        # Ping test
        self._client.ping()
        self._initialized = True

        self._logger.info("🟢 Redis Connected & Ready.")

    
    @retry_on_failure(max_retries=3, base_delay=0.5)
    def set_telemetry(self, payload: TelemetryPayload) -> None:
        
        key = f"sessions:{payload.session_id}:telemetry"
        json_data = payload.model_dump_json()
        self._client.set(key, json_data, ex=self._ttl)

        self._logger.debug(f"🟢 Saved Telemetry data for {payload.session_id}")


    @retry_on_failure(max_retries=3, base_delay=0.5)
    def get_telemetry(self, session_id: str) -> Optional[TelemetryPayload]:
        
        key = f"sessions:{session_id}:telemetry"

        data = self._client.get(key)
        if not data:
            self._logger.warning(f"⚠️ Telemetry data not present for session id {session_id}")
            return None
        
        try:
            telemetry_data = TelemetryPayload.model_validate_json(data)
        except ValidationError as e:
            self._logger.warning(f"⚠️ Telemetry data not present for session id {session_id}: {e}")
            return None
        
        self._logger.debug(f"🟢 Telemetry data validated for {session_id}")
        
        return telemetry_data


    @retry_on_failure(max_retries=3, base_delay=0.5)
    def set_session(self, payload: SessionState) -> None:
        
        key = f"sessions:{payload.session_id}:state"
        json_data = payload.model_dump_json()
        self._client.set(key, json_data, ex=self._ttl)

        self._logger.debug(f"🟢 Saved session state data for {payload.session_id}")


    @retry_on_failure(max_retries=3, base_delay=0.5)
    def get_session(self, session_id: str) -> Optional[SessionState]:
        
        key = f"sessions:{session_id}:state"

        data = self._client.get(key)
        if not data:
            self._logger.warning(f"⚠️ SessionState data corrupted for session id {session_id}")
            return None
        
        try:
            session_state_data = SessionState.model_validate_json(data)
        except ValidationError as e:
            self._logger.warning(f"⚠️ SessionState data corrupted for session id {session_id}: {e}")
            return None
        
        self._logger.debug(f"🟢 SessionState data validated for {session_id}")
        
        return session_state_data
    

    @retry_on_failure(max_retries=3, base_delay=0.5)
    def update_telemetry(self, payload: TelemetryPayload) -> bool:
        
        key = f"sessions:{payload.session_id}:telemetry"

        try:
            self._client.set(key, payload.model_dump_json(), ex=self._ttl)
            self._logger.debug(f"📡 Telemetry snapshot updated for {payload.session_id}")
            return True
        except Exception as e:
            self._logger.error(f"❌ Telemetry update failed: {e}")
            return False


    @retry_on_failure(max_retries=3, max_delay=0.5)
    def update_session(self, payload: TelemetryPayload) -> bool:
        
        key = f"sessions:{payload.session_id}:state"

        try:
            self._client.set(key, payload.model_dump_json(), ex=self._ttl)
            self._logger.debug(f"📡 SessionState snapshot updated for {payload.session_id}")
            return True
        except Exception as e:
            self._logger.error(f"❌ SessionState update failed: {e}")
            return False
    

    @retry_on_failure(max_retries=3, max_delay=1.0)
    def delete_telemetry(self, session_id: str) -> bool:
        
        try:
            key = f"sessions:{session_id}:telemetry"
            result = self._client.delete(key)
            if result > 0:
                self._logger.info(f"🟢 Telemetry data deleted for session {session_id}")
                return True
            else:
                self._warning(f"⚠️ No data found for Telemetry {session_id}")
        except Exception as e:
            self._logger.error(f"❌ Telemetry delete failed: {e}")
        
        return False


    @retry_on_failure(max_delay=3, base_delay=1.0)
    def delete_session(self, session_id: str):
    
        try:
            key = f"sessions:{session_id}:state"
            result = self._client.delete(key)
            if result > 0:
                self._logger.info(f"🟢 SessionState data deleted for session {session_id}")
                return True
            else:
                self._warning(f"⚠️ No data found for SessionState {session_id}")
        except Exception as e:
            self._logger.error(f"❌ SessionState delete failed: {e}")
            
        return False

    
    def clear_all(self):
        
        if os.getenv("ENV") != "test" and os.getenv("ALLOW_CLEANUP") != "true":
            raise PermissionError(f"Operation Denied. Ambient not setted for testing")
        
        self._inernal_clean_all()


    def _internal_clear_all(self):
        
        try:
            
            pattern = "sessions/*" # get all sessions
            keys = self._client.keys(pattern)

            if keys:
                self._client.delete(keys)
                self._logger.info(f"🧹 Database cleaned: removed {len(keys)} keys with pattern '{pattern}'")
            else:
                self._logger.debug(f"⚠️ No key found with pattern {pattern}. Already cleaned.")

        except Exception as e:

            self._logger.error(f"❌ Errore during method clear_all: {e}")
