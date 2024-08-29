import plotly.express as px

from trame.ui.html import DivLayout
from trame.widgets import plotly, vuetify


OPTION = {
    "name": "scatter_plot",
    "label": "Scatter Plot",
    "icon": "mdi-chart-scatter-plot",
}


# scatter plot of two variables
def initialize(server, ross_file):
    state, ctrl = server.state, server.controller

    if OPTION not in state.grid_options:
        state.grid_options.append(OPTION)

    def create_line(selected_scatter_array_x, selected_scatter_array_y):
        df = ross_file.pe_engine_df

        # not sure if this is the best way to handle this.
        # this is so we can call create_line, when the time changes, but
        # we don't have the array selection. we save it in the state so 
        # we'll be able to access the values later when we call this
        # on time change.
        state.last_scatter_array_x = selected_scatter_array_x
        state.last_scatter_array_y = selected_scatter_array_y

        kwargs = {
            "x": selected_scatter_array_x,
            "y": selected_scatter_array_y,
            "color": "PE_ID",
            "labels": {
                selected_scatter_array_x: selected_scatter_array_x.replace("_", " ").title(),
                selected_scatter_array_y: selected_scatter_array_y.replace("_", " ").title(),
                "PE_ID": "PE ID"
            },
        }
        figure = px.scatter(df, **kwargs)

        figure.update_layout(margin=dict(t=0, b=0, l=0, r=0))
        return figure

    @state.change(
        "selected_scatter_array_x",
        "selected_scatter_array_y"
    )
    @ctrl.add("on_ross_active_state_index_changed")
    def on_cell_change(
        selected_scatter_array_x,
        selected_scatter_array_y,
        **kwargs
    ):
        ctrl.update_scatter_plot(create_line(selected_scatter_array_x, selected_scatter_array_y))

    @ctrl.add("on_ross_time_range_changed")
    def on_time_change():
        print("updating scatter plot for time")
        ctrl.update_scatter_plot(create_line(state.last_scatter_array_x, state.last_scatter_array_y))

    with DivLayout(server, template_name="scatter_plot") as layout:
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
            # selected=(on_event, "["selected", utils.safe($event)]"),
            # hover=(on_event, "["hover", utils.safe($event)]"),
            # selecting=(on_event, "["selecting", $event]"),
            # unhover=(on_event, "["unhover", $event]"),
        )
        ctrl.update_scatter_plot = figure.update

        with vuetify.VRow(classes="pt-2", dense=True):
            with vuetify.VCol(cols="5"):
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
                    v_model=("selected_scatter_array_x", "events_processed"),
                    items=(
                        "available_scatter_arrays", arrays
                    ),
                    hide_details=True,
                    dense=True,
                    style="max-width: 220px",
                )

            with vuetify.VCol(cols="5"):
                vuetify.VSelect(
                    v_model=("selected_scatter_array_y", "events_rolled_back"),
                    items=(
                        "available_scatter_arrays", arrays
                    ),
                    hide_details=True,
                    dense=True,
                    style="max-width: 220px",
                )
