from dataclasses import dataclass, field, asdict
from typing import Dict, Optional, Tuple
from ocw_project.config.base import validate_float
import logging

logger = logging.getLogger(__name__)

@dataclass
class MaatregelMappingItem:
    naam: str
    prijs: float

@dataclass
class Onderhoudswaarden:
    lokaal: MaatregelMappingItem
    algemeen_v1: MaatregelMappingItem
    algemeen_v2: MaatregelMappingItem
    algemeen_v3: MaatregelMappingItem
    versterking_v1: MaatregelMappingItem
    versterking_v2: MaatregelMappingItem
    versterking_v3: MaatregelMappingItem

    def load_from_dict(self, data: dict):
        for onderhoud_name in self.__dataclass_fields__:
            if onderhoud_name in data:
                onderhoud_data = data[onderhoud_name]
                setattr(
                    self,
                    onderhoud_name,
                    MaatregelMappingItem(
                        naam=onderhoud_data.get("naam", "N/A"), 
                        prijs=validate_float(onderhoud_data.get("prijs", -1), onderhoud_name, min_val=-1)
                ))

            else:
                logger.warning(f"Ignoring unknown keys: {onderhoud_name}")
                raise KeyError(f"Unknown onderhoudswaarde in configuration: {onderhoud_name}")

    def to_dict(self) -> dict:
        return asdict(self)

def default_onderhoudswaarden():
    item = MaatregelMappingItem("N/A", 10.0)
    return Onderhoudswaarden(
        lokaal=item, algemeen_v1=item, algemeen_v2=item, algemeen_v3=item,
        versterking_v1=item, versterking_v2=item, versterking_v3=item
    )

@dataclass
class MaatregelMappingConfig:
    asfalt: Onderhoudswaarden = field(default_factory=lambda: default_onderhoudswaarden())
    beton: Onderhoudswaarden = field(default_factory=lambda: default_onderhoudswaarden())
    elementen: Onderhoudswaarden = field(default_factory=lambda: default_onderhoudswaarden())

    def load_from_dict(self, params: dict):
        for key, value in params.items():
            if hasattr(self, key):
                getattr(self, key).load_from_dict(value)
            
            else:
                logger.warning(f"Ignoring unknown keys (MAATREGEL_MAPPING): {key}")
                raise KeyError(f"Unknown MAATREGEL_MAPPING in configuration: {key}")
            
        logger.info("MAATREGEL_MAPPING successfully loaded.")
        logger.debug(f"{self.__str__()}")

    def to_dict(self):
        return {
            "asfalt": self.asfalt.to_dict(),
            "beton": self.beton.to_dict(),
            "elementen": self.elementen.to_dict()
        }

    def get_maatregel_info(self, verharding: str, onderhoud_type: Optional[str]) -> Tuple[str, float]:
        """Get maatregel name and cost for given surface type and maintenance type."""
        if not onderhoud_type or onderhoud_type == 'None':
            return ('None', 0.0)
        
        onderhoudswaarden = getattr(self, verharding, None)
        if onderhoudswaarden is None:
            raise ValueError(f"Unknown verharding type: {verharding}")

        maatregel = getattr(onderhoudswaarden, onderhoud_type, None)
        if maatregel is None:
            raise ValueError(f"Unknown onderhoud_type: {onderhoud_type}")

        return (maatregel.naam, maatregel.prijs)



if __name__ == "__main__":
    session = MaatregelMappingConfig()

    print(session)

    naam, prijs = session.get_maatregel_info("asfalt", "algemeen_v1")
    print(f"Maatregel: {naam}, Prijs: {prijs}")