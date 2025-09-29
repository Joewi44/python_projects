from dataclasses import dataclass, field, asdict
from typing import Dict, Optional, Union, List
import logging

logger = logging.getLogger(__name__)

@dataclass
class ScenarioItems:
    routine: Optional[Union[float, List[float]]] = 0.9
    lokaal: Optional[Union[float, List[float]]] = None
    algemeen_v1: Optional[Union[float, List[float]]] = None
    algemeen_v2: Optional[Union[float, List[float]]] = None
    algemeen_v3: Optional[Union[float, List[float]]] = None
    versterking_v1: Optional[float] = None
    versterking_v2: Optional[float] = None
    versterking_v3: Optional[float] = None

    def load_from_dict(self, data: dict):
        for onderhoud_type in self.__dataclass_fields__:
            if onderhoud_type in data:
                setattr(self, onderhoud_type, data.get(onderhoud_type))
            
            else:
                logger.warning(f"Ignoring unknown keys: {onderhoud_type}")
                raise KeyError(f"Unknown onderhoudswaarde in configuration: {onderhoud_type}")

    def to_dict(self):
        return asdict(self)
    
    def get_maintenance_type(self, globale_idex: float, globale_idex_min1_jaar: float) -> Optional[str]:
        """
        Determine which maintenance type applies based on the current (G) 
        and previous (G_min1) values, following priority order:
        1. routine / lokaal
        2. lokaal
        3. herstelling (algemeen_v1..v3)
        4. versterking (versterking_v1..v3)
        """
        # Priority 1: Check routine vs lokaal range
        if self.routine is not None and self.lokaal is not None:
            lokaal_values = self._as_list(self.lokaal)
            if self.routine >= globale_idex >= max(lokaal_values):
                return None

        # Priority 2: lokaal crossed between G_min1 and G
        if self.lokaal is not None:
            for drempel in self._as_list(self.lokaal):
                if globale_idex_min1_jaar >= drempel >= globale_idex:
                    return 'lokaal'

        # Priority 3: herstelling crossed between G_min1 and G
        herstelling_vals = {
            'algemeen_v1': self.algemeen_v1,
            'algemeen_v2': self.algemeen_v2,
            'algemeen_v3': self.algemeen_v3
        }
        for name, val in herstelling_vals.items():
            for v in self._as_list(val):
                if v is not None and globale_idex_min1_jaar >= v >= globale_idex:
                    return name

        # Priority 4: versterking crossed between G_min1 and G
        versterking_vals = {
            'versterking_v1': self.versterking_v1,
            'versterking_v2': self.versterking_v2,
            'versterking_v3': self.versterking_v3
        }
        for name, val in versterking_vals.items():
            if val is not None and globale_idex_min1_jaar >= val >= globale_idex:
                return name

        return None  # No threshold matched

    @staticmethod
    def _as_list(val):
        return val if isinstance(val, list) else [val]


@dataclass
class ScenarioConfig:
    sc_1: ScenarioItems = field(default_factory=lambda: ScenarioItems())

    def __post_init__(self):
        for i in range(2,19):
            setattr(self, f"sc_{i}", ScenarioItems())

    def __repr__(self):
        fields = [f"sc_{i}={getattr(self, f'sc_{i}')}" for i in range(1, 19)]
        return f"ScenarioConfig({', '.join(fields)})"

    def load_from_dict(self, params: dict):
        for key, value in params.items():
            if hasattr(self, key):
                getattr(self, key).load_from_dict(value)
            
            else:
                logger.warning(f"Ignoring unknown keys (scenarios): {key}")
                raise KeyError(f"Unknown scenarios in configuration: {key}")
            
        logger.info("scenarios successfully loaded.")
        logger.debug(f"{self.__str__()}")

    def to_dict(self):
        return {k: v.to_dict() for k, v in self.__dict__.items()}
    
    def get_maintenance_type(self, globale_idex: float, globale_idex_min1_jaar: float, scenario_id: int) -> Optional[str]:
        """Get maintenance type considering current and previous G values."""
        try:
            scenario = getattr(self, f"sc_{scenario_id}")
        except AttributeError:
            logger.error(f"Scenario {scenario_id} not found")
            raise KeyError(f"Scenario {scenario_id} not found")
        
        return scenario.get_maintenance_type(globale_idex, globale_idex_min1_jaar)

if __name__ == "__main__":
    session = ScenarioConfig()

    print(session)

    print(session.get_maintenance_type(globale_idex=0.49,globale_idex_min1_jaar=0.51,scenario_id=11))
