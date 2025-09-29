import panel as pn
import os

pn.extension('tabulator')

from ocw_project.viewer.params_tab import create_params_tab
from ocw_project.viewer.upload_tab import create_upload_tab
from ocw_project.viewer.process_tab import create_process_tab
from ocw_project.viewer.general_analyse_tab import create_general_analyse_tab
from ocw_project.viewer.segment_analyse_tab import create_segment_analyse_tab
from ocw_project.viewer.globaal_analyse_tab import create_globaal_analyse_tab
from ocw_project.viewer.map_view_tab import create_map_view_tab
from ocw_project.viewer.shared_state import shared_state
from ocw_project.OcwSystematiek import OCWSystematiek
from ocw_project.config.logger_config import setup_logging

setup_logging()

import logging

logger = logging.getLogger(__name__)
logger.info(f"Started panel application in PID {os.getpid()}")

@pn.depends(shared_state.param.gdf_result, watch=True)
def update_selectors(gdf_result):
    if shared_state.gdf_result is not None and not shared_state.gdf_result.empty:
        guids = sorted(shared_state.gdf_result['guid'].unique().tolist())
        shared_state.guid_selector.options = guids
        shared_state.guid_selector.value = guids[0]

        scenario_options = sorted(shared_state.gdf_result["scenario_nm"].unique())
        shared_state.scenario_selector.options = scenario_options
        shared_state.scenario_selector.value = scenario_options[0]

        jaar_options = sorted(shared_state.gdf_result['jaar'].unique())
        shared_state.year_selector.options = jaar_options
        shared_state.year_selector.value = min(jaar_options)
        
    else:
        shared_state.guid_selector.options = []
        shared_state.guid_selector.value = None

        shared_state.scenario_selector.options = []
        shared_state.scenario_selector.value = None

        shared_state.year_selector.options = []
        shared_state.year_selector.value = None

def create_dashboard():
    # Initiate OCW model
    try:
        shared_state.ocw_model = OCWSystematiek()
    except Exception as e:
        logger.warning(f"Default configuration not loaded: {e}")

    tabs = pn.Tabs(
        ('Upload data', create_upload_tab),
        ("Parameters", create_params_tab),
        ("Process data", create_process_tab),
        ("General analyse", create_general_analyse_tab),
        ("Segment analyse", create_segment_analyse_tab),
        ("Globaal analyse", create_globaal_analyse_tab),
        ("Map view", pn.panel(create_map_view_tab, load=True)),
        dynamic=True
    )

    return tabs

dashboard = create_dashboard()

# Register for panel serve CLI (optional)
dashboard.servable()



#  panel serve ocw_project/viewer/frontend_app.py --show