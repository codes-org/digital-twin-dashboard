import plotly.express as px
import numpy as np

from trame.ui.html import DivLayout
from trame.widgets import plotly, vuetify, client


OPTION = {
    "name": "heatmap",
    "label": "Heatmap",
    "icon": "mdi-chart-box",
}


def init1(server):
    if OPTION not in server.state.grid_options:
        server.state.grid_options.append(OPTION)

# heatmap of the selected variable showing connections between the  
# so when we don't preload data, this network_file is None and we can't do anything
# and it can't be updated later?
# maybe we should make this a class that can be updated as things are loaded
# this would also let us have multiple instances of a vis so that we could have multiple heatmaps
def initialize(server, network_file):
    state, ctrl = server.state, server.controller

    if OPTION not in state.grid_options:
        state.grid_options.append(OPTION)

    # lets provide the ability to color by either the count of messages or the amount of 
    # data sent. right now this is the same thing (Because all messages are the same size).
    # but this could be different in the future, so lets go ahead and support it because then it's set
    # up the same way all the other graphs are
    def create_heatmap(selected_heatmap_variable):
        # so we have our event trace which has the source and dest, send and receive times, and event type
        print("CREATE HEATMAP CALLED")
        if not hasattr(network_file, "network_df") or network_file.network_df is None:
            return None
        df = network_file.network_df
        matrix = df.groupby(['source_lp', 'dest_lp']).size().unstack(fill_value=0)
        print(matrix)

        # TODO: make it so you can get the number of bytes sent
        state.last_heatmap_variable = selected_heatmap_variable

        figure = px.imshow(matrix)

        figure.update_layout(margin=dict(t=0, b=0, l=0, r=0),
                             xaxis_title="Receiving LP ID",
                             yaxis_title="Sending LP ID",
                             coloraxis_colorbar=dict(title=selected_heatmap_variable))
        return figure

    @state.change(
        "selected_heatmap_variable"
    )
    @ctrl.add("on_ross_active_state_index_changed")
    def on_cell_change(
        selected_heatmap_variable,
        **kwargs
    ):
        ctrl.update_heatmap(create_heatmap(selected_heatmap_variable))

    @ctrl.add("on_ross_time_range_changed")
    def on_time_change():
        print("updating heatmap for time")
        ctrl.update_heatmap(create_heatmap(state.last_heatmap_variable))

    @state.change("event_file_uploaded")
    def on_event_file_uploaded(event_file_uploaded, **kwargs):
        if event_file_uploaded:
            ctrl.update_heatmap(create_heatmap(state.last_heatmap_variable))

    @state.change("update_vis") 
    def on_update_vis(update_vis, **kwargs):
        if update_vis:
            ctrl.update_heatmap(create_heatmap(state.last_heatmap_variable))

    with DivLayout(server, template_name="heatmap") as layout:
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
        ctrl.update_heatmap = figure.update

        with vuetify.VRow(classes="pt-2", dense=True):
            with vuetify.VCol(cols="5"):
                array_list = ["num_messages", "bytes_sent"]
                arrays = [
                            dict(text=key.replace("_", " ").title(), value=key)
                            for key in array_list 
                         ]
                vuetify.VSelect(
                    v_model=("selected_heatmap_variable", "num_messages"),
                    items=(
                        "available_heatmap_arrays", arrays
                    ),
                    hide_details=True,
                    dense=True,
                    style="max-width: 220px",
                )