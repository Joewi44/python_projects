from dataclasses import dataclass, field, asdict
from typing import Dict, Optional, Union, List, Literal
import logging

logger = logging.getLogger(__name__)

# Define types
MaterialType = Literal["asfalt", "beton", "elementen"]
MaintenanceType = Literal["routine", "lokaal", "algemeen_v1", "algemeen_v2", 
                         "algemeen_v3", "versterking_v1", "versterking_v2", "versterking_v3", "None"]
RoadFunctionType = Literal["erf", "verzamel", "doorgang"]

@dataclass
class SimulationState:
    """Stores current simulation state variables"""
    verharding: MaterialType
    functie: RoadFunctionType
    K_visueel: float                # Will be initialized from WEG_KENMERKEN
    K_structureel: float            # Will be initialized from WEG_KENMERKEN
    T: float                        # Will be initialized from WEG_KENMERKEN
    B_visueel: float                # Will be initialized from VERHARDINGSSOORT_KENMERKEN
    B_structureel: float            # Will be initialized from VERHARDINGSSOORT_KENMERKEN
    cumul_B: float = 0
    cumul_W: float = 0
    visueel: float = 0.9
    structureel: float = 0.9
    g_min1: float = 0.9
    globaal: float = 0.9
    onderhouds_type: MaintenanceType = "None"


    