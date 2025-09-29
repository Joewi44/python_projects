from dataclasses import dataclass, field
from typing import Dict
from .base import validate_float
import logging

logger = logging.getLogger(__name__)

@dataclass
class WegKenmerkenItem:
    K_visueel: float        # Parameter die de invloed op de weg uitdrukt door de belasting van het zware verkeer
    K_structureel: float    # Parameter die de invloed op de weg uitdrukt door de belasting van het zware verkeer
    T: float                # Vast groeipercentage van het verkeer over de jaren

    def __post_init__(self):
        self.K_visueel = validate_float(self.K_visueel, "K_visueel")
        self.K_structureel = validate_float(self.K_structureel, "K_structureel")
        self.T = validate_float(self.T, "T")

@dataclass
class WegKenmerkenConfig:
    erf: WegKenmerkenItem = field(default_factory=lambda: WegKenmerkenItem(1.0, 1.2, 0.0))
    verzamel: WegKenmerkenItem = field(default_factory=lambda: WegKenmerkenItem(1.25, 1.5, 0.0))
    doorgang: WegKenmerkenItem = field(default_factory=lambda: WegKenmerkenItem(1.35, 1.62, 0.0))

    def load_from_dict(self, params: dict):
        for key, value in params.items():
            if hasattr(self, key):
                item = getattr(self, key)
                item.K_visueel = validate_float(value.get("K_visueel", item.K_visueel), "K_visueel")
                item.K_structureel = validate_float(value.get("K_structureel", item.K_structureel), "K_structureel")
                item.T = validate_float(value.get("T", item.T), "T")
            
            else:
                logger.warning(f"Ignoring unknown keys (wegsoort): {key}")
                raise KeyError(f"Unknown wegsoort in configuration: {key}")
            
        logger.info("WEG_KENMERKEN successfully loaded.")
        logger.debug(f"{self.__str__()}")

    def to_dict(self):
        return {
            "erf": {"K_visueel": self.erf.K_visueel, "K_structureel": self.erf.K_structureel, "T": self.erf.T},
            "verzamel": {"K_visueel": self.verzamel.K_visueel, "K_structureel": self.verzamel.K_structureel, "T": self.verzamel.T},
            "doorgang": {"K_visueel": self.doorgang.K_visueel, "K_structureel": self.doorgang.K_structureel, "T": self.doorgang.T},
        }
    