from dataclasses import dataclass, asdict
from typing import Dict, Optional, Tuple, Union, List
import numpy as np
import logging
import json

logger = logging.getLogger(__name__)

@dataclass
class Scenario:
    routine: Optional[Union[float, List[float]]] = 0.9
    lokaal: Optional[Union[float, List[float]]] = np.nan
    algemeen_v1: Optional[Union[float, List[float]]] = np.nan
    algemeen_v2: Optional[Union[float, List[float]]] = np.nan
    algemeen_v3: Optional[Union[float, List[float]]] = np.nan
    versterking_v1: Optional[float] = np.nan
    versterking_v2: Optional[float] = np.nan
    versterking_v3: Optional[float] = np.nan

    def get_maintenance_type(self, G: float, G_min1: float) -> Optional[str]:
        # Get all non-NaN herstelling values (algemeen)
        herstelling_vals = {
            'algemeen_v1': self.algemeen_v1,
            'algemeen_v2': self.algemeen_v2,
            'algemeen_v3': self.algemeen_v3
        }
        
        # Priority 1: Check if its not NAN
        if self._is_not_nan(self.routine) and self._is_not_nan(self.lokaal):
            #check if lokaal is list
            if isinstance(self.lokaal, list):
                if self.routine >= G >= max(self.lokaal):
                    return None
            else:
                # G between routine and lokaal
                if self.routine >= G >= self.lokaal:
                    return None
        
        # Priority 2:  Check if its not NAN
        if self._is_not_nan(self.lokaal):
            #check if lokaal is list
            if isinstance(self.lokaal, list):
                for drempel in self.lokaal:
                    if G_min1 >= drempel >= G:
                        return 'lokaal'
            # G between G_min1 and G
            else:
                if G_min1 >= self.lokaal >= G:
                    return 'lokaal'
            
        # Priority 3: Check herstelling between G_min1 and G
        for name, val in herstelling_vals.items():
            if isinstance(val, list):
                for v in val:
                    if not np.isnan(v) and G_min1 >= v >= G:
                        return name
            else:
                if not np.isnan(val) and G_min1 >= val >= G:
                    return name

        # Priority 4: Check versterking between G_min1 and G
        versterking_vals = {
            'versterking_v1': self.versterking_v1,
            'versterking_v2': self.versterking_v2,
            'versterking_v3': self.versterking_v3
        }
        for name, val in versterking_vals.items():
            if not np.isnan(val) and G_min1 > val >= G:
                return name
        
        return None  # No condition matched
    
    @staticmethod
    def _is_not_nan(value):
        if isinstance(value, list):
            return all(not np.isnan(v) for v in value)
        return not np.isnan(value)
    
@dataclass
class Maatregel:
    naam: str
    prijs: float

@dataclass
class Kwaliteit:
    naam: str
    max_value: float
    min_value: float

class KwaliteitsIndex:
    KWALITEITSINDEX: Dict[str, Kwaliteit] = {}

    @classmethod
    def load_kwaliteits_index(cls, data: dict):
        for naam, values in data.items():
            try:
                if "min" not in values or "max" not in values:
                    logger.error(f"Failed to load, missing 'min' or 'max' for {naam}")
                    raise KeyError(f"Failed to load, missing 'min' or 'max' for {naam}")

                max_value = cls._validate_numbers(values['max'], f"{naam}_max")
                min_value = cls._validate_numbers(values['min'], f"{naam}_min")

                if min_value > max_value:
                    logger.error(f"Failed to load for '{naam}', min > max: {min_value} > {max_value}")
                    raise ValueError(f"Failed to load for '{naam}', min > max: {min_value} > {max_value}")

                cls.KWALITEITSINDEX[naam] = Kwaliteit(naam, max_value, min_value)
            except Exception as e:
                logger.error(f"Failed to load kwaliteit for '{naam}': {e}")
                raise 

        logger.info("KWALITEITSINDEX successfully loaded.")

    @classmethod
    def serialize_to_dict(cls) -> Dict[str, Kwaliteit]:
        data = {}
        for k, v in cls.KWALITEITSINDEX.items():
            data[v.naam] = {
                "max" : v.max_value, 
                "min" : v.min_value}
        logger.debug(f"returned KWALITEITSINDEX {data}")
        return data

    @classmethod
    def _validate_numbers(cls, value: float, name: str) -> float:
        if value is None:
            logger.error(f"{name} is None")
            raise ValueError(f"{name} cannot be None")
        if not isinstance(value, (int, float)):
            logger.error(f"{name} must be numeric, got {type(value)}")
            raise TypeError(f"{name} must be numeric, got {type(value)}")
        if value < 0 or value > 0.9:
            logger.error(f"{name} must be between 0 and 0.9 inclusive, got {value}")
            raise ValueError(f"{name} must be between 0 and 0.9 inclusive, got {value}")
        return float(value)

    @classmethod
    def save_to_json(cls, file_path: str, parent_key: str="KWALITEITSINDEX") -> None:
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

        data[parent_key].update(cls.get_values())
        logger.info(f"Updated data for '{parent_key}': {cls.get_values()}")

        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)
            logger.debug(f"Data successfully written to {file_path}")

    @classmethod
    def lookup_kwaliteits_index(cls, globaal: float) -> str:
        for kwaliteit in cls.KWALITEITSINDEX.values():
            if kwaliteit.min_value <= globaal <= kwaliteit.max_value:
                return kwaliteit.naam
        return None

