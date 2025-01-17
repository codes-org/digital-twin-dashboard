import plotly.express as px
import numpy as np

from trame.ui.html import DivLayout
from trame.widgets import plotly, vuetify


OPTION = {
    "name": "heatmap",
    "label": "Heatmap",
    "icon": "mdi-chart-box",
}


class Heatmap:
    # here we can just set up the server stuff and bare minimum of what we need
    def __init__(self, server):
        self.network_file = None
        self.state = server.state
        self.ctrl = server.controller

        if OPTION not in self.state.grid_options:
            self.state.grid_options.append(OPTION)

        self.state.change("selected_heatmap_variable", self.on_cell_change)
        self.ctrl.add("on_ross_active_state_index_changed", self.on_cell_change)

        self.ctrl.add("on_ross_time_range_changed", self.on_time_change)

        self.ctrl.event_file_uploaded.add(self.on_event_file_uploaded)

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
            self.ctrl.update_heatmap = figure.update

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

    # this is called once the data is loaded, then we can finish any remaining init
    def initialize(self, network_file):
        self.network_file = network_file


    def create_heatmap(self, selected_heatmap_variable):
        # so we have our event trace which has the source and dest, send and receive times, and event type
        print("CREATE HEATMAP CALLED")
        if not hasattr(self.network_file, "network_df") or self.network_file.network_df is None:
            print("heatmap has no network_file!")
            return None

        df = self.network_file.network_df
        matrix = df.groupby(['source_lp', 'dest_lp']).size().unstack(fill_value=0)
        print(matrix)

        # TODO: make it so you can get the number of bytes sent
        self.state.last_heatmap_variable = selected_heatmap_variable

        figure = px.imshow(matrix)

        figure.update_layout(margin=dict(t=0, b=0, l=0, r=0),
                             xaxis_title="Receiving LP ID",
                             yaxis_title="Sending LP ID",
                             coloraxis_colorbar=dict(title=selected_heatmap_variable))
        return figure


    def on_cell_change(self, selected_heatmap_variable, **kwargs):
        self.ctrl.update_heatmap(self.create_heatmap(selected_heatmap_variable))


# todo make sure last_heatmap_var is set
    def on_time_change(self):
        print("updating heatmap for time")
        self.ctrl.update_heatmap(self.create_heatmap(self.state.last_heatmap_variable))


    def on_event_file_uploaded(self, event_file_uploaded, **kwargs):
        if event_file_uploaded:
            self.ctrl.update_heatmap(self.create_heatmap(self.state.last_heatmap_variable))

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