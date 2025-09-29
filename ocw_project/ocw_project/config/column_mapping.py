import logging
from dataclasses import dataclass, field, asdict
from typing import Dict, Any

logger = logging.getLogger(__name__)

@dataclass
class ColumnMappingConfig:
    guid: Dict[str, Any] = field(default_factory=lambda: {"value": "WSO_SPLIT_", "info": "WSO_SPLIT_ or Guid"})
    straat: Dict[str, Any] = field(default_factory=lambda: {"value": "Straat", "info": "Straat or Straat"})
    gemeente: Dict[str, Any] = field(default_factory=lambda: {"value": "Gemeente", "info": "Gemeente or Gemeente"})
    deelgemeente: Dict[str, Any] = field(default_factory=lambda: {"value": "Deelgemeen", "info": "Deelgemeen or ?"})
    wegsectie: Dict[str, Any] = field(default_factory=lambda: {"value": "WSO_GUID", "info": "WSO_GUID or Wegsectie"})
    oppervlakte: Dict[str, Any] = field(default_factory=lambda: {"value": "Shape_STAr", "info": "Shape_STAr or Oppervlakt"})
    verharding: Dict[str, Any] = field(default_factory=lambda: {"value": "verhtype", "info": "verhtype or verharding"})
    functie: Dict[str, Any] = field(default_factory=lambda: {"value": "wegfunct", "info": "Road function"})
    visuele_index: Dict[str, Any] = field(default_factory=lambda: {"value": "iv", "info": "Visual condition index"})
    visuele_index_date: Dict[str, Any] = field(default_factory=lambda: {"value": "Edited", "info": "Visual index date"})
    structurele_index: Dict[str, Any] = field(default_factory=lambda: {"value": "is_mix", "info": "Structural index"})
    structurele_index_date: Dict[str, Any] = field(default_factory=lambda: {"value": "bouwdate", "info": "Structural index date"})
    globale_index: Dict[str, Any] = field(default_factory=lambda: {"value": "ig_mix", "info": "Global index"})
    globale_index_date: Dict[str, Any] = field(default_factory=lambda: {"value": "bouwdate", "info": "Global index date"})
    bouwdate: Dict[str, Any] = field(default_factory=lambda: {"value": "bouwdate", "info": "Construction date"})
    prioriteit: Dict[str, Any] = field(default_factory=lambda: {"value": "Prioriteit", "info": "Priority level"})
    geometry: Dict[str, Any] = field(default_factory=lambda: {"value": "geometry", "info": "Geometry data"})

    def load_from_dict(self, data: dict):
        if not isinstance(data, dict):
            logger.warning("ColumnMappingConfig expects a dict")
            raise ValueError("ColumnMappingConfig expects a dict")
        
        for key, val in data.items():
            if hasattr(self, key):
                if isinstance(val, dict):
                    if "value" in val:
                        getattr(self, key)["value"] = val["value"]
                    if "info" in val:
                        getattr(self, key)["info"] = val["info"]
                else:
                    getattr(self, key)["value"] = val
            else:
                logger.warning(f"Ignoring unknown keys: {key}")

        logger.info("COLUMNS_MAPPING successfully loaded.")
        logger.debug(f"{self.__str__()}")


    def to_dict(self):
        # RETURN {"guid": "value", ...}
        field_dict = {}
        for field_name in self.__dataclass_fields__:
            obj = getattr(self, field_name)
            field_dict[field_name] = obj["value"]
        return field_dict


