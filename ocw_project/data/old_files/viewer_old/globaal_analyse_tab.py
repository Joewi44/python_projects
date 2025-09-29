import pandas as pd
import panel as pn
from bokeh.models import NumeralTickFormatter
import numpy as np
import json
from ocw_project.viewer_old.shared_state import shared_state
import logging

logger = logging.getLogger(__name__)

params_path = shared_state.param_file_path

try:
    if params_path.exists():
        raw_text = params_path.read_text()
        KWALITEITSINDEX = json.loads(raw_text)['KWALITEITSINDEX']
        logger.info("KWALITEITSINDEX loaded")
    else:
        logger.error(f"Json-file for KWALITEITSINDEX does not exist: {params_path}")
        KWALITEITSINDEX = {}
except Exception as e:
    logger.error(f"Error loading params: {e}")
    KWALITEITSINDEX = {}


def create_global_scenario_analysis_tab(scenario, gdf):
    if gdf is None or gdf.empty:
        return pn.pane.Alert("⚠️ First load data", alert_type="warning")

    subset = gdf[gdf["scenario_nm"] == scenario]
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
        logger.error(f"⚠️ No data available for selected Scenario {scenario}")
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
        x='jaar', y='cost', title='Kosten per jaar',
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
        title=f'Kost per maatregel per jaar - (scenario {scenario})',
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