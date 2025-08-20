import asyncio
import random
import logging
from functools import wraps
from typing import Callable, Any, Coroutine

from app.utils.config import settings  # Your Pydantic config singleton

logger = logging.getLogger(__name__)


def async_timeout(timeout: int = None):
    """
    Async decorator to enforce a timeout on an async function call.
    If the function exceeds the timeout, asyncio.TimeoutError is raised.

    Args:
        timeout (int): Timeout in seconds. Defaults to settings.LLM_TIMEOUT_SECONDS.

    Usage:
        @async_timeout()
        async def some_async_function(...):
            ...
    """
    def decorator(func: Callable[..., Coroutine[Any, Any, Any]]) -> Callable[..., Coroutine[Any, Any, Any]]:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            nonlocal timeout
            if timeout is None:
                timeout = settings.LLM_TIMEOUT_SECONDS

            try:
                # asyncio.wait_for will cancel if timeout exceeded
                return await asyncio.wait_for(func(*args, **kwargs), timeout=timeout)
            except asyncio.TimeoutError:
                logger.error(f"Function '{func.__name__}' timed out after {timeout} seconds")
                raise
        return wrapper
    return decorator


def async_retry(
    max_retries: int = None,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    jitter: float = 0.1,
    exceptions: tuple = (Exception,),
):
    """
    Async decorator to retry an async function upon failure with exponential backoff and jitter.

    Args:
        max_retries (int): Maximum retry attempts before giving up. Defaults to settings.LLM_MAX_RETRIES.
        initial_delay (float): Initial delay before retry in seconds.
        backoff_factor (float): Multiplier for delay after each retry.
        jitter (float): Random jitter added/subtracted to avoid thundering herd.
        exceptions (tuple): Exception types to catch and retry on.

    Usage:
        @async_retry()
        async def some_async_function(...):
            ...
    """
    def decorator(func: Callable[..., Coroutine[Any, Any, Any]]) -> Callable[..., Coroutine[Any, Any, Any]]:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            nonlocal max_retries
            if max_retries is None:
                max_retries = settings.LLM_MAX_RETRIES

            attempt = 0
            delay = initial_delay

            while attempt <= max_retries:
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    attempt += 1
                    if attempt > max_retries:
                        logger.error(f"Function '{func.__name__}' failed after {attempt} attempts. Raising exception.")
                        raise
                    jitter_value = random.uniform(-jitter, jitter)
                    sleep_time = delay + jitter_value
                    logger.warning(f"Function '{func.__name__}' failed with {e}. Retrying in {sleep_time:.2f} seconds... (Attempt {attempt}/{max_retries})")
                    await asyncio.sleep(sleep_time)
                    delay *= backoff_factor
        return wrapper
    return decorator
