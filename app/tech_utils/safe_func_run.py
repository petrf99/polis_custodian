import functools
import logging

logger = logging.getLogger(__name__)

def safe_run_sync(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            logger.debug(f"[SAFE WRAPPER] Running {func.__name__}")
            return func(*args, **kwargs)
        except Exception as e:
            logger.exception(f"[SAFE WRAPPER] {func.__name__} failed with error: {e}")
            raise
    return wrapper
