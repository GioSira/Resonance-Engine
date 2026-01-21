from abc import ABC, abstractmethod
from typing import Optional
from pydantic import validate_call
from schemas.session import SessionConfig, SessionState
from schemas.metrics import TelemetryPayload 

class IDatabase(ABC):
    """
    Strategy Interface: Definisce le operazioni obbligatorie 
    per qualsiasi sistema di persistenza.
    Tutti i metodi sono protetti da validazione a runtime.
    """

    @abstractmethod
    def connect(self) -> None:
        pass

    @abstractmethod
    @validate_call
    def set_telemetry(self, payload: TelemetryPayload) -> None:
        """
        Aggiorna la telemetria.
        Accetta SOLO un oggetto TelemetryPayload validato.
        """
        pass

    @abstractmethod
    @validate_call
    def set_session(self, payload: SessionState) -> None:
        """
        Aggiorna la sessione.
        Accetta SOLO un oggetto SessionState validato.
        """
        pass

    @abstractmethod
    @validate_call
    def get_telemetry(self, session_id: str) -> Optional[TelemetryPayload]:
        """
        Return telemetry associated to session_id

        :param session_id: the session id
        :type session_id: str
        """
        pass

    @abstractmethod
    @validate_call
    def get_session(self, session_id: str) -> Optional[SessionState]:
        """
        Return session state associated to session_id

        :param session_id: the session id
        :type session_id: str
        """
        pass
