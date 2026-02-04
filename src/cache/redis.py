import os
import re
from typing import Optional, Dict
from pydantic import ValidationError

from .interface import ICache
from src.schemas.metrics import TelemetryPayload
from src.schemas.session import SessionState

from src.shared.logger import get_logger
from src.shared.decorator import retry_on_failure
from src.shared.config import settings

import redis


class RedisCache(ICache):
    """
    Singleton implementation of ICache using Redis for high-performance data storage.
    Handles session state, telemetry payloads, and atomic high-frequency metrics.
    """

    _instance = None
    _METRIC_PATTERN = re.compile(r"^[a-zA-Z0-9_]+$")

    def __init__(self):
        """Initializes the RedisCache instance with default TTL and logger."""
        self._client = None
        self._ttl = 3600  # 1 hour
        self._logger = get_logger("REDIS_CACHE")
        self._initialized = False

    def __new__(cls):
        """Ensures a singleton instance of the RedisCache class."""
        if cls._instance is None:
            cls._instance = super(RedisCache, cls).__new__(cls)
        return cls._instance

    @retry_on_failure(max_retries=5, base_delay=2.0)
    def connect(self):
        """
        Establishes a connection to the Redis server using environment settings.
        Validates the connection with a ping test.
        """
        if self._initialized:
            return

        host = settings.REDIS_HOST or 'localhost'
        port = int(settings.REDIS_PORT) or 6379
        user = settings.REDIS_USER
        password = settings.REDIS_PASSWORD

        self._logger.info(f"⚪ Connecting Redis to {host}:{port}...")

        self._client = redis.Redis(
            host=host,
            port=port,
            decode_responses=True,
            username=user,
            password=password,
        )

        self._client.ping()
        self._initialized = True
        self._logger.info("🟢 Redis Connected & Ready.")

    # ---------------------------------------------------------
    # SECTION 1: Standard JSON Storage (Session & Telemetry)
    # ---------------------------------------------------------

    @retry_on_failure(max_retries=3, base_delay=0.5)
    def set_telemetry(self, payload: TelemetryPayload) -> None:
        """Serializes and stores telemetry data for a specific session."""
        key = f"sessions:{payload.session_id}:telemetry"
        self._client.set(key, payload.model_dump_json(), ex=self._ttl)
        self._logger.debug(f"🟢 Saved Telemetry data for {payload.session_id}")

    @retry_on_failure(max_retries=3, base_delay=0.5)
    def get_telemetry(self, session_id: str) -> Optional[TelemetryPayload]:
        """Retrieves and validates telemetry data from Redis for a session."""
        key = f"sessions:{session_id}:telemetry"
        data = self._client.get(key)
        if not data:
            self._logger.warning(f"⚠️ Telemetry data not present for session id {session_id}")
            return None
        
        try:
            return TelemetryPayload.model_validate_json(data)
        except ValidationError as e:
            self._logger.warning(f"⚠️ Telemetry data corrupted for session id {session_id}: {e}")
            return None

    @retry_on_failure(max_retries=3, base_delay=0.5)
    def set_session(self, payload: SessionState) -> None:
        """Stores the current session state as a JSON string in Redis."""
        key = f"sessions:{payload.session_id}:state"
        self._client.set(key, payload.model_dump_json(), ex=self._ttl)
        self._logger.debug(f"🟢 Saved session state data for {payload.session_id}")

    @retry_on_failure(max_retries=3, base_delay=0.5)
    def get_session(self, session_id: str) -> Optional[SessionState]:
        """Retrieves and validates the session state from Redis."""
        key = f"sessions:{session_id}:state"
        data = self._client.get(key)
        if not data:
            self._logger.warning(f"⚠️ SessionState not found for session id {session_id}")
            return None
        
        try:
            return SessionState.model_validate_json(data)
        except ValidationError as e:
            self._logger.warning(f"⚠️ SessionState data corrupted for session id {session_id}: {e}")
            return None

    @retry_on_failure(max_retries=3, base_delay=0.5)
    def update_telemetry(self, payload: TelemetryPayload) -> bool:
        """Updates an existing telemetry entry, returning success status."""
        key = f"sessions:{payload.session_id}:telemetry"
        try:
            self._client.set(key, payload.model_dump_json(), ex=self._ttl)
            self._logger.debug(f"📡 Telemetry snapshot updated for {payload.session_id}")
            return True
        except Exception as e:
            self._logger.error(f"❌ Telemetry update failed: {e}")
            return False

    @retry_on_failure(max_retries=3, max_delay=0.5)
    def update_session(self, payload: SessionState) -> bool:
        """Updates an existing session state entry, returning success status."""
        key = f"sessions:{payload.session_id}:state"
        try:
            self._client.set(key, payload.model_dump_json(), ex=self._ttl)
            return True
        except Exception as e:
            self._logger.error(f"❌ SessionState update failed: {e}")
            return False

    @retry_on_failure(max_retries=3, max_delay=1.0)
    def delete_telemetry(self, session_id: str) -> bool:
        """Removes telemetry data for a session from the cache."""
        try:
            key = f"sessions:{session_id}:telemetry"
            return bool(self._client.delete(key))
        except Exception as e:
            self._logger.error(f"❌ Telemetry delete failed: {e}")
            return False

    @retry_on_failure(max_delay=3, base_delay=1.0)
    def delete_session(self, session_id: str) -> bool:
        """Removes session state data from the cache."""
        try:
            key = f"sessions:{session_id}:state"
            return bool(self._client.delete(key))
        except Exception as e:
            self._logger.error(f"❌ SessionState delete failed: {e}")
            return False

    # ---------------------------------------------------------
    # SECTION 2: TTRPG High-Frequency Metrics (Atomic)
    # ---------------------------------------------------------

    @retry_on_failure(max_retries=3, base_delay=1.0)
    def set_metric(self, session_id: str, metric: str, value: float) -> None:
        """
        Atomically sets a numeric metric using Redis HSET.
        Includes sanitization to prevent key injection.
        """
        if not self._METRIC_PATTERN.match(metric):
            self._logger.error(f"⛔ Injection attempt detected on metric {metric}")
            raise ValueError("Invalid metric name")
        
        key = f"sessions:{session_id}:metrics"
        self._client.hset(key, metric, value)
        self._client.expire(key, self._ttl)
        self._logger.debug(f"🟢 Metric {metric} set to {value} for session {session_id}")

    @retry_on_failure(max_retries=3, base_delay=1.0)
    def update_metric(self, session_id: str, metric: str, delta: float) -> float:
        """
        Atomically updates a numeric metric using Redis HINCRBYFLOAT.
        Includes sanitization to prevent key injection.
        """
        if not self._METRIC_PATTERN.match(metric):
            self._logger.error(f"⛔ Injection attempt detected on metric {metric}")
            raise ValueError("Invalid metric name")
        
        key = f"sessions:{session_id}:metrics"
        try:
            new_value = self._client.hincrbyfloat(key, metric, delta)
            self._client.expire(key, self._ttl)
            return float(new_value)
        except Exception as e:
            self._logger.error(f"❌ Failed to update metric {metric}: {e}")
            raise e

    @retry_on_failure(max_retries=3, base_delay=1.0)
    def get_metric(self, session_id: str, metric: str) -> float:
        
        """Retrieves all hash fields (metrics) for a given session."""
        
        key = f"sessions:{session_id}:metrics"
        data = self._client.hget(key, metric)

        if not data:
            self._logger.warning(f"⚠️ Metrics not found for session id {session_id}")
            return None
        
        try:
            return float(data)
        except ValueError:
            self._logger.warning(f"⚠️ Invalid metric value for session id {session_id}")
            return None

    @retry_on_failure(max_retries=3, base_delay=1.0)
    def delete_metric(self, session_id: str, metric: str) -> bool:
        
        """Deletes a specific metric for a given session."""
       
        if not self._METRIC_PATTERN.match(metric):
            self._logger.error(f"⛔ Injection attempt detected on metric {metric}")
            raise ValueError("Invalid metric name")
        
        key = f"sessions:{session_id}:metrics"
        try:
            return bool(self._client.hdel(key, metric))
        except Exception as e:
            self._logger.error(f"❌ Failed to delete metric {metric}: {e}")
            raise e

    @retry_on_failure(max_retries=3, base_delay=1.0)
    def get_all_metrics(self, session_id: str) -> Dict[str, float]:
        
        """Retrieves all hash fields (metrics) for a given session."""
        
        key = f"sessions:{session_id}:metrics"
        data = self._client.hgetall(key)

        if not data:
            self._logger.warning(f"⚠️ Metrics not found for session id {session_id}")
            return None
        
        try:
            return {k.decode(): float(v.decode()) for k, v in data.items()}
        except ValueError:
            self._logger.warning(f"⚠️ Invalid metric values for session id {session_id}")
            return None

    @retry_on_failure(max_retries=3, base_delay=1.0)
    def clear_all_metrics(self, session_id: str) -> bool:
        
        """Clears all metrics for a given session."""
        
        key = f"sessions:{session_id}:metrics"
        try:
            return bool(self._client.delete(key))
        except Exception as e:
            self._logger.error(f"❌ Failed to clear metrics for session {session_id}: {e}")
            raise e


    # ---------------------------------------------------------
    # SECTION 3: Maintenance & Testing
    # ---------------------------------------------------------
    
    def clear_all(self):
        """Safe wrapper for clearing all session data, restricted to test/cleanup environments."""
        if os.getenv("ENV") != "test" and os.getenv("ALLOW_CLEANUP") != "true":
            raise PermissionError("Operation Denied. Environment not configured for cleanup.")
        self._internal_clear_all()

    def _internal_clear_all(self):
        """Internal logic to find and delete all session keys using the 'sessions:*' pattern."""
        try:
            pattern = "sessions:*"
            keys = self._client.keys(pattern)
            if keys:
                self._client.delete(*keys)
                self._logger.info(f"🧹 Database cleaned: removed {len(keys)} keys.")
        except Exception as e:
            self._logger.error(f"❌ Error during clear_all: {e}")
