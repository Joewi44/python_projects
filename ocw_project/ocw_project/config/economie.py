from dataclasses import dataclass, asdict, field
import json
from .base import validate_float
import logging

logger = logging.getLogger(__name__)

@dataclass
class EconomicConfig:
    standaard_r: float = field(default=0.10)
    standaard_i: float = field(default=0.05)
    standaard_sigma: float = field(default=0.08)
    uitgebreid_r: float = field(default=0.04)
    uitgebreid_i: float = field(default=0.03)
    uitgebreid_sigma: float = field(default=0.09)

    def __post_init__(self):
        for name, value in asdict(self).items():
            setattr(self, name, validate_float(value, name))
        
        logger.info("ECONOMIE successfully initialised.")
        logger.debug(f"{self.__str__()}")

    def __str__(self):
        return (f"Standaard => r={self.standaard_r} - i={self.standaard_i} - sigma={self.standaard_sigma}\n"
                f"Uitgebreid => r={self.uitgebreid_r} - i={self.uitgebreid_i} - sigma={self.uitgebreid_sigma}")

    def to_dict(self):
        return asdict(self)

    
    def load_from_dict(self, params: dict):
        for key, value in params.items():
            if hasattr(self, key):
                setattr(self, key, validate_float(value, key))
            else:
                logger.warning(f"Ignoring unknown keys: {key}")

        logger.info("ECONOMIE successfully loaded.")
        logger.debug(f"{self.__str__()}")
