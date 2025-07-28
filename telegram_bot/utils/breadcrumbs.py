import logging
from functools import wraps
from telegram import Update


def breadcrumb(func):
    """Decorador para registrar entrada y salida de handlers."""
    if hasattr(func, "__call__"):
        @wraps(func)
        async def wrapper(update: Update, context, *args, **kwargs):
            logger = logging.getLogger(func.__module__)
            user_id = getattr(update.effective_user, "id", "unknown") if update else "unknown"
            logger.debug(f"➡️ {func.__name__} (user:{user_id})")
            result = await func(update, context, *args, **kwargs)
            logger.debug(f"⬅️ {func.__name__} (user:{user_id})")
            return result
        return wrapper
    return func
