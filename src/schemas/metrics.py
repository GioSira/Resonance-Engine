from pydantic import BaseModel, Field, field_validator, StrictFloat
from typing import Dict
import time
import math

class TelemetryPayload(BaseModel):

    session_id: str = Field(..., min_length=3, description="mandatory session ID")
    timestamp: float = Field(default_factory=time.time)
    metrics: Dict[str, StrictFloat]

    @field_validator('metrics')
    @classmethod
    def check_metrics_integrity(cls, v):
        if not v:
            raise ValueError("Il payload delle metriche non può essere vuoto")
        
        # Impediamo valori infiniti o NaN (Not a Number) che rompono i JSON
        for key, value in v.items():
            if not math.isfinite(value):
                raise ValueError(f"La metrica {key} ha un valore infinito non valido: {value}.")
        
        return v