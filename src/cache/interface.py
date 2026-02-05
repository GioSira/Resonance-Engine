from abc import ABC, abstractmethod
from pydantic import validate_call
from typing import Optional
from src.schemas.session import SessionConfig, SessionState
from src.schemas.metrics import TelemetryPayload 


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

    @abstractmethod
    @validate_call
    def update_telemetry(self, payload: TelemetryPayload) -> bool:
        pass

    @abstractmethod
    @validate_call
    def update_session(self, payload: SessionState) -> bool:
        pass

    @abstractmethod
    @validate_call
    def delete_telemetry(self, session_id: str) -> bool:
        pass

    @abstractmethod
    @validate_call
    def delete_session(sef, session_id: str) -> bool:
        pass

    @abstractmethod
    @validate_call
    def clear_all(self) -> None:
        pass

    # ---------------------------------------------------------
    # SECTION 2: TTRPG High-Frequency Metrics (Atomic)
    # ---------------------------------------------------------

    @abstractmethod
    @validate_call
    def set_metric(self, session_id: str, metric: str, value: float) -> None:
        pass

    @abstractmethod
    @validate_call
    def update_metric(self, session_id: str, metric: str, delta: float) -> float:
        pass

    @abstractmethod
    @validate_call
    def get_metric(self, session_id: str, metric: str) -> float:
        pass

    @abstractmethod
    @validate_call
    def delete_metric(self, session_id: str, metric: str) -> bool:
        pass

    @abstractmethod
    @validate_call
    def get_all_metrics(self, session_id: str) -> dict[str, float]:
        pass

    @abstractmethod
    @validate_call
    def clear_all_metrics(self, session_id: str) -> bool:
        pass
