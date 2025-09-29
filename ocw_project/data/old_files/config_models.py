from dataclasses import dataclass, asdict
from typing import Dict, Literal, TypedDict
import json
from importlib.resources import files
import logging

logger = logging.getLogger(__name__)

class EconomicConfig:
    def __init__(
        self,
        standaard_r: float = 0.10,
        standaard_i: float = 0.05,
        standaard_sigma: float = 0.08,
        uitgebreid_r: float = 0.04,
        uitgebreid_i: float = 0.03,
        uitgebreid_sigma: float = 0.09,
    ):
        # Standard scenario
        self.standaard_r = self._validate_float(standaard_r, "standaard_r")
        self.standaard_i = self._validate_float(standaard_i, "standaard_i")
        self.standaard_sigma = self._validate_float(standaard_sigma, "standaard_sigma")
        
        # Extended scenario
        self.uitgebreid_r = self._validate_float(uitgebreid_r, "uitgebreid_r")
        self.uitgebreid_i = self._validate_float(uitgebreid_i, "uitgebreid_i")
        self.uitgebreid_sigma = self._validate_float(uitgebreid_sigma, "uitgebreid_sigma")

    def __str__(self):
        return (f"Standaard => r={self.standaard_r} - i={self.standaard_i} - sigma={self.standaard_sigma}\n"
                f"Uitgebreid => r={self.uitgebreid_r} - i={self.uitgebreid_i} - sigma={self.uitgebreid_sigma}")

    def serialize_to_dict(self):
        return self.__dict__

    def _validate_float(self, value: float, name: str) -> float:
        if value is None:
            logger.error(f"{name} is None")
            raise ValueError(f"{name} cannot be None")
        if not isinstance(value, (int, float)):
            logger.error(f"{name} must be numeric, got {type(value)}")
            raise TypeError(f"{name} must be numeric, got {type(value)}")
        if value <= 0:
            logger.warning(f"{name} must be > 0, got {value}")
            raise ValueError(f"{name} must be > 0, got {value}")
        return float(value)
    
    def load_from_file(self, params: dict):
        valid_keys = set(self.__dict__.keys())
        input_keys = set(params.keys())
        
        unknown_keys = input_keys - valid_keys
        if unknown_keys:
            logger.warning(f"Ignoring unknown keys: {unknown_keys}")
        
        for key in valid_keys.intersection(input_keys):
            setattr(self, key, self._validate_float(params[key], key))

        logger.info("ECONOMIE successfully loaded.")
        logger.debug(f"{self.__str__()}")
        
    def save_to_json(self, file_path: str, parent_key: str="ECONOMIE") -> None:
        logger.debug(f"Saving updates to {file_path} under parent key '{parent_key}'")
    
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            raise
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in file: {file_path}")
            raise

        if parent_key not in data:
            logger.warning(f"Parent key '{parent_key}' not found in JSON.")
            data[parent_key] = {}

        data[parent_key].update(self.__dict__)
        logger.info(f"Updated data for '{parent_key}': {self.__dict__}")

        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)
            logger.debug(f"Data successfully written to {file_path}")

# Define types
MaterialType = Literal["asfalt", "beton", "elementen"]
MaintenanceType = Literal["routine", "lokaal", "algemeen_v1", "algemeen_v2", 
                         "algemeen_v3", "versterking_v1", "versterking_v2", "versterking_v3", "None"]
RoadFunctionType = Literal["erf", "verzamel", "doorgang"]

class RoadCharacteristics(TypedDict):
    K_visueel: float
    K_structureel: float
    T: float

@dataclass
class RoadParameters:
    """Stores all road material parameters"""
    B_visueel_standaard: float
    B_structureel_standaard: float
    B_visueel_na_onderhoud: Dict[MaintenanceType, float]
    leeftijd: int

