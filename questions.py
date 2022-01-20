import pathlib
import dash
from dash import dcc
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
import dash.html as html
import pandas as pd
from functools import cache

from concepts import Context
from fcapsy.cohesion import cohesion_avg
from binsdpy.similarity import jaccard
from fcapsy.typicality import typicality_avg

from fcapsy_experiments.centrality import Centrality
from fcapsy_experiments.mca import MCAConcept
from fcapsy_experiments.typicality import ConceptTypicality


@cache
def cohesion_avg_cached(concept, similarity):
    return cohesion_avg(concept, similarity)


@cache
def similarity_cached(x, y):
    return jaccard(x, y)


app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1"},
    ],
)

server = app.server


df = pd.read_csv(
    pathlib.Path.cwd() / "data" / "kaggle" / "kaggle_context.csv", index_col=0
)
attributes = df.sum().sort_values(ascending=False)

df_original = pd.read_csv(
    pathlib.Path.cwd() / "data" / "kaggle" / "kaggle.csv", index_col=0
)

context = Context.fromjson(pathlib.Path.cwd() / "data" / "kaggle" / "lattice.json")

bl = tuple(
    map(
        float,
        (pathlib.Path.cwd() / "data" / "kaggle" / "basic_level.txt")
        .read_text()
        .split(","),
    )
)


def filter_concept_list(concepts, context, min_, max_):
    return (
        concept
        for concept in concepts
        if concept not in [context.lattice.supremum, context.lattice.infimum]
        and len(concept.extent) >= min_
        and len(concept.extent) <= max_
    )


def get_concept_id(concept):
    return context.lattice._concepts.index(concept)


def concept_links(concepts, intent=[], id="", limit=None):
    # concepts = sorted(concepts, key=lambda c: bl[get_concept_id(c)], reverse=True)
    concepts = [
        c
        for c in sorted(concepts, key=lambda c: bl[get_concept_id(c)], reverse=True)
        if c != context.lattice.supremum
    ]

    if limit:
        concepts = concepts[:limit]

    layout = html.Ul(
        [
            html.Li(
                [
                    dcc.Link(
                        f"{', '.join(set(c.intent).symmetric_difference(set(intent)))}",
                        href=f"{get_concept_id(c)}",
                        className="link-primary",
                    ),
                    html.Span(
                        [
                            dbc.Badge(
                                f"{len(c.extent)}",
                                color="primary",
                            ),
                            dbc.Badge(
                                f"BL {bl[get_concept_id(c)]:.2f}",
                                color="success",
                                className="ms-1",
                            ),
                        ],
                        className="position-absolute top-0 end-0",
                    ),
                ]
            )
            for c in concepts
        ],
        id=id,
    )

    return layout


navbar = dbc.NavbarSimple(
    brand="Kaggle Questions Dataset",
    brand_href="/",
    color="dark",
    dark=True,
    fluid=True,
)

min_extent_size = len(min(context.lattice, key=lambda c: len(c.extent)).extent)
max_extent_size = len(max(context.lattice, key=lambda c: len(c.extent)).extent)

concepts = dbc.Col(
    html.Div(
        [
            dbc.Row(
                [
                    html.H2("Concepts"),
                    dcc.Dropdown(
                        id="intent-dropdown",
                        options=[
                            {"label": f"{label} ({count})", "value": label}
                            for label, count in attributes.iteritems()
                        ],
                        multi=True,
                    ),
                    dcc.RangeSlider(
                        id="concept-size-slider",
                        min=min_extent_size,
                        max=max_extent_size,
                        step=1,
                        value=[min_extent_size, max_extent_size],
                        allowCross=False,
                        tooltip={"placement": "bottom", "always_visible": False},
                    ),
                ],
                className="pt-3 pb-2",
            ),
            dbc.Row(
                className="flex-grow-1 overflow-auto full-height-fix", id="concepts"
            ),
        ],
        className="h-100 d-flex flex-column",
    ),
    width=2,
    id="keywords-col",
    className="border-right",
)

