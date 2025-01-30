import os

from trame.app import get_server, dev
from trame.app.file_upload import ClientFile
from trame.decorators import TrameApp, change, controller
from trame.ui.vuetify import SinglePageWithDrawerLayout
from trame.widgets import client, grid, html, vuetify, trame, router
from trame.ui.router import RouterViewLayout
from trame.ui.html import DivLayout
from trame.widgets import plotly
import plotly.express as px

from .ui import (
    empty, 
    parallel_coords, 
    time_plot,
    scatter_plot,
    network_time,
    heatmap
)
from .core.ross_binary_file import ROSSFile
from .core.event_trace_file import EventFile
from .core.model_file import ModelFile

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
        self.state.trame__title = "Visualization Dashboard"
        self.state.setdefault("grid_options", [])
        self.state.setdefault("model_grid_item_dirty_key", 0)
        self.state.setdefault("engine_grid_item_dirty_key", 0)

        self._args = self._app_settings()
        self._ross_file = None
        self._event_file = None
        self._model_file = None

        # only true when both event file and model file are uploaded
        self.state.all_model_data_uploaded = False
        self.state.sim_engine_data_uploaded = False

        # can be none, model-only, engine-only, both
        self.state.view_mode = "none"
        if self._args.data_file is not None:
            self._ross_file = ROSSFile(self._args.data_file)
            self._ross_file.read()
            self.state.sim_engine_data_uploaded = True
        
        if self._args.event_data_file is not None:
            self._event_file = EventFile(self._args.event_data_file)
            self._event_file.read()

        if self._args.model_data_file is not None:
            self._model_file = ModelFile(self._args.model_data_file)
            self._model_file.read()

        if self._model_file is not None and self._event_file is not None:
            self.state.all_model_data_uploaded = True

        # at this point, set up default layouts, which if nothing is loaded, is just
        # empty. maybe it should be an empty vcontainer or something, that we can then
        # change once data gets loaded
        # so I think we actually need to have all the figures created in the beginning
        # and use v_for to hide them until they're needed
        # so maybe each vis type gets a function that just sets up the inital plotly figure
        # but doesn't have to set up any of the other stuff, or maybe there's just a default
        # function that sets up some empty figures and hides them, then that can be adapted
        # to the correct type of figure when the data is loaded
        self.init_all_visualizations()

        self.LAYOUTS = {}
        self.set_up_model_vis_view()
        self.set_up_sim_engine_vis_view()

        if self.server.hot_reload:
            self.server.controller.on_server_reload.add(self._build_ui)
        self.ui = self._build_ui()


    @property
    def ctrl(self):
        return self.server.controller
    

    @property
    def state(self):
        return self.server.state


    # can choose to load any of the data files through the command line
    def _app_settings(self):
        data_kwargs = {
            "help": "Sim Engine data file to load",
            "dest": "data_file",
        }

        event_data_kwargs = {
            "help": "Event data file to load",
            "dest": "event_data_file",
        }

        model_data_kwargs = {
            "help": "model data file to load",
            "dest": "model_data_file",
        }

        default = os.getenv(DATA_PATH_ENV_NAME)
        if default is not None:
            # If the environment variable has been provided, use that for the default
            data_kwargs["default"] = default
            event_data_kwargs["default"] = default
            model_data_kwargs["default"] = default

        self.server.cli.add_argument("--data", **data_kwargs)
        self.server.cli.add_argument("--event-data", **event_data_kwargs)
        self.server.cli.add_argument("--model-data", **model_data_kwargs)
        args, _ = self.server.cli.parse_known_args()
        return args


    def init_all_visualizations(self):
        empty.init_options(self.server)
        heatmap.init_options(self.server)
        network_time.init_options(self.server)
        parallel_coords.init_options(self.server)
        scatter_plot.init_options(self.server)
        time_plot.init_options(self.server)


    def set_up_model_vis_view(self):
        # this also gets added to the state.grid_options, do we need both?
        self.state[f"model_grid_view_heatmap"] = heatmap.OPTION
        self.state[f"model_grid_view_network_time_plot"] = network_time.OPTION

        name = 'model_layout'
        layout = DivLayout(self.server, name,
                           width='1200px')
        self.LAYOUTS[name] = layout
        with layout:
            with vuetify.VCard(style="height: 100%; width: 100%;",
                               classes="ma-1 position-absolute top-0 left-0",
                                #width=1200, height=800
            ):
                vuetify.VCardTitle("Model Data Visualizations")
                vuetify.VDivider()
                layout.content = vuetify.VCardText()
                layout.content.vis_views = {}
                with layout.content:
                    with vuetify.VRow(v_if="all_model_data_uploaded == false"):
                        with vuetify.VCol(cols="12"):
                            html.Div("Load a model data file and event trace file to view visualizations")
                    self._create_model_vis_view(layout)


    def set_up_sim_engine_vis_view(self):
        self.state[f"engine_grid_view_parallel_coords"] = parallel_coords.OPTION
        self.state[f"engine_grid_view_scatter_plot"] = scatter_plot.OPTION
        self.state[f"engine_grid_view_time_plot"] = time_plot.OPTION

        name = 'sim_engine_layout'
        layout = DivLayout(self.server, name)
        self.LAYOUTS[name] = layout
        with layout:
            with vuetify.VCard(style="height: 100%; width: 100%;",
                                #width=1200, height=800
            ):
                vuetify.VCardTitle("Simulation Engine Visualizations")
                vuetify.VDivider()
                layout.content = vuetify.VCardText()
                layout.content.vis_views = {}
                with layout.content:
                    with vuetify.VRow(v_if="sim_engine_data_uploaded == false"):
                        with vuetify.VCol(cols="12"):
                            html.Div("Load a simulation engine file to view visualizations")
                    self._create_sim_engine_vis_view(layout)


    @change("sim_engine_file")
    def sim_engine_file_uploaded(self, sim_engine_file, **kwargs):
        if sim_engine_file is None:
            return
        
        file = ClientFile(sim_engine_file)
        self._ross_file = ROSSFile(file)
        self._ross_file.read()

        if self.state.view_mode == "none" or self.state.view_mode == "engine-only":
            self.state.view_mode = "engine-only"
        else:
            self.state.view_mode = "both"

        self.state.sim_engine_data_uploaded = True

        parallel_coords.initialize(self.server, self._ross_file)
        scatter_plot.initialize(self.server, self._ross_file)
        time_plot.initialize(self.server, self._ross_file)

        # TODO: update the sim engine layout
        layout = self.LAYOUTS["sim_engine_layout"]
        with layout:
            with layout.content:
                for name, view in layout.content.vis_views.items():
                    view.clear()
                    with view:
                        client.ServerTemplate(name=name)

        self.ctrl.init_parallel_coords()


    @change("model_data_file")
    def model_data_file_uploaded(self, model_data_file, **kwargs):
        if model_data_file is None:
            return

        file = ClientFile(model_data_file)
        self._model_file = ModelFile(file)
        self._model_file.read()

        if self.state.view_mode == "none" or self.state.view_mode == "model-only":
            self.state.view_mode = "model-only"
        else:
            self.state.view_mode = "both"


        if self._event_file is not None:
            self.state.all_model_data_uploaded = True

    
    @change("event_data_file")
    def event_data_file_uploaded(self, event_data_file, **kwargs):
        if event_data_file is None:
            return

        file = ClientFile(event_data_file)
        self._event_file = EventFile(file)
        self._event_file.read()


        if self.state.view_mode == "none" or self.state.view_mode == "model-only":
            self.state.view_mode = "model-only"
        else:
            self.state.view_mode = "both"

        if self._model_file is not None:
            self.state.all_model_data_uploaded = True


    @change("all_model_data_uploaded")
    def model_data_uploaded(self, all_model_data_uploaded, **kwargs):
        if not all_model_data_uploaded:
            return
        
        heatmap.initialize(self.server, self._event_file)
        network_time.initialize(self.server, self._model_file)

        # now we can update the model_layout
        layout = self.LAYOUTS["model_layout"]
        with layout:
            with layout.content:
                for name, view in layout.content.vis_views.items():
                    view.clear()
                    with view:
                        client.ServerTemplate(name=name)


    @controller.set("view_update")
    def update_views_time(self):
        self.ctrl.on_ross_time_range_changed()


    def create_vis(self, layout, grid_view_name, template_name, key):
        with vuetify.VCard(#style="height: 100%;",
                        key=key,
                        height=400,
                        width=600
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
                                v_text=f"get(`{grid_view_name}`).icon"
                            )
                        html.Div(
                            f"{{{{ get(`{grid_view_name}`).label }}}}",
                            classes="ml-1 text-subtitle-2",
                        )
                    with vuetify.VList(dense=True):
                        with vuetify.VListItem(
                            v_for="(option, index) in grid_options",
                            key="index",
                            click=f"""
                                set(`{grid_view_name}`, option);
                                {key}++;
                            """,
                        ):
                            with vuetify.VListItemIcon():
                                vuetify.VIcon(v_text="option.icon")
                            vuetify.VListItemTitle("{{ option.label }}")
            vuetify.VDivider()
            style = "; ".join(
                [
                    "position: relative",
                    "height: calc(100% - 37px)",
                    "overflow: auto",
                ]
            )
            layout.content.vis_views[template_name] = vuetify.VCardText(style=style, classes="drag_ignore")
            with layout.content.vis_views[template_name]:
                client.ServerTemplate(name=f"{template_name}_init")


    def _create_model_vis_view(self, layout):
        with vuetify.VContainer(v_if="all_model_data_uploaded == true"):
            with vuetify.VRow():
                with vuetify.VCol(cols="12"):
                    self.create_vis(layout, "model_grid_view_heatmap", "heatmap", "model_grid_item_dirty_key")
            with vuetify.VRow():
                with vuetify.VCol(cols="20"):
                    self.create_vis(layout, "model_grid_view_network_time_plot", "network_time_plot", "model_grid_item_dirty_key")

        
    def _create_sim_engine_vis_view(self, layout):
        with vuetify.VContainer(v_if="sim_engine_data_uploaded == true"):
            with vuetify.VRow():
                with vuetify.VCol(cols="12"):
                    self.create_vis(layout, "engine_grid_view_parallel_coords", "parallel_coords", "engine_grid_item_dirty_key")
            with vuetify.VRow():
                with vuetify.VCol(cols="12"):
                    self.create_vis(layout, "engine_grid_view_scatter_plot", "scatter_plot", "engine_grid_item_dirty_key")
            with vuetify.VRow():
                with vuetify.VCol(cols="12"):
                    self.create_vis(layout, "engine_grid_view_time_plot", "time_plot", "engine_grid_item_dirty_key")


    def _build_ui(self, *args, **kwargs):
        with RouterViewLayout(self.server, "/"):
            with vuetify.VCard():
                vuetify.VCardTitle("Getting Started")
                vuetify.VCardText(
                    """
                        To get started, load a file for either simulation engine data
                        or model level data on the left.
                    """
                )

        with RouterViewLayout(self.server, "/model"):
            client.ServerTemplate(name="model_layout")

        with RouterViewLayout(self.server, "/engine"):
            client.ServerTemplate(name="sim_engine_layout")

        with SinglePageWithDrawerLayout(self.server) as layout:
            layout.title.set_text("Visualization Dashboard")
            layout.root.classes = ("{ busy: trame__busy }",)

            with layout.toolbar as toolbar:
                toolbar.clear()

                toolbar.height = 50

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

                vuetify.VSpacer()

                with vuetify.VBtn(value="home", to="/"):
                    vuetify.VIcon("mdi-home")


            with layout.drawer as drawer:
                drawer.width = 325
                with vuetify.VCard():
                    vuetify.VCardTitle("Simulation Engine Data")
                    vuetify.VFileInput(v_model=("sim_engine_file", None), label="Simulation Engine File")
                with vuetify.VCard():
                    vuetify.VCardTitle("Model Data")
                    vuetify.VFileInput(v_model=("model_data_file", None), label="Model Data File")
                    vuetify.VFileInput(v_model=("event_data_file", None), label="Event Data File")
                with vuetify.VCard():
                    vuetify.VCardTitle("Choose Visualizations")
                    vuetify.VBtn("View Simulation Engine Visualizations", to="/engine")
                    vuetify.VBtn("View Model Visualizations", to="/model")
                    vuetify.VBtn("View Combined", to="/both")

            with layout.content:
                with vuetify.VContainer(
                    style="user-select: none; width=100%;",
                ):
                    router.RouterView()

            return layout



