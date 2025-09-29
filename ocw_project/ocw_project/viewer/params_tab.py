import panel as pn
from ocw_project.viewer.shared_state import shared_state
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)
pn.extension()

def create_widget(key, value, dropdown=None):
    if dropdown is None:
        if isinstance(value, (float)):
            return pn.widgets.FloatInput(name=key, value=value, step=0.01)
        elif isinstance(value, int):
            return pn.widgets.FloatInput(name=key, value=value, step=0.01)
        elif isinstance(value, str):
            return pn.widgets.TextInput(name=key, value=value, placeholder="N/A")
        elif isinstance(value, bool):
            return pn.widgets.Checkbox(name=key, value=value)
        else:
            return pn.pane.Str(f"{key}: {value}")
    else:
        if hasattr(shared_state.ocw_model, key):
            information = getattr(shared_state.ocw_model.column_mapping, key)
            return pn.widgets.Select(name=f"{key} -- {information.info}", value=value, options=shared_state.uploaded_gdf.columns.to_list())
        else:
            return pn.widgets.Select(name=key, value=value, options=shared_state.uploaded_gdf.columns.to_list())

def load_config_section(model, section, dropdown=None):
    """
    Load and create UI for a specific configuration section
    """
    section_map = {
        "economie": model.economie,
        "weg_kenmerken": model.weg_kenmerken,
        "verhardingssoort_kenmerken": model.verhardingssoort_kenmerken,
        "maatregel_mapping": model.maatregel_mapping,
        "kwaliteitsindex": model.kwaliteitsindex,
        "column_mapping": model.column_mapping
    }
    
    widget_dict = {}
    obj = getattr(model, section, None)
    if obj is None or not hasattr(obj, "to_dict"):
        logger.warning(f"{section} is missing or has no to_dict()")
        return pn.Column(pn.pane.Markdown(f"### {section} not found"))

    params_dict = obj.to_dict()

    def process_attribute(prefix, obj):
        if isinstance(obj, dict):
            for key, value in obj.items():
                new_prefix = f"{prefix}.{key}" if prefix else key
                process_attribute(new_prefix, value)
        else:
            widget_dict[prefix] = create_widget(prefix, obj, dropdown)

    process_attribute("", params_dict)

    cards_layout = make_card(widget_dict)
    status = pn.pane.Markdown("")

    def save_values(event):
        try:
            new_values = {k: w.value for k, w in widget_dict.items()}
            for full_key, new_v in new_values.items():
                section_obj = section_map[section]
                set_nested_attr_from_section(section_obj, full_key, new_v)
            logging.info(f"Updated the instance '{section}': {section_obj}")

            save_buton_name = "✅ Saved instance"
            status_object_name = f"✅ Instance saved successfully: {new_values}"

            if save_default_json_checkbox.value:
                try:
                    save_path = model.app_config.update_partial_data_to_json(section)
                    save_buton_name += " & to default parameter file"
                    status_object_name += f"\n ✅ Saved successfully: {section.upper()} to {save_path}."
                except Exception as e:
                    logger.error(f"❌ Error saving to default parameter file: {str(e)}")
                    status.object = f"❌ Error saving to default parameter file: {str(e)}"
                    status.styles = {"color": "red"}

            save_btn.name = save_buton_name
            status.object = f"{status_object_name}"
            status.styles = {"color": "green"}

        except Exception as e:
            logger.error(f"❌ Error saving: {str(e)}")
            status.object = f"❌ Error saving: {str(e)}"
            status.styles = {"color": "red"}

    save_btn = pn.widgets.Button(name="Save to instance", button_type="primary")
    save_btn.on_click(save_values)
    save_default_json_checkbox = pn.widgets.Checkbox(name="Save to default parameter file")
    button_row = pn.Row(save_btn, save_default_json_checkbox, sizing_mode="stretch_width")

    return pn.Column(
        pn.pane.Markdown(f"### {section.capitalize()} Parameters"),
        button_row,
        status,
        cards_layout
    )

def make_card(widget_dict):
    """
    Group widgets by their top-level section (before the first dot)
    and create cards for each group.
    """
    grouped_widgets = defaultdict(dict)
    
    # Group widgets by their top-level section
    for full_key, widget in widget_dict.items():
        # else Kwaliteitsindex has per quality different Card
        max_min_list = ["max", "min"]
        if '.' in full_key and full_key.split('.')[-1] not in max_min_list:
            # Split on first dot only
            parts = full_key.split('.', 1)
            section_name = parts[0]
            param_name = parts[1]
            grouped_widgets[section_name][param_name] = widget
        else:
            # Parameters without dots go to a 'general' section
            grouped_widgets['general'][full_key] = widget
    
    cards = []
    
    # Create cards for each section
    for section_name, widgets in grouped_widgets.items():
        card_content = pn.Column(
            pn.pane.Markdown(f"**{section_name.capitalize()}**", margin=(0, 0, 10, 0)),
            *widgets.values()
        )
        
        card = pn.Card(
            card_content,
            title=section_name.capitalize(),
            collapsible=True,
            collapsed=False,
            margin=(5, 5, 5, 5)
        )
        cards.append(card)

        # Split sub_cards into rows
        sub_card_rows = []
        #for i in range(0, len(cards)):

    
    return pn.Row(*cards, sizing_mode="stretch_width")

def set_nested_attr_from_section(section_obj, nested_path, value):
    """
    Set nested attribute given a top-level object and a dot-separated path.
    """
    attrs = nested_path.split(".")
    obj = section_obj
    for attr in attrs[:-1]:
        obj = getattr(obj, attr)

    final_attr = attrs[-1]
    current_value = getattr(obj, final_attr)
    # If the current value is a dictionary with a "value" key, update just the value
    if isinstance(current_value, dict) and "value" in current_value:
        current_value["value"] = value
        setattr(obj, final_attr, current_value)
    else:
        # Otherwise, set the attribute directly
        setattr(obj, final_attr, value)

@pn.depends(shared_state.param.ocw_model)
def create_params_tab(model=None):
    """
    Build the full parameters UI.
    This is automatically re-run whenever shared_state.ocw_model changes.
    """
    model = model or shared_state.ocw_model
    if model is None:
        return pn.pane.Alert("⚠️ OCW model not initialized!", alert_type="warning")

    parameters = [
        "economie",
        "verhardingssoort_kenmerken",
        "weg_kenmerken",
        "maatregel_mapping",
        "kwaliteitsindex"
    ]

    tabs_list = [(p.upper(), load_config_section(model, p)) for p in parameters]

    return pn.Column(
        pn.pane.Markdown("## OCW System Parameters"),
        pn.Tabs(*tabs_list)
    )

"""param_tab = create_params_tab()
param_tab.servable()"""

#panel serve ocw_project/viewer/params_tab2.py --show