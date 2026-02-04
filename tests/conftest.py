import os
import pytest


@pytest.fixture(scope="session", autouse=True)
def set_test_env():

    os.environ["ENV"] = "test"
    os.environ["ALLOW_CLEANUP"] = "true"
    os.environ["LOG_FOLDER"] = "logs/test"
    
    # Creiamo la cartella se non esiste per evitare errori nel logger
    os.makedirs("logs/test", exist_ok=True)

