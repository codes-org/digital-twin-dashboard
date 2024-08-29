import os

from trame.app import get_server, dev
from trame.decorators import TrameApp, change, controller
from trame.ui.vuetify import SinglePageLayout
from trame.widgets import client, grid, html, vuetify

from .ui import (
    empty, 
    parallel_coords, 
    time_plot,
    scatter_plot
)
from .core.ross_binary_file import ROSSFile

# The user can set this via an environment variable
DATA_PATH_ENV_NAME = "ROSS_DATA_PATH"

DEFAULT_NB_ROWS = 8

def get_next_y_from_layout(layout):
    next_y = 0
    for item in layout:
        y, h = item.get("y", 0), item.get("h", 1)
        if y + h > next_y:
            next_y = y + h
    return next_y

@TrameApp()
class CodesDashboard:
    def __init__(self, server_or_name=None) -> None:
        self.server = get_server(server_or_name, client_type="vue2")

        self._args = self._app_settings()
        self._ross_file = ROSSFile(self._args.data_file)
        self._ross_file.read()

        if self.server.hot_reload:
            self.server.controller.on_server_reload.add(self._build_ui)
        self.ui = self._build_ui()

        # set state variables
        self.state.trame__title = "CODES Dashboard"

    def _app_settings(self):
        data_kwargs = {
            "help": "Data file to load",
            "dest": "data_file",
        }

        default = os.getenv(DATA_PATH_ENV_NAME)
        if default is not None:
            # If the environment variable has been provided, use that for the default
            data_kwargs["default"] = default
        else:
            # Otherwise, the CLI argument is required
            data_kwargs["required"] = True

        self.server.cli.add_argument("--data", **data_kwargs)
        args, _ = self.server.cli.parse_known_args()
        return args


    @property
    def ctrl(self):
        return self.server.controller
    
    @property
    def state(self):
        return self.server.state


    @controller.set("view_update")
    def update_views_time(self):
        print("update views for time change")
        self.ctrl.on_ross_time_range_changed()


    def _build_ui(self, *args, **kwargs):
        self.state.setdefault("grid_item_dirty_key", 0)

        # Initialize all visualizations
        self.state.setdefault("grid_options", [])
        self.state.setdefault("grid_layout", [])
        parallel_coords.initialize(self.server, self._ross_file)
        time_plot.initialize(self.server, self._ross_file)
        scatter_plot.initialize(self.server, self._ross_file)
        empty.initialize(self.server)

        # Reserve the various views
        available_view_ids = [f"{v+1}" for v in range(10)]
        for view_id in available_view_ids:
            self.state[f"grid_view_{view_id}"] = empty.OPTION

        # Parallel Coordinates
        view_id = available_view_ids.pop(0)
        self.state.grid_layout.append(
            dict(x=0, y=0, w=8, h=10, i=view_id),
        )
        self.state[f"grid_view_{view_id}"] = parallel_coords.OPTION

        # Time plot
        view_id = available_view_ids.pop(0)
        self.state.grid_layout.append(
            dict(x=0, y=20, w=8, h=10, i=view_id),
        )
        self.state[f"grid_view_{view_id}"] = time_plot.OPTION

        # Scatter plot
        view_id = available_view_ids.pop(0)
        self.state.grid_layout.append(
            dict(x=0, y=10, w=4, h=8, i=view_id),
        )
        self.state[f"grid_view_{view_id}"] = scatter_plot.OPTION

        @controller.set("grid_add_view")
        def add_view():
            next_view_id = available_view_ids.pop()
            next_y = get_next_y_from_layout(self.state.grid_layout)
            self.state.grid_layout.append(
                dict(x=0, w=12, h=DEFAULT_NB_ROWS, y=next_y, i=next_view_id)
            )
            self.state.dirty("grid_layout")


        @controller.set("grid_remove_view")
        def remove_view(view_id):
            available_view_ids.append(view_id)
            self.state.grid_layout = list(
                filter(lambda item: item.get("i") != view_id, self.state.grid_layout)
            )

        # Setup main layout
        with SinglePageLayout(self.server) as layout:
            layout.root.classes = ("{ busy: trame__busy }",)

            # Toolbar
            with layout.toolbar as toolbar:
                toolbar.clear()

                toolbar.height = 36

                vuetify.VSpacer()

                with html.Div(
                    style="width: 25px",
                    classes="mr-2",
                ):
                    vuetify.VProgressCircular(
                        indeterminate=True,
                        v_show=("trame__busy",),
                        style="background-color: lightgray; border-radius: 50%",
                        background_opacity=1,
                        bg_color="#01549b",
                        color="#04a94d",
                        size=16,
                        width=3,
                    )

                vuetify.VSelect(
                    v_model=("selected_array", "events_processed"),
                    items=(
                        "available_arrays",
                        [
                            dict(text=key.replace("_", " ").title(), value=key)
                            for key in self._ross_file.pe_engine_df.columns
                        ],
                    ),
                    hide_details=True,
                    dense=True,
                    style="max-width: 220px",
                )

            #    with vuetify.VBtn(icon=True, click=ctrl.grid_add_view):
            #        vuetify.VIcon("mdi-plus")

            # Main content
            with layout.content:
                layout.content.style = "overflow: auto; margin: 36px 0px 35px; padding: 0;"
                with vuetify.VContainer(
                    fluid=True,
                    classes="pa-0 fill-height",
                    style="user-select: none;",
                ):
                    with grid.GridLayout(
                        layout=("grid_layout", []),
                        row_height=30,
                        vertical_compact=True,
                        style="width: 100%; height: 100%;",
                    ):
                        with grid.GridItem(
                            v_for="item in grid_layout",
                            key="item.i",
                            v_bind="item",
                            style="touch-action: none;",
                            drag_ignore_from=".drag_ignore",
                        ):
                            with vuetify.VCard(
                                style="height: 100%;",
                                key="grid_item_dirty_key",
                            ):
                                with vuetify.VCardTitle(classes="py-1 px-1"):
                                    with vuetify.VMenu(offset_y=True):
                                        with vuetify.Template(
                                            v_slot_activator="{ on, attrs }"
                                        ):
                                            with vuetify.VBtn(
                                                icon=True,
                                                small=True,
                                                v_bind="attrs",
                                                v_on="on",
                                            ):
                                                vuetify.VIcon(
                                                    v_text="get(`grid_view_${item.i}`).icon"
                                                )
                                            html.Div(
                                                "{{ get(`grid_view_${item.i}`).label }}",
                                                classes="ml-1 text-subtitle-2",
                                            )
                                        with vuetify.VList(dense=True):
                                            with vuetify.VListItem(
                                                v_for="(option, index) in grid_options",
                                                key="index",
                                                click="""
                                                    set(`grid_view_${item.i}`, option);
                                                    grid_item_dirty_key++;
                                                """,
                                            ):
                                                with vuetify.VListItemIcon():
                                                    vuetify.VIcon(v_text="option.icon")
                                                vuetify.VListItemTitle("{{ option.label }}")
                                    vuetify.VSpacer()
                                    with vuetify.VBtn(
                                        icon=True,
                                        x_small=True,
                                        click=(self.ctrl.grid_remove_view, "[item.i]"),
                                    ):
                                        vuetify.VIcon(
                                            "mdi-delete-forever-outline", small=True
                                        )
                                vuetify.VDivider()

                                style = "; ".join(
                                    [
                                        "position: relative",
                                        "height: calc(100% - 37px)",
                                        "overflow: auto",
                                    ]
                                )
                                with vuetify.VCardText(style=style, classes="drag_ignore"):
                                    # Add template for value of get(`grid_view_${item.i}`)
                                    client.ServerTemplate(
                                        name=("get(`grid_view_${item.i}`).name",)
                                    )