class MaintenanceManager:
    # Mapping: onderhouds_type per verharding → (maatregel_naam, kostprijs)
    MAATREGEL_MAPPING: Dict[str, Dict[str, Maatregel]] = {}

    @classmethod
    def load_maatregel_mapping(cls, data: dict):
        """Load maatregel mapping and convert inner values to Maatregel instances."""
        for mat_type, onderhouds_type in data.items():
            try:
                if mat_type not in cls.MAATREGEL_MAPPING:
                    cls.MAATREGEL_MAPPING[mat_type] = {}

                for onderhoud, value in onderhouds_type.items():
                    cls.MAATREGEL_MAPPING[mat_type][onderhoud] = Maatregel(
                        naam=value['naam'],
                        prijs=cls._validate_numbers(value['prijs'], f"{onderhoud}_prijs")
                    )
                    logger.debug(f"{mat_type} - {onderhoud} - {value}")

                logger.info("MAATREGEL_MAPPING successfully loaded.")

            except Exception as e:
                logger.error(f"Failed to load kwaliteit for '{mat_type}': {e}")
                raise 

    @classmethod
    def serialize_to_dict(cls):
        data = {}
        for k, v in cls.MAATREGEL_MAPPING.items():
            data[k] = {
                k2: asdict(v2) for k2, v2 in v.items()
            }
        return data
    
    @classmethod
    def _validate_numbers(cls, value: float, name: str) -> float:
        if value is None:
            logger.error(f"{name} is None")
            raise ValueError(f"{name} cannot be None")
        if not isinstance(value, (int, float)):
            logger.error(f"{name} must be numeric, got {type(value)}")
            raise TypeError(f"{name} must be numeric, got {type(value)}")
        if value < -1:
            logger.error(f"{name} must be > -1, got {value}")
            raise ValueError(f"{name} must be > -1, got {value}")
        return float(value)

    @classmethod
    def save_to_json(cls, file_path: str, parent_key: str="MAATREGEL_MAPPING2") -> None:
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

        data[parent_key].update(cls.get_values())
        logger.info(f"Updated data for '{parent_key}': {cls.get_values()}")

        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)
            logger.debug(f"Data successfully written to {file_path}")

    # Scenario database
    SCENARIOS: Dict[int, Scenario] = {
        1: Scenario(routine=0.9, lokaal=0.8, algemeen_v3=0.5, versterking_v3=0.3),
        2: Scenario(routine=0.9, lokaal=0.8, algemeen_v3=0.5, versterking_v2=0.3),
        3: Scenario(routine=0.9, lokaal=0.8, algemeen_v3=0.5, versterking_v1=0.3),
        4: Scenario(routine=0.9, lokaal=0.8, algemeen_v2=0.5, versterking_v3=0.3),
        5: Scenario(routine=0.9, lokaal=0.8, algemeen_v2=0.5, versterking_v2=0.3),
        6: Scenario(routine=0.9, lokaal=0.8, algemeen_v2=0.5, versterking_v1=0.3),
        7: Scenario(routine=0.9, lokaal=0.8, algemeen_v1=0.5, versterking_v3=0.3),
        8: Scenario(routine=0.9, lokaal=0.8, algemeen_v1=0.5, versterking_v2=0.3),
        9: Scenario(routine=0.9, lokaal=0.8, algemeen_v1=0.5, versterking_v1=0.3),
        10: Scenario(routine=0.9, lokaal=[0.8, 0.5], versterking_v3=0.3),
        11: Scenario(routine=0.9, lokaal=[0.8, 0.5], versterking_v2=0.3),
        12: Scenario(routine=0.9, lokaal=[0.8, 0.5], versterking_v1=0.3),
        13: Scenario(routine=0.9, lokaal=0.8, algemeen_v3=[0.5, 0.3]),
        14: Scenario(routine=0.9, lokaal=0.8, algemeen_v2=[0.5, 0.3]),
        15: Scenario(routine=0.9, lokaal=0.8, algemeen_v1=0.5, algemeen_v3=0.3),
        16: Scenario(routine=0.9, lokaal=0.8, algemeen_v1=0.5, algemeen_v2=0.3),
        17: Scenario(routine=0.9, lokaal=[0.8, 0.5, 0.3]),
        18: Scenario(routine=0.9)
    }

    @staticmethod
    def get_maintenance_type(G: float, G_min1: float, scenario_id: int) -> Optional[str]:
        """Get maintenance type considering current and previous G values."""
        scenario = MaintenanceManager.SCENARIOS.get(scenario_id)
        if scenario is None:
            logger.error(f"Scenario {scenario_id} not found")
            raise 
        return scenario.get_maintenance_type(G, G_min1)
    
    @staticmethod
    def list_scenarios() -> Dict[int, Scenario]:
        """Get all available scenarios."""
        return MaintenanceManager.SCENARIOS
    
    @classmethod
    def get_maatregel_info(cls, verharding: str, onderhoud_type: Optional[str]) -> Tuple[str, float]:
        """Get maatregel name and cost for given surface type and maintenance type."""
        if not onderhoud_type or onderhoud_type == 'None':
            return ('None', 0.0)
        
        verharding = verharding.strip().lower()
        maatregel = cls.MAATREGEL_MAPPING.get(verharding, {}).get(onderhoud_type)
        
        if maatregel is None:
            logger.warning("Geen maatregel gevonden voor verharding='{verharding}' en onderhoud_type='{onderhoud_type}'")
            return ("Onbekend", 0.0)
        
        if maatregel.prijs < 0:
            return (maatregel.naam, 0.0)
            
        return (maatregel.naam, maatregel.prijs)
    
