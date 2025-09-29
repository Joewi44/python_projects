import panel as pn
import geopandas as gpd
import pandas as pd
from bokeh.models.widgets.tables import NumberFormatter, DateFormatter
import zipfile
import io
import os
import tempfile
from ocw_project.viewer.shared_state import shared_state
import logging
import time

logger = logging.getLogger(__name__)

@pn.depends(shared_state.param.uploaded_gdf)
def create_process_tab(uploaded_gdf:gpd.GeoDataFrame=None):
    spinner = pn.indicators.LoadingSpinner(value=False, width=20, height=20, color="primary")
    loading_text = pn.pane.Markdown("", styles={"color": "blue", "font-size": "12px"})

    uploaded_gdf = uploaded_gdf if uploaded_gdf is None else shared_state.uploaded_gdf
    if uploaded_gdf is None:
        return pn.pane.Alert("⚠️ Dataframe not loaded!", alert_type="warning")

    scenarios = [k.replace("sc_","") for k in shared_state.ocw_model.scenarios.to_dict().keys()]
    scenario_selector = pn.widgets.MultiChoice(
                name="Scenarios", 
                options=scenarios
                )

    years_slider = pn.widgets.IntSlider(name="Jaren", start=5, end=40, value=20)

    status = pn.pane.Markdown("📂 Select scenario, filters and years and press button...")

    def process_data(event):
        start = time.time()
        spinner.value = True
        loading_text.object = "🔄 Loading..."
        try:
            if not scenario_selector.value:
                logger.warning("No scenario selected")
                status.object = "⚠️ Please select a scenario"
                return

            model = shared_state.ocw_model
            
            filtered_df = filtering_tabulator.current_view
            filtered_df = filtered_df.merge(uploaded_gdf[[mapped['guid'], mapped['geometry']]], on=mapped['guid'], how='left')

            ocw_instances = model.segmenteren_wegennet(filtered_df)
            logger.info(f"Filter applied: {filtered_df.shape[0]} rows filtered from {uploaded_gdf.shape[0]} original")

            # CALCULATE
            for scenario in scenario_selector.value:
                model.bereken_index_alle_segmenten(
                    scenario=scenario, 
                    segmenten=ocw_instances, 
                    jaren=years_slider.value
                    )
            
            # Get results
            gdf_result = model.get_all_df_onderhoud(segmenten=ocw_instances, geometry=True)
            gdf_result_export = model.get_all_df_onderhoud(segmenten=ocw_instances, geometry=True, export_df=True)
            shared_state.gdf_result = gdf_result
            logger.info(f"Dataframe {gdf_result_export.shape} ready for download")

            # Write shapefile to a temporary folder
            tmp_dir = tempfile.mkdtemp()
            shp_path = os.path.join(tmp_dir, "export.shp")

            gdf_result_export.to_file(shp_path, driver="ESRI Shapefile")

            # Zip all shapefile components
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w") as zf:
                for ext in [".shp", ".shx", ".dbf", ".prj", ".cpg"]:
                    fpath = f"{tmp_dir}/export{ext}"
                    try:
                        zf.write(fpath, arcname=f"export{ext}")
                    except FileNotFoundError:
                        pass  # some extensions may not exist

            zip_buffer.seek(0)

            # Attach to download widget
            shapefile_download.file = zip_buffer
            shapefile_download.filename = "export.zip"
            shapefile_download.disabled = False

            # ✅ Update status
            status.object = (
                    f"✅ Completed processing\n\n"
                    f"- **Scenarios:** {len(scenario_selector.value)}\n"
                    f"- **Segments:** {filtered_df.shape[0]}\n"
                    f"- **Years:** {years_slider.value}\n"
                    f"- **Rows generated:** {gdf_result.shape[0]}\n"
                    f"- **Estimated entries:** "
                    f"{filtered_df.shape[0] * len(scenario_selector.value) * (years_slider.value + 1)}\n\n"
                    f"📥 Ready for download."
                )
            
        except Exception as e:
            logger.error(f"Error processing data: {str(e)}")
            status.object = f"❌ Error: {str(e)}"
        
        finally:
            spinner.value = False
            loading_text.object = ""
            duration = time.time() - start
            logger.info(f"✅ Processed {len(scenario_selector.value)} scenario(s) in {duration}")

    # FileDownload widget for exporting the shapefile
    shapefile_download = pn.widgets.FileDownload(
        label="Download Shapefile",
        button_type="success",
        filename="export.shp",
        disabled=True,
        file=None
        )


    mapped:dict = shared_state.ocw_model.column_mapping.to_dict()

    # Define which columns have filters and how
    show_columns = ['guid', 'straat', 'gemeente', 'deelgemeente', 
                        'wegsectie', 'oppervlakte', 'verharding', 'functie', 'prioriteit',
                        'visuele_index', 'structurele_index', 'globale_index', 
                        'bouwdate', 'visuele_index_date']
    show= [mapped.get(col) for col in show_columns if col in mapped]
    filter_columns = {
            mapped["gemeente"]: {'type': 'list', 'func': 'in', 'valuesLookup': True, 'sort': 'asc', 'multiselect': True},
            mapped["deelgemeente"]: {'type': 'list', 'func': 'in', 'valuesLookup': True, 'sort': 'asc', 'multiselect': True},
            mapped["functie"]: {'type': 'list', 'func': 'in', 'valuesLookup': True, 'sort': 'asc', 'multiselect': True},
            mapped["verharding"]: {'type': 'list', 'func': 'in', 'valuesLookup': True, 'sort': 'asc', 'multiselect': True},
            mapped["prioriteit"]: {'type': 'list', 'func': 'in', 'valuesLookup': True, 'sort': 'asc', 'multiselect': True},
        }
    float_limit = ['oppervlakte', 'visuele_index', 'structurele_index', 'globale_index']
    bokeh_formatters = {
        mapped[col]: NumberFormatter(format='0.00') for col in float_limit
        }

    filtering_tabulator = pn.widgets.Tabulator(
                                        uploaded_gdf[show],
                                        show_index=False,
                                        header_filters=filter_columns,
                                        pagination='local', 
                                        layout='fit_data_stretch', 
                                        page_size=100, 
                                        formatters=bokeh_formatters,
                                        disabled=True
                                    )
    

    process_button = pn.widgets.Button(name="Process (filtered) data", button_type="primary")
    process_button.on_click(process_data)

    return pn.Column(
        pn.pane.Markdown("## Process Road Data"),
        pn.Row(
            scenario_selector,
            years_slider
            ),
        status,
        pn.Row(
            pn.Row(process_button,spinner, loading_text, sizing_mode="stretch_width")
            ),
        shapefile_download,
        filtering_tabulator
    )