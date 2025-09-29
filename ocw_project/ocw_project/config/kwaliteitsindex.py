from dataclasses import dataclass, field
from typing import Dict
from ocw_project.config.base import validate_float
import logging

logger = logging.getLogger(__name__)

@dataclass
class KwaliteitsIndexItem:
    max: float
    min: float

@dataclass
class KwaliteitsIndexConfig:
    Zeer_goed: KwaliteitsIndexItem = field(default_factory=lambda: KwaliteitsIndexItem(max=0.9, min=0.8))
    Goed: KwaliteitsIndexItem = field(default_factory=lambda: KwaliteitsIndexItem(max=0.8, min=0.75))
    Acceptable: KwaliteitsIndexItem = field(default_factory=lambda: KwaliteitsIndexItem(max=0.75, min=0.5))
    Matig: KwaliteitsIndexItem = field(default_factory=lambda: KwaliteitsIndexItem(max=0.5, min=0.45))
    Slecht: KwaliteitsIndexItem = field(default_factory=lambda: KwaliteitsIndexItem(max=0.45, min=0.3))
    Onaanvaardbaar: KwaliteitsIndexItem = field(default_factory=lambda: KwaliteitsIndexItem(max=0.3, min=0.0))

    def load_from_dict(self, params: dict):
        for key, value in params.items():
            if hasattr(self, key):
                item = getattr(self, key)
                item.max = validate_float(value.get("max", item.max), key, min_val=value.get("min", item.min))
                item.min = validate_float(value.get("min", item.min), key, max_val=value.get("max", item.max))
            else:
                logger.warning(f"Ignoring unknown keys: {key}")

        logger.info("KWALITEITSINDEX successfully loaded.")
        logger.debug(f"{self.__str__()}")

    def to_dict(self):
        return {
            "Zeer_goed": {"max": self.Zeer_goed.max, "min": self.Zeer_goed.min},
            "Goed": {"max": self.Goed.max, "min": self.Goed.min},
            "Acceptable": {"max": self.Acceptable.max, "min": self.Acceptable.min},
            "Matig": {"max": self.Matig.max, "min": self.Matig.min},
            "Slecht": {"max": self.Slecht.max, "min": self.Slecht.min},
            "Onaanvaardbaar": {"max": self.Onaanvaardbaar.max, "min": self.Onaanvaardbaar.min}
        }
    
    def get_kwaliteits_index(self, globaal: float):
        for kwaliteit in self.__dataclass_fields__:
            item = getattr(self, kwaliteit)
            if item.min <= globaal <= item.max:
                return kwaliteit

        return None
            

if __name__ == "__main__":
    session = KwaliteitsIndexConfig()

    print(session.get_kwaliteits_index(0.81))
    print(session.get_kwaliteits_index(0.0))