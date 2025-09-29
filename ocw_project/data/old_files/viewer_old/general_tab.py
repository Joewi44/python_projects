import panel as pn
import pandas as pd
import hvplot.pandas
from ocw_project.viewer_old.shared_state import shared_state
import logging

logger = logging.getLogger(__name__)


@pn.depends(shared_state.param.gdf_export)
def create_general_info_tab(gdf):
    gdf = shared_state.gdf_export

    if gdf is None or gdf.empty:
        return pn.pane.Alert("⚠️ First load data", alert_type="warning")
    
    unique_parcels = gdf.drop_duplicates(subset='guid')
    stats = pd.DataFrame({
        'Metric': ['Totaal unieke straatnamen', 'Totaal aantal wegsectieonderdelen', 'Totaaloppervlak rijweg (m²)', 
                  'Aantal scenarios berekend', 'Start en eind jaar'],
        'Value': [
            len(unique_parcels['straat'].unique()),
            len(unique_parcels),
            f"{unique_parcels['oppervlakte'].sum():.0f}",
            len(gdf['scenario_nm'].unique()),
            f"{int(gdf['jaar'].min())}-{int(gdf['jaar'].max())}",
        ]
    })
    logger.info("create_general_info_tab created without errors")

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
