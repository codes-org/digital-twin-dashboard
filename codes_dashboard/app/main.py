from functools import partial
import os

from trame.app import get_server, dev

from . import ui
from .core.ross_binary_file import ROSSFile

# The user can set this via an environment variable
DATA_PATH_ENV_NAME = "ROSS_DATA_PATH"


def _reload(ross_file):
    server = get_server()
    dev.reload(ui)
    ui.initialize(server, ross_file)


def main(server=None, **kwargs):
    # Get or create server
    if server is None:
        server = get_server(client_type="vue2")

    if isinstance(server, str):
        server = get_server(server, client_type="vue2")

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

    server.cli.add_argument("--data", **data_kwargs)
    args, _ = server.cli.parse_known_args()
    data_file = args.data_file

    ross_file = ROSSFile(data_file)

    f = partial(_reload, ross_file=ross_file)

    # Make UI auto reload
    server.controller.on_server_reload.add(f)

    # Init application
    ui.initialize(server, ross_file)

    # Start server
    server.start(**kwargs)


if __name__ == "__main__":
    main()
