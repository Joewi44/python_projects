from dataclasses import dataclass, field, asdict
from typing import Dict
from .base import validate_float, validate_positive_int
import logging

logger = logging.getLogger(__name__)

@dataclass
class Onderhoudswaarden:
    routine: float
    lokaal: float
    algemeen_v1: float
    algemeen_v2: float
    algemeen_v3: float
    versterking_v1: float
    versterking_v2: float
    versterking_v3: float

    def load_from_dict(self, data: dict):
        for field_name in self.__dataclass_fields__:
            if field_name in data:
                setattr(
                    self,
                    field_name,
                    validate_float(data[field_name], f"B_visueel_na_onderhoud[{field_name}]")
                )

            else:
                logger.warning(f"Ignoring unknown keys: {field_name}")
                raise KeyError(f"Unknown verhardingssoort in configuration: {field_name}")

    def to_dict(self) -> dict:
        #return {field_name: getattr(self, field_name) for field_name in self.__dataclass_fields__}
        return asdict(self)

@dataclass
class VerhardingssoortKenmerkenItem:
    B_visueel_standaard: float
    B_structureel_standaard: float
    B_visueel_na_onderhoud: Onderhoudswaarden
    leeftijd: int

    def load_from_dict(self, data: dict):
        self.B_visueel_standaard = validate_float(
            data.get("B_visueel_standaard", self.B_visueel_standaard),
            "B_visueel_standaard"
        )
        self.B_structureel_standaard = validate_float(
            data.get("B_structureel_standaard", self.B_structureel_standaard),
            "B_structureel_standaard"
        )

        if "B_visueel_na_onderhoud" in data:
            self.B_visueel_na_onderhoud.load_from_dict(data["B_visueel_na_onderhoud"])

        self.leeftijd = validate_positive_int(
            data.get("leeftijd", self.leeftijd),
            "leeftijd"
        )

    def to_dict(self) -> dict:
        return {
            "B_visueel_standaard": self.B_visueel_standaard,
            "B_structureel_standaard": self.B_structureel_standaard,
            "B_visueel_na_onderhoud": self.B_visueel_na_onderhoud.to_dict(),
            "leeftijd": self.leeftijd
        }

@dataclass
class VerhardingssoortKenmerkenConfig:
    asfalt: VerhardingssoortKenmerkenItem = field(default_factory=lambda: VerhardingssoortKenmerkenItem(
        B_visueel_standaard=0.02,
        B_structureel_standaard=0.02,
        B_visueel_na_onderhoud=Onderhoudswaarden(
            routine=0.02, lokaal=0.055, algemeen_v1=0.04, algemeen_v2=0.03, algemeen_v3=0.03,
            versterking_v1=0.028, versterking_v2=0.02, versterking_v3=0.02
        ),
        leeftijd=25
    ))
    beton: VerhardingssoortKenmerkenItem= field(default_factory=lambda: VerhardingssoortKenmerkenItem(
        B_visueel_standaard=0.013,
        B_structureel_standaard=0.013,
        B_visueel_na_onderhoud=Onderhoudswaarden(
            routine=0.013, lokaal=0.033, algemeen_v1=0.026, algemeen_v2=0.026, algemeen_v3=0.026,
            versterking_v1=0.013, versterking_v2=0.013, versterking_v3=0.013
        ),
        leeftijd=40
    ))
    elementen: VerhardingssoortKenmerkenItem = field(default_factory=lambda: VerhardingssoortKenmerkenItem(
        B_visueel_standaard=0.013,
        B_structureel_standaard=0.013,
        B_visueel_na_onderhoud=Onderhoudswaarden(
            routine=0.016, lokaal=0.016, algemeen_v1=0.016, algemeen_v2=0.016, algemeen_v3=0.016,
            versterking_v1=0.016, versterking_v2=0.016, versterking_v3=0.016
        ),
        leeftijd=30
    ))

    def load_from_dict(self, params: dict):
        for key, value in params.items():
            if hasattr(self, key):
                getattr(self, key).load_from_dict(value)
            else:
                logger.warning(f"Ignoring unknown keys: {key}")
                raise KeyError(f"Unknown verhardingssoort in configuration: {key}")
            
        logger.info("VERHARDINGSSOORT_KENMERKEN successfully loaded.")
        logger.debug(f"{self.__str__()}")


    def to_dict(self) -> dict:
        return {
            "asfalt": self.asfalt.to_dict(),
            "beton": self.beton.to_dict(),
            "elementen": self.elementen.to_dict()
        }