import param
from importlib.resources import files

class SharedState(param.Parameterized):
    gdf_export = param.Parameter(default=None)
    param_file_path = param.Parameter(default=files("ocw_project").joinpath("_parameters.json"))
    ocw_model = param.Parameter(default=None)

    
# Create a singleton instance
shared_state = SharedState()
