import dash.html as html
import dash_bootstrap_components as dbc
from dash import dcc


def li_navigation(intent, question_count, basic_level, detail_href, direction="up"):
    if direction == "up":
        text = "+"
        color = "success"
    elif direction == "down":
        text = "-"
        color = "danger"
    else:
        raise ValueError(
            f"Direction {direction} is not supported, only up and down is supported."
        )

    badge = dbc.Badge(
        text, color=color, className="position-absolute top-0 start-0 h-100"
    )

    layout = html.Li(
        [
            badge,
            dcc.Link(
                f"{', '.join(intent)}",
                href=f"{detail_href}",
                className="link-primary",
            ),
            html.Span(
                [
                    dbc.Badge(
                        f"{question_count}",
                        color="primary",
                    ),
                    dbc.Badge(
                        f"BL {basic_level:.2f}",
                        color="success",
                        className="ms-1",
                    ),
                ],
                className="position-absolute top-0 end-0",
            ),
        ],
        className="sign",
    )

    return layout


def li_concept(intent, question_count, basic_level, detail_href):
    layout = html.Li(
        [
            dcc.Link(
                f"{', '.join(intent)}",
                href=f"{detail_href}",
                className="link-primary",
            ),
            html.Span(
                [
                    dbc.Badge(
                        f"{question_count}",
                        color="primary",
                    ),
                    dbc.Badge(
                        f"BL {basic_level:.2f}",
                        color="success",
                        className="ms-1",
                    ),
                ],
                className="position-absolute top-0 end-0",
            ),
        ]
    )

    return layout


def li_question(text, href, typ, followers, answered):
    layout = html.Li(
        [
            html.A(
                text,
                href=f"https://quora.com/{href}",
                target="_blank",
            ),
            html.Span(
                [
                    dbc.Badge(
                        f"Typ: {typ:.2f}",
                        color="white",
                        text_color="muted",
                    ),
                    dbc.Badge(
                        f"Followers: {followers}",
                        color="white",
                        text_color="info",
                    ),
                    dbc.Badge(
                        f"Answered: {answered}",
                        color="white",
                        text_color="success",
                    ),
                ],
                className="position-absolute bottom-0 end-0 w-100 status-bar",
            ),
        ]
    )

    return layout


def li_centrality(attribute, centrality):
    layout = html.Li(
        [
            attribute,
            dbc.Badge(
                f"Centrality: {centrality:.2f}",
                color="white",
                text_color="muted",
                className="position-absolute end-0",
            ),
        ]
    )

    return layout
