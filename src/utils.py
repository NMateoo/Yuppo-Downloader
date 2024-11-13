import os
import time
import logging
from functools import wraps

def retry(retries=3, delay=5):
    """
    Decorador para reintentar una función cuando ocurre una excepción.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    logging.warning(f"Intento {attempt + 1}/{retries} fallido con error: {e}")
                    if attempt < retries - 1:
                        time.sleep(delay)
                    else:
                        raise
        return wrapper
    return decorator


def create_directory(directory):
    """
    Crea un directorio si no existe.
    """
    try:
        os.makedirs(directory, exist_ok=True)
    except OSError as e:
        logging.error(f"Error al crear el directorio {directory}: {e}")