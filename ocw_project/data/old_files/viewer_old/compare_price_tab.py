import panel as pn
import pandas as pd
from ocw_project.viewer_old.shared_state import shared_state
import logging

logger = logging.getLogger(__name__)

def create_compare_price_tab():
    gdf = shared_state.gdf_export

    if gdf is None or gdf.empty:
        return pn.pane.Alert("⚠️ First load data", alert_type="warning")
    
    gdf_copy = gdf.copy()
    gdf_compare_price = gdf_copy.groupby(by=['scenario_nm', 'jaar'])['cost'].sum().unstack().T
    gdf_compare_price = gdf_compare_price.reset_index()

    gdf_compare_price = gdf_compare_price.round(2)

    exclude_cols = ['jaar']
    formatters = {
        'jaar': {'type': 'number', 'format': '0'}  # integer year
    }

    for col in gdf_compare_price.columns:
        if col not in exclude_cols:
            formatters[f'{col}'] = {'type': 'number', 'format': ',.2f'}

    

    tabulator = pn.widgets.Tabulator(gdf_compare_price, show_index=False, formatters=formatters)
    logger.info("create_compare_price_tab created")

    return tabulator