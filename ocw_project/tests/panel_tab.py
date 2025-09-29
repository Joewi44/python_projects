import panel as pn
import geopandas as gpd
import pandas as pd
import holoviews as hv
from bokeh.models import NumeralTickFormatter
import hvplot.pandas
import numpy as np
import json
import folium
from folium import GeoJson
import branca.colormap as cm


# Initialize extensions
hv.extension('bokeh')
pn.extension('tabulator')

with open("ocw_project/_parameters.json", 'r') as f:
    KWALITEITSINDEX = json.load(f)['KWALITEITSINDEX']

# Load and prepare data
#merged_gdf = gpd.read_parquet('data/output_ocw/df_all_onderhoud_scenario1.parquet')
merged_gdf = gpd.read_file("data/output_ocw/df_all_onderhoud_scenario1.sqlite", layer='onderhoud')


# Reproject to WGS84 for web map display
if 'geometry' in merged_gdf.columns:
    gdf_geo = merged_gdf.copy()
    if gdf_geo.crs and gdf_geo.crs.to_string() != "EPSG:4326":
        gdf_geo = gdf_geo.to_crs("EPSG:4326")
    merged_gdf = merged_gdf.drop(columns='geometry', errors='ignore')

# Create a serializable copy of the dataframe for display purposes
def make_serializable(gdf):
    df = gdf.copy()
    # Convert geometry to WKT (Well-Known Text) format
    df['geometry_wkt'] = df['geometry'].apply(lambda x: x.wkt)
    # Drop the original geometry column
    df = df.drop(columns=['geometry'], errors='ignore')
    return df

# Create widgets
scenario_selector = pn.widgets.Select(
    name="Scenario", 
    options=sorted(merged_gdf["scenario_nm"].unique()),
    value=merged_gdf["scenario_nm"].unique()[0]
)

guid_selector = pn.widgets.Select(
    name="Guid", 
    options=sorted(merged_gdf["guid"].unique().tolist()),
    value=sorted(merged_gdf["guid"].unique().tolist())[0]  # Default to "ALL"
)

year_slider = pn.widgets.IntSlider(
    name="Year", 
    start=int(merged_gdf['jaar'].min()), 
    end=int(merged_gdf['jaar'].max()),
    value=int(merged_gdf['jaar'].min())
)

