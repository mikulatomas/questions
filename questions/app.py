from pydoc import classname
import dash.html as html
import dash_bootstrap_components as dbc

from dash import dcc

from .server import app, server
from .data import (
    attribute_counts,
    min_extent_size,
    max_extent_size,
)
from . import callbacks


navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink("Info", id="open-offcanvas", n_clicks=0)),
        dbc.NavItem(
            dbc.NavLink("Github", href="https://github.com/mikulatomas/questions")
        ),
    ],
    brand="Kaggle Questions Dataset",
    brand_href="/",
    color="dark",
    dark=True,
    fluid=True,
)

concepts = dbc.Col(
    html.Div(
        [
            dbc.Row(
                [
                    html.H2("Concepts"),
                    dbc.Label("Keywords"),
                    dcc.Dropdown(
                        id="intent-dropdown",
                        options=[
                            {"label": f"{label} ({count})", "value": label}
                            for label, count in attribute_counts.iteritems()
                        ],
                        multi=True,
                        className="mb-2",
                    ),
                    dbc.Label("Minimal number of questions"),
                    dcc.Slider(
                        id="concept-size-slider",
                        min=min_extent_size,
                        max=max_extent_size // 5,
                        step=1,
                        value=10,
                        tooltip={"placement": "bottom", "always_visible": False},
                        className="ps-4 pe-4",
                    ),
                ],
                className="pt-3",
            ),
            dbc.Row(
                html.Ul(
                    id="concepts",
                ),
                className="flex-grow-1 overflow-auto full-height-fix pt-2",
            ),
        ],
        className="h-100 d-flex flex-column",
    ),
    width=2,
    id="keywords-col",
    className="border-right background-gray",
)


detail = dbc.Col(
    html.Div(
        [
            dbc.Row(
                [
                    html.Div(
                        [
                            html.H2("Concept detail"),
                            dbc.Label("Metadata"),
                            html.Ul(id="metadata"),
                            dbc.Label("Related keywords"),
                        ]
                    ),
                ],
                className="pt-3 pb-2",
            ),
            dbc.Row(
                html.Ul(
                    id="centrality",
                ),
                className="flex-grow-1 overflow-auto full-height-fix",
            ),
        ],
        className="h-100 d-flex flex-column",
    ),
    width=2,
    className="border-right background-gray",
)

navigation = dbc.Col(
    html.Div(
        [
            dbc.Row(
                [
                    html.Div(
                        [
                            html.H2("Navigation"),
                        ]
                    ),
                ],
                className="pt-3 pb-2",
            ),
            dbc.Row(
                [
                    html.Div(
                        [
                            dbc.Label("More general"),
                            html.Div(id="upper-concepts"),
                            dbc.Label("More specific"),
                            html.Div(id="lower-concepts"),
                        ]
                    ),
                ],
                className="flex-grow-1 overflow-auto full-height-fix",
            ),
        ],
        className="h-100 d-flex flex-column",
    ),
    id="navigation",
    width=2,
    className="border-right background-gray",
)

tabs = dbc.Tabs(
    [
        dbc.Tab(
            [
                dbc.Row(
                    [
                        html.Ul(id="question-list"),
                    ],
                    className="pt-3",
                ),
            ],
            label="Questions",
        ),
        dbc.Tab(
            dbc.Row(
                id="mca",
                className="pt-3 pb-2",
            ),
            label="MCA Plot",
        ),
    ],
    className="mt-2 mb-2",
)

questions = dbc.Col(
    html.Div(
        tabs,
        className="h-100 d-flex flex-column",
    ),
    id="questions",
    className="border-right",
)


info = dbc.Offcanvas(
    html.P(
        [
            "Original dataset is avaliable ",
            html.A(
                "here",
                href="https://www.kaggle.com/umairnasir14/all-kaggle-questions-on-qoura-dataset",
            ),
            ".",
        ]
    ),
    id="info",
    title="Kaggle Question Dataset",
    is_open=False,
)

app.layout = html.Div(
    [
        dcc.Location(id="url", refresh=False),
        info,
        dbc.Container(
            [
                dbc.Row(navbar),
                dbc.Row(
                    [concepts, questions, detail, navigation], className="flex-grow-1"
                ),
            ],
            fluid=True,
            className="min-vh-100 d-flex flex-column",
        ),
    ],
)
