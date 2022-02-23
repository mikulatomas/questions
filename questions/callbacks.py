import dash.html as html
import dash_bootstrap_components as dbc

from functools import cache
from dash.dependencies import Input, Output, State
from dash import dcc

from fcapsy_experiments.mca import MCAConcept
from fcapsy_experiments.centrality import Centrality
from fcapsy_experiments.typicality import ConceptTypicality
from fcapsy.typicality import typicality_avg
from binsdpy.similarity import jaccard

from .components import li_navigation, li_concept, li_question, li_centrality
from .server import app
from .data import (
    dataset_df,
    context,
    basic_levels,
)


@cache
def similarity_cached(x, y, *args, **kwargs):
    return jaccard(x, y, *args, **kwargs)


def filter_concept_list(concepts, context, min_extent_size):
    return (
        concept
        for concept in concepts
        if concept not in [context.lattice.supremum, context.lattice.infimum]
        and len(concept.extent) >= min_extent_size
    )


def get_concept_id(concept):
    return context.lattice._concepts.index(concept)


def navigation_links(concepts, direction, intent=[]):
    concepts = sorted(
        concepts, key=lambda c: basic_levels[get_concept_id(c)], reverse=True
    )

    layout = dbc.Row(
        html.Ul(
            [
                li_navigation(
                    set(c.intent).symmetric_difference(set(intent)),
                    len(c.extent),
                    basic_levels[get_concept_id(c)],
                    get_concept_id(c),
                    direction,
                )
                for c in concepts
            ],
            className="navigation",
        )
    )

    return layout


def concept_links(concepts, intent=[], limit=None):
    concepts = [
        c
        for c in sorted(
            concepts, key=lambda c: basic_levels[get_concept_id(c)], reverse=True
        )
        if c != context.lattice.supremum
    ]

    if limit:
        concepts = concepts[:limit]

    layout = [
        li_concept(
            set(c.intent).symmetric_difference(set(intent)),
            len(c.extent),
            basic_levels[get_concept_id(c)],
            get_concept_id(c),
        )
        for c in concepts
    ]

    return layout


@app.callback(
    Output("concepts", "children"),
    Input("intent-dropdown", "value"),
    Input("concept-size-slider", "value"),
)
def update_concepts(values, slider):
    min_extent_size = slider

    if values:
        concepts = filter_concept_list(
            context.lattice.downset_union([context.lattice[values]]),
            context,
            min_extent_size,
        )

        return concept_links(concepts)
    else:
        concepts = filter_concept_list(context.lattice, context, min_extent_size)

        return concept_links(concepts, limit=300)


@app.callback(
    Output("metadata", "children"),
    Output("centrality", "children"),
    [Input("url", "pathname")],
)
def update_detail(pathname):
    if len(pathname) > 1:
        concept_id = int(pathname.lstrip("/"))
        concept = context.lattice[concept_id]

        shape = (len(concept.extent), len(concept.intent))

        centrality = Centrality(concept, core_indicator=True, axis=1)

        centrality_df = centrality._filter_sort_df(include_core_flag=True)

        metadata = [
            html.Li(
                [
                    "Keywords: ",
                    html.I(f"{', '.join(concept.intent)}"),
                ]
            ),
            html.Li(["Shape: ", html.I(f"{shape}")]),
            html.Li(
                [
                    "Basic level: ",
                    html.I(f"{basic_levels[concept_id]:.2f}"),
                ]
            ),
        ]

        centrality = [
            li_centrality(keyword, centrality_df.loc[keyword]["Centrality"])
            for keyword in centrality_df.index
        ]

        return metadata, centrality

    return ["N/A"], ["N/A"]


@app.callback(
    Output("upper-concepts", "children"),
    Output("lower-concepts", "children"),
    [Input("url", "pathname")],
)
def update_navigation(pathname):
    if len(pathname) > 1:
        concept_id = int(pathname.lstrip("/"))
        concept = context.lattice[concept_id]

        upper = navigation_links(
            concept.upper_neighbors,
            "down",
            concept.intent,
        )
        lower = navigation_links(concept.lower_neighbors, "up", concept.intent)

        return upper, lower

    return ["N/A"], ["N/A"]


@app.callback(
    Output("mca", "children"),
    Output("question-list", "children"),
    [Input("url", "pathname")],
)
def update_questions(pathname):
    if len(pathname) > 1:
        concept_id = int(pathname.lstrip("/"))
        concept = context.lattice[concept_id]

        typicality_functions = {
            "typ_avg": {
                "func": typicality_avg,
                "args": {"J": {"similarity": similarity_cached}},
            }
        }

        typicality = ConceptTypicality(
            concept,
            typicality_functions=typicality_functions,
            extra_columns={
                "link": dataset_df["Link"],
                "followers": dataset_df["Followers"],
                "answered": dataset_df["Answered"],
            },
        )

        data = typicality.df.rename(columns={"typ_avg(J)": "typ"})

        data = data.sort_values("typ", ascending=False)

        if len(concept.extent) > 2:
            mca = MCAConcept(
                concept, n_components=3, n_iter=5, color_by=["typ", data["typ"]]
            )

            fig = mca.to_plotly()
            fig.update_traces(marker={"size": 7})
            mca_plot = [dcc.Graph(id="mca_3d", figure=fig)]
        else:
            mca_plot = []

        questions = [
            li_question(
                question,
                metadata["link"],
                metadata["typ"],
                metadata["followers"],
                metadata["answered"],
            )
            for question, metadata in data.iterrows()
        ]

        return mca_plot, questions

    return None, []


@app.callback(
    Output("info", "is_open"),
    Input("open-offcanvas", "n_clicks"),
    [State("info", "is_open")],
)
def toggle_offcanvas(n1, is_open):
    if n1:
        return not is_open
    return is_open
