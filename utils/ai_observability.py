import logging
import time
from typing import Callable, Any
from functools import wraps

# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("AIObservability")

def observe_ai_call(provider_name: str):
    """
    Decorator to track latency, success, and errors for AI provider calls.
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                latency = time.time() - start_time
                logger.info(f"[{provider_name}] Call successful. Latency: {latency:.2f}s")
                return result
            except Exception as e:
                latency = time.time() - start_time
                logger.error(f"[{provider_name}] Call failed. Latency: {latency:.2f}s, Error: {str(e)}")
                raise
        return wrapper
    return decorator
