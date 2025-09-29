import panel as pn
import geopandas as gpd
import tempfile, os
from ocw_project.viewer.shared_state import shared_state
from ocw_project.viewer.params_tab import load_config_section
import logging

logger = logging.getLogger(__name__)

pn.extension('filedropper')

@pn.depends(shared_state.param.ocw_model)
def create_upload_tab(model=None):
    """
    Build the full parameters UI.
    This is automatically re-run whenever shared_state.ocw_model changes.
    """
    model = model or shared_state.ocw_model
    if model is None:
        return pn.pane.Alert("⚠️ OCW model not initialized!", alert_type="warning")
    
    file_input = pn.widgets.FileInput(
        name="Upload Shapefile Parts",
        accept=".shp,.dbf,.shx,.prj",
        multiple=True
    )
    file_hint = pn.pane.Markdown(
        "🗂️ **Please upload the files containing the following shapefile components:**\n"
        "- `.shp`\n"
        "- `.shx`\n"
        "- `.dbf`\n"
        "- (optionally: `.prj`)",
        styles={"font-size": "12px", "color": "gray"}
        )

    status = pn.pane.Markdown("📂 Awaiting shapefile upload...")
    column_mapping_section = pn.Column(pn.pane.Markdown("Upload a shapefile to see column mapping options"))

    def handle_upload(event=None):
        if not file_input.value:
            return

        with tempfile.TemporaryDirectory() as tmpdir:
            # Save all uploaded files
            for data, name in zip(file_input.value, file_input.filename):
                path = os.path.join(tmpdir, name)
                with open(path, "wb") as f:
                    f.write(data)

            # Find the .shp file among them
            shp_files = [f for f in file_input.filename if f.endswith(".shp")]
            if not shp_files:
                status.object = "❌ No .shp file found in upload."
                logger.error("❌ No .shp file found in upload.")
                return

            shp_path = os.path.join(tmpdir, shp_files[0])
            try:
                gdf = gpd.read_file(shp_path)
                shared_state.uploaded_gdf = gdf  # <-- Store in shared_state
                status.object = f"✅ Loaded {len(gdf)} features from **{shp_files[0]}**"
                logger.info(f"✅ Loaded {len(gdf)} features from **{shp_files[0]}**")
            except Exception as e:
                status.object = f"❌ Failed to read shapefile: {e}"
                logger.error(f"❌ Failed to read shapefile: {e}")

    # Trigger when new files are uploaded
    file_input.param.watch(handle_upload, "value")

    @pn.depends(shared_state.param.uploaded_gdf, watch=True)
    def on_new_data(gdf):
        if gdf is not None:
            print(f"New GeoDataFrame with {len(gdf)} rows loaded")
            
            column_mapping_section.objects = [load_config_section(shared_state.ocw_model, "column_mapping", True)]

    return pn.Column(
        pn.pane.Markdown("## Upload and Process Road Data"),
        file_input, file_hint,
        status,
        column_mapping_section
    )
