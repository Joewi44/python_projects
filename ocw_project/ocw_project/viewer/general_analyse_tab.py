import panel as pn
from bokeh.models import NumberFormatter
import geopandas as gpd
import pandas as pd
import hvplot.pandas
from ocw_project.viewer.shared_state import shared_state
from ocw_project.config.app_config import AppConfig
import logging

logger = logging.getLogger(__name__)

@pn.depends(shared_state.param.gdf_result)
def create_general_analyse_tab(gdf_result: pd.DataFrame= None):
    gdf_result = gdf_result if gdf_result is not None else shared_state.gdf_result
    if gdf_result is None:
        return pn.pane.Alert("⚠️ Process first", alert_type="warning")
    
    unique_parcels = gdf_result.drop_duplicates(subset='guid')
    stats = gpd.GeoDataFrame({
        'Metric': ['Totaal unieke straatnamen', 'Totaal aantal wegsectieonderdelen', 'Totaaloppervlak rijweg (m²)', 
                  'Aantal scenarios berekend', 'Start en eind jaar'],
        'Value': [
            len(unique_parcels['straat'].unique()),
            len(unique_parcels),
            f"{unique_parcels['oppervlakte'].sum():.0f}",
            len(gdf_result['scenario_nm'].unique()),
            f"{int(gdf_result['jaar'].min())}-{int(gdf_result['jaar'].max())}",
        ]
    })


    export_cols = ["guid", "straat", "gemeente", "deelgemeente","wegsectie", 
                   "oppervlakte", "verharding", "functie", "visuele_index", 
                   "structurele_index", "globale_index", "bouwdate", 
                   "prioriteit", "jaar", "onderhouds_type", "maatregel"]
    df_start_year = unique_parcels[export_cols].sort_values("globale_index")
    
    def float_formatter(x):
        """Format float values with Dutch decimal comma"""
        if pd.isna(x):
            return ""
        return f"{x:.2f}".replace('.', ',')

    dataframe_start_year = pn.pane.DataFrame(
        df_start_year,
        index=False, 
        float_format=float_formatter,
        decimal=",",
        height=900,  # Explicit height
        width=1400,   # Explicit width
        sizing_mode='fixed'  # Fixed sizing
        )

    
    def make_grouped_table(group_col):
        df = unique_parcels.groupby(group_col).agg(
            avg_globaal_index=('globaal_index', 'mean'),
            avg_visueel_index=('visueel_index', 'mean'),
            avg_structureel_index=('structureel_index', 'mean'),
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
                'avg_globaal_index': round(unique_parcels['globaal_index'].mean(), 4),
                'avg_visueel_index': round(unique_parcels['visueel_index'].mean(), 4),
                'avg_structureel_index': round(unique_parcels['structureel_index'].mean(), 4),
                'sum_oppervlakte': round(unique_parcels['oppervlakte'].sum(), 0)
            }

        df = pd.concat([df, pd.DataFrame([total_row])], ignore_index=True)
        # Rename columns for display
        df = df.rename(columns={group_col: group_col.title(), 
                                'avg_globaal_index': 'Globaal', 
                                'avg_visueel_index': 'Visueel', 
                                'avg_structureel_index': 'Structureel',
                                'sum_oppervlakte': 'oppervlakte m²'})
        return pn.pane.DataFrame(df, index=False, width=700, height=400, sizing_mode='fixed')

    def make_grouped_plot(group_col):
        df = unique_parcels.groupby(group_col).agg(
            avg_globaal_index=('globaal_index', 'mean'),
            avg_visueel_index=('visueel_index', 'mean'),
            avg_structureel_index=('structureel_index', 'mean'),
            sum_oppervlakte=('oppervlakte', 'sum')
        ).reset_index()
        df[group_col] = df[group_col].astype(str)
        
        return df.hvplot.bar(
            x=group_col, y=['avg_globaal_index', 'avg_visueel_index', 'avg_structureel_index'],
            stacked=False, rot=45, width=600, height=300,
            title=f'Gemiddelde indexen per {group_col.title()}'
    )
    

    return pn.Column(
        pn.pane.Markdown("## General analyse"),
        pn.pane.DataFrame(stats, index=False),

        pn.pane.Markdown("## Grouping per type"),
        pn.Tabs(
            ('Verharding', pn.Row(
                    make_grouped_plot('verharding'), 
                    make_grouped_table('verharding'),
                    sizing_mode= 'stretch_both'
                )),
                ('Functie', pn.Row(
                    make_grouped_plot('functie'), 
                    make_grouped_table('functie')
                ))
        ),
        pn.pane.Markdown("## Data from year 0 (order_by Globale Index)"),
        pn.Row(dataframe_start_year)

    )