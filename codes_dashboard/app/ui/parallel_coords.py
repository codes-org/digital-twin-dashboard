import plotly.express as px

from trame.ui.html import DivLayout
from trame.widgets import plotly


OPTION = {
    "name": "parallel_coords",
    "label": "Parallel Coordinates", 
    "icon": "mdi-chart-line-stacked",
}


def initialize(server, ross_file):
    state, ctrl = server.state, server.controller

    if OPTION not in state.grid_options:
        state.grid_options.append(OPTION)

    def create_line():
        df = ross_file.pe_engine_df

        kwargs = {
            "color": "PE_ID",
            "dimensions": ["PE_ID", "events_processed", "events_rolled_back", "total_rollbacks", "secondary_rollbacks"],
            "labels": {"PE_ID": "PE ID", "events_processed": "Events Processed",
                       "events_rolled_back": "Events Rolled Back", "total_rollbacks": "Total Rollbacks",
                       "secondary_rollbacks": "Secondary Rollbacks"}
        }
        figure = px.parallel_coordinates(df, **kwargs)

        figure.update_layout(margin=dict(t=0, b=0, l=0, r=0))
        return figure

    #TODO: not sure how to get rid of selected_array fully without it messing up the figure. 
    # I think because it needs some kind of event to trigger this.
    # But I think I will add some other options to the toolbar in the future that
    # could trigger a state change so just leaving for now
    @state.change(
        "selected_array",
    )
    @ctrl.add("on_ross_active_state_index_changed")
    def on_cell_change(
        selected_array,
        **kwargs
    ):
        ctrl.update_parallel_coords(create_line())

    with DivLayout(server, template_name="parallel_coords") as layout:
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

