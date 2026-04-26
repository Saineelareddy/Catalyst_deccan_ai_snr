from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import logging

logger = logging.getLogger("AIRetry")

def log_retry_attempt(retry_state):
    """Callback to log when a retry happens."""
    logger.warning(
        f"Retrying AI call. Attempt {retry_state.attempt_number}. "
        f"Exception: {retry_state.outcome.exception()}"
    )

def with_retry():
    """
    Decorator for AI calls with exponential backoff.
    Retries up to 3 times, waiting 2^x * 1 seconds between each retry.
    Catches general exceptions (in a real app, you'd specify Provider-specific APIErrors).
    """
    return retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception), # Or more specific like ConnectionError
        before_sleep=log_retry_attempt,
        reraise=True
    )
