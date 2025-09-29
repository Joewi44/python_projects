from dataclasses import dataclass, field
from typing import Literal, Optional, Dict
import json
from pathlib import Path
import os
from datetime import datetime

from ocw_project.config.wegkenmerken import WegKenmerkenConfig
from ocw_project.config.verhardingssoortkenmerken import VerhardingssoortKenmerkenConfig
from ocw_project.config.maatregel_mapping import MaatregelMappingConfig
from ocw_project.config.kwaliteitsindex import KwaliteitsIndexConfig
from ocw_project.config.economie import EconomicConfig
from ocw_project.config.scenarios import ScenarioConfig
from ocw_project.config.simulation import SimulationState
from ocw_project.config.column_mapping import ColumnMappingConfig

import logging

logger = logging.getLogger(__name__)

# Define types
MaterialType = Literal["asfalt", "beton", "elementen"]
MaintenanceType = Literal["routine", "lokaal", "algemeen_v1", "algemeen_v2", 
                         "algemeen_v3", "versterking_v1", "versterking_v2", "versterking_v3", "None"]
RoadFunctionType = Literal["erf", "verzamel", "doorgang"]

@dataclass
class AppConfig:
    WEG_KENMERKEN: WegKenmerkenConfig = field(default_factory=WegKenmerkenConfig)
    VERHARDINGSSOORT_KENMERKEN: VerhardingssoortKenmerkenConfig = field(default_factory=VerhardingssoortKenmerkenConfig)
    MAATREGEL_MAPPING: MaatregelMappingConfig = field(default_factory=MaatregelMappingConfig)
    KWALITEITSINDEX: KwaliteitsIndexConfig = field(default_factory=KwaliteitsIndexConfig)
    ECONOMIE: EconomicConfig = field(default_factory=EconomicConfig)
    SCENARIOS: ScenarioConfig = field(default_factory=ScenarioConfig)
    COLUMN_MAPPING: ColumnMappingConfig = field(default_factory=ColumnMappingConfig)
    CONFIG_VALUE_MAPS: Dict = field(default_factory=lambda: {"functie": {
        'ERF': 'erf',   # Erffunctie
        'VW': 'verzamel',   # Verzamelweg
        'DGW': 'doorgang'   # Doorgangsweg
    },
    "verharding": {
        'BS': 'asfalt',   # Asfalt (bitumineuze verharding)
        'CS': 'beton',    # Beton
        'BP': 'elementen' # Elementenverharding
    }})

    def __post_init__(self,config_path: Optional[str] = None,
        save_path: Optional[str] = None,
    ):
        # Define default paths relative to the project root
        self.BASE_DIR = Path(__file__).resolve().parent.parent.parent
        self.DEFAULT_CONFIG = self.BASE_DIR / "ocw_project" / "config" / "_parameters.json"
        logger.debug(f"Parameter location: {self.DEFAULT_CONFIG}")

         # Generate a timestamp for the save file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_save_filename = f"_parameters_new_{timestamp}.json"
        self.DEFAULT_SAVE = self.BASE_DIR / "data" / "output_ocw" / default_save_filename

        # Use provided paths or environment variables, otherwise use defaults
        self.config_path = Path(os.getenv("CONFIG_PATH", config_path or str(self.DEFAULT_CONFIG)))
        self.save_path = Path(os.getenv("SAVE_PATH", save_path or str(self.DEFAULT_SAVE)))

    def load_all_data_from_json(self):
        """Load configuration data from a JSON file."""
        loaded_keys = []
        try:
            with open(self.config_path, 'r') as f:
                data = json.load(f)
        except FileNotFoundError:
            logger.error(f"Config file not found: {self.config_path}")
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {self.config_path}: {e}")
            raise TypeError(f"Invalid JSON in {self.config_path}: {e}")

        for key, value in data.items():
            if hasattr(self, key):
                attr = getattr(self, key)
                if hasattr(attr, 'load_from_dict'):
                    try:
                        attr.load_from_dict(value)
                        loaded_keys.append(key)
                    except AttributeError as e:
                        logger.error(f"Failed to load data for {key}: {e}")
                        raise TypeError(f"Failed to load data for {key}: {e}")
                else:
                    logger.warning(f"Attribute {key} does not have load_from_dict method")
            else:
                logger.warning(f"Ignoring unknown configuration keys: {key}")

        logger.info(f"Configuration loaded: {', '.join(loaded_keys)}")
        logger.debug(f"Loaded configuration keys: {loaded_keys}")

    def load_all_data_to_json(self, viewer:bool=False):
        data = {key: value.to_dict() for key, value in self.__dict__.items() 
                if hasattr(value, "to_dict")}
        
        if viewer:
            return data

        try:
            with open(self.save_path, "w") as f:
                json.dump(data, f, indent=4)
        except FileNotFoundError:
            logger.error(f"File not found: {self.config_path}")
            raise FileNotFoundError(f"File not found: {self.config_path}")
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in file: {self.config_path}")
            raise

        logger.info(f"Configuration saved to {self.save_path}")
        return self.save_path

    def update_partial_data_to_json(self, parent_key: str) -> None:
        parent_key = parent_key.upper()
        if hasattr(self, parent_key):
            obj = getattr(self, parent_key)
        else:
            logger.warning(f"Ignoring unknown configuration keys: {parent_key}")
            raise AttributeError(f"Unknown configuration key: {parent_key}")
    
        try:
            with open(self.config_path, 'r') as f:
                data = json.load(f)
        except FileNotFoundError:
            logger.error(f"File not found: {self.config_path}")
            raise FileNotFoundError(f"File not found: {self.config_path}")
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in file: {self.config_path}")
            raise

        if parent_key not in data:
            logger.warning(f"Parent key '{parent_key}' not found in JSON.")
            raise KeyError(f"Parent key '{parent_key}' not found in JSON.")

        try:
            new_data = obj.to_dict()
            logger.debug(f"Parent key: {parent_key}")
            logger.debug(f"Existing data type: {type(data[parent_key])}")
            logger.debug(f"Existing data: {data[parent_key]}")
            logger.debug(f"New data type: {type(new_data)}")
            logger.debug(f"New data: {new_data}")
        
            data[parent_key].update(new_data)
        except Exception as e:
            logger.warning(f"Issue updating {e} {parent_key} {obj}")
            import traceback
            logger.warning(f"Full traceback: {traceback.format_exc()}")


        with open(self.config_path, 'w') as f:
            json.dump(data, f, indent=4)
            logger.info(f"Updated data for '{parent_key}' in '{self.config_path}': {obj.to_dict()}")
            logger.debug(f"Data successfully written to {self.config_path}")

        return self.config_path

    def initialize_simulation(self, verharding: MaterialType, functie: RoadFunctionType) -> SimulationState:
        material = getattr(self.VERHARDINGSSOORT_KENMERKEN, verharding)
        weg_functie = getattr(self.WEG_KENMERKEN, functie)

        state = SimulationState(
            verharding=verharding,
            functie=functie,
            K_visueel= weg_functie.K_visueel,
            K_structureel=weg_functie.K_structureel,
            T=weg_functie.T,
            B_visueel=material.B_visueel_standaard,
            B_structureel=material.B_structureel_standaard
        )

        logger.debug(f"SimulationState initialized: {state}")
        return state
    
    def pas_index_aan_na_onderhoud(self, state: SimulationState, onderhouds_type: str, verharding: MaterialType) -> SimulationState:
        material = getattr(self.VERHARDINGSSOORT_KENMERKEN, verharding)
        if onderhouds_type.startswith('lokaal') or onderhouds_type.startswith("algemeen"):
            state.visueel = 0.9
            state.cumul_B = 0
            if hasattr(material.B_visueel_na_onderhoud, onderhouds_type):
                state.B_visueel = getattr(material.B_visueel_na_onderhoud, onderhouds_type)
            else:
                logger.warning(f"Unknown onderhouds_type: {onderhouds_type}")
        elif onderhouds_type.startswith("versterking"):
            state.visueel, state.structureel = 0.9, 0.9
            state.cumul_B, state.cumul_W = 0, 0
            if hasattr(material.B_visueel_na_onderhoud, onderhouds_type):
                state.B_visueel = getattr(material.B_visueel_na_onderhoud, onderhouds_type)
            else:
                logger.warning(f"Unknown onderhouds_type: {onderhouds_type}")

        return state


if __name__ == "__main__":
    session = AppConfig()
    print("Before loading:")

    session.load_all_data_from_json()
    print("\nAfter loading:")

    print(session)
    print()

    print(session.SCENARIOS.get_maintenance_type(globale_idex=0.79, globale_idex_min1_jaar=0.81, scenario_id=1))

    session.load_all_data_to_json()

    state = session.initialize_simulation("asfalt", "erf")

    print(state)