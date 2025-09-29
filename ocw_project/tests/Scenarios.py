from dataclasses import dataclass
import numpy as np
from typing import Dict, Optional

@dataclass
class Scenario:
    routine: float = 0.9
    lokaal: float = np.nan
    algemeen_v1: float = np.nan
    algemeen_v2: float = np.nan
    algemeen_v3: float = np.nan
    versterking_v1: float = np.nan
    versterking_v2: float = np.nan
    versterking_v3: float = np.nan

    def get_maintenance_type(self, G: float, G_min1: float) -> Optional[str]:
        # Get all non-NaN herstelling values (algemeen)
        herstelling_vals = {
            'algemeen_v1': self.algemeen_v1,
            'algemeen_v2': self.algemeen_v2,
            'algemeen_v3': self.algemeen_v3
        }
        
        # Priority 1: Check if its not NAN
        if self.is_not_nan(self.routine) and self.is_not_nan(self.lokaal):
            #check if lokaal is list
            if isinstance(self.lokaal, list):
                if self.routine >= G >= max(self.lokaal):
                    return None
            else:
                # G between routine and lokaal
                if self.routine >= G >= self.lokaal:
                    return None
        
        # Priority 2:  Check if its not NAN
        if self.is_not_nan(self.lokaal):
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
    def is_not_nan(value):
        if isinstance(value, list):
            return all(not np.isnan(v) for v in value)
        return not np.isnan(value)