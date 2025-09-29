import numpy as np
import pandas as pd
import geopandas as gpd
from typing import Dict, List
import os
from ocw_project.WegVakonderdeel import WegVakonderdeel
from ocw_project.config.app_config import AppConfig
from importlib.resources import files
import logging
import time

logger = logging.getLogger(__name__)

class OCWSystematiek:
    def __init__(self):
        logger.info("INIT OCWSystematiek")
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self._load_configurations()
        
    def _load_configurations(self):
        logger.info("Load all configurations from JSON files")

        self.app_config = AppConfig()
        self.app_config.load_all_data_from_json()

        self.economie = self.app_config.ECONOMIE
        self.param_config = self.app_config.VERHARDINGSSOORT_KENMERKEN
        self.verhardingssoort_kenmerken = self.param_config
        self.weg_kenmerken = self.app_config.WEG_KENMERKEN
        self.maatregel_mapping = self.app_config.MAATREGEL_MAPPING
        self.kwaliteitsindex = self.app_config.KWALITEITSINDEX
        self.scenarios = self.app_config.SCENARIOS
        self.column_mapping = self.app_config.COLUMN_MAPPING
        self.config_value_maps = self.app_config.CONFIG_VALUE_MAPS

        
        self._validate_parameters()

    def _validate_parameters(self):
        logger.info("Validate parameters")

        logger.info("Validatie van parameters succesvol voltooid!")

    def _apply_mappings(self, df: pd.DataFrame, inplace: bool = False) -> pd.DataFrame:
        """
        Apply domain mappings to input dataframe.
        - Uses maps from self.app_config.CONFIG_VALUE_MAPS
        - Preserves original values in '<col>_original'
        - Raises ValueError if required columns are missing or contain unexpected values
        - Returns a new DataFrame unless inplace=True
        """
        if not inplace:
            df = df.copy()

        config_value_maps = getattr(self.app_config, "CONFIG_VALUE_MAPS", None)
        functie_map = config_value_maps.get("functie")
        verharding_map = config_value_maps.get("verharding")
       
        functie_col = self.column_mapping.functie.get('value')
        verharding_col = self.column_mapping.verharding.get('value')

        to_map = {functie_col: functie_map, 
                  verharding_col: verharding_map}

        for col, mapping in to_map.items():
            if col not in df.columns:
                logger.warning(f"Source column '{col}' not found in dataframe.")
                raise ValueError(f"Source column '{col}' not found in dataframe.")
            
            unique_vals = set(df[col].dropna().unique())
        
            if unique_vals.issubset(set(mapping.keys())):
                df[f"{col}_original"] = df[col]
                mapped = df[col].map(mapping)
                unmapped = df[col][mapped.isna()].unique()
                if len(unmapped) > 0:
                    logger.warning(f"Unmapped values in '{col}': {unmapped}")
                df[col] = mapped
                logger.info(f"Mapped '{col}' with {len(mapping)} entries")
                
            elif unique_vals.issubset(set(mapping.values())):
                logger.info(f"'{col}' already contains mapped values")
            else:
                logger.warning(
                f"Unexpected values in '{col}': {unique_vals} "
                f"(expected subset of {set(mapping.keys())})"
                )
                raise ValueError(f"Unexpected values in '{col}': {unique_vals}")

        return df

    def bereken_index_segment(self, segment: WegVakonderdeel, jaren: int, 
                              scenario_nm: int=18) -> List[Dict]:
        """
        Calculate index evolution with cumulative degradation and dynamic B-values.
        Key improvements:
        1. Tracks cumulative degradation separately for visual (B) and structural (W) indices
        2. Dynamically adjusts B-value based on maintenance type
        3. Applies road-type specific degradation models
        4. Properly resets degradation after maintenance
        """
        state = self.app_config.initialize_simulation(
            verharding=segment.verharding, functie=segment.functie
            )
        
        # Track existing degradation (mogelijk al gedegradeerd)
        state.cumul_B = max(0, (0.9 - segment.visuele_index))
        state.cumul_W = max(0, (0.9 - segment.structurele_index))
        data = []
        state.visueel = segment.visuele_index
        state.structureel = segment.structurele_index
        state.globaal = segment.globale_index
        
        # Voeg technische levensduur check toe
        # Handle backlog (immediate maintenance if IG < 0.3)
        if state.globaal < 0.3:
            state.onderhouds_type = "versterking_v3"
            state = self.app_config.pas_index_aan_na_onderhoud(
                state, state.onderhouds_type, segment.verharding)

        # Voeg jaar 0 toe
        data.append(self._create_data_row(segment=segment, 
                                          state=state, 
                                          jaar_offset=0, 
                                          scenario_nm=scenario_nm))    
        
        for jaar in range(1, jaren + 1):
            # Bereken nieuwe degradatie (afhankelijk van wegtype)
            delta_B = state.K_visueel * (1 + state.T) * state.B_visueel
            delta_W = state.K_structureel * (1 + state.T) * state.B_structureel
            
            # Pas cumulatieve degradatie toe
            state.cumul_B += delta_B
            state.cumul_W += delta_W
            
            # LIMIT ONDER NUL
            state.visueel = max(0, 0.9 - state.cumul_B)
            state.structureel = max(0, 0.9 - state.cumul_W)
            state.g_min1 = state.globaal
            state.globaal = (state.visueel + state.structureel) / 2
            
            # Bepaal onderhoudsadvies
            state.onderhouds_type = self.scenarios.get_maintenance_type(
                globale_idex=state.globaal,
                globale_idex_min1_jaar=state.g_min1,
                scenario_id=scenario_nm)
            
            # Log huidige staat
            data.append(self._create_data_row(segment=segment, 
                                          state=state, 
                                          jaar_offset=jaar, 
                                          scenario_nm=scenario_nm)) 
            
            # Pas onderhoud toe (reset cumulatieve degradatie indien nodig)
            if state.onderhouds_type:
                state = self.app_config.pas_index_aan_na_onderhoud(state, state.onderhouds_type, segment.verharding)

        # BEWAAR ONDERHOUD DATA VOOR SCENARIO
        segment.save_scenario(data, scenario_nm)

        return data
    
    def bereken_index_alle_segmenten(self, scenario: int, segmenten: WegVakonderdeel, jaren: int=20) -> Dict:
        resultaten = {}
        for segment in segmenten:
            resultaten[segment] = self.bereken_index_segment(segment=segment, scenario_nm=scenario, jaren=jaren)
        logger.info(f"Scenario {scenario}: berekend voor {len(segmenten)} segmenten over {jaren} jaar.")
        return resultaten
    
    def segmenteren_wegennet(self, df: pd.DataFrame, preprocess: bool = True) -> List[WegVakonderdeel]:
        start = time.time()
        mapping = self.column_mapping.to_dict()
        
        missing = [col for col in mapping.values() if col not in df.columns]
        if missing:
            logger.warning("Missing columns: {missing}")
            raise ValueError(f"Missing columns: {missing}")
        
        # Apply mapping if requested
        if preprocess:
            df = self._apply_mappings(df)
        
        instances = [
        WegVakonderdeel(**{k: row[mapping[k]] for k in mapping})
        for _, row in df.iterrows()
        ]

        duration = time.time() - start
        logger.info(f"Segmenteren wegennet: {len(instances)} segmenten ingeladen in {duration:.2f} seconden.")
        return instances
    
    def _bereken_kosten(self, segment: WegVakonderdeel, onderhoud_type: str) -> float:
        """Bereken geschatte kosten voor onderhoud"""

        # Get base price per m²
        try:
            prijs_per_m2 = self.maatregel_mapping.get_maatregel_info(segment.verharding, onderhoud_type)[1]
        except KeyError:
            logging.warning(f"Price m2 is empty for {onderhoud_type}")
            prijs_per_m2 = 0

        if onderhoud_type == None:
            return 0
        elif onderhoud_type == 'lokaal':  # lokaal
            return max(0,prijs_per_m2 * segment.oppervlakte) # 10% van oppervlakte
        elif onderhoud_type.startswith(('versterking', 'algemeen')):
            return max(0,prijs_per_m2 * segment.oppervlakte)
        else:
            return 0  # Geen kosten voor routineonderhoud
        
    def _create_data_row(self, segment: WegVakonderdeel, state: AppConfig, 
                         jaar_offset: int, scenario_nm: int) -> Dict:
        """Genereer uniforme datarij"""
        data_row = {
            'jaar': segment.visuele_index_date.year + jaar_offset,
            'scenario_nm': scenario_nm,
            'onderhouds_type': state.onderhouds_type,
            'maatregel': self.maatregel_mapping.get_maatregel_info(
                segment.verharding, state.onderhouds_type
            )[0],
            'visueel_index': state.visueel,
            'structureel_index': state.structureel,
            'globaal_index': state.globaal,
            'cumul_B': state.cumul_B,
            'cumul_W': state.cumul_W,
            'B_visueel': state.B_visueel,
            'cost': self._bereken_kosten(segment, state.onderhouds_type),
            'kwaliteit': self.kwaliteitsindex.get_kwaliteits_index(state.globaal)
        }
        return data_row

    def get_all_df_onderhoud(self, segmenten: List[WegVakonderdeel], geometry: bool=True, export_df: bool=False) -> gpd.GeoDataFrame:
        start_time = time.time()
        dfs = []

        for segment in segmenten:
            df_single = segment.df_onderhouds_historie.copy()

            if df_single.empty:
                logger.debug(f"Segment {segment.guid} heeft geen onderhoudshistorie, wordt overgeslagen.")
                continue
            # Change column mapping for export
            if export_df:
                for col, val in self.column_mapping.to_dict().items():
                    df_single[val] = getattr(segment, col)
            else:
                for col in self.column_mapping.to_dict().keys():
                    df_single[col] = getattr(segment, col)


            dfs.append(df_single)

        if not dfs:
            logger.warning("Geen onderhoudshistorie gevonden in segmenten.")
            return gpd.GeoDataFrame(columns=[], geometry='geometry')

        df_all = pd.concat(dfs, ignore_index=True)
        logger.info(f"Totaal onderhoudsrecords samengevoegd: {len(df_all)} uit {len(segmenten)} segmenten.")

        gdf_all = gpd.GeoDataFrame(df_all, geometry='geometry', crs='EPSG:31370')

        if not geometry:
            gdf_all = gdf_all.drop(columns='geometry')

        logger.info(f"GeoDataFrame opgebouwd in {time.time() - start_time:.2f} seconden, {len(gdf_all)} rijen.")
        #logger.debug(gdf_all.info())
        return gdf_all
    
    def economische_optimalisatie(self, segment: WegVakonderdeel, onderhouds_type: str) -> Dict:
        """
        Economische optimalisatie voor onderhoud (9.3 en 9.4)
        """
        # Vereenvoudigd model (9.3.4)
        _, prijs_onderhoud = self.maatregel_mapping.get_maatregel_info(segment.verharding, onderhouds_type)
        _, prijs_lokaal = self.maatregel_mapping.get_maatregel_info(segment.verharding, 'lokaal')
        T_vereenvoudigd = np.sqrt(prijs_onderhoud / prijs_lokaal)
        
        # Uitgebreid model (9.4.1.2)
        T_uitgebreid = self._bereken_uitgebreid_model(
            segment, onderhouds_type)
        
        return {
            'vereenvoudigd': T_vereenvoudigd,
            'uitgebreid': T_uitgebreid,
        }

    def _bereken_uitgebreid_model(self, segment: WegVakonderdeel, onderhouds_type: str) -> float:
        # Configuratie
        r = self.economie.uitgebreid_r          # Disconteringsvoet      
        i = self.economie.uitgebreid_i          # Inflatie
        sigma = self.economie.uitgebreid_sigma  # Groeipercentage gewoon onderhoud
        jaren = 30                              # Maximale horizon voor analyse

        # Vector van jaren [1, 2, ..., 30]
        t = np.arange(1, jaren + 1)
        
        # Basis kosten (per m² × oppervlakte)
        cr = self.maatregel_mapping.get_maatregel_info(segment.verharding, onderhouds_type)[1] * segment.oppervlakte  # Reparatiekost
        ce = self.maatregel_mapping.get_maatregel_info(segment.verharding, 'lokaal')[1] * segment.oppervlakte  # Jaarlijks onderhoud

        # 1. Capital Recovery Factor
        CRF = (r * (1 + r)**t) / ((1 + r)**t - 1)
        
        # 2. Gewoon onderhoud (CE)
        CE = ce * (1 + sigma)**(t-1) * (1 + i)**(t-1)  # Groei met sigma en inflatie
        CEA = CE * (1 + r)**-(t-1)                     # Geactualiseerd
        CEAC = np.cumsum(CEA)                          # Cumulatief geactualiseerd
        CEACE = CRF * CEAC                              # Equivalente annuïteit

        # 3. Reparatiekosten (CR)
        CR = cr * (1 + i)**(t-1)                       # Inflatiecorrectie
        CRA = CR * (1 + r)**-(t-1)                     # Geactualiseerd
        CRACC = CRF * CRA                               # Equivalente annuïteit

        # 4. Totale jaarlijkse kost
        CTA = CEACE + CRACC

        disconteringsvoet, inflatie, sigma_array, reparatie_kost, onderhoud_kost = [
            np.full(30, val) for val in (r, i, sigma, cr, ce)
            ]
        columns = (["CRF", "CE", "CEA", "CEAC", "CEACE",
                     "CR", "CRA", "CRACC", "CTA", "disconteringsvoet",
                    "inflatie", "sigma", "reparatie_kost", "jaarlijks_onderhoud"
                     ])
        data = np.column_stack([CRF, CE, CEA, CEAC, CEACE, CR, 
                                CRA, CRACC, CTA, disconteringsvoet, inflatie, 
                                sigma_array, reparatie_kost, onderhoud_kost])
        new_data= pd.DataFrame(data=data, columns=columns)
        new_data['onderhoud_type'] = onderhouds_type
        segment.set_uitgebreid_model(new_data, np.argmin(CTA) + 1, onderhouds_type)

        return np.argmin(CTA) + 1
    
