import os
from typing import Optional
from pydantic import ValidationError

from .interface import ICache
from schemas.metrics import TelemetryPayload
from schemas.session import SessionState

from shared.logger import get_logger
from shared.decorator import retry_on_failure
from shared.config import settings

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

        self.log.info(f"⚪ Connecting Redis to {host}:{port}...")

        self._client = redis.Redis(
            host=host, 
            port=port, 
            decode_responses=True,
            socket_timeout=5
        )

        # Ping test
        self.client.ping()
        self._initialized = True

        self.log.info("🟢 Redis Connected & Ready.")

    @retry_on_failure(max_retries=3, base_delay=0.5)
    def set_telemetry(self, payload: TelemetryPayload) -> None:
        
        key = os.environ.get("REDIS_COLLECTION", 'sessions/{0}/{1}').format(payload.session_id, "telemetry")
        json_data = payload.model_dump_json()
        self._client.set(key, json_data, ex=self._ttl)

        self._logger.debug(f"🟢 Saved telemetry data for {payload.session_id}")


    @retry_on_failure(max_retries=3, base_delay=0.5)
    def get_telemetry(self, session_id: str) -> Optional[TelemetryPayload]:
        
        key = os.environ.get("REDIS_COLLECTION", 'sessions/{0}/{1}').format(session_id, "telemetry")

        data = self.client.get(key)
        if not data:
            self._logger.warning(f"⚠️ Telemetry data not present for session id {session_id}")
            return None
        
        try:
            telemetry_data = TelemetryPayload.model_validate_json(data)
        except ValidationError as e:
            self._logger.warning(f"⚠️ Telemetry data not present for session id {session_id}")
            return None
        
        self._logger.debug(f"🟢 Telemetry data validated for {session_id}")
        
        return telemetry_data


    @retry_on_failure(max_retries=3, base_delay=0.5)
    def set_session(self, payload: SessionState) -> None:
        
        key = os.environ.get("REDIS_COLLECTION", 'sessions/{0}/{1}').format(payload.config.session_id, "state")
        json_data = payload.model_dump_json()
        self._client.set(key, json_data, ex=self._ttl)

        self._logger.debug(f"🟢 Saved session state data for {payload.config.session_id}")


    @retry_on_failure(max_retries=3, base_delay=0.5)
    def get_session(self, session_id: str) -> Optional[SessionState]:
        
        key = os.environ.get("REDIS_COLLECTION", 'sessions/{0}/{1}').format(session_id, "state")

        data = self.client.get(key)
        if not data:
            self._logger.warning(f"⚠️ Session state data corrupted for session id {session_id}")
            return None
        
        try:
            session_state_data = SessionState.model_validate_json(data)
        except ValidationError as e:
            self._logger.warning(f"⚠️ Session state data corrupted for session id {session_id}: {e}")
            return None
        
        self._logger.debug(f"🟢 Session state data validated for {session_id}")
        
        return session_state_data
