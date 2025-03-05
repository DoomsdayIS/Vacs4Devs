import asyncio
from functools import wraps
from typing import Callable, Type


def retry(
    tries: int,
    *,
    delay: float = 0.1,
    backoff: float = 2,
    exceptions: tuple[Type[Exception]],
) -> Callable:
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for _ in range(tries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    await asyncio.sleep(delay * backoff)

        return wrapper

    return decorator