class RoadParameterConfig:
    def __init__(self):
        self.ROAD_DATA: Dict[MaterialType, RoadParameters] = {}
        self.WEGKENMERKEN: Dict[RoadFunctionType, RoadCharacteristics] = {}

    def serialize_to_dict(self):
        data = {}
        data["ROAD_DATA"] = {
            material: asdict(params)
            for material, params in self.ROAD_DATA.items()
        }
        data["WEGKENMERKEN"] = self.WEGKENMERKEN
        return data

    def load_from_file(self, raw_road_data: dict, raw_wegkenmerken: dict) -> None:
        self.WEGKENMERKEN = raw_wegkenmerken

        for material, entry in raw_road_data.items():
            if entry["B_visueel_standaard"] < 0:
                logger.error(f"Negative value for B_visueel_standaard in material '{material}'")
                raise ValueError(f"B_visueel_standaard for {material} is negative.")
            if entry["B_structureel_standaard"] < 0:
                logger.error(f"Negative value for B_structureel_standaard in material '{material}'")
                raise ValueError(f"B_structureel_standaard for {material} is negative.")
            if entry["leeftijd"] < 0:
                logger.error(f"Negative value for leeftijd in material '{material}'")
                raise ValueError(f"Leeftijd for {material} is negative.")
            for maint_type, val in entry["B_visueel_na_onderhoud"].items():
                if val < 0:
                    logger.error(
                        f"Negative value for B_visueel_na_onderhoud[{maint_type}] in material '{material}'"
                    )
                    raise ValueError(
                        f"B_visueel_na_onderhoud[{maint_type}] for {material} is negative."
                    )

        self.ROAD_DATA = {
                material: RoadParameters(
                    B_visueel_standaard=entry["B_visueel_standaard"],
                    B_structureel_standaard=entry["B_structureel_standaard"],
                    B_visueel_na_onderhoud=entry["B_visueel_na_onderhoud"],
                    leeftijd=entry["leeftijd"]
                )
                for material, entry in raw_road_data.items()
            }

        logger.info("ROAD_DATA & WEGKENMERKEN successfully loaded.")
        logger.debug(f"{self.ROAD_DATA} - {self.WEGKENMERKEN}")

    def save_to_json(self, file_path: str, parent_keys: list=["ROAD_DATA", "WEGKENMERKEN"]) -> None:
        logger.debug(f"Saving updates to {file_path} under parent key '{parent_keys}'")
    
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)

        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            raise
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in file: {file_path}")
            raise
        
        for parent_key in parent_keys:
            if parent_key not in data:
                logger.warning(f"Parent key '{parent_key}' not found in JSON.")
                data[parent_key] = {}

        # Serialize ROAD_DATA
        data[parent_keys[0]] = {
            material: asdict(params)
            for material, params in self.ROAD_DATA.items()
        }

        # WEGKENMERKEN is already a plain dict
        data[parent_keys[1]] = self.WEGKENMERKEN

        logger.info(f"Updated data for '{parent_key}': {self.__dict__}")

        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)
            logger.debug(f"Data successfully written to {file_path}")


@dataclass
class SimulationState:
    """Stores current simulation state variables"""
    verharding: MaterialType
    functie: RoadFunctionType
    K_visueel: float                # Will be initialized from WEGKENMERKEN
    K_structureel: float            # Will be initialized from WEGKENMERKEN
    T: float                        # Will be initialized from WEGKENMERKEN
    B_visueel: float                # Will be initialized from RoadParameters
    B_structureel: float            # Will be initialized from RoadParameters
    cumul_B: float = 0
    cumul_W: float = 0
    visueel: float = 0.9
    structureel: float = 0.9
    g_min1: float = 0.9
    globaal: float = 0.9
    onderhouds_type: MaintenanceType = "None"


class SimulationHelper:
    def __init__(self, param_config: RoadParameterConfig):
        self.param_config = param_config

    def __str__(self):
        return f"Simulationhelper {self.param_config}"

    def initialize_simulation(self, verharding: MaterialType, functie: RoadFunctionType) -> SimulationState:
        self._validate_input(verharding, functie)

        material = self.param_config.ROAD_DATA[verharding]
        weg = self.param_config.WEGKENMERKEN[functie]

        state = SimulationState(
            verharding=verharding,
            functie=functie,
            K_visueel=weg["K_visueel"],
            K_structureel=weg["K_structureel"],
            T=weg["T"],
            B_visueel=material.B_visueel_standaard,
            B_structureel=material.B_structureel_standaard
        )

        logger.debug(f"SimulationState initialized: {state}")
        return state
    
    def pas_index_aan_na_onderhoud(self, state: SimulationState, onderhouds_type: str, verharding: MaterialType) -> SimulationState:
        if verharding not in self.param_config.ROAD_DATA:
            raise ValueError(f"Unknown material: {verharding}")

        material = self.param_config.ROAD_DATA[verharding]

        if onderhouds_type.startswith('lokaal') or onderhouds_type.startswith("algemeen"):
            state.visueel = 0.9
            state.cumul_B = 0
            state.B_visueel = material.B_visueel_na_onderhoud.get(onderhouds_type, state.B_visueel)
        elif onderhouds_type.startswith("versterking"):
            state.visueel, state.structureel = 0.9, 0.9
            state.cumul_B, state.cumul_W = 0, 0
            state.B_visueel = material.B_visueel_na_onderhoud.get(onderhouds_type, state.B_visueel)

        return state

    def _validate_input(self, verharding, functie):
        if verharding not in self.param_config.ROAD_DATA:
            raise ValueError(f"Unknown material: {verharding}")
        if functie not in self.param_config.WEGKENMERKEN:
            raise ValueError(f"Unknown road function: {functie}")