# General Info Tab
def create_general_info(gdf):
    unique_parcels = gdf.drop_duplicates(subset='guid')
    stats = pd.DataFrame({
        'Metric': ['Totaal aantal wegen', 'Totaal aantal segmenten', 'Totaaloppervlak rijweg: (m²)', 
                  'Aantal scenarios berekend', 'Van jaar tot'],
        'Value': [
            len(unique_parcels['straat'].unique()),
            len(unique_parcels),
            f"{unique_parcels['oppervlakte'].sum():.0f}",
            len(gdf['scenario_nm'].unique()),
            f"{int(gdf['jaar'].min())}-{int(gdf['jaar'].max())}",
        ]
    })

    def make_grouped_table(group_col):
        df = unique_parcels.groupby(group_col).agg(
            avg_globaal_index=('start_globaal_index', 'mean'),
            avg_visueel_index=('start_visueel_index', 'mean'),
            avg_structureel_index=('start_structureel_index', 'mean'),
            sum_oppervlakte=('oppervlakte', 'sum')
        ).reset_index()
        df[group_col] = df[group_col].astype(str)
        # Round the numeric columns
        df['avg_globaal_index'] = round(df['avg_globaal_index'],4)
        df['avg_visueel_index'] = round(df['avg_visueel_index'],4)
        df['avg_structureel_index'] = round(df['avg_structureel_index'],4)
        df['sum_oppervlakte'] = round(df['sum_oppervlakte'],0)
        # Create the totals/summary row
        total_row = {
                group_col: 'Totaal',
                'avg_globaal_index': round(unique_parcels['start_globaal_index'].mean(), 4),
                'avg_visueel_index': round(unique_parcels['start_visueel_index'].mean(), 4),
                'avg_structureel_index': round(unique_parcels['start_structureel_index'].mean(), 4),
                'sum_oppervlakte': round(unique_parcels['oppervlakte'].sum(), 0)
            }

        df = pd.concat([df, pd.DataFrame([total_row])], ignore_index=True)
        # Rename columns for display
        df = df.rename(columns={group_col: group_col.title(), 
                                'avg_globaal_index': 'Globaal', 
                                'avg_visueel_index': 'Visueel', 
                                'avg_structureel_index': 'Structureel',
                                'sum_oppervlakte': 'oppervlakte m²'})
        return pn.widgets.Tabulator(df, show_index=False)

    def make_grouped_plot(group_col):
        df = unique_parcels.groupby(group_col).agg(
            avg_globaal_index=('start_globaal_index', 'mean'),
            avg_visueel_index=('start_visueel_index', 'mean'),
            avg_structureel_index=('start_structureel_index', 'mean'),
            sum_oppervlakte=('oppervlakte', 'sum')
        ).reset_index()
        df[group_col] = df[group_col].astype(str)
        return df.hvplot.bar(
            x=group_col, y=['avg_globaal_index', 'avg_visueel_index', 'avg_structureel_index'],
            stacked=False, rot=45, width=700, height=400,
            title=f'Gemiddelde indexen per {group_col.title()}'
    )
    
    
    return pn.Column(
        pn.pane.Markdown(f"## {gdf.gemeente.unique()[0]} Dataset Overview"),
        pn.widgets.Tabulator(stats, show_index=False),

        pn.pane.Markdown("## Groeperingen per type"),
        pn.Tabs(
            ("Verharding", pn.Column(
                make_grouped_plot('verharding'),
                make_grouped_table('verharding')
            )),
            ("Functie", pn.Column(
                make_grouped_plot('functie'),
                make_grouped_table('functie')
            )),
        ),

        pn.pane.Markdown("## TOP 20 slechtste wegen"),
        pn.widgets.Tabulator(unique_parcels.drop(columns=['geometry', 'jaar', 'scenario_nm'], errors='ignore')
                             .sort_values(by="start_globaal_index")
                             .head(20), 
                             page_size=20)
    )

