import pytest
from hypothesis import given, strategies as st
from hypothesis import settings, HealthCheck, Verbosity

from src.cache.factory import CacheFactory
from src.cache.interface import ICache
from src.schemas.metrics import TelemetryPayload
from src.schemas.session import SessionConfig, SessionState, TriggerRule

# Configurazioni Hypothesis per non stressare troppo (come richiesto)
settings.register_profile("ci", max_examples=10, deadline=None)
settings.load_profile("ci")

# ========= STRATEGIES ===========

st_session_id = st.text(min_size=3, max_size=50, alphabet=st.characters(blacklist_categories=("Cs",)))
extreme_floats = st.floats(allow_infinity=False, allow_nan=False)

st_rule_list = st.lists(st.builds(TriggerRule, 
                  metric_name=st.sampled_from(["hp", "sanity", "adrenalina"]),
                  operator=st.sampled_from(["lt", "gt", "eq"]),
                  threshold=extreme_floats,
                  target_genre=st_session_id,
                  priority=st.integers(min_value=0, max_value=100))
                )

st_session_config = st.builds(SessionConfig, session_id=st_session_id, rules=st_rule_list)
st_session_state = st.builds(SessionState, config=st_session_config)

st_telemetry = st.builds(
    TelemetryPayload,
    session_id=st_session_id,
    metrics=st.fixed_dictionaries({
        'hp': st.floats(allow_nan=False, allow_infinity=False),
        'sanity': st.floats(allow_nan=False, allow_infinity=False)
    })
)


# ======== TEST CLASS =========

@pytest.mark.integration
class TestRedisCache:

    # ===================== INIT AND CLEAR DB =======================

    @pytest.fixture(scope="function")
    def cache_db(self):

        cache = CacheFactory.get_cache("REDIS")
        yield cache
        cache.clear_all()


    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(payload=st_session_state)
    def test_set_and_get_session_integrity(self, cache_db, payload):

        # Salvataggio
        cache_db.set_session(payload)
        
        # Recupero
        retrieved = cache_db.get_session(payload.session_id)
        
        # Asserzione profonda
        assert retrieved is not None
        assert retrieved.session_id == payload.session_id
        assert retrieved.config.rules == payload.config.rules
        
        # Verifica namespace corretto (White-box testing)
        # Il codice usa f"sessions:{id}:state"
        raw_key = f"sessions:{payload.session_id}:state"
        assert cache_db._client.exists(raw_key)


       
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(payload=st_telemetry)
    def test_set_and_get_telemetry_integrity(self, cache_db, payload):

        # Salvataggio
        cache_db.set_telemetry(payload)
        
        # Recupero
        retrieved = cache_db.get_telemetry(payload.session_id)
        
        # Asserzione profonda
        assert retrieved is not None
        assert retrieved.session_id == payload.session_id
        assert retrieved.metrics["hp"] == payload.metrics["hp"]
        
        raw_key = f"sessions:{payload.session_id}:telemetry"
        assert cache_db._client.exists(raw_key)


    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(payload=st_telemetry)
    def test_telemetry_isolation(self, cache_db, payload):
        """
        Verifica che la telemetria non sovrascriva lo stato della sessione e viceversa.
        (Namespace collision check).
        """
        cache_db.set_telemetry(payload)
        
        # Verifichiamo che non sia accessibile tramite get_session
        # Questo fallirebbe se le chiavi fossero identiche
        session_data = cache_db.get_session(payload.session_id)
        assert session_data is None

        # Verifichiamo il recupero corretto
        retrieved = cache_db.get_telemetry(payload.session_id)
        assert retrieved == payload


    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(session_data=st_session_state)
    def test_delete_session(self, cache_db, session_data):

        s_id = session_data.session_id
        
        cache_db.set_session(session_data)
        result = cache_db.delete_session(s_id)

        assert result == True


    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(telemetry_data=st_telemetry)
    def test_delete_telemetry(self, cache_db, telemetry_data):

        s_id = telemetry_data.session_id
        
        cache_db.set_telemetry(telemetry_data)
        result = cache_db.delete_telemetry(s_id)

        assert result is True


    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(payload=st_telemetry)
    def test_update_telemetry_consistency(self, cache_db, payload):
    
        result = cache_db.update_telemetry(payload)
        assert result is True
        
        stored = cache_db.get_telemetry(payload.session_id)
        assert stored == payload


    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(payload=st_session_state)
    def test_update_session_consistency(self, cache_db, payload):

        result = cache_db.update_session(payload)
        assert result is True

        stored = cache_db.get_session(payload.session_id)
        assert stored == payload


    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_typos_and_attribute_errors(self, cache_db):
        """
        Smoke test per verificare che i typo (self.log vs self._logger) non facciano crashare
        il codice quando viene chiamato connect o delete.
        """
        # Connect è già chiamato dalla fixture, se non è crashato lì, ok.
        
        # Testiamo delete_telemetry che contiene `self._warning` (metodo inesistente)
        # Dobbiamo forzare il ramo 'else' simulando una chiave inesistente
        try:
            cache_db.delete_telemetry("non_existent_id")
        except AttributeError as e:
            pytest.fail(f"CRASH rilevato su attributo mancante (probabile self._warning): {e}")
