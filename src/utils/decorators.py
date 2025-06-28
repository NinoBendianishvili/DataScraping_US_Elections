import time
import logging
from functools import wraps
import requests

logger = logging.getLogger(__name__)

def retry_on_failure(max_retries: int = 3, backoff_factor: float = 1.0):
    """
    A decorator that retries a function if it raises a network-related exception.

    It uses an exponential backoff strategy to wait between retries.

    Args:
        max_retries (int): The maximum number of times to retry the function.
        backoff_factor (float): The base delay in seconds for the backoff.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    # Attempt to execute the decorated function
                    return func(*args, **kwargs)
                except requests.RequestException as e:
                    # Log the failure and the attempt number
                    logger.warning(
                        f"Network request in '{func.__name__}' failed (Attempt {attempt + 1}/{max_retries}): {e}"
                    )
                    if attempt + 1 == max_retries:
                        logger.error(f"All {max_retries} retries failed for '{func.__name__}'.")
                        return None  # Return None after all retries fail

                    # Calculate wait time and sleep
                    wait_time = backoff_factor * (2 ** attempt)
                    logger.info(f"Waiting {wait_time:.2f}s before next retry...")
                    time.sleep(wait_time)
        return wrapper
    return decorator