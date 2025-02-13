from typing import Callable
from functools import wraps


def protective_call(
    error_handler: Callable[[Exception], any], *errors_to_except: Exception
):
    """Simple wrapper to hide primitive try-except constructions"""

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except errors_to_except as e:
                return error_handler(e)

        return wrapper

    return decorator
