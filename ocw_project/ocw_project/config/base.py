from dataclasses import dataclass
import logging
import math

logger = logging.getLogger(__name__)

def validate_float(value: float, name: str, min_val: float = None, max_val: float = None) -> float:
    """Validate that a value is a positive float and optionally within a range."""
    if not isinstance(value, (int, float)):
        logger.error(f"{name} must be numeric, got {type(value)}")
        raise TypeError(f"{name} must be numeric, got {type(value)}")
    if value < 0 and min_val is None:
        logger.error(f"{name} must be > 0, got {value}")
        raise ValueError(f"{name} must be > 0, got {value}")
    if min_val is not None and value < min_val:
        logger.error(f"{name} must be >= {min_val}, got {value}")
        raise ValueError(f"{name} must be >= {min_val}, got {value}")
    if max_val is not None and value > max_val:
        logger.error(f"{name} must be <= {max_val}, got {value}")
        raise ValueError(f"{name} must be <= {max_val}, got {value}")
    return float(value)

def validate_dict(value: dict, name: str, allowed_keys: set = None) -> dict:
    """Validate that a value is a dictionary and optionally has only allowed keys."""
    if not isinstance(value, dict):
        logger.error(f"{name} must be a dictionary, got {type(value)}")
        raise TypeError(f"{name} must be a dictionary, got {type(value)}")
    if allowed_keys and not set(value.keys()).issubset(allowed_keys):
        unknown_keys = set(value.keys()) - allowed_keys
        logger.error(f"Unknown keys in {name}: {unknown_keys}")
        raise ValueError(f"Unknown keys in {name}: {unknown_keys}")
    return value

def validate_positive_int(value, name: str) -> int:
    if not isinstance(value, int):
        logger.error(f"{name} must be an integer, got {type(value).__name__}")
        raise ValueError(f"{name} must be an integer, got {type(value).__name__}")
    if value < 0:
        logger.error(f"{name} must be positive, got {value}")
        raise ValueError(f"{name} must be positive, got {value}")
    return value
