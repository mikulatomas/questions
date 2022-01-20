import pathlib
from pydoc import classname
import dash
from dash import dcc
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
import dash.html as html
import pandas as pd
from functools import cache

from concepts import Context
from fcapsy.basic_level import basic_level_avg
from fcapsy.cohesion import cohesion_avg
from binsdpy.similarity import jaccard
from fcapsy.typicality import typicality_avg

from fcapsy_experiments.centrality import Centrality
from fcapsy_experiments.mca import MCAConcept


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

df_original = pd.read_csv(pathlib.Path.cwd() / "data" / "kaggle" / "kaggle.csv")

context = Context.fromjson(pathlib.Path.cwd() / "data" / "kaggle" / "lattice.json")

bl = tuple(map(float, (pathlib.Path.cwd() / "data" / "kaggle" / "basic_level.txt").read_text().split(",")))


def filter_supremum_infimum(concepts, context):
    return (
        concept
        for concept in concepts
        if concept not in [context.lattice.supremum, context.lattice.infimum]
    )


def get_concept_id(concept):
    return context.lattice._concepts.index(concept)

def concept_links(concepts, intent=[], id="", limit=None):
    # concepts = sorted(concepts, key=lambda c: bl[get_concept_id(c)], reverse=True)
    concepts = [c for c in sorted(concepts, key=lambda c: len(c.extent), reverse=True) if c != context.lattice.supremum]

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

concept_links_all = concept_links(context.lattice, id="keywords", limit=300)

navbar = dbc.NavbarSimple(
    brand="Kaggle Questions Dataset",
    brand_href="/",
    color="dark",
    dark=True,
    fluid=True,
)

keywords = dbc.Col(
    html.Div(
        [
            dbc.Row(
                [
                    html.H2(children="Keywords"),
                    dcc.Dropdown(
                        id="intent-dropdown",
                        options=[
                            {"label": f"{label} ({count})", "value": label}
                            for label, count in attributes.iteritems()
                        ],
                        multi=True,
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
    className="border-right"
)

# right = dbc.Col(
#     dbc.Row(
#         [html.H2(children="Selected concept"), html.Div(id="concept-detail")],
#         className="pt-3 pb-3",
#     )
# )

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
                    [keywords, questions, detail, navigation], className="flex-grow-1"
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
    elif sign == "-":
        sign_badge = dbc.Badge(
            "-", color="danger", className="position-absolute top-0 start-0 h-100"
        )
    else:
        sign_badge = ""

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


@app.callback(Output("intent-dropdown", "options"), Input("intent-dropdown", "value"))
def update_intent_dropdown(values):
    if values:
        concepts = filter_supremum_infimum(
            context.lattice.downset_union([context.lattice[values]]), context
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


@app.callback(Output("concepts", "children"), Input("intent-dropdown", "value"))
def update_output(values):
    if values:
        concepts = filter_supremum_infimum(
            context.lattice.downset_union([context.lattice[values]]), context
        )

        return concept_links(concepts, id="keywords")
    else:
        return concept_links_all


@app.callback(Output("detail", "children"), [Input("url", "pathname")])
def detail(pathname):
    if len(pathname) > 1:
        concept_id = int(pathname.lstrip("/"))
        concept = context.lattice[concept_id]

        shape = (len(concept.extent), len(concept.intent))

        centrality = Centrality(concept, core_indicator=True, axis=1)

        centrality_df = centrality._filter_sort_df(include_core_flag=True)
        # centrality_df = centrality_df.loc[centrality_df["is core"] == 0]

        return html.Div(
            [
                dbc.Row(
                    [
                        html.Div(
                            [
                                html.H2("Concept detail"),
                                # html.H3("Metadata"),
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
                                            [html.B("Basic level: "), f"{bl[concept_id]}"]
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
                                ], id="centrality"
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

        questions = df_original.iloc[list(concept.extent)]

        typicality = [
            typicality_avg(item, concept, similarity_cached) for item in concept.extent
        ]

        data = [
            (row["Questions"], row["Link"], row["Followers"], row["Answered"], typ)
            for typ, (_, row) in zip(typicality, questions.iterrows())
        ]

        data = sorted(data, key=lambda x: x[4], reverse=True)

        return html.Div(
            [
                dbc.Row(
                    [
                        html.H2("Questions"),
                    ],
                    className="pt-3 pb-2",
                ),
                dbc.Row(
                    [
                        html.Ul(
                            [
                                html.Li(
                                    [
                                        html.A(
                                            row[0],
                                            href=f"https://quora.com/{row[1]}",
                                            target="_blank",
                                        ),
                                        html.Span(
                                            [
                                                dbc.Badge(
                                                    f"Typ: {row[4]:.2f}",
                                                    color="white",
                                                    text_color="muted",
                                                    className="",
                                                ),
                                                dbc.Badge(
                                                    f"Follow: {row[2]}",
                                                    color="white",
                                                    text_color="info",
                                                    className="",
                                                ),
                                                dbc.Badge(
                                                    f"Answers: {row[3]}",
                                                    color="white",
                                                    text_color="success",
                                                    className="",
                                                ),
                                            ],
                                            className="position-absolute bottom-0 end-0 w-100 status-bar",
                                        ),
                                    ]
                                )
                                for row in data
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
