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
        self.state.setdefault("grid_options", [])
        self.state.setdefault("grid_item_dirty_key", 0)

        self._args = self._app_settings()
        self._ross_file = None
        self._event_file = None
        self._model_file = None

        self.state.all_model_data_uploaded = False

        # can be none, model-only, engine-only, both
        self.state.view_mode = "none"
        if self._args.data_file is not None:
            self._ross_file = ROSSFile(self._args.data_file)
            self._ross_file.read()
        
        if self._args.event_data_file is not None:
            self._event_file = EventFile(self._args.event_data_file)
            self._event_file.read()

        if self._args.model_data_file is not None:
            self._model_file = ModelFile(self._args.model_data_file)
            self._model_file.read()

        # at this point, set up default layouts, which if nothing is loaded, is just
        # empty. maybe it should be an empty vcontainer or something, that we can then
        # change once data gets loaded
        # so I think we actually need to have all the figures created in the beginning
        # and use v_for to hide them until they're needed
        # so maybe each vis type gets a function that just sets up the inital plotly figure
        # but doesn't have to set up any of the other stuff, or maybe there's just a default
        # function that sets up some empty figures and hides them, then that can be adapted
        # to the correct type of figure when the data is loaded
        self.set_up_initial_vis()

        self.layout_names = ["model_layout"]
        self.LAYOUTS = {}
        for name in self.layout_names:
            layout = DivLayout(self.server, name)
            self.LAYOUTS[name] = layout
            with layout:
                trame.LifeCycleMonitor(name=f"{name} layout", events=("['created']",))
                with vuetify.VCard(width=1200, height=800):
                    vuetify.VCardTitle(name)
                    vuetify.VDivider()
                    layout.content = vuetify.VCardText()
                    with layout.content:
                        with vuetify.VRow(v_if="view_mode == 'none'"):
                            with vuetify.VCol(cols="12"):
                                html.Div("No data loaded yet")
                        with vuetify.VCard(v_if="view_mode == 'model-only'"):
                            with vuetify.VCardTitle():
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
                                                "mdi-chart-box"
                                            )
                                        html.Div(
                                            "Heatmap",
                                            classes="ml-1 text-subtitle-2",
                                        )
                            vuetify.VDivider()
                            layout.content.heatmap_vis = vuetify.VCardText()
                            with layout.content.heatmap_vis:
                                client.ServerTemplate(name="heatmap_init")
                        #with vuetify.VRow(v_if="view_mode == 'model-only'"):
                        #    with vuetify.VCol(cols="12"):
                        #        client.ServerTemplate(name="heatmap")

        self.state.model_layout = [
            dict(x=0, y=10, w=8, h=10, i=1),
            #dict(x=4, y=10, w=4, h=10, i=2),
        ]
        #self.state[f"grid_view_{self.state.model_layout[0]['i']}"] = network_time.OPTION
        self.state[f"grid_view_{self.state.model_layout[0]['i']}"] = heatmap.OPTION

        if self.server.hot_reload:
            self.server.controller.on_server_reload.add(self._build_ui2)
        self.ui = self._build_ui2()


    def set_up_initial_vis(self):
        # TODO: create for every type of visualization
        empty.create_empty_vis(self.server, "heatmap")


    def __init_old(self, server_or_name=None) -> None:
        self.server = get_server(server_or_name, client_type="vue2")
        self.server.debug = True

        self._args = self._app_settings()
        self._ross_file = None
        self._event_file = None
        self._model_file = None

        self.state.setdefault("grid_options", [])
        self.state.setdefault("grid_layout", [])
        self.state.setdefault("grid_item_dirty_key", 0)

        self._available_view_ids = [f"{v+1}" for v in range(10)]
        print(f'created avail view ids: {self._available_view_ids}')
        for view_id in self._available_view_ids:
            self.state[f"grid_view_{view_id}"] = empty.OPTION
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
        self.state[f"grid_view_{self.state.model_layout[0]['i']}"] = network_time.OPTION

        if network_time.OPTION not in self.state.grid_options:
            self.state.grid_options.append(network_time.OPTION)
        if empty.OPTION not in self.state.grid_options:
            self.state.grid_options.append(empty.OPTION)

        self.state.empty_layout = []
        self.state.dual_layout = []

        self.state.current_layout = "none"

        # can be none, model-only, engine-only, both
        self.state.view_mode = "none"
        if self._args.data_file is not None:
            self._ross_file = ROSSFile(self._args.data_file)
            self._ross_file.read()
        
        if self._args.event_data_file is not None:
            self._event_file = EventFile(self._args.event_data_file)
            self._event_file.read()

        if self._args.model_data_file is not None:
            self._model_file = ModelFile(self._args.model_data_file)
            self._model_file.read()

        if self._ross_file is not None and self._model_file is not None and self._event_file is not None:
            self.state.view_mode = "both"
            self.state.current_layout = "both"
        elif self._ross_file is not None and self._model_file is None and self._event_file is None:
            self.state.view_mode = "engine-only"
            self.state.current_layout = "sim_engine"
        elif self._ross_file is None and self._model_file is not None and self._event_file is not None:
            self.state.view_mode = "model-only"
            self.state.current_layout = "model"


        if self.server.hot_reload:
            self.server.controller.on_server_reload.add(self._build_ui2)
        self.ui = self._build_ui2()

        # set state variables
        self.state.trame__title = "NetMaestro Visualization Dashboard"
        self.state.setdefault("active_ui", None)



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


    @property
    def ctrl(self):
        return self.server.controller
    
    @property
    def state(self):
        return self.server.state


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

        self._init_sim_engine_plots()
        self.create_sim_engine_figures()


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


        #network_time.initialize(self.server, self._model_file)
        #view_id = self._available_view_ids.pop(0)
        #print(f'avail view ids: {self._available_view_ids}')
        #print(f'network time plot is view_id {view_id}')
        #self.state.grid_layout.append(
        #    dict(x=0, y=30, w=8, h=10, i=view_id),
        #)
        #self.state[f"grid_view_{view_id}"] = network_time.OPTION
        #self._build_ui()
        #self.ui.flush_content()

    
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

        #self.state.event_file_uploaded = True

        #heatmap.initialize(self.server, self._event_file)
        #view_id = self._available_view_ids.pop(0)
        #print(f'avail view ids: {self._available_view_ids}')
        #print(f'heatmap plot is view_id {view_id}')
        #self.state.grid_layout.append(
        #    dict(x=4, y=10, w=4, h=10, i=view_id),
        #)
        #self.state[f"grid_view_{view_id}"] = heatmap.OPTION
        #self._build_ui()
        #self.ui.flush_content()


    @change("all_model_data_uploaded")
    def model_data_uploaded(self, all_model_data_uploaded, **kwargs):
        if not all_model_data_uploaded:
            return
        
        heatmap.initialize(self.server, self._event_file)
        
        #network_time.initialize(self.server, self._model_file)

        # now we can update the model_layout
        layout = self.LAYOUTS["model_layout"]
        with layout:
            with layout.content:
                layout.content.heatmap_vis.clear()
                client.ServerTemplate(name="heatmap")
                #layout.content.clear()
                #with vuetify.VCard(height=500):
                #    vuetify.VCardTitle("heatmap test")
                #    vuetify.VDivider()
                #    with vuetify.VCardText():
                #        #style = "; ".join(
                #        #    [
                #        #        "width: 100%",
                #        #        "height: 80%",
                #        #        "user-select: none",
                #        #    ]
                #        #)
                #        figure = plotly.Figure()
                #        self.ctrl.update_heatmap = figure.update
            print(layout.content)
                #self.ctrl.update_heatmap = figure.update
                #with vuetify.VContainer():
                    #with vuetify.VCard(
                    #    style="height: 100%;",
                    #    key="grid_item_dirty_key",
                    #):
                    #    with vuetify.VCardTitle(classes="py-1 px-1"):
                    #        with vuetify.VMenu(offset_y=True):
                    #            with vuetify.Template(
                    #                v_slot_activator="{ on, attrs }"
                    #            ):
                    #                with vuetify.VBtn(
                    #                    icon=True,
                    #                    small=True,
                    #                    v_bind="attrs",
                    #                    v_on="on",
                    #                ):
                    #                    vuetify.VIcon(
                    #                        "mdi-chart-box"
                    #                    )
                    #                html.Div(
                    #                    "Heatmap",
                    #                    classes="ml-1 text-subtitle-2",
                    #                )
                    #            #with vuetify.VList(dense=True):
                    #            #    with vuetify.VListItem(
                    #            #        v_for="(option, index) in grid_options",
                    #            #        key="index",
                    #            #        click="""
                    #            #            set(`grid_view_${item.i}`, option);
                    #            #            grid_item_dirty_key++;
                    #            #        """,
                    #            #    ):
                    #            #        with vuetify.VListItemIcon():
                    #            #            vuetify.VIcon(v_text="option.icon")
                    #            #        vuetify.VListItemTitle("{{ option.label }}")
                    #        vuetify.VSpacer()
                    #        with vuetify.VBtn(
                    #            icon=True,
                    #            x_small=True,
                    #            click=(self.ctrl.grid_remove_view, "1"),
                    #        ):
                    #            vuetify.VIcon(
                    #                "mdi-delete-forever-outline", small=True
                    #            )
                    #    vuetify.VDivider()

                    #    style = "; ".join(
                    #        [
                    #            "position: relative",
                    #            "height: calc(100% - 37px)",
                    #            "overflow: auto",
                    #        ]
                    #    )
                    #    with vuetify.VCardText(style=style, classes="drag_ignore"):
                        #    with DivLayout(self.server) as vis:
                        #        pass
                                
                            # Add template for value of get(`grid_view_${item.i}`)
                            #client.ServerTemplate(
                            #    name="heatmap"
                            #)

        # at this point call the update
        #df = self._event_file.network_df
        #matrix = df.groupby(['source_lp', 'dest_lp']).size().unstack(fill_value=0)
        #fig = px.imshow(matrix)
        #fig.update_layout(margin=dict(t=0, b=0, l=0, r=0),
        #                    xaxis_title="Receiving LP ID",
        #                    yaxis_title="Sending LP ID",
        #                    coloraxis_colorbar=dict(title="Number of Messages"))
        #self.ctrl.update_heatmap(fig)


                # Add template for value of get(`grid_view_${item.i}`)
                    #client.ServerTemplate(
                    #    name="heatmap"
                    #)
                #with grid.GridLayout(
                #    layout=("model_layout", []),
                #    row_height=30,
                #    is_draggable="draggable",
                #    vertical_compact=True,
                #    style="width: 100%; height: 100%;",
                #):
                #    with grid.GridItem(
                #        v_for="item in model_layout",
                #        key="item.i",
                #        v_bind="item",
                #        style="touch-action: none;",
                #        drag_ignore_from=".drag_ignore",
                #    ):
                #        with vuetify.VCard(
                #            style="height: 100%;",
                #            key="grid_item_dirty_key",
                #        ):
                #            with vuetify.VCardTitle(classes="py-1 px-1"):
                #                with vuetify.VMenu(offset_y=True):
                #                    with vuetify.Template(
                #                        v_slot_activator="{ on, attrs }"
                #                    ):
                #                        with vuetify.VBtn(
                #                            icon=True,
                #                            small=True,
                #                            v_bind="attrs",
                #                            v_on="on",
                #                        ):
                #                            vuetify.VIcon(
                #                                v_text="get(`grid_view_${item.i}`).icon"
                #                            )
                #                        html.Div(
                #                            "{{ get(`grid_view_${item.i}`).label }}",
                #                            classes="ml-1 text-subtitle-2",
                #                        )
                #                    with vuetify.VList(dense=True):
                #                        with vuetify.VListItem(
                #                            v_for="(option, index) in grid_options",
                #                            key="index",
                #                            click="""
                #                                set(`grid_view_${item.i}`, option);
                #                                grid_item_dirty_key++;
                #                            """,
                #                        ):
                #                            with vuetify.VListItemIcon():
                #                                vuetify.VIcon(v_text="option.icon")
                #                            vuetify.VListItemTitle("{{ option.label }}")
                #                vuetify.VSpacer()
                #                with vuetify.VBtn(
                #                    icon=True,
                #                    x_small=True,
                #                    click=(self.ctrl.grid_remove_view, "[item.i]"),
                #                ):
                #                    vuetify.VIcon(
                #                        "mdi-delete-forever-outline", small=True
                #                    )
                #            vuetify.VDivider()

                #            style = "; ".join(
                #                [
                #                    "position: relative",
                #                    "height: calc(100% - 37px)",
                #                    "overflow: auto",
                #                ]
                #            )
                #            with vuetify.VCardText(style=style, classes="drag_ignore"):
                #                # Add template for value of get(`grid_view_${item.i}`)
                #                client.ServerTemplate(
                #                    name=("get(`grid_view_${item.i}`).name",)
                #                )

    @controller.set("view_update")
    def update_views_time(self):
        self.ctrl.on_ross_time_range_changed()


    # So vera core must have just had 10 different views that were already created
    # and you could only readd the ones you deleted. so this will need to be changed
    # so that you can select what type of view you want to add. will need to have a 
    # variable that changes so we can access that here, and then we can create the
    # correct type of view
    # will also need to have some error checking for if we have any available view ids.
    # should we limit it to 10 views? 
    # maybe switch to using a drawer and it will have a list of the views showing,
    # and that's where you add views
    # it can kinda be like a pipeline view
    # that way there can be an assortment of settings for creating the new view, eg
    # is it model data or sim perf data? do we want to look at a specific type of LP?
    #@controller.set("grid_add_view")
    #@change("selected_view")
    #def add_view(self, selected_view, **kwargs):
    #    next_view_id = self._available_view_ids.pop()
    #    # TODO: need to determine how to select the view to be added
    #    print(f'adding view id {next_view_id} of type {selected_view}')
    #    print(f'avail view ids: {self._available_view_ids}')
    #    next_y = get_next_y_from_layout(self.state.grid_layout)
    #    self.state.grid_layout.append(
    #        dict(x=0, w=12, h=DEFAULT_NB_ROWS, y=next_y, i=next_view_id)
    #    ) 
    #    self.state.dirty("grid_layout")


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


    def create_sim_engine_figures(self):
        if self._ross_file is None:
            return

        print("CREATING FIGURES")
        # Parallel Coordinates
        view_id = self._available_view_ids.pop(0)
        print(f'avail view ids: {self._available_view_ids}')
        print(f'parallel coords is view_id {view_id}')
        self.state.grid_layout.append(
            dict(x=0, y=0, w=8, h=10, i=view_id),
        )
        self.state[f"grid_view_{view_id}"] = parallel_coords.OPTION

        print("par coords created")
        # Time plot
        #TODO: maybe time plot should have to stay, and there can only be 1?
        view_id = self._available_view_ids.pop(0)
        print(f'avail view ids: {self._available_view_ids}')
        print(f'time plot is view_id {view_id}')
        self.state.grid_layout.append(
            dict(x=0, y=20, w=8, h=10, i=view_id),
        )
        self.state[f"grid_view_{view_id}"] = time_plot.OPTION
        print("time plot created")

        # Scatter plot
        view_id = self._available_view_ids.pop(0)
        print(f'avail view ids: {self._available_view_ids}')
        print(f'scatter plot is view_id {view_id}')
        self.state.grid_layout.append(
            dict(x=0, y=10, w=4, h=10, i=view_id),
        )
        self.state[f"grid_view_{view_id}"] = scatter_plot.OPTION
        print("scatter plot created")


    def _init_sim_engine_plots(self):
        if self._ross_file is None:
            return

        parallel_coords.initialize(self.server, self._ross_file)
        time_plot.initialize(self.server, self._ross_file)
        scatter_plot.initialize(self.server, self._ross_file)


    def _init_plots(self):
        empty.initialize(self.server)
        self._init_sim_engine_plots()
        if self._model_file is not None:
            network_time.initialize(self.server, self._model_file)
        #if self._event_file is not None:
        #heatmap.initialize(self.server, self._event_file)


    def _reserve_views(self):
        # Reserve the various views
        self._available_view_ids = [f"{v+1}" for v in range(10)]
        print(f'created avail view ids: {self._available_view_ids}')
        for view_id in self._available_view_ids:
            self.state[f"grid_view_{view_id}"] = empty.OPTION

        #if self._model_file is not None:
        # network time plot
        view_id = self._available_view_ids.pop(0)
        print(f'avail view ids: {self._available_view_ids}')
        print(f'network time plot is view_id {view_id}')
        self.state.grid_layout.append(
            dict(x=0, y=30, w=8, h=10, i=view_id),
        )
        self.state[f"grid_view_{view_id}"] = network_time.OPTION

        #if self._event_file is not None:
        # heatmap
        view_id = self._available_view_ids.pop(0)
        print(f'avail view ids: {self._available_view_ids}')
        print(f'heatmap plot is view_id {view_id}')
        self.state.grid_layout.append(
            dict(x=4, y=10, w=4, h=10, i=view_id),
        )
        self.state[f"grid_view_{view_id}"] = heatmap.OPTION

        #self.create_sim_engine_figures()


    def _build_ui_init(self, *args, **kwargs):
        print("begin _build_ui_init")
        self.state.setdefault("grid_item_dirty_key", 0)

        # Initialize all visualizations
        self.state.setdefault("grid_layout", [])

        self._init_plots()
        self._reserve_views()

        print("end _build_ui_init")
        return self._build_ui()
        # now maybe with self.ui.content, we can update the content?


    def _create_vis_view_not_working(self, layout_name):
        #if self.state.view_mode == "none":
        #    pass
        #elif self.state.view_mode == "engine-only":
        #    pass
        #elif self.state.view_mode == "model-only":
        #    self.state.grid_layout = self.state.model_layout
        #    self.state[f"grid_view_{self.state.grid_layout[0]['i']}"] = network_time.OPTION
        #    #self.state[f"grid_view_{self.state.grid_layout['i']}"] = heatmap.OPTION
        #elif self.state.view_mode == "both":
        #    pass

        with grid.GridLayout(
            layout=("model_layout", []),
            #layout=(f"{layout_name}", []),
            row_height=30,
            vertical_compact=True,
            style="width: 100%; height: 100%;",
        ):
            with grid.GridItem(
                v_for="item in model_layout",
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

    def _create_vis_view(self, layout_name):
        # so the initialize calls create the templates for the views, and then the
        # grid layout loops through and adds the ServerTemplate. So that's probably what is messed
        # up in the way I'm trying to get things to work. 
        # see the multi-layout example in my test dir. we can have an empty layout to start
        # then once the files are loaded, clear out the content of the empty layouts, and 
        # create the actual layouts with the correct views
        with vuetify.VSheet(
            #classes="pa-3 ma-2 overflow-hidden",
            #align="center",
            #style="height: 100%; width: 100%;",
        ):
         #   with vuetify.VCol(align_self="center", cols=4):
            client.ServerTemplate(name=layout_name)


    def _build_ui2(self, *args, **kwargs):
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
            with vuetify.VContainer():
                self._create_vis_view("model_layout")

        with RouterViewLayout(self.server, "/engine"):
            with vuetify.VContainer():
                self._create_vis_view("sim_engine_layout")

        with SinglePageWithDrawerLayout(self.server) as layout:
            layout.root.classes = ("{ busy: trame__busy }",)

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

                with vuetify.VList(
                    shaped=True,
                    v_model=("selectedRoute", 0),
                    v_model_opened=("open", []),
                    __properties=[("v_model_opened", "v-model:opened")]
                ):
                    with vuetify.VListItem(to="/"):#, prepend_icon="mdi-home", title="Home")
                        with vuetify.VListItemIcon():
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
                    style="user-select: none;",
                ):
                    #with vuetify.VRow():
                    #    for key in self.LAYOUTS:
                    #        with vuetify.VCol(align_self="center", cols=4):
                    #            client.ServerTemplate(
                    #                name=key, classes="pa-4"
                    #            )
                    router.RouterView()

            return layout



    def _build_ui(self, *args, **kwargs):
        print("begin _build_ui")
        # so i think this should be pretty basic and just have the layout stuff
        # other things should be moved so we can load with an inital set of vis (depending
        # on what is preloaded), then we can update as files get loaded

        _available_view_types = ["scatter_plot", "parallel_coordinates"]

        # Setup main layout
        with SinglePageWithDrawerLayout(self.server) as layout:
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