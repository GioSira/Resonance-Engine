from pydantic import BaseModel, Field, ConfigDict
from typing import List, Literal, Optional, Dict
from enum import Enum


# Enum per definire l'operazione di confronto
class _TriggerOperator(str, Enum):
    LESS_THAN = "lt"      # Per HP, Sanity (Allarme se scende)
    GREATER_THAN = "gt"   # Per Stress, Terrore (Allarme se sale)
    EQUALS = "eq"         # Per stati specifici



class TriggerRule(BaseModel):
    """
    Una singola regola di attivazione musicale.
    """

    metric_name: str       # Es: "hp", "sanity", "tension"
    operator: _TriggerOperator
    threshold: float       # Il valore di soglia
    
    target_genre: str      # Es: "metal" (se HP bassi), "dark-ambient" (se Sanity bassa)
    priority: int = 1      # Se scattano più regole, vince quella con priorità più alta!

    class Config:
        use_enum_values = True

    def __eq__(self, other):
        if not isinstance(other, TriggerRule):
            return False
        return (self.metric_name == other.metric_name and 
                self.operator == other.operator and 
                self.threshold == other.threshold and 
                self.target_genre == other.target_genre and 
                self.priority == other.priority)

    def __hash__(self):
        # Usiamo una tupla dei campi per generare l'hash unico
        return hash((self.metric_name, self.operator, self.threshold, self.target_genre, self.priority))

    

class SessionConfig(BaseModel):
    
    """
    La configurazione completa della partita.
    """
    session_id: str
    default_genre: Optional[str] = None
    
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

    @property
    def session_id(self) -> str:
        return self.config.session_id