# Scenario Analysis Tab
@pn.depends(scenario_selector.param.value, guid_selector.param.value)
def create_scenario_analysis(scenario, guid):
    subset = merged_gdf[
            (merged_gdf["guid"] == guid) & 
            (merged_gdf['scenario_nm'] == scenario)
        ].sort_values("jaar").copy()
    subset1 = subset[['jaar','globaal_index', 'visueel_index', 'structureel_index', 'cost', 
                      'verharding', 'maatregel', 'functie', 'straat', 'onderhouds_type', 
                      'scenario_nm']].copy()
    subset1['cost'] = round(subset1['cost'], 2)
        
    if subset1.empty:
        return pn.pane.Alert("⚠️ No data available for selected Guid and Scenario", alert_type="warning")

    # Create plots
    global_plot = subset1.hvplot.line(
        x='jaar', y='globaal_index', title='Global Index',
        ylim=(0, 1), grid=True, width=400, height=300,
        hover_cols=['jaar', 'cost', 'verharding', 'maatregel', 'functie']
    ).opts(
        xticks=subset1['jaar'].to_list(),
        xrotation=45
    )
    
    visual_plot = subset1.hvplot.line(
        x='jaar', y='visueel_index', title='Visual Index',
        ylim=(0, 1), grid=True, width=400, height=300, 
        hover_cols=['jaar', 'cost', 'verharding', 'maatregel', 'functie']
    ).opts(
        xticks=subset1['jaar'].to_list(),
        xrotation=45
    )
    
    structural_plot = subset1.hvplot.line(
        x='jaar', y='structureel_index', title='Structural Index',
        ylim=(0, 1), grid=True, width=400, height=300, 
        hover_cols=['jaar', 'cost', 'verharding', 'maatregel', 'functie']
    ).opts(
        xticks=subset1['jaar'].to_list(),
        xrotation=45
    )

    cost_plot = subset1.hvplot.bar(
        x='jaar', y='cost', title='Cost per Year', ylim=(float(0), max(subset1['cost'])*1.10),
        rot=45, width=800, height=300, 
        hover_cols=['jaar', 'cost', 'verharding', 'maatregel', 'functie'],   
    ).opts(
        shared_axes=False,
        xticks=subset1['jaar'].to_list()
    )

    # Filter rows that have a 'maatregel' value (non-empty and not 'None')
    annot_rows = subset1[
        subset1['maatregel'].notna() & 
        (subset1['maatregel'] != 'None')
    ]

    # Create hv.Text objects for each row
    texts = hv.Overlay([
        hv.Text(x=row['jaar'], y=0, text=row['maatregel']).opts(
            angle=90,
            text_align='left',
            text_color='black',
            text_font_size='8pt'
        ).opts(
            shared_axes=False
        )
        for _, row in annot_rows.iterrows()
    ])

    cost_plot = cost_plot * texts
    cost_plot = cost_plot.opts(shared_axes=False)

    return pn.Column(
        pn.pane.Markdown(f"## Analysis for Guid {guid} - {subset1.straat.unique()[0]} - {subset1.verharding.unique()[0]} - {subset1.functie.unique()[0]} (Scenario {scenario})"),
        pn.Row(global_plot, visual_plot, structural_plot),
        pn.panel(cost_plot),
        pn.pane.Markdown("### Detailed Data"),
        pn.widgets.Tabulator(subset1, page_size=5)
    )