# this was the original way of doing things, taken from VeraCore, but i couldn't get it
# to work correctly when uploading files (as opposed to providing files via the command line).
# I ended up not using the grid layout, but it's very clunky so I'm leaving this code here
# for now in case I want to go back to it.
# other methods after this are related to how it was done before, but not using them
# in the new way of setting things up
    def _build_ui_old(self, *args, **kwargs):
        _available_view_types = ["scatter_plot", "parallel_coordinates"]

        # Setup main layout
        with SinglePageWithDrawerLayout(self.server) as layout:
            layout.root.classes = ("{ busy: trame__busy }",)

            # Toolbar
            with layout.toolbar as toolbar:
                toolbar.clear()

                toolbar.height = 40

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

                #removing this messes up the parallel coords graph for some reason
                # but it doesn't matter that we removed the ref to the ross_file for array names
                vuetify.VSelect(
                    v_model=("selected_array", "events_processed"),
                    items=(
                        "available_arrays",
                        [
                           { "test": "test"}
                        ],
                    ),
                    hide_details=True,
                    dense=True,
                    style="max-width: 220px",
                )

                # the following code was added for adding new views, but it doesn't fully work yet,
                # so commenting out for now
                #vuetify.VSelect(
                #    v_model=("selected_view", "scatter_plot"),
                #    items=(
                #        "available_views",
                #        [
                #            dict(text=key.replace("_", " ").title(), value=key)
                #            for key in _available_view_types
                #        ],
                #    ),
                #    hide_details=True,
                #    dense=True,
                #    style="max-width: 220px",
                #)

                #with vuetify.VBtn(icon=True, click=self.ctrl.grid_add_view):
                #    vuetify.VIcon("mdi-plus")

            # drawer components
            with layout.drawer as drawer:
                drawer.width = 325
                self.vis_selection()
                vuetify.VDivider(classes="mb-2")
                self.sim_engine_card()
                self.model_vis_card()


            # Main content
            with layout.content:
