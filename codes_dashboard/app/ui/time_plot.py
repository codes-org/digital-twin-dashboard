import plotly.express as px

from trame.ui.html import DivLayout
from trame.widgets import html, plotly, vuetify


OPTION = {
    "name": "time_plot",
    "label": "Time Plot",
    "icon": "mdi-chart-line",
}

# this plots the some PE array over either real or virtual time.
# zooming in on the graph will grab x-axis values so we can update
# other views based on the time selection
def initialize(server, ross_file):
    state, ctrl = server.state, server.controller

    if OPTION not in state.grid_options:
        state.grid_options.append(OPTION)

    def create_line(selected_time_array, selected_time_type_array):
        df = ross_file.pe_engine_df

        # need to keep track of whether we're using real or virtual time,
        # so we can filter the data appropriately
        state.selected_time_type_array = selected_time_type_array

        kwargs = {
            "x": selected_time_type_array,
            "y": selected_time_array,
            "color": "PE_ID",
            "labels": {
                selected_time_type_array: selected_time_type_array.replace("_", " ").title(),
                selected_time_array: selected_time_array.replace("_", " ").title(),
                "PE_ID": "PE ID"
            },
        }
        figure = px.line(df, **kwargs)

        figure.update_layout(margin=dict(t=0, b=0, l=0, r=0))
        return figure

    @state.change(
        "selected_time_array",
        "selected_time_type_array"
    )
    def on_cell_change(
        selected_time_array,
        selected_time_type_array,
        **kwargs
    ):
        ctrl.update_time_plot(create_line(selected_time_array, selected_time_type_array))


    def on_layout_change(event):
        view_changed = False
        if "xaxis.range[0]" in event:
            ross_file.min_time = event["xaxis.range[0]"]
            view_changed = True
        if "xaxis.range[1]" in event:
            ross_file.max_time = event["xaxis.range[1]"]
            view_changed = True
        if view_changed:
            ctrl.view_update()


    def on_double_click():
        ross_file.reset_time_range()
        ctrl.view_update()


    with DivLayout(server, template_name="time_plot") as layout:
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
        ctrl.update_time_plot = figure.update

        with vuetify.VRow(classes="pt-2", dense=True):
            with vuetify.VCol(cols="4"):
                array_list = list(ross_file.pe_engine_df.columns)
                if "PE_ID" in array_list:
                    array_list.remove("PE_ID")
                if "real_time" in array_list:
                    array_list.remove("real_time")
                if "virtual_time" in array_list:
                    array_list.remove("virtual_time")
                arrays = [
                            dict(text=key.replace("_", " ").title(), value=key)
                            for key in array_list 
                         ]
                vuetify.VSelect(
                    v_model=("selected_time_array", "events_processed"),
                    items=(
                        "available_time_arrays", arrays
                    ),
                    hide_details=True,
                    dense=True,
                    style="max-width: 220px",
                )

            time_list = ["virtual_time", "real_time"]
            with vuetify.VCol(cols="4"):
                vuetify.VSelect(
                    v_model=("selected_time_type_array", "virtual_time"),
                    items=(
                        "available_time_type_arrays",
                        [
                            dict(text=key.replace("_", " ").title(), value=key)
                            for key in time_list 
                        ],
                    ),
                    hide_details=True,
                    dense=True,
                    style="max-width: 220px",
                )
