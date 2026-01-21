import pytest
from pydantic import ValidationError
from src.schemas.metrics import TelemetryPayload
from src.schemas.session import SessionConfig, SessionState, TriggerRule


# ============================== TEST SEZIONE METRICHE (TELEMETRY) ============================

class TestTelemetrySchema:

    def test_valid_telemetry_payload(self):

        data = {
            "session_id": "sess_test_01",
            "metrics": {
                "hp": 85,
                "sanity": 40.0,
                "tension": 0.9
            },
            "timestamp": 1700000000000.0
        }

        payload = TelemetryPayload(**data)

        assert payload.session_id == "sess_test_01"

        assert payload.metrics["hp"] == 85


    def test_invalid_telemetry_payload(self):

        data = {
            "session_id": "sess_err",
            "metrics": {
                "hp": "85",
                "sanity": "quaranta",
                "tension": 0.9
            }        
        }

        with pytest.raises(ValidationError) as excinfo:
            TelemetryPayload(**data)

            assert "Input should be a valid number" in str(excinfo.value)


    def test_missing_telemetry_values(self):

        with pytest.raises(ValidationError) as excinfo:

            TelemetryPayload(metrics={"hp": 100.0})


    def test_telemetry_serialization(self):

        """
        Test to serialize/deserialize TelemetryPayload object
        Foundamental for Redis and Firestore
        """

        original = TelemetryPayload(session_id="cycle_test", metrics={"xp": 99.9})

        # serialize
        json_str = original.model_dump_json()

        # deserialize
        restored = TelemetryPayload.model_validate_json(json_str)

        assert original.session_id == restored.session_id
        
        assert original.metrics == restored.metrics



# ========================== TEST SEZIONE SESSIONE E REGOLE (CONFIG) =========================


class TestSessionSchema:
    
    def test_valid_trigger_rule(self):
        
        rule = TriggerRule(
            metric_name="sanity",
            operator="lt",
            threshold=20.0,
            target_genre="horror",
            priority=10
        )
        assert rule.metric_name == "sanity"
        assert rule.priority == 10

    def test_valid_session_config(self):
        
        rule1 = TriggerRule(metric_name="hp", operator="lt", threshold=10, target_genre="funeral")
        rule2 = TriggerRule(metric_name="energy", operator="gt", threshold=90, target_genre="battle")
        
        config = SessionConfig(
            session_id="campaign_ravenloft",
            rules=[rule1, rule2],
            default_genre="exploration"
        )
        
        assert len(config.rules) == 2
        assert config.rules[0].target_genre == "funeral"

    def test_session_state_defaults(self):

        config = SessionConfig(session_id="test_state", rules=[])
        
        state = SessionState(config=config)
        
        assert state.config.session_id == "test_state"
        assert state.config.default_genre is None
        
    def test_invalid_operator(self):
        
        with pytest.raises(ValidationError) as excinfo:
            TriggerRule(
                metric_name="hp", 
                operator="super_mario_jump", # Operatore inesistente
                threshold=10, 
                target_genre="test"
            )
