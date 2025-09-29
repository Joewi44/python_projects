import panel as pn
import pandas as pd
import geopandas as gpd
from io import BytesIO
import zipfile
import tempfile
import os
from ocw_project.viewer_old.shared_state import shared_state
import logging

logger = logging.getLogger(__name__)

pn.extension('tabulator')

def create_upload_tab():
    # File upload widget
    spinner = pn.indicators.LoadingSpinner(value=False, width=20, height=20, color="primary")
    loading_text = pn.pane.Markdown("", styles={"color": "blue", "font-size": "12px"})
    
    file_upload = pn.widgets.FileInput(accept='.zip', multiple=False)
    file_hint = pn.pane.Markdown(
        "🗂️ **Please upload a `.zip` file containing the following shapefile components:**\n"
        "- `.shp`\n"
        "- `.shx`\n"
        "- `.dbf`\n"
        "- (optionally: `.prj`)",
        styles={"font-size": "12px", "color": "gray"}
        )

    # Scenario controls
    scenario_selector = pn.widgets.MultiChoice(
                name="Scenarios", 
                options=list(range(1, 19))
                )

    years_slider = pn.widgets.IntSlider(name="Jaren", start=5, end=40, value=20)

    # Create DataFrames for mappings
    road_function_df = pd.DataFrame({
        'Original': ['ERF', 'VW', 'DGW'],
        'Mapped': ['erf', 'verzamel', 'doorgang']
        })

    pavement_type_df = pd.DataFrame({
        'Original': ['BS', 'CS', 'BP'],
        'Mapped': ['asfalt', 'beton', 'elementen']
        })

    # Create editable DataFrame widgets
    road_function_editor = pn.widgets.Tabulator(road_function_df, name='Road Function Mapping')
    pavement_type_editor = pn.widgets.Tabulator(pavement_type_df, name='Pavement Type Mapping')

    output_pane = pn.Column()

    # Expected internal column names
    expected_fields = [
        'guid', 'straat', 'gemeente', 'wegsectie', 'oppervlakte',
        'verharding', 'functie', 'visuele_index', 'visuele_index_date',
        'structurele_index', 'structurele_index_date',
        'globale_index', 'globale_index_date', 'prioriteit', 'geometry'
    ]

    # Dropdown selectors shown after shapefile load
    column_mapping_selectors = {f: pn.widgets.Select(name=f, options=[]) for f in expected_fields}
    column_mapping_panel = pn.Column(pn.pane.Markdown("### Koppel shapefile-kolommen aan verwachte velden"), *column_mapping_selectors.values())

    def read_zipped_shapefile(file_bytes):
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = os.path.join(tmpdir, "uploaded.zip")
            with open(zip_path, "wb") as f:
                f.write(file_bytes)
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(tmpdir)
            for fname in os.listdir(tmpdir):
                if fname.endswith(".shp"):
                    return gpd.read_file(os.path.join(tmpdir, fname))
        
        output_pane.objects = [pn.pane.Alert("No .shp file found in the uploaded ZIP", alert_type="warning")]
        logger.warning("No .shp file found in ZIP")
        raise ValueError("No .shp file found in zip")
    
    def generate_zip(gdf_export):
        with tempfile.TemporaryDirectory() as tmpdir:
            shp_path = os.path.join(tmpdir, "output.shp")
            gdf_export.to_file(shp_path)

            # Create zip of all Shapefile components
            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, "w") as zip_file:
                for filename in os.listdir(tmpdir):
                    file_path = os.path.join(tmpdir, filename)
                    zip_file.write(file_path, arcname=filename)

            zip_buffer.seek(0)
            return zip_buffer

    def process_data(event):
        spinner.value = True
        loading_text.object = "🔄 Loading..."
        try:
            if not file_upload.value:
                output_pane.objects = [pn.pane.Alert("Please upload a file first", alert_type="warning")]
                logger.warning("No (ZIP-)File loaded")
                return
            if not scenario_selector.value:
                output_pane.objects = [pn.pane.Alert("Please select a scenario", alert_type="warning")]
                logger.warning("No scenario selected")
                return


            # Load uploaded file
            gdf = read_zipped_shapefile(file_upload.value)

            # Populate column mapping dropdowns
            col_options = list(gdf.columns)
            for key, selector in column_mapping_selectors.items():
                selector.options = col_options
                if key in col_options:
                    selector.value = key  # auto-assign if names match
                elif key == 'geometry':
                    selector.value = 'geometry'
                else:
                    selector.value = None

            type_dict = {
                'G_date': 'datetime64[ns]',
                'S_date': 'datetime64[ns]',
                'DATUM': 'datetime64[ns]'
            }
            gdf = gdf.astype(type_dict)
            
            # Convert mappings from editors to dicts
            road_map = dict(zip(road_function_editor.value['Original'], 
                            road_function_editor.value['Mapped']))
            pavement_map = dict(zip(pavement_type_editor.value['Original'], 
                                pavement_type_editor.value['Mapped']))
            
            # Apply mappings
            gdf['functie'] = gdf['Wegfunctie'].map(road_map)
            gdf['verharding'] = gdf['Verharding'].map(pavement_map)

            # Process with OCWSystematiek
            model = shared_state.ocw_model

            # Build user-defined column mapping
            column_mapping = {field: sel.value for field, sel in column_mapping_selectors.items()}
            if any(v is None for v in column_mapping.values()):
                output_pane.objects = [pn.pane.Alert("Niet alle velden zijn gekoppeld. Vul alle dropdowns in.", alert_type="warning")]
                return

            ocw = model.segmenteren_wegennet(df=gdf, column_mapping=column_mapping)
            for scenario in scenario_selector.value:
                model.bereken_index_alle_segmenten(
                    scenario=scenario,
                    segmenten=ocw,
                    jaren=years_slider.value
                )
            
            # Get results
            gdf_export = model.get_all_df_onderhoud(segmenten=ocw, geometry=True)
            shared_state.gdf_export = gdf_export
            logger.info(f"Dataframe {gdf_export.shape} ready for download")

            # MAKE READY FOR DOWNLOAD & Enable download button with new callback
            zip_io = generate_zip(shared_state.gdf_export)
            shapefile_download.file = zip_io
            shapefile_download.disabled = False

            output_pane.objects = [
                    pn.widgets.Tabulator(
                        gdf_export.head(20).drop(columns='geometry'), 
                        height=300, 
                        sizing_mode="stretch_width"
                    )
                ]
        
        except Exception as e:
            logger.error(f"Error process_data: {str(e)}")
            output_pane.objects = [pn.pane.Alert(f"Error: {str(e)}", alert_type="danger")]
        
        finally:
            spinner.value = False
            loading_text.object = ""

    # FileDownload widget for exporting the shapefile
    shapefile_download = pn.widgets.FileDownload(
        label="Download Shapefile",
        button_type="success",
        filename="export.zip",
        disabled=True,
        file=None
    )

    process_btn = pn.widgets.Button(name="Process Data", button_type="primary")
    process_btn_hint = pn.pane.Markdown(
    "⚠️ **Please make sure to update and save the parameters before processing the data.**",
    styles={"color": "orange", "font-size": "13px"}
    )
    process_btn.on_click(process_data)

    upload_tab = pn.Column(
            pn.pane.Markdown("## Upload and Process Road Data"),
            pn.Row(file_hint),
            pn.Row(file_upload),
            pn.Row(scenario_selector, years_slider),
            pn.pane.Markdown("## Kolomkoppeling"),
            column_mapping_panel,
            pn.Row(process_btn_hint),
            pn.Row(process_btn,spinner, loading_text),
            shapefile_download,
            pn.pane.Markdown("## First 20 lines of processed data"),
            pn.Row(output_pane)
        )
    return upload_tab

                
# if __name__ == '__main__':
#     upload_tab = create_upload_tab()
#     upload_tab.servable()

#panel serve ocw_project/viewer/upload_tab.py --show