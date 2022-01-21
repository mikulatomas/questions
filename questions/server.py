import pathlib

import dash
import dash_bootstrap_components as dbc

app = dash.Dash(
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    assets_folder=pathlib.Path(__file__).parent / "assets",
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1"},
    ],
)

server = app.server
