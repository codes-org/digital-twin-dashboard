import plotly.express as px

from trame.ui.html import DivLayout
from trame.widgets import html, plotly, vuetify

OPTION = {
    "name": "network_time_plot",
    "label": "Network Time Plot",
    "icon": "mdi-chart-network",
}

# This plots some PE array over network time.
# Zooming in on the graph will grab x-axis values so we can update
# other views based on the time selection
def initialize(server, model_file):
    state, ctrl = server.state, server.controller

    if OPTION not in state.grid_options:
        state.grid_options.append(OPTION)

    def create_line(selected_network_time_array, selected_network_time_type_array):
        if selected_network_time_type_array == "virtual_time":
            model_file.use_virtual_time = True
        else:
            model_file.use_virtual_time = False

        df = model_file.network_df

        # need to keep track of whether we're using real or virtual time,
        # so we can filter the data appropriately
        state.selected_network_time_type_array = selected_network_time_type_array

        kwargs = {
            "x": selected_network_time_type_array,
            "y": selected_network_time_array,
            "color": "lp_id",
            "labels": {
                selected_network_time_type_array: selected_network_time_type_array.replace("_", " ").title(),
                selected_network_time_array: selected_network_time_array.replace("_", " ").title(),
                "lp_id": "LP ID"
            },
        }
        figure = px.line(df, **kwargs)

        figure.update_layout(margin=dict(t=0, b=0, l=0, r=0))
        return figure

    @state.change("selected_network_time_array",
                  "selected_network_time_type_array")
    def on_cell_change(
        selected_network_time_array, 
        selected_network_time_type_array, 
        **kwargs
    ):
        ctrl.update_network_time_plot(create_line(selected_network_time_array, selected_network_time_type_array))

    # TODO: will want to update the event file time too
    def on_layout_change(event):
        print("time plot: on_layout_change")
        view_changed = False
        if "xaxis.range[0]" in event:
            model_file.min_time = event["xaxis.range[0]"]
            view_changed = True
        if "xaxis.range[1]" in event:
            model_file.max_time = event["xaxis.range[1]"]
            view_changed = True
        if view_changed:
            ctrl.view_update()

    def on_double_click():
        print("network time plot: on_double_click")
        model_file.reset_time_range()
        ctrl.view_update()

    with DivLayout(server, template_name="network_time_plot") as layout:
        layout.root.style = "height: 100%; width: 100%;"

        style = "; ".join(
            [
                "width: 100%",
                "height: 80%",
                "user-select: none",
            ]
        )
        figure = plotly.Figure(
            display_logo=False,
            display_mode_bar=False,
            style=style,
            relayout=(on_layout_change, "[$event]"),
            double_click=(on_double_click, ""),
        )
        ctrl.update_network_time_plot = figure.update

        with vuetify.VRow(classes="pt-2", dense=True):
            with vuetify.VCol(cols="4"):
                array_list = list(model_file.network_df.columns)
                if "lp_id" in array_list:
                    array_list.remove("lp_id")
                if "component_id" in array_list:
                    array_list.remove("component_id")
                if "real_time" in array_list:
                    array_list.remove("real_time")
                if "virtual_time" in array_list:
                    array_list.remove("virtual_time")
                arrays = [
                    dict(text=key.replace("_", " ").title(), value=key)
                    for key in array_list
                ]
                vuetify.VSelect(
                    v_model=("selected_network_time_array", "send_count"),
                    items=("available_network_time_arrays", arrays),
                    hide_details=True,
                    dense=True,
                    style="max-width: 220px",
                )

            time_list = ["virtual_time", "real_time"]
            with vuetify.VCol(cols="4"):
                vuetify.VSelect(
                    v_model=("selected_network_time_type_array", "virtual_time"),
                    items=(
                        "available_network_time_type_arrays",
                        [
                            dict(text=key.replace("_", " ").title(), value=key)
                            for key in time_list
                        ],
                    ),
                    hide_details=True,
                    dense=True,
                    style="max-width: 220px",
                )
