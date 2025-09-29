import pandas as pd
import panel as pn
import hvplot.pandas
import holoviews as hv
from ocw_project.viewer_old.shared_state import shared_state
import logging

logger = logging.getLogger(__name__)

def create_scenario_tab(scenario, guid, gdf):
    if gdf is None or gdf.empty:
        return pn.pane.Alert("⚠️ First load data", alert_type="warning")

    subset = gdf[
            (gdf["guid"] == guid) & 
            (gdf['scenario_nm'] == scenario)
        ].sort_values("jaar").copy()
    subset1 = subset[['jaar','globaal_index', 'visueel_index', 'structureel_index', 'cost', 
                      'verharding', 'maatregel', 'functie', 'straat', 'onderhouds_type', 
                      'scenario_nm']].copy()
    subset1['cost'] = round(subset1['cost'], 2)
        
    if subset1.empty:
        logger.warning("⚠️ No data available for selected Guid and Scenario")
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

    logger.info("create_scenario_tab created")

    return pn.Column(
        pn.pane.Markdown(f"## Analysis for Guid {guid} - {subset1.straat.unique()[0]} - {subset1.verharding.unique()[0]} - {subset1.functie.unique()[0]} (Scenario {scenario})"),
        pn.Row(global_plot, visual_plot, structural_plot),
        pn.panel(cost_plot),
        pn.pane.Markdown("### Detailed Data"),
        pn.widgets.Tabulator(subset1, page_size=5)
    )
