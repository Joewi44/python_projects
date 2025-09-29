import geopandas as gpd
import panel as pn
import folium
import branca.colormap as cm
from ocw_project.viewer.shared_state import shared_state
import logging

logger = logging.getLogger(__name__)

@pn.depends(shared_state.param.gdf_result)
def create_map_view_tab(gdf_result):
    gdf_result = gdf_result if gdf_result is not None else shared_state.gdf_result
    if gdf_result is None:
        return pn.pane.Alert("⚠️ Process first", alert_type="warning")
    
    # Reactive title
    @pn.depends(shared_state.scenario_selector.param.value,shared_state.year_selector.param.value)
    def title_md(scenario, year):
        return pn.pane.Markdown(f"## Map view - Scenario {scenario}, Year {year}")

    # Cache filtered & processed GeoDataFrame
    @pn.depends(shared_state.scenario_selector.param.value,shared_state.year_selector.param.value)
    def filtered_gdf(scenario, year):
        filtered = gdf_result[
            (gdf_result['scenario_nm'] == scenario) & 
            (gdf_result['jaar'] == year)
        ].copy()

        if filtered.empty:
            return None

        # Ensure EPSG:4326
        if filtered.crs is not None and filtered.crs.to_string() != 'EPSG:4326':
            filtered = filtered.to_crs('EPSG:4326')

        # Format datetime columns
        for col in filtered.select_dtypes(include=['datetime64[ns]']).columns:
            filtered[col] = filtered[col].astype(str)

        # Precompute centroids
        filtered['location'] = filtered['geometry'].apply(lambda pt: [pt.centroid.y, pt.centroid.x])

        return filtered
    
    # Generate Folium map from cached filtered_gdf
    @pn.depends(shared_state.scenario_selector.param.value,
            shared_state.year_selector.param.value)
    def update_map(scenario, year):
        filtered = filtered_gdf(scenario, year)
        if filtered is None or filtered.empty:
            return pn.pane.Alert("No data available for selected scenario and year", alert_type="warning")

        # Center map
        lats = filtered['location'].apply(lambda loc: loc[0])
        lons = filtered['location'].apply(lambda loc: loc[1])
        center = [lats.mean(), lons.mean()]
        
        # Color map
        colormap = cm.StepColormap(colors=['red', 'yellow', 'green'],
                                index=[0,0.3,0.75,0.9],
                                vmin=0,
                                vmax=0.9)
        
        # Column used for color
        color_column = 'globaal_index'
        def style_function(feature):
            value = feature['properties'][color_column]
            return {
                'fillColor': colormap(value),
                'color': 'black',
                'weight': 0.5,
                'fillOpacity': 0.7,
            }

        # Create Folium map
        m = folium.Map(location=center, zoom_start=13, tiles="cartodb positron")
        folium.GeoJson(filtered, style_function=style_function,
                tooltip=folium.GeoJsonTooltip(
                    fields=['straat','globaal_index', 'maatregel', 'kwaliteit'])
            ).add_to(m)
        
        
        # Add legend
        colormap.caption = f"{color_column} (0 = red, 0.9 = green)"
        colormap.add_to(m)

        # add marker
        gdf_marker = filtered[filtered['globaal_index'] <= 0.3]
        for _, row in gdf_marker.iterrows():
            folium.Marker(
                location=row.location,
                popup=(f"Globaal index: {row.globaal_index:2f} \nmaatregel: {str(row.maatregel)}"),
                icon=folium.Icon(color='red')
            ).add_to(m)

        return pn.pane.HTML(m._repr_html_(), height=600, width=800)

    return pn.Column(
        title_md,
        pn.Row(shared_state.scenario_selector, shared_state.year_selector),
        update_map
    )