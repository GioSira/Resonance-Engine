from abc import ABC, abstractmethod
from pydantic import validate_call

class IMusicProvider(ABC):

    @abstractmethod
    def connect(self) -> None:
        """Autenticazione API o inizializzazione driver."""
        pass

    @abstractmethod
    @validate_call
    def play_genre(self, genre: str) -> bool:
        """Cambia la musica in base al genere ricevuto dall'Orchestrator."""
        pass

    @abstractmethod
    def set_volume(self, level: int) -> None:
        """Livello da 0 a 100."""
        pass

    @abstractmethod
    def stop(self) -> None:
        """Silenzio immediato."""
        pass
