from pydantic import BaseModel, Field, validator
from typing import List, Literal, Optional, Dict
from enum import Enum

# Enum per definire l'operazione di confronto
class TriggerOperator(str, Enum):
    LESS_THAN = "lt"      # Per HP, Sanity (Allarme se scende)
    GREATER_THAN = "gt"   # Per Stress, Terrore (Allarme se sale)
    EQUALS = "eq"         # Per stati specifici

class TriggerRule(BaseModel):
    """
    Una singola regola di attivazione musicale.
    """
    metric_name: str       # Es: "hp", "sanity", "tension"
    operator: TriggerOperator
    threshold: float       # Il valore di soglia
    
    target_genre: str      # Es: "metal" (se HP bassi), "dark-ambient" (se Sanity bassa)
    priority: int = 1      # Se scattano più regole, vince quella con priorità più alta!

    class Config:
        use_enum_values = True

class SessionConfig(BaseModel):
    """
    La configurazione completa della partita.
    """
    session_id: str
    default_genre: str = None
    
    # Qui risiede la potenza: una lista di N regole
    rules: List[TriggerRule] = []

    def get_highest_priority_rule(self, triggered_rules: List[TriggerRule]):
        """Helper per decidere chi vince in caso di conflitto"""
        if not triggered_rules: return None
        # Ordina per priorità decrescente
        return sorted(triggered_rules, key=lambda x: x.priority, reverse=True)[0]

class SessionState(BaseModel):
    """
    Lo stato salvato su Redis/Firebase.
    Unisce la Configurazione (Regole) con gli ultimi Dati (Metrics).
    """
    config: SessionConfig
    last_metrics: Optional[Dict[str, float]] = None
    current_status: Literal["NOMINAL", "CRITICAL"] = "NOMINAL"
    active_rule_metric: Optional[str] = None # Quale regola sta suonando ora?
