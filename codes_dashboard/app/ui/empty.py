from trame.ui.html import DivLayout
from trame.widgets import plotly, vuetify

OPTION = {
    "name": "empty",
    "label": "Undefined content",
    "icon": "mdi-help-circle-outline",
}


def initialize(server):
    state = server.state

    if OPTION not in state.grid_options:
        state.grid_options.append(OPTION)

    with DivLayout(server, template_name="empty") as layout:
        layout.root.add_child("Some empty content...")
    
def create_empty_vis(server, template_name):
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

        layout.options = vuetify.VRow(classes="pt-2", dense=True)
        