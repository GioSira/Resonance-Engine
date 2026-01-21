import time
import random
import functools
from typing import Type, Tuple, Union
from .logger import get_logger

# Logger specifico per il sistema di resilienza
logger = get_logger("RESILIENCE")

def retry_on_failure(
    max_retries: int = 5, 
    base_delay: float = 1.0, 
    max_delay: float = 30.0,
    exceptions: Union[Type[Exception], Tuple[Type[Exception], ...]] = Exception
):
    """
    :param max_retries: Numero massimo di tentativi prima di arrendersi.
    :param base_delay: Attesa iniziale (secondi).
    :param max_delay: Tetto massimo di attesa (cap).
    :param exceptions: Quali errori fanno scattare il retry (default: tutti).
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 0
            current_delay = base_delay

            while attempt < max_retries:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    attempt += 1
                    
                    if attempt >= max_retries:
                        logger.critical(f"🔴 FAILURE | {func.__name__} fallita dopo {max_retries} tentativi. Err: {e}")
                        raise e # Rilancia l'errore al chiamante finale
                    
                    # Calcolo Jitter (Variazione casuale +/- 10%)
                    jitter = random.uniform(0.9, 1.1)
                    sleep_time = min(current_delay * jitter, max_delay)
                    
                    logger.warning(
                        f"🟡 RETRY {attempt}/{max_retries} | {func.__name__} | "
                        f"Errore: {e}. Attendo {sleep_time:.2f}s..."
                    )
                    
                    time.sleep(sleep_time)
                    
                    # Incremento esponenziale del ritardo per il prossimo giro
                    current_delay *= 2 
            return None
        return wrapper
    return decorator