detail = dbc.Col(id="detail", width=2, className="border-right")

navigation = dbc.Col(id="navigation", width=2, className="border-right")

questions = dbc.Col(id="questions", className="border-right")


app.layout = html.Div(
    [
        dcc.Location(id="url", refresh=False),
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


def concept_links_detail(concepts, intent=[], sign="", id="", className=""):
    if sign == "+":
        sign_badge = dbc.Badge(
            "+", color="success", className="position-absolute top-0 start-0 h-100"
        )
    else:
        sign_badge = dbc.Badge(
            "-", color="danger", className="position-absolute top-0 start-0 h-100"
        )

    concepts = sorted(concepts, key=lambda c: bl[get_concept_id(c)], reverse=True)

    layout = dbc.Row(
        html.Ul(
            [
                html.Li(
                    [
                        sign_badge,
                        dcc.Link(
                            f"{', '.join(set(c.intent).symmetric_difference(set(intent)))}",
                            href=f"{get_concept_id(c)}",
                            className="link-primary",
                        ),
                        html.Span(
                            [
                                dbc.Badge(
                                    f"{len(c.extent)}",
                                    color="primary",
                                ),
                                dbc.Badge(
                                    f"BL {bl[get_concept_id(c)]:.2f}",
                                    color="success",
                                    className="ms-1",
                                ),
                            ],
                            className="position-absolute top-0 end-0",
                        ),
                    ],
                    className="sign",
                )
                for c in concepts
            ],
            id=id,
            className=className,
        )
    )

    return layout


@app.callback(
    Output("intent-dropdown", "options"),
    Input("intent-dropdown", "value"),
    Input("concept-size-slider", "value"),
)
def update_intent_dropdown(values, slider):
    min_, max_ = slider
    if values:
        concepts = filter_concept_list(
            context.lattice.downset_union([context.lattice[values]]),
            context,
            min_,
            max_,
        )

        filtered_intents = []

        for concept in concepts:
            filtered_intents.extend(concept.intent)

        filtered_intents = set(filtered_intents)

        return [
            {"label": f"{label} ({count})", "value": label}
            for label, count in attributes.iteritems()
            if label in filtered_intents
        ]

    return [
        {"label": f"{label} ({count})", "value": label}
        for label, count in attributes.iteritems()
    ]


@app.callback(
    Output("concepts", "children"),
    Input("intent-dropdown", "value"),
    Input("concept-size-slider", "value"),
)
def update_output(values, slider):
    min_, max_ = slider
    print(min_, max_)

    if values:
        concepts = filter_concept_list(
            context.lattice.downset_union([context.lattice[values]]),
            context,
            min_,
            max_,
        )

        concept_links(concepts, id="keywords")
    else:
        concepts = filter_concept_list(context.lattice, context, min_, max_)

        return concept_links(concepts, id="keywords", limit=300)


@app.callback(Output("detail", "children"), [Input("url", "pathname")])
def detail(pathname):
    if len(pathname) > 1:
        concept_id = int(pathname.lstrip("/"))
        concept = context.lattice[concept_id]

        shape = (len(concept.extent), len(concept.intent))

        centrality = Centrality(concept, core_indicator=True, axis=1)

        centrality_df = centrality._filter_sort_df(include_core_flag=True)

        return html.Div(
            [
                dbc.Row(
                    [
                        html.Div(
                            [
                                html.H2("Concept detail"),
                                html.Ul(
                                    [
                                        html.Li(
                                            [
                                                html.B("Keywords: "),
                                                f"{', '.join(concept.intent)}",
                                            ]
                                        ),
                                        html.Li([html.B("Shape: "), f"{shape}"]),
                                        html.Li(
                                            [
                                                html.B("Basic level: "),
                                                f"{bl[concept_id]:.2f}",
                                            ]
                                        ),
                                    ]
                                ),
                                html.H3("Related keywords"),
                            ]
                        ),
                    ],
                    className="pt-3 pb-2",
                ),
                dbc.Row(
                    html.Ul(
                        [
                            html.Li(
                                [
                                    keyword,
                                    dbc.Badge(
                                        f"Centrality: {centrality_df.loc[keyword]['Centrality']:.2f}",
                                        color="white",
                                        text_color="muted",
                                        className="position-absolute end-0",
                                    ),
                                ]
                            )
                            for keyword in centrality_df.index
                        ],
                        id="centrality",
                    ),
                    className="flex-grow-1 overflow-auto full-height-fix",
                ),
            ],
            className="h-100 d-flex flex-column",
        )


@app.callback(Output("navigation", "children"), [Input("url", "pathname")])
def navigation(pathname):
    if len(pathname) > 1:
        concept_id = int(pathname.lstrip("/"))
        concept = context.lattice[concept_id]

        upper = concept_links_detail(
            concept.upper_neighbors, concept.intent, "-", className="navigation"
        )
        lower = concept_links_detail(
            concept.lower_neighbors, concept.intent, "+", className="navigation"
        )

        return html.Div(
            [
                dbc.Row(
                    [
                        html.Div(
                            [
                                html.H2("Navigation"),
                                html.H3("More general"),
                                upper,
                                html.H3("More specific"),
                                lower,
                            ]
                        ),
                    ],
                    className="flex-grow-1 overflow-auto full-height-fix pt-3 pb-2",
                ),
            ],
            className="h-100 d-flex flex-column",
        )


@app.callback(Output("questions", "children"), [Input("url", "pathname")])
def questions(pathname):
    if len(pathname) > 1:
        concept_id = int(pathname.lstrip("/"))
        concept = context.lattice[concept_id]

        typicality_functions = {
            "typ_avg": {
                "func": typicality_avg,
                "args": {"J": [similarity_cached]},
            }
        }

        typicality = ConceptTypicality(
            concept,
            typicality_functions=typicality_functions,
            extra_columns={
                "link": df_original["Link"],
                "followers": df_original["Followers"],
                "answered": df_original["Answered"],
            },
        )

        data = typicality.df.rename(columns={"typ_avg(J)": "typ"})

        data = data.sort_values("typ", ascending=False)

        mca = MCAConcept(
            concept, n_components=3, n_iter=5, color_by=["typ", data["typ"]]
        )
        fig = mca.to_plotly()
        fig.update_traces(marker={"size": 7})

        return html.Div(
            [
                dbc.Row(
                    [html.H2("Questions"), dcc.Graph(id="mca_3d", figure=fig)],
                    className="pt-3 pb-2",
                ),
                dbc.Row(
                    [
                        html.Ul(
                            [
                                html.Li(
                                    [
                                        html.A(
                                            question,
                                            href=f"https://quora.com/{metadata['link']}",
                                            target="_blank",
                                        ),
                                        html.Span(
                                            [
                                                dbc.Badge(
                                                    f"Typ: {metadata['typ']:.2f}",
                                                    color="white",
                                                    text_color="muted",
                                                    className="",
                                                ),
                                                dbc.Badge(
                                                    f"Followers: {metadata['followers']}",
                                                    color="white",
                                                    text_color="info",
                                                    className="",
                                                ),
                                                dbc.Badge(
                                                    f"Answered: {metadata['answered']}",
                                                    color="white",
                                                    text_color="success",
                                                    className="",
                                                ),
                                            ],
                                            className="position-absolute bottom-0 end-0 w-100 status-bar",
                                        ),
                                    ]
                                )
                                for question, metadata in data.iterrows()
                            ]
                        ),
                    ],
                    className="flex-grow-1 overflow-auto full-height-fix",
                ),
            ],
            className="h-100 d-flex flex-column",
        )


if __name__ == "__main__":
    app.run_server(debug=True)
