import panel as pn
import os
from ocw_project.viewer.upload_tab import create_upload_tab
from ocw_project.viewer.params_tab import create_params_tab
from ocw_project.viewer.general_tab import create_general_info_tab
from ocw_project.viewer.scenario_tab import create_scenario_tab
from ocw_project.viewer.globaal_analyse_tab import create_global_scenario_analysis_tab
from ocw_project.viewer.map_view_tab import create_map_view_tab
from ocw_project.viewer.compare_price_tab import create_compare_price_tab
from ocw_project.viewer.shared_state import shared_state
from ocw_project.config.logger_config import setup_logging
from ocw_project.OcwSystematiek import OCWSystematiek
from functools import lru_cache

setup_logging()

import logging

logger = logging.getLogger(__name__)
logger.info(f"Started panel application in PID {os.getpid()}")

guid_selector = pn.widgets.Select(name="Guid", options=[])
scenario_selector = pn.widgets.Select(name="Scenario", options=[])
year_selector = pn.widgets.Select(name="Jaar", options=[])

# Example for General Info Tab
@pn.cache
def cached_general_info_tab(gdf_id):
    return create_general_info_tab(shared_state.gdf_export)

@pn.depends(shared_state.param.gdf_export)
def reactive_general_info_tab(gdf):
    return cached_general_info_tab(id(gdf))


# Example for Scenario Tab
@pn.cache
def cached_scenario_tab(scenario, guid, gdf_id):
    return create_scenario_tab(scenario, guid, shared_state.gdf_export)

@pn.depends(scenario_selector.param.value, guid_selector.param.value, shared_state.param.gdf_export)
def reactive_scenario_tab(scenario, guid, gdf):
    return cached_scenario_tab(scenario, guid, id(gdf))

# Example for Global Scenario Analysis Tab
@pn.cache
def cached_global_scenario_analysis_tab(scenario, gdf_id):
    return create_global_scenario_analysis_tab(scenario, shared_state.gdf_export)

@pn.depends(scenario_selector.param.value, shared_state.param.gdf_export)
def reactive_global_scenario_analysis_tab(scenario, gdf):
    return cached_global_scenario_analysis_tab(scenario, id(gdf))

# Example for Map View Tab
@pn.cache
def cached_create_map_view_tab(scenario, year, gdf_id):
    return create_map_view_tab(scenario, year, shared_state.gdf_export)

@pn.depends(scenario_selector.param.value, year_selector.param.value, shared_state.param.gdf_export)
def reactive_create_map_view_tab(scenario, year, gdf):
    return cached_create_map_view_tab(scenario, year, id(gdf))

# Example for Compare Price Tab (no widgets)
@pn.cache
def cached_compare_price_tab(gdf_id):
    return create_compare_price_tab()

@pn.depends(shared_state.param.gdf_export)
def reactive_create_compare_price_tab(gdf):
    return cached_compare_price_tab(id(gdf))


@pn.depends(shared_state.param.gdf_export, watch=True)
def update_selectors(gdf_export):
    if shared_state.gdf_export is not None and not shared_state.gdf_export.empty:
        guids = sorted(shared_state.gdf_export['guid'].unique().tolist())
        guid_selector.options = guids
        guid_selector.value = guids[0]

        scenario_options = sorted(shared_state.gdf_export["scenario_nm"].unique())
        scenario_selector.options = scenario_options
        scenario_selector.value = scenario_options[0]

        jaar_options = sorted(gdf_export['jaar'].unique())
        year_selector.options = jaar_options
        year_selector.value = min(jaar_options)
        
    else:
        guid_selector.options = []
        guid_selector.value = None

        scenario_selector.options = []
        scenario_selector.value = None

def create_dashboard():
    # Initiate OCW model
    try:
        shared_state.ocw_model = OCWSystematiek()
    except Exception as e:
        logger.warning(f"Default configuration not loaded: {e}")

    update_selectors(shared_state.gdf_export)
    
    # Create tabs
    tabs = pn.Tabs(
        ("System Parameters", create_params_tab()),
        ("Data Upload", create_upload_tab()),
        ("Overview", reactive_general_info_tab),
        ("Scenario Analyse", pn.Column(guid_selector, scenario_selector, reactive_scenario_tab)),
        ("Globale Analyse", pn.Column(scenario_selector, reactive_global_scenario_analysis_tab)),
        ("Map visualization", pn.Column(scenario_selector, year_selector, reactive_create_map_view_tab)),
        ("Compared prices", reactive_create_compare_price_tab),
        dynamic=True
    )
    
    return tabs

pn.panel(create_dashboard).servable()