#                print(f'self.state.grid_layout : {self.state.grid_layout}')
                layout.content.style = "overflow: auto; margin: 36px 0px 35px; padding: 0;"
                with vuetify.VContainer(
                    fluid=True,
                    classes="pa-0 fill-height",
                    style="user-select: none;",
                ):
                    # welcome page when no files have been loaded
                    with vuetify.VCard(v_if=("view_mode == 'none'"), classes = "ma-8"):
                        vuetify.VCardText("Getting Started")
                        vuetify.VCardText(
                            """
                             To get started, load a file for either simulation engine data
                             or model level data on the left.
                            """
                        )

                    # now we can create 3 views, sim engine only,
                    # model data only
                    # both together
                    # need some way to specify for each vis type what kind it is
                    # then the grid layout can loop through that?

                    # model data vis only
                    with grid.GridLayout(
                        v_if="view_mode == 'model-only'",
                        layout=("grid_layout", []),
                        row_height=30,
                        #is_draggable="draggable",
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
            return layout


    def __init_old(self, server_or_name=None) -> None:

        self.state.setdefault("grid_layout", [])

        self.state.sim_engine_layout = [
                {"x:": 0, "y": 0, "w": 8, "h": 10, "i": "0"},
                {"x:": 0, "y": 20, "w": 8, "h": 10, "i": "1"},
                {"x:": 0, "y": 10, "w": 4, "h": 10, "i": "2"},
        ]
        self.state.model_layout = [
                #{"x:": 0, "y": 30, "w": 8, "h": 10, "i": 1},
            dict(x=4, y=10, w=4, h=10, i=1),
                #{"x:": 4, "y": 10, "w": 4, "h": 10, "i": 1},
        ]

        self.state.current_layout = "none"

        # can be none, model-only, engine-only, both
        self.state.view_mode = "none"

        if self._ross_file is not None and self._model_file is not None and self._event_file is not None:
            self.state.view_mode = "both"
            self.state.current_layout = "both"
        elif self._ross_file is not None and self._model_file is None and self._event_file is None:
            self.state.view_mode = "engine-only"
            self.state.current_layout = "sim_engine"
        elif self._ross_file is None and self._model_file is not None and self._event_file is not None:
            self.state.view_mode = "model-only"
            self.state.current_layout = "model"


        self.state.setdefault("active_ui", None)


    @controller.set("grid_remove_view")
    def remove_view(self, view_id):
        print(f'removing view id {view_id}')
        self._available_view_ids.append(view_id)
        print(f'avail view ids: {self._available_view_ids}')
        # clear out the details of the previous view
        self.state[f"grid_view_{view_id}"] = empty.OPTION
        self.state.grid_layout = list(
            filter(lambda item: item.get("i") != view_id, self.state.grid_layout)
        )


    def actives_change(self, ids):
        _id = ids[0]
        if _id == "1":
            self.state.active_ui = "engine"
        elif _id == "2":
            self.state.active_ui = "model"
        else:
            self.state.active_ui = "nothing"


    def visibility_change(self, event):
        _id = event["id"]
        _visibility = event["visible"]

        if _id == "1":
            # engine
            pass
        elif _id == "2":
            #model
            pass


    def vis_selection(self):
        trame.GitTree(
            sources=(
                "pipeline",
                [
                    {"id": "1", "parent": "0", "visible": 1, "name": "Simulation Engine"},
                    {"id": "2", "parent": "1", "visible": 1, "name": "Network Model"},
                ],
            ),
            actives_change=(self.actives_change, "[$event]"),
            visibility_change=(self.visibility_change, "[$event]"),
        )


    def ui_card(self, title, ui_name):
        with vuetify.VCard(v_show=f"active_ui == '{ui_name}'"):
            vuetify.VCardTitle(
                title,
                classes="grey lighten-1 py-1 grey--text text--darken-3",
                style="user-select: none; cursor: pointer",
                hide_details=True,
                dense=True,
            )
        content = vuetify.VCardText(classes="py-2")
        return content


    def sim_engine_card(self):
        with self.ui_card(title="Simulation Engine", ui_name="engine"):
            vuetify.VFileInput(v_model=("sim_engine_file", None), label="Simulation Engine File")


    def model_vis_card(self):
        with self.ui_card(title="Network Model", ui_name="model"):
            vuetify.VFileInput(v_model=("model_data_file", None), label="Model Data File")
            vuetify.VFileInput(v_model=("event_data_file", None), label="Event Data File")