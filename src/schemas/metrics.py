from pydantic import BaseModel, Field, field_validator
from typing import Dict
import time

class TelemetryPayload(BaseModel):

    session_id: str = Field(..., min_length=3, description="mandatory session ID")
    timestamp: float = Field(default_factory=time.time)
    metrics: Dict[str, float]

    @field_validator('metrics')
    def check_metrics_integrity(cls, v):
        if not v:
            raise ValueError("Il payload delle metriche non può essere vuoto")
        # Esempio: impediamo valori infiniti o NaN (Not a Number) che rompono i JSON
        for key, value in v.items():
            if not value or value == float('inf') or value == float('-inf'):
                raise ValueError(f"La metrica {key} ha un valore infinito non valido.")
        return v