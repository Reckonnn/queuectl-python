from src.db import get_cfg, set_cfg

def _get_int(key, default):
    """Get integer value from config table or return default."""
    v = get_cfg(key)
    try:
        return int(v)
    except Exception:
        return default

def backoff_base():
    """Base for exponential backoff (default 2)."""
    return _get_int("backoff_base", 2)

def max_retries():
    """Maximum retries before moving to DLQ (default 3)."""
    return _get_int("max_retries", 3)

def set_value(key, value):
    """Set or update config value."""
    set_cfg(key, value)
