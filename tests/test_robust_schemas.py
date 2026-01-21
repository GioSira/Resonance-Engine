import pytest
from hypothesis import given, strategies as st
from pydantic import ValidationError
from src.schemas.metrics import TelemetryPayload
from src.schemas.session import SessionConfig, TriggerRule

# Strategie di generazione dati
valid_ids = st.text(min_size=3, max_size=50, alphabet=st.characters(whitelist_categories=('L', 'N', 'P')))
messy_strings = st.text(min_size=0, max_size=1000) # Test stringhe vuote o enormi
extreme_floats = st.floats(allow_nan=False, allow_infinity=False)

class TestSchemaRobustness:

    @given(session_id=valid_ids, hp=extreme_floats, sanity=extreme_floats)
    def test_telemetry_fuzzing_valid(self, session_id, hp, sanity):
        """
        Genera migliaia di combinazioni di numeri VALID (anche negativi, enormi, piccolissimi).
        Il sistema NON deve crashare.
        """
        payload = TelemetryPayload(
            session_id=session_id,
            metrics={"hp": hp, "sanity": sanity}
        )
        assert payload.session_id == session_id
        assert isinstance(payload.metrics["hp"], float)

    @given(session_id=valid_ids)
    def test_telemetry_rejects_nan_inf(self, session_id):
        """
        Stress test: inviamo NaN (Not a Number) o Infinito.
        Pydantic DEVE bloccarli, altrimenti l'Engine matematico esplode dopo.
        """

        with pytest.raises(ValidationError):
            TelemetryPayload(
                session_id=session_id,
                metrics={"hp": float("inf")}
            )

        with pytest.raises(ValidationError):
            TelemetryPayload(
                session_id=session_id,
                metrics={"hp": float("-inf")}
            )

        with pytest.raises(ValidationError):
            TelemetryPayload(
                session_id=session_id,
                metrics={"hp": None}
            )

    @given(rules_list=st.lists(
        st.builds(TriggerRule, 
                  metric_name=st.sampled_from(["hp", "sanity", "adrenalina"]),
                  operator=st.sampled_from(["lt", "gt", "eq"]),
                  threshold=extreme_floats,
                  target_genre=valid_ids,
                  priority=st.integers(min_value=0, max_value=100)),
        min_size=1, max_size=50
    ))
    def test_config_heavy_load(self, rules_list):
        """
        Stress test: Creiamo configurazioni con 50 regole randomiche.
        Verifica che il parser non rallenti o crashi con liste lunghe.
        """
        config = SessionConfig(
            session_id="stress_test_session",
            rules=rules_list
        )
        assert len(config.rules) == len(rules_list)