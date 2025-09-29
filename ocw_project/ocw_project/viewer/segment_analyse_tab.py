import pandas as pd
import panel as pn
import hvplot.pandas
import holoviews as hv
from ocw_project.viewer.shared_state import shared_state
import logging

logger = logging.getLogger(__name__)

@pn.depends(shared_state.param.gdf_result)
def create_segment_analyse_tab(gdf_result: pd.DataFrame=None):
    gdf_result = gdf_result if gdf_result is not None else shared_state.gdf_result
    if gdf_result is None:
        return pn.pane.Alert("⚠️ Process first", alert_type="warning")
    
    # Reactive title
    @pn.depends(shared_state.scenario_selector.param.value,shared_state.guid_selector.param.value)
    def title_md(scenario, guid):
        return pn.pane.Markdown(f"## Segment view - scenario {scenario}, guid {guid}")
    
    # Reactive graph
    @pn.depends(shared_state.scenario_selector.param.value,shared_state.guid_selector.param.value)
    def create_graph_segment(scenario, guid):
        gdf_subset = gdf_result[(gdf_result["guid"] == guid) & (gdf_result["scenario_nm"] == scenario)].sort_values("jaar").copy()
        export_cols = ['jaar','globaal_index', 'visueel_index', 'structureel_index', 'cost', 
                      'verharding', 'maatregel', 'functie', 'straat', 'onderhouds_type', 
                      'scenario_nm']
        gdf_subset = gdf_subset[export_cols]

        if gdf_subset.empty:
            logger.warning("⚠️ No data available for selected Guid and Scenario")
            return pn.pane.Alert("⚠️ No data available for selected Guid and Scenario", alert_type="warning")

        # Create plots
        global_plot = gdf_subset.hvplot.line(
            x='jaar', y='globaal_index', title='Global Index',
            ylim=(0, 1), grid=True, width=400, height=300,
            hover_cols=['jaar', 'cost', 'verharding', 'maatregel', 'functie']
        ).opts(
            xticks=gdf_subset['jaar'].to_list(),
            xrotation=45
        )
        
        visual_plot = gdf_subset.hvplot.line(
            x='jaar', y='visueel_index', title='Visual Index',
            ylim=(0, 1), grid=True, width=400, height=300, 
            hover_cols=['jaar', 'cost', 'verharding', 'maatregel', 'functie']
        ).opts(
            xticks=gdf_subset['jaar'].to_list(),
            xrotation=45
        )
        
        structural_plot = gdf_subset.hvplot.line(
            x='jaar', y='structureel_index', title='Structural Index',
            ylim=(0, 1), grid=True, width=400, height=300, 
            hover_cols=['jaar', 'cost', 'verharding', 'maatregel', 'functie']
        ).opts(
            xticks=gdf_subset['jaar'].to_list(),
            xrotation=45
        )

        cost_plot = gdf_subset.hvplot.bar(
            x='jaar', y='cost', title='Cost per Year', ylim=(float(0), max(gdf_subset['cost'])*1.10),
            rot=45, width=800, height=300, 
            hover_cols=['jaar', 'cost', 'verharding', 'maatregel', 'functie'],   
        ).opts(
            shared_axes=False,
            xticks=gdf_subset['jaar'].to_list()
        )

        # Filter rows that have a 'maatregel' value (non-empty and not 'None')
        annot_rows = gdf_subset[
            gdf_subset['maatregel'].notna() & 
            (gdf_subset['maatregel'] != 'None')
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

        return pn.Column(pn.Row(global_plot, visual_plot, structural_plot),
        pn.panel(cost_plot),
        pn.pane.Markdown("### Detailed Data"),
        pn.pane.DataFrame(gdf_subset, index=False))


    return pn.Column(
        pn.pane.Markdown(f"## Segment analysis"),
        title_md,
        pn.Row(shared_state.scenario_selector, shared_state.guid_selector),
        create_graph_segment
    )