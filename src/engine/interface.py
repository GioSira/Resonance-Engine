from abc import ABC, abstractmethod
from typing import Optional
from schemas.metrics import TelemetryPayload
from schemas.session import SessionState

class IOrchestrator(ABC):

    @abstractmethod
    def process_telemetry(self, payload: TelemetryPayload) -> bool:
        pass

    @abstractmethod
    def process_session(self, payload: SessionState) -> bool:
        pass

    @abstractmethod
    def get_telemetry(self,  session_id: str) -> Optional[TelemetryPayload]:
        pass

    @abstractmethod
    def get_session(self, session_id: str) -> Optional[SessionState]:
        pass
