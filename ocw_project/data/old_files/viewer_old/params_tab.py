import json
import panel as pn
from ocw_project.viewer.shared_state import shared_state
from ocw_project.Maintenance_Manager import MaintenanceManager, KwaliteitsIndex
import logging

logger = logging.getLogger(__name__)

pn.extension()

def create_params_tab():
    status = pn.pane.Markdown("")

    # Load existing parameters
    params_path = shared_state.param_file_path
    model = shared_state.ocw_model

    def create_widget(key, value):
        if isinstance(value, (float)):
            return pn.widgets.FloatInput(name=key, value=value, step=0.01)
        elif isinstance(value, int):
            return pn.widgets.FloatInput(name=key, value=value, step=0.01)
        elif isinstance(value, str):
            return pn.widgets.TextInput(name=key, value=value)
        elif isinstance(value, bool):
            return pn.widgets.Checkbox(name=key, value=value)
        else:
            return pn.pane.Str(f"{key}: {value}")

    def economie():
        widget = {}
        economie_dict = model.economie.serialize_to_dict()
        for key, value in economie_dict.items():
            widget[key] = create_widget(key, value)
        
        # Add action buttons
        def save_values(event):
            try:
                new_values = {}
                for key, w in widget.items():
                    new_values[key] = w.value
                
                model.economie.load_from_file(new_values)
                model.economie.save_to_json(params_path)
                
                save_btn.name = "✅ Saved!"
                # Update status
                status.object = f"✅ Saved successfully: {new_values}"
                status.styles = {"color": "green"}
            except Exception as e:
                status.object = f"❌ Error saving: {str(e)}"
                status.styles = {"color": "red"}
        
        save_btn = pn.widgets.Button(name="Save Changes", button_type="primary")
        save_btn.on_click(save_values)
        
        button_row = pn.Row(save_btn, sizing_mode="stretch_width")
        
        return pn.Column(
            pn.pane.Markdown("### Economie Parameters"),
            *widget.values(),
            button_row,
            status
        )
    
    def road_attributes():
        widget = {}
        road_dict = model.param_config.serialize_to_dict()

        status = pn.pane.Markdown("")

        def process_attribute(prefix, obj):
            """Recursively process attributes, handling both dicts and objects"""
            if isinstance(obj, dict):
                # Handle regular dictionaries
                for key, value in obj.items():
                    new_prefix = f"{prefix}.{key}" if prefix else key
                    process_attribute(new_prefix, value)
            else:
                # Handle primitive vsalues
                widget[prefix] = create_widget(prefix, obj)
                
        process_attribute("", road_dict)

        def make_card(widget_dict, cards_per_row=3):
            grouped_widgets = {}
            for key, widget in widget_dict.items():
                group_name = key.split('.')[0]
                sub_group_name = key.split('.')[1]
                if group_name not in grouped_widgets:
                    grouped_widgets[group_name] = {}
                if sub_group_name not in grouped_widgets[group_name]:
                    grouped_widgets[group_name][sub_group_name] = {}
                grouped_widgets[group_name][sub_group_name][key] = widget

            top_level_cards = []
            for group_name, subgroups in grouped_widgets.items():
                sub_cards = []
                for sub_group_name, widgets in subgroups.items():
                    card = pn.Row(pn.Card(
                    *widgets.values(),
                    title=sub_group_name,
                    collapsed=False
                    ))
                    sub_cards.append(card)

                # Split sub_cards into rows
                sub_card_rows = []
                for i in range(0, len(sub_cards), cards_per_row):
                    row = pn.Row(*sub_cards[i:i + cards_per_row])
                    sub_card_rows.append(row)

                top_card = pn.Card(
                   *sub_card_rows,
                   title=group_name,
                   collapsed=False
                )
                top_level_cards.append(top_card)
            return top_level_cards

        cards = make_card(widget)
        def save_values(event):
            try:
                new_values = {}
                for key, w in widget.items():
                    new_values[key] = w.value

                nested = {}
                for key, value in new_values.items():
                    parts = key.split(".")
                    d = nested
                    for part in parts[:-1]:
                        d = d.setdefault(part, {})
                    d[parts[-1]] = value

                model.param_config.load_from_file(nested['ROAD_DATA'], nested['WEGKENMERKEN'])
                model.param_config.save_to_json(params_path)
                
                save_btn.name = "✅ Saved!"
                # Update status
                status.object = f"✅ Saved successfully: {nested}"
                status.styles = {"color": "green"}
            except Exception as e:
                status.object = f"❌ Error saving: {str(e)}"
                status.styles = {"color": "red"}
        
        save_btn = pn.widgets.Button(name="Save Changes", button_type="primary")
        save_btn.on_click(save_values)
        
        button_row = pn.Row(save_btn, sizing_mode="stretch_width")
        
        return pn.Column(
            pn.pane.Markdown("### Road Parameters"),
            pn.Row(*cards),
            button_row,
            status
        )

    def maatregel_mapping():
        widget = {}
        maatregel_dict = MaintenanceManager.serialize_to_dict()
        logger.debug(f"Get Values from MaintenanceManager {maatregel_dict}")

        status = pn.pane.Markdown("")

        def process_attribute(prefix, obj):
            """Recursively process attributes, handling both dicts and objects"""
            if isinstance(obj, dict):
                # Handle regular dictionaries
                for key, value in obj.items():
                    new_prefix = f"{prefix}.{key}" if prefix else key
                    process_attribute(new_prefix, value)
            else:
                # Handle primitive vsalues
                widget[prefix] = create_widget(prefix, obj)
                
        process_attribute("", maatregel_dict)

        def make_card(widget_dict):
            grouped_widgets = {}
            for key, widget in widget_dict.items():
                group_name = key.split('.')[0]
                if group_name not in grouped_widgets:
                    grouped_widgets[group_name] = {}
                grouped_widgets[group_name][key] = widget
            
            cards = []
            for card_name, card_values in grouped_widgets.items():
                card = pn.Card(
                    *card_values.values(),
                    title=card_name,
                    collapsed=False
                )
                cards.append(card)
            return cards
        
        cards = make_card(widget)


        def save_values(event):
            try:
                new_values = {}
                for key, w in widget.items():
                    new_values[key] = w.value

                nested = {}
                for key, value in new_values.items():
                    parts = key.split(".")
                    d = nested
                    for part in parts[:-1]:
                        d = d.setdefault(part, {})
                    d[parts[-1]] = value

                MaintenanceManager.load_maatregel_mapping(nested)
                MaintenanceManager.save_to_json(params_path)
                
                save_btn.name = "✅ Saved!"
                # Update status
                status.object = f"✅ Saved successfully: {nested}"
                status.styles = {"color": "green"}
            except Exception as e:
                status.object = f"❌ Error saving: {str(e)}"
                status.styles = {"color": "red"}
        
        save_btn = pn.widgets.Button(name="Save Changes", button_type="primary")
        save_btn.on_click(save_values)
        
        button_row = pn.Row(save_btn, sizing_mode="stretch_width")
        
        return pn.Column(
            pn.pane.Markdown("### Maatregel mapping"),
            pn.Row(*cards),
            button_row,
            status
        )

    def kwaliteits_index():
        widget = {}
        kwaliteit_dict = KwaliteitsIndex.serialize_to_dict()
        logger.debug(kwaliteit_dict)

        status = pn.pane.Markdown("")

        def process_attribute(prefix, obj):
            """Recursively process attributes, handling both dicts and objects"""
            if isinstance(obj, dict):
                for key, value in obj.items():
                    new_prefix = f"{prefix}.{key}" if prefix else key
                    process_attribute(new_prefix, value)
            else:
                # Handle primitive vsalues
                widget[prefix] = create_widget(prefix, obj)
                
        process_attribute("", kwaliteit_dict)

        # Convert final widgets to list
        full_widget_list = list(widget.values())

        # Split into two columns
        left_col = full_widget_list[::2]
        right_col = full_widget_list[1::2]

        def save_values(event):
            try:
                new_values = {}
                for key, w in widget.items():
                    new_values[key] = w.value

                nested = {}
                for key, value in new_values.items():
                    name, attr = key.rsplit(".", 1)
                    if name not in nested:
                        nested[name] = {}
                    nested[name][attr] = value

                KwaliteitsIndex.load_kwaliteits_index(nested)
                KwaliteitsIndex.save_to_json(params_path)
                
                save_btn.name = "✅ Saved!"
                # Update status
                status.object = f"✅ Saved successfully: {nested}"
                status.styles = {"color": "green"}
            except Exception as e:
                status.object = f"❌ Error saving: {str(e)}"
                status.styles = {"color": "red"}
        
        save_btn = pn.widgets.Button(name="Save Changes", button_type="primary")
        save_btn.on_click(save_values)
        
        button_row = pn.Row(save_btn, sizing_mode="stretch_width")
        
        return pn.Column(
            pn.pane.Markdown(f"### Kwaliteits index"),
            pn.Row(
            pn.Column(*left_col),
            pn.Column(*right_col)
            ),
            button_row,
            status
        )

    params_tab = pn.Column(
        pn.pane.Markdown("## OCW System Parameters"),
        pn.Tabs(("ECONOMIE", economie()), 
                ("WEGKENMERKEN", road_attributes()), 
                ("MAATREGEL MAPPING", maatregel_mapping),
                ("KWALITEITSINDEX", kwaliteits_index))
    )

    return params_tab


#panel serve ocw_project/viewer/params_tab.py --show