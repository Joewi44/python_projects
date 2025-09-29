import logging

logger = logging.getLogger(__name__)

class ColumnMappingConfig:
    def __init__(self):
        # default mapping
        self.mapping = {
            "guid": "WSO_SPLIT_",
            "straat": "Straat",
            "gemeente": "Gemeente",
            "deelgemeente": "Deelgemeen",
            "wegsectie": "WSO_GUID",
            "oppervlakte": "Shape_STAr",
            "verharding": "verhtype",
            "functie": "wegfunct",
            "visuele_index": "iv",
            "visuele_index_date": "Edited",
            "structurele_index": "is_mix",
            "structurele_index_date": "bouwdate",
            "globale_index": "ig_mix",
            "globale_index_date": "bouwdate",
            "bouwdate": "bouwdate",
            "prioriteit": "Prioriteit",
            "geometry": "geometry"
        }

    def __repr__(self):
        return f"{self.mapping}"

    def load_from_dict(self, data: dict):
        if not isinstance(data, dict):
            raise ValueError("ColumnMappingConfig expects a dict")
        self.mapping.update(data)

    def to_dict(self):
        return self.mapping