# Run the application                   
if __name__ == '__main__':
    
    print(os.getcwd())

    file2 = "data/input_viabel/Machelen_Data_Shapefiles/Wegsectieonderdeel_SPLIT.shp"
    df_import = gpd.read_file(file2)

    """type_dict = {
        'G_date': 'datetime64[ns]',
        'S_date': 'datetime64[ns]',
        'DATUM': 'datetime64[ns]'
    }
    df_import = df_import.astype(type_dict)"""
    print(df_import.columns)

    # Map road functions (k)
    road_function_map = {
        'ERF': 'erf',       # Erffunctie
        'VW': 'verzamel',   # Verzamelweg
        'DGW': 'doorgang'   # Doorgangsweg
    }

    # Map pavement types (j)
    pavement_type_map = {
        'BS': 'asfalt',  # Asfalt (bitumineuze verharding)
        'CS': 'beton',  # Beton
        'BP': 'elementen'   # Elementenverharding
    }
    
    # Create new columns with mapped values
    df_import['functie'] = df_import['wegfunct'].map(road_function_map)
    #df_import['verharding'] = df_import['verhtype'].map(pavement_type_map)

    df_import.drop(columns=['wegfunct'], inplace=True)
    df_import.rename(columns={'functie': 'wegfunct', 'verharding': 'verhtype'}, inplace=True)



    model = OCWSystematiek()
 


    ocw = model.segmenteren_wegennet(df=df_import)
    
    model.bereken_index_alle_segmenten(1, ocw, 20)
    model.bereken_index_alle_segmenten(2, ocw, 20)
    #Segmenteren wegennet
    straat_erf_elementen = ocw[200]
    straat_erf_asfalt = ocw[20]
    straat_doorgang_asfalt = ocw[0]
    straat_0 = ocw[1]
    straat = ocw[4]

    print(f"Aantal straten {len(ocw)}")
    print(f"Straat ERF-ELEMENTEN: {straat_erf_elementen}")
    print(f"Globale index eerste straat: {straat_0.globale_index:.2f},"
            f"{straat_0.straat} {straat_0.functie} {straat_0.verharding}")
    print(f"Globale index tweede straat: {straat.globale_index:.2f}, {straat.functie} {straat.verharding}")

    print(ocw[200].onderhouds_acties)

    print(model.economische_optimalisatie(straat, 'algemeen_v3'))


