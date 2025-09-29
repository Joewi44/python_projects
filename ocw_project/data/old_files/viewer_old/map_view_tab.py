import geopandas as gpd
import panel as pn
import folium
import branca.colormap as cm
import logging

logger = logging.getLogger(__name__)


def create_map_view_tab(scenario, year, gdf):
    if gdf is None or gdf.empty:
        return pn.pane.Alert("⚠️ First load data", alert_type="warning")

    filtered = gdf[
        (gdf['scenario_nm'] == scenario) & 
        (gdf['jaar'] == year)
    ].copy()

    if filtered.crs is not None and filtered.crs.to_string() != 'EPSG:4326':
        filtered = filtered.to_crs('EPSG:4326')

    gdf_1_clean = filtered.copy()
    for col in gdf_1_clean.select_dtypes(include=['datetime64[ns]']).columns:
        gdf_1_clean[col] = gdf_1_clean[col].astype(str)
    
    if filtered.empty:
        logger.warning("No data available for selected scenario and year")
        return pn.pane.Alert("No data available for selected scenario and year", alert_type="warning")

    
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

    # Center map
    gdf_1_clean['location'] = gdf_1_clean['geometry'].apply(lambda pt:[pt.centroid.y, pt.centroid.x])
    # centroids = gdf_1_clean.geometry.centroid
    # center = [centroids.y.mean(), centroids.x.mean()]
    lats = gdf_1_clean['location'].apply(lambda loc: loc[0])
    lons = gdf_1_clean['location'].apply(lambda loc: loc[1])
    center = [lats.mean(), lons.mean()]

    # Create Folium map
    m = folium.Map(location=center, zoom_start=13, tiles="cartodb positron")
    folium.GeoJson(gdf_1_clean, style_function=style_function,
            tooltip=folium.GeoJsonTooltip(
                fields=['straat','globaal_index', 'maatregel', 'kwaliteit'])
        ).add_to(m)
    
    # Add legend
    colormap.caption = f"{color_column} (0 = red, 0.9 = green)"
    colormap.add_to(m)

    # add marker
    gdf_marker = gdf_1_clean[gdf_1_clean['globaal_index'] <= 0.3]
    for _, row in gdf_marker.iterrows():
        folium.Marker(
            location=row.location,
            popup=(f"Globaal index: {row.globaal_index:2f} \nmaatregel: {str(row.maatregel)}"),
            icon=folium.Icon(color='red')
        ).add_to(m)


    folium_html = m._repr_html_()
    
    logger.info("create_map_view_tab created")

    return pn.Column(
        pn.pane.Markdown(f"## Spatial Distribution - Scenario {scenario}"),
        pn.pane.HTML(folium_html, height=600, width=800),
        pn.pane.Markdown(f"### Maintenance Overview"),
    )