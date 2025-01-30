from trame.ui.html import DivLayout
from trame.widgets import plotly, vuetify

OPTION = {
    "name": "empty",
    "label": "Undefined content",
    "icon": "mdi-help-circle-outline",
}


def init_options(server):
    state = server.state

    if OPTION not in state.grid_options:
        state.grid_options.append(OPTION)


# Created this because it seems that I need to create some kind of initial
# plotly figure, so that way once data does get loaded, the figure will show up
# without doing this, the figure will never show up
def init_empty_vis(server, template_name):
    state, ctrl = server.state, server.controller

    with DivLayout(server, template_name=f'{template_name}_init') as layout:
        layout.root.style = "height: 100%; width: 100%;"

        style = "; ".join(
            [
                "width: 100%",
                "height: 80%",
                "user-select: none",
            ]
        )
        layout.figure = plotly.Figure(
            display_logo=False,
            display_mode_bar=False,
            style=style,
        )