# Globaal scenario Analysis Tab
@pn.depends(scenario_selector.param.value)
def create_global_scenario_analysis(scenario):
    subset = merged_gdf[merged_gdf["scenario_nm"] == scenario]
    subset1 = subset.groupby('jaar').agg({
            'globaal_index': 'mean',
            'cost': 'sum'
        }).reset_index()
    # Format the globaal_index values for display
    subset1['globaal_index_label'] = subset1['globaal_index'].apply(lambda x: f"{x:.2f}")

    # for bar plot with maatregel
    subset2 = subset.groupby(['jaar', 'maatregel']).agg({
            'cost': 'sum'
        }).reset_index()
    subset2['jaar_str'] = subset2['jaar'].astype(str)

    # Count occurrences per category per year
    df_counts = subset.groupby(['jaar', 'kwaliteit']).size().unstack().fillna(0)

    if subset1.empty:
        return pn.pane.Alert("⚠️ No data available for selected Scenario", alert_type="warning")

    # Create plots
    global_plot = subset1.hvplot.line(
        x='jaar', y='globaal_index', title=f'Globale Index per jaar - (scenario {scenario})',
        ylim=(0, 1), grid=True, width=900, height=600, hover=False
            ).opts(
                xticks=subset1['jaar'].unique(),
                yticks=np.linspace(0,1,11)
            )

    intervention_markers = subset1.hvplot.scatter(
    x='jaar', y='globaal_index', color='blue', size=1000,
    hover_cols=['jaar', 'globaal_index', 'cost'],
    marker='dot', legend=False
            ).opts(
                hover_tooltips = [
                    ("jaar", "@jaar"),
                    ("globaal_index", "@globaal_index{0.2f}"),
                    ("cost", "€@cost{0.0a}"),
                ]
            )
    # Add labels above the dots
    labels = subset1.hvplot.labels(
        x='jaar',
        y='globaal_index',
        text='globaal_index_label',
        text_font_size='8pt',
        text_align='center',
        text_baseline='bottom'
            ).opts(text_color='black', yoffset=0.02)

    cost_plot = subset1.hvplot.bar(
        x='jaar', y='cost', title='Kost per jaar',
        rot=45, width=900, height=300
            ).opts(
                xaxis='bottom',
                xticks=subset1['jaar'].unique(),
                yformatter=NumeralTickFormatter(format='0a'),
                ylabel='Kost €',
                hover_tooltips = [
                    ("jaar", "@jaar"),
                    ("cost", "€@cost{0.0a}"),
                ]
            )

    cost_plot_maatregel = subset2.hvplot.bar(
        x='jaar_str', y='cost', by='maatregel', rot=45, width=900, height=500, stacked=True,
        title=f'Kosten per maatregel per jaar - (scenario {scenario})',
    ).opts(
        shared_axes=False,
        yformatter=NumeralTickFormatter(format='0a'),
        legend_position='bottom',
        legend_cols=2,  # Adjust based on number of items
        legend_opts={'label_text_font_size': '8pt'},
        hover_tooltips = [
                    ("jaar_str", "@jaar_str"),
                    ("maatregel", "@maatregel"),
                    ("cost", "€@cost{0.0a}"),
                ]
    )
    
    # Define the desired order (worst to best)
    category_order = [x for x in KWALITEITSINDEX][::-1]

    # Ensure the DataFrame columns follow this order
    df_counts = df_counts[category_order]  # Reorder columns

    # Define colors in the same order (worst to best)
    colors = ["darkred", "red", "orange", "gold", "limegreen", "green"]

    # Create the color map dynamically
    color_map = dict(zip(category_order, colors))

    road_condition = df_counts.hvplot.bar(
        x='jaar',
        stacked=True,
        color=[color_map[col] for col in df_counts.columns],
        title=f'Kwaliteit van de wegen - (scenario {scenario})',
        width=900,
        height=500
    ).opts(
        shared_axes=False,
        legend_position='bottom',
        legend_cols=1,
    )

    return pn.Column(
        pn.pane.Markdown(f"## Globale analysis for {subset['gemeente'].unique()[0]} - (Scenario {scenario})"),
        pn.Row(global_plot * intervention_markers * labels),
        cost_plot,
        pn.Row(cost_plot_maatregel),
        road_condition
    )

# Map Visualization Tab
@pn.depends(scenario_selector.param.value, year_slider.param.value)
def create_map_view(scenario, year):
    filtered = gdf_geo[
        (gdf_geo['scenario_nm'] == scenario) & 
        (gdf_geo['jaar'] == year)
    ].copy()
    gdf_1_clean = filtered.copy()
    for col in gdf_1_clean.select_dtypes(include=['datetime64[ns]']).columns:
        gdf_1_clean[col] = gdf_1_clean[col].astype(str)
    
    if filtered.empty:
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
    GeoJson(gdf_1_clean, style_function=style_function,
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
    
    

    return pn.Column(
        pn.pane.Markdown(f"## Spatial Distribution - Scenario {scenario}"),
        pn.Row(
            pn.Column(scenario_selector, year_slider)
        ),
        pn.pane.HTML(folium_html, height=600, width=800),
        pn.pane.Markdown(f"### Maintenance Overview"),
    )

# Create dashboard
dashboard = pn.Tabs(
    ("Overview", create_general_info(merged_gdf)),
    ("Scenario Analysis", pn.Column(guid_selector, scenario_selector, create_scenario_analysis)),
    ("Globale Analys", pn.Column(scenario_selector, create_global_scenario_analysis)),
    ("Map View", create_map_view),
    ("Data Explorer", pn.widgets.Tabulator(merged_gdf, page_size=50))
)

# Serve the dashboard
dashboard.servable(title=f"{merged_gdf.gemeente.unique()[0]} Scenario Analysis")

    #
    # panel serve ocw_project/viewer/panel_tab.py --show
    # test
    