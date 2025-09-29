import pandas as pd
import pytest
from ocw_project.OcwSystematiek import OCWSystematiek

class DummyConfig:
    CONFIG_VALUE_MAPS = {
        "functie": {"ERF": "erf", "VW": "verzamel", "DGW": "doorgang"},
        "verharding": {"BS": "asfalt", "CS": "beton", "BP": "elementen"},
    }

class DummyColumnMapping:
    functie = {"value": "Wegfunctie"}
    verharding = {"value": "Verharding"}
    mapping = {"functie": "Wegfunctie", "verharding": "Verharding"}

@pytest.fixture
def systematiek():
    model = OCWSystematiek()
    model.app_config = DummyConfig()
    model.column_mapping = DummyColumnMapping()
    return model

def test_apply_mappings_success(systematiek):
    df = pd.DataFrame({"Wegfunctie": ["ERF", "VW"], "Verharding": ["BS", "CS"]})
    mapped = systematiek._apply_mappings(df)

    assert set(mapped["Wegfunctie"]) <= {"erf", "verzamel"}
    assert set(mapped["Verharding"]) <= {"asfalt", "beton"}
    assert "Wegfunctie_original" in mapped.columns
    assert "Verharding_original" in mapped.columns

def test_already_mapped(systematiek, caplog):
    df = pd.DataFrame({"Wegfunctie": ["erf"], "Verharding": ["asfalt"]})
    mapped = systematiek._apply_mappings(df)

    assert mapped.equals(df)  # nothing changed
    assert "already contains mapped" in caplog.text

def test_missing_column(systematiek):
    df = pd.DataFrame({"Verharding": ["BS"]})  # Wegfunctie is missing
    with pytest.raises(ValueError):
        systematiek._apply_mappings(df)

def test_unexpected_values(systematiek):
    df = pd.DataFrame({"Wegfunctie": ["XXX"], "Verharding": ["BS"]})
    with pytest.raises(ValueError):
        systematiek._apply_mappings(df)
