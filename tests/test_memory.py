import pytest
from src.database.factory import DatabaseFactory
from src.schemas.metrics import TelemetryPayload
from src.schemas.session import SessionConfig, SessionState, TriggerRule
from hypothesis import given, strategies as st
from hypothesis import settings, HealthCheck

valid_ids = st.text(min_size=3, max_size=50, alphabet=st.characters(whitelist_categories=('L', 'N', 'P')))
messy_strings = st.text(min_size=0, max_size=1000)
extreme_floats = st.floats(allow_nan=False, allow_infinity=False)


class TestMemoryDB:

    # ===================== INIT AND CLEAR DB =======================

    @pytest.fixture(scope="function")
    def memory_db(self):

        db = DatabaseFactory.get_database("MEMORY")
        yield db
        db.clear_all()


    # ===================== TEST TELEMETRY =======================

    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(session_id=valid_ids, hp=extreme_floats, sanity=extreme_floats)
    def test_valid_telemetry_storage(self, memory_db, session_id, hp, sanity):

        payload = TelemetryPayload(
            session_id=session_id,
            metrics={"hp": hp, "sanity": sanity}
        )

        memory_db.set_telemetry(payload)
        retrieved_telemetry = memory_db.get_telemetry(session_id)

        assert retrieved_telemetry.session_id == payload.session_id
        assert retrieved_telemetry.metrics["hp"] == payload.metrics["hp"]


    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(session_id=valid_ids, hp=extreme_floats, sanity=extreme_floats)
    def test_valid_telemetry_update(self, memory_db, session_id, hp, sanity):

        payload = TelemetryPayload(
            session_id=session_id,
            metrics={"hp": 50.0, "sanity": 35.0}
        )

        memory_db.set_telemetry(payload)

        new_payload = TelemetryPayload(
            session_id = session_id,
            metrics={"hp": hp, "sanity": sanity}
        )

        updated_flag = memory_db.update_telemetry(new_payload)

        retrieved_payload = memory_db.get_telemetry(session_id)

        assert updated_flag == True
        assert session_id == retrieved_payload.session_id
        assert retrieved_payload.metrics["hp"] == hp
        assert retrieved_payload.metrics["sanity"] == sanity

    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(session_id=valid_ids, hp=extreme_floats, sanity=extreme_floats)
    def test_valid_telemetry_delete(self, memory_db, session_id, hp, sanity):
    
        payload = TelemetryPayload(
            session_id=session_id,
            metrics={"hp": hp, "sanity": sanity}
        )

        memory_db.set_telemetry(payload)

        # delete payload
        memory_db.delete_telemetry(payload.session_id)

        with pytest.raises(ValueError):
            memory_db.get_telemetry(session_id)



    # ===================== TEST SESSION =======================


    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(session_id=valid_ids, hp=extreme_floats, sanity=extreme_floats, rules_list=st.lists(
        st.builds(TriggerRule, 
                  metric_name=st.sampled_from(["hp", "sanity", "adrenalina"]),
                  operator=st.sampled_from(["lt", "gt", "eq"]),
                  threshold=extreme_floats,
                  target_genre=valid_ids,
                  priority=st.integers(min_value=0, max_value=100)),
        min_size=1, max_size=50
    ))
    def test_valid_session_storage(self, memory_db, rules_list, session_id, hp, sanity):

        config = SessionConfig(session_id=session_id, rules=rules_list)
        payload = SessionState(
            config=config,
        )

        memory_db.set_session(payload)
        retrieved_session = memory_db.get_session(session_id)

        assert retrieved_session.session_id == payload.session_id
        assert len(retrieved_session.config.rules) > 0


    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(session_id=valid_ids, 
        rules_list=st.lists(
        st.builds(TriggerRule, 
                  metric_name=st.sampled_from(["hp", "sanity", "adrenalina"]),
                  operator=st.sampled_from(["lt", "gt", "eq"]),
                  threshold=extreme_floats,
                  target_genre=valid_ids,
                  priority=st.integers(min_value=0, max_value=100)),
                  min_size=1, max_size=50), 
        new_rules_list=st.lists(
        st.builds(TriggerRule, 
                  metric_name=st.sampled_from(["hp", "sanity", "adrenalina"]),
                  operator=st.sampled_from(["lt", "gt", "eq"]),
                  threshold=extreme_floats,
                  target_genre=valid_ids,
                  priority=st.integers(min_value=0, max_value=100)),
                  min_size=1, max_size=50
    ))
    def test_valid_session_update(self, memory_db, session_id, rules_list, new_rules_list):

        config = SessionConfig(
            session_id=session_id,
            rules=rules_list
        )
        state = SessionState(config=config)

        memory_db.set_session(state)

        new_config = SessionConfig(
            session_id = session_id,
            rules=new_rules_list,
        )
        new_state = SessionState(config=new_config)

        memory_db.update_session(new_state)

        retrieved_payload = memory_db.get_session(session_id)
        
        assert retrieved_payload.config.session_id == session_id
        assert retrieved_payload.config.rules == new_rules_list

    
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(session_id=valid_ids, rules_list=st.lists(
        st.builds(TriggerRule, 
                  metric_name=st.sampled_from(["hp", "sanity", "adrenalina"]),
                  operator=st.sampled_from(["lt", "gt", "eq"]),
                  threshold=extreme_floats,
                  target_genre=valid_ids,
                  priority=st.integers(min_value=0, max_value=100)),
        min_size=1, max_size=50
    ))
    def test_valid_session_delete(self, memory_db, session_id, rules_list):
    
        config = SessionConfig(
            session_id=session_id,
            rules=rules_list
        )
        state = SessionState(config=config)

        memory_db.set_session(state)

        # delete payload
        memory_db.delete_session(session_id)

        with pytest.raises(ValueError):
            memory_db.get_session(session_id)
