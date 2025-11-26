import plotly.express as px

from trame.ui.html import DivLayout
from trame.widgets import plotly

from . import empty

OPTION = {
    "name": "parallel_coords",
    "label": "Parallel Coordinates", 
    "icon": "mdi-chart-line-stacked",
}

TEMPLATE_NAME = "parallel_coords"

def init_options(server):
    if OPTION not in server.state.grid_options:
        server.state.grid_options.append(OPTION)

    empty.init_empty_vis(server, TEMPLATE_NAME)

def initialize(server, ross_file):
    state, ctrl = server.state, server.controller

    def create_line():
        print("parcoords create_line called")
        df = ross_file.pe_engine_df

        kwargs = {
            "color": "PE_ID",
            "dimensions": ["PE_ID", "events_processed", "events_rolled_back", "total_rollbacks", "secondary_rollbacks"],
            "labels": {"PE_ID": "PE ID", "events_processed": "Events Processed",
                       "events_rolled_back": "Events Rolled Back", "total_rollbacks": "Total Rollbacks",
                       "secondary_rollbacks": "Secondary Rollbacks"}
        }
        figure = px.parallel_coordinates(df, **kwargs)

        figure.update_layout(margin=dict(t=40, b=20, l=25, r=20))
        return figure

    @ctrl.add("init_parallel_coords")
    def on_cell_change():
        print("on_cell_change called")
        ctrl.update_parallel_coords(create_line())

    @ctrl.add("on_ross_time_range_changed")
    def on_time_change():
        print("updating par coords for time")
        ctrl.update_parallel_coords(create_line())

    with DivLayout(server, template_name=TEMPLATE_NAME) as layout:
        layout.root.style = "height: 100%; width: 100%;"

        style = "; ".join(
            [
                "width: 100%",
                "height: 100%",
                "user-select: none",
            ]
        )
        figure = plotly.Figure(
            display_logo=False,
            display_mode_bar=False,
            style=style,
        #    # selected=(on_event, "["selected", utils.safe($event)]"),
        #    # hover=(on_event, "["hover", utils.safe($event)]"),
        #    # selecting=(on_event, "["selecting", $event]"),
        #    # unhover=(on_event, "["unhover", $event]"),
        )
        ctrl.update_parallel_coords = figure.update

