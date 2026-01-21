from abc import ABC, abstractmethod
from pydantic import validate_call
from typing import Optional
from schemas.session import SessionConfig, SessionState
from schemas.metrics import TelemetryPayload 


class ICache(ABC):

    @abstractmethod
    def connect(self) -> None:
        pass

    @abstractmethod
    @validate_call
    def set_telemetry(self, payload: TelemetryPayload) -> None:
        pass

    @abstractmethod
    @validate_call
    def get_telemetry(self, session_id: str) -> Optional[TelemetryPayload]:
        pass

    @abstractmethod
    @validate_call
    def set_session(self, payload: SessionState) -> None:
        pass

    @abstractmethod
    @validate_call
    def get_session(self, session_id: str) -> Optional[SessionState]:
        pass
