import pandas as pd
import datetime
import logging

logger = logging.getLogger(__name__)

class WegVakonderdeel:
    """Dataklasse voor een wegvakonderdeel volgens OCW-systematiek"""

    def __init__(self, **kwargs):
        self.guid = kwargs.get('guid')
        self.straat = kwargs.get('straat')
        self.gemeente = kwargs.get('gemeente')
        self.deelgemeente = kwargs.get('deelgemeente', "None")
        self.wegsectie = kwargs.get('wegsectie', "None")
        self.prioriteit = kwargs.get('prioriteit', 0) # Weet niet waarvoor deze gebruikt wordt
        self.oppervlakte =  kwargs.get('oppervlakte') # in meters2
        self.verharding = kwargs.get('verharding')  # 'asfalt /BS', 'beton/CS', 'elementen/BP'
        self.functie = kwargs.get('functie')  # 'erf/ ERF', 'verzamel / VW', 'doorgang / DGW'
        self.geometry = kwargs.get('geometry')  # Polygon geo data
        
        self.visuele_index = kwargs.get('visuele_index', 0)
        self.visuele_index_date = kwargs.get('visuele_index_date')
        self.structurele_index = kwargs.get('structurele_index', 0)
        self.structurele_index_date = kwargs.get('structurele_index_date')
        self.globale_index = kwargs.get('globale_index', 0.5 * (self.structurele_index+self.visuele_index))
        self.globale_index_date = kwargs.get('globale_index_date')
        self.bouwdate = kwargs.get('bouwdate')
        self.leeftijd = self.bereken_leeftijd(self.bouwdate)
        
        # self.toegewezen_strategie = kwargs.get('toegewezen_strategie', 1)
        # Track maintenance actions (original dict format)
        self.onderhouds_acties = {}
        self.uitgebreid_model_jaar = []
        self.df_uitgebreid_model = pd.DataFrame()

        # Degradation/maintenance history as DataFrame
        self.df_onderhouds_historie = pd.DataFrame(columns=[
            'jaar', 'scenario_nm', 'visueel_index', 'structureel_index',
            'globaal_index', 'onderhouds_type','maatregel', 'cumul_B', 'cumul_W', 'B_visueel', 'cost',
            'kwaliteit'
        ])
        if self.guid is None:
            logger.warning("WegVakonderdeel initialized without a GUID.")

    def bereken_leeftijd(self, datum)-> int: 
        vandaag = datetime.datetime.now()
        if datum is None:
            logger.warning(f"Leeftijd kan niet berekend worden: datum is None for {self.guid}")
            return None
        try:
            leeftijd = vandaag.year - datum.year - ((vandaag.month, vandaag.day) < (datum.month, datum.day))
            logger.debug(f"Berekende leeftijd voor {self.guid}: {leeftijd} jaar")
            return leeftijd
        except Exception as e:
            logger.error(f"Fout bij berekening van leeftijd voor {self.guid}: {e}")
            return None

    def set_uitgebreid_model(self, new_data, jaar, onderhoud_type):
        self.uitgebreid_model_jaar.append((onderhoud_type, jaar))
        self.df_uitgebreid_model = pd.concat([self.df_uitgebreid_model, new_data], ignore_index=True)
        #self.df_uitgebreid_model.index = [f"{year}" for year in range(self.visuele_index_date.year, self.visuele_index_date.year +30)]
        self.df_uitgebreid_model.columns.name = "year"

    def save_scenario(self, data: dict, scenario_nm: int): 
        logger.debug(f"Opslaan scenario {scenario_nm} voor {self.guid}, aantal jaren: {len(data)}")
        if scenario_nm not in self.onderhouds_acties:
            self.onderhouds_acties[scenario_nm] = {}

        self.onderhouds_acties[scenario_nm] = data
        new_data = pd.DataFrame(data)

        if self.df_onderhouds_historie.empty:
            self.df_onderhouds_historie = new_data
        else:
            self.df_onderhouds_historie = pd.concat(
                [self.df_onderhouds_historie, new_data],
                ignore_index=True
            )

    def __repr__(self):
        return (
            f"WegVakonderdeel(guid={self.guid!r}, straat={self.straat!r}, oppervlakte={self.oppervlakte}, "
            f"verharding={self.verharding!r}, functie={self.functie!r}, leeftijd={self.leeftijd}, "
            f"visuele_index={self.visuele_index}, structurele_index={self.structurele_index}, "
            f"globale_index={self.globale_index}, globale_index_date={self.globale_index_date})"
            f"scenario={self.df_onderhouds_historie}"
        )
