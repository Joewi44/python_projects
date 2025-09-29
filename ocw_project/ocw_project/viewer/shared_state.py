import param
import panel as pn

class SharedState(param.Parameterized):
    uploaded_gdf = param.Parameter(default=None)
    ocw_model = param.Parameter(default=None)
    gdf_result = param.Parameter(default=None)
    export_params = param.Parameter(default=None)
    scenario_selector = pn.widgets.Select(name="Scenario", options=[], value=None)
    guid_selector = pn.widgets.Select(name="Guid", options=[], value=None)
    year_selector = pn.widgets.Select(name="Year", options=[], value=None)
    
# Create a singleton instance
shared_state = SharedState()
