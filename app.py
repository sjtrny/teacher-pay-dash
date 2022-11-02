from functools import lru_cache
from urllib.parse import urlencode

import dash
import dash_bootstrap_components as dbc
import flask
import inflect
import numpy as np
import pandas as pd
import plotly.graph_objs as go
from dash import Input, Output, State, ctx, dcc, html
from dash.exceptions import PreventUpdate

from app_util import apply_default_value, dash_kwarg, parse_state
from process_data import *

p = inflect.engine()

data_2021 = process_census_data(
    "data/teacher_pay_2021.csv",
    column_mapping_2021,
    incp_low_mapping_2021,
    incp_high_mapping_2021,
)
data_2021["YEAR"] = 2021

data_2016 = process_census_data(
    "data/teacher_pay_2016.csv",
    column_mapping_2016,
    incp_low_mapping_2016,
    incp_high_mapping_2016,
)
data_2016["YEAR"] = 2016

data_2011 = process_census_data(
    "data/teacher_pay_2011.csv",
    column_mapping_2011,
    incp_low_mapping_2011,
    incp_high_mapping_2011,
)
data_2011["YEAR"] = 2011

data_2006 = process_census_data(
    "data/teacher_pay_2006.csv",
    column_mapping_2006,
    incp_low_mapping_2006,
    incp_high_mapping_2006,
)
data_2006["YEAR"] = 2006

data = pd.concat([data_2021, data_2016, data_2011, data_2006], axis=0)
combinations = data[["OCCP4D", "AGE10P", "STATE", "YEAR"]].drop_duplicates()

states_australia = [
    "All",
    "New South Wales",
    "Victoria",
    "Queensland",
    "Western Australia",
    "South Australia",
    "Tasmania",
    "Australian Capital Territory",
    "Northern Territory",
]

scale_options = {"Annual": 52, "Weekly": 1}

years = pd.Series(combinations["YEAR"].unique()).sort_values(ascending=False)
latest_year = combinations["YEAR"].iloc[0]

occs_latest = data.query(f"YEAR == {latest_year}")["OCCP4D"].unique()

occs_default_selected = [
    "Secondary School Teachers",
    "Primary School Teachers",
]

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "NSW Teacher Pay"
server = app.server

instructions = dbc.Row(
    [
        dbc.Col(
            [
                dcc.Markdown(
                    """
        #### Instructions

        Select occupations and adjust the percentile,
        year, state or scale to your needs.

        The figure will automatically update when any change is made.

        Changing year may result in losing the currently selected
        occupations. This is due to changes in occupational codes
        between census years.

        #### About

        This tool provides relative comparison of income by
        occupation for Australian Full Time Employees.

        Values reported are estimates calculated from INCP (Total Personal Income (weekly))
        from the census using [Von Hippel et al (2017)](https://sociologicalscience.com/download/vol-4/november/SocSci_v4_641to655.pdf).

        #### Sharing or Saving results

        You can share your figure by copying the current URL. Each
        time a change is made the URL will update.

        Alternatively you may download an image of the current plot by
        clicking the Download button.

        #### Definitions

        **Percentile**: The value at which the given percentage of
        employees fall below. For example, the 80th percentile
        represents the income at which 80% of all employees are below.

        **Year**: Census year

        **Scale**: The scale of the vertical axis, which represents income.
        Either weekly or annual.

        **State or Territory**: Which state or territory to estimate
        incomes for. Setting to "All" will give estimates for all
        of Australia.

        """
                )
            ],
            width=6,
        ),
        dbc.Col(
            [
                dcc.Markdown(
                    """
        #### Authors

        1. [Professor John Buchanan](https://www.sydney.edu.au/business/about/our-people/academic-staff/john-buchanan.html) (corresponding author)
        2. Dr Huon Curtis
        3. Ron Callus
        4. [Dr Stephen Tierney](https://www.sydney.edu.au/business/about/our-people/academic-staff/stephen-tierney.html) (statistical analysis, visuals, programming)

        #### Source Code and Data

        https://github.com/sjtrny/teacher_pay_dash

        #### Acknowledgements

        This dashboard was developed as part of the "*NSW Teachers’
        Pay: How it has changed and how it compares*" report.

        This report was prepared for the Commission of Inquiry into
        Work Value of NSW Public School Teachers by the NSW
        Teachers Federation.

        This project was funded by the NSW Teachers’ Federation.
        """
                )
            ],
            width=6,
        ),
    ]
)


def build_layout(params):
    return html.Div(
        [
            dcc.Store(
                id="store_year",
                data=latest_year
                if "dropdown_year" not in params
                else params["dropdown_year"],
            ),
            html.Hr(),
            dbc.Form(
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    dbc.Label("Occupations", style={"font-size": 22}),
                                    apply_default_value(params)(dcc.Dropdown)(
                                        id="checkbox_occupations",
                                        options=[
                                            {"label": x, "value": x}
                                            for x in np.sort(occs_latest)
                                        ],
                                        value=occs_default_selected,
                                        multi=True,
                                    ),
                                ],
                                width=9,
                            ),
                            dbc.Col(
                                [
                                    dbc.Button(
                                        id="button_reset",
                                        children="Reset Occupations",
                                        color="danger",
                                        className="float-right align-text-bottom",
                                        style={"margin-top": "41px"},
                                    )
                                ],
                                width=3,
                            ),
                        ]
                    ),
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    dbc.Label("Percentile", style={"font-size": 22}),
                                    apply_default_value(params)(dcc.Dropdown)(
                                        id="dropdown_percentile",
                                        value=80,
                                        clearable=False,
                                        options=[
                                            {"label": x, "value": x}
                                            for x in np.arange(10, 100, 10)
                                        ],
                                    ),
                                ],
                                width=2,
                            ),
                            dbc.Col(
                                [
                                    dbc.Label("Year", style={"font-size": 22}),
                                    apply_default_value(params)(dcc.Dropdown)(
                                        id="dropdown_year",
                                        value=latest_year,
                                        clearable=False,
                                        options=[
                                            {"label": x, "value": x} for x in years
                                        ],
                                    ),
                                ],
                                width=2,
                            ),
                            dbc.Col(
                                [
                                    dbc.Label("Scale", style={"font-size": 22}),
                                    apply_default_value(params)(dcc.Dropdown)(
                                        id="dropdown_scale",
                                        value=list(scale_options.keys())[0],
                                        clearable=False,
                                        options=[
                                            {"label": x, "value": x}
                                            for x in scale_options.keys()
                                        ],
                                    ),
                                ],
                                width=2,
                            ),
                            dbc.Col(
                                [
                                    dbc.Label(
                                        "State or Territory", style={"font-size": 22}
                                    ),
                                    apply_default_value(params)(dcc.Dropdown)(
                                        id="dropdown_state",
                                        value="All",
                                        clearable=False,
                                        options=[
                                            {"label": x, "value": x}
                                            for x in states_australia
                                        ],
                                    ),
                                ],
                                width=6,
                            ),
                        ]
                    ),
                    dbc.Row(
                        dbc.Col(
                            [
                                dbc.Button(
                                    id="button_download",
                                    children="Download Plot",
                                    # color="danger",
                                    className="float-right align-text-bottom",
                                    style={"margin-top": "41px"},
                                ),
                                dcc.Download(id="download_plot"),
                            ],
                            width=4,
                        )
                    ),
                ]
            ),
        ],
    )


app.layout = html.Div(
    [
        dcc.Location(id="url", refresh=False),
        dcc.ConfirmDialog(
            id="confirm",
            message="Changing years will reset occupation selections to default values. Are you sure you want to continue?",
        ),
        dbc.Container(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                dcc.Graph(
                                    id="graph",
                                    config={
                                        "displayModeBar": False,
                                        "staticPlot": False,
                                        "responsive": True,
                                    },
                                ),
                            ],
                            width=12,
                        )
                    ]
                ),
                html.Div(id="page-layout", children=build_layout([])),
                html.Div(
                    [
                        html.Hr(),
                        instructions,
                    ]
                ),
            ]
        ),
    ]
)


components = [
    ("dropdown_state", "value"),
    ("dropdown_percentile", "value"),
    ("store_year", "data"),
    ("dropdown_scale", "value"),
    ("checkbox_occupations", "value"),
]

graph_inputs = [Input(x[0], x[1]) for x in components]
graph_states = [State(x[0], x[1]) for x in components]


@app.callback(
    Output("page-layout", "children"),
    inputs=[Input("url", "href")],
)
def page_load(href):
    if not href:
        return []
    state = parse_state(href)
    return build_layout(state)


@app.callback(
    Output("url", "search"),
    inputs=graph_inputs,
)
# Add dash kward arg here
@dash_kwarg(graph_inputs)
def update_url_state(**kwargs):
    state = urlencode(kwargs)
    return f"?{state}"


@lru_cache(maxsize=128)
def get_pcntiles(state, year, occupation):
    pcntile_range = np.arange(0, 101, 10).reshape(-1, 1) / 100

    combins = combinations.query(
        f"STATE == '{state}' and OCCP4D == '{occupation}' and YEAR == {year}"
    )
    results = []
    for idx, row in combins.iterrows():
        year = row["YEAR"]
        occ = row["OCCP4D"]
        age_group = row["AGE10P"]
        state = row["STATE"]
        subset = data.query(
            f"OCCP4D == '{occ}' and AGE10P == '{age_group}' and STATE == '{state}' and YEAR == {year}"
        )
        subset = subset.sort_values("INCP_HIGH", ascending=True)

        # If the subset has no observations then fill with 0
        if subset["COUNT"].sum() > 0:
            edges = subset["INCP_HIGH"].values
            counts = subset["COUNT"].values

            # Collapse zeros
            idx = counts != 0
            edges = edges[idx]
            counts = counts[idx]
            edges = np.concatenate(([0], edges))
            counts = np.concatenate(([0], counts))

            bs = BinSmooth()
            bs.fit(
                edges,
                counts,
                includes_tail=True,
            )

            pcntile_vals = bs.inv_cdf(pcntile_range)
        else:
            pcntile_vals = np.full(pcntile_range.shape, 0)

        result = pd.concat(
            [
                pd.Series(
                    (pcntile_range.squeeze() * 100).astype(int), name="PERCENTILE"
                ),
                pd.Series(pcntile_vals.squeeze().round(4), name="PERCENTILE_VALUE"),
            ],
            axis=1,
        )

        result["YEAR"] = year
        result["OCCP4D"] = occ
        result["AGE10P"] = age_group
        result["STATE"] = state

        results.append(result)

    return pd.concat(results, axis=0)


def figure_dict(state, percentile, year, scale, occupations):
    plot_list = []
    occs = np.sort(occupations)

    for occ in occs:

        line_data = (
            get_pcntiles(state, year, occ)
            .query(f"PERCENTILE == {percentile}")
            .sort_values("AGE10P")
        )

        plot_list.append(
            go.Scatter(
                x=line_data["AGE10P"],
                y=line_data["PERCENTILE_VALUE"] * scale_options[scale],
                name=occ,
            )
        )

    layout = go.Layout(
        height=800,
        title=dict(
            text=f"Estimated {scale} Income of Full Time Employees<br>{year} - {p.ordinal(percentile)} Percentile",
            font_size=24,
        ),
        yaxis={
            "title": f"{scale} Income (Estimated)",
            "title_font_size": 18,
            "fixedrange": True,
        },
        xaxis={"fixedrange": True},
        legend=dict(
            orientation="h",
            title_text="Occupation",
            title_side="top",
            title_font_size=18,
            font_size=16,
        ),
    )

    return {"data": plot_list, "layout": layout}


@app.callback(
    Output(component_id="graph", component_property="figure"),
    inputs=graph_inputs,
)
def update_graph(*args):
    return figure_dict(*args)


@app.callback(
    output=[
        Output("confirm", "displayed"),
        Output("confirm", "message"),
        Output(component_id="checkbox_occupations", component_property="options"),
        Output(component_id="checkbox_occupations", component_property="value"),
        Output(component_id="store_year", component_property="data"),
    ],
    inputs=[
        Input("dropdown_year", "value"),
        Input("confirm", "submit_n_clicks"),
        Input("button_reset", "n_clicks"),
    ],
    state=[State("store_year", "data"), State("checkbox_occupations", "value")],
    prevent_initial_call=True,
)
@dash_kwarg(
    [
        Input("dropdown_year", "value"),
        Input("confirm", "submit_n_clicks"),
        Input("button_reset", "n_clicks"),
        State("store_year", "value"),
        State("checkbox_occupations", "value"),
    ]
)
def year_change(**kwargs):
    ctx = dash.callback_context

    if ctx.triggered:

        changed_id = ctx.triggered[0]["prop_id"].split(".")[0]

        # First the year dropdown gets changed
        if changed_id == "dropdown_year":
            if kwargs["dropdown_year"] != kwargs["store_year"]:

                # Check if changing years will cause issues with occupations
                occs_selected_set = set(kwargs["checkbox_occupations"])
                occs_year_set = set(
                    combinations.query(f"YEAR == {kwargs['dropdown_year']}")[
                        "OCCP4D"
                    ].unique()
                )

                if occs_selected_set.issubset(occs_year_set):
                    occupations = combinations.query(
                        f"YEAR == {kwargs['dropdown_year']}"
                    )["OCCP4D"].unique()

                    return (
                        False,
                        "",
                        [{"label": x, "value": x} for x in np.sort(occupations)],
                        kwargs["checkbox_occupations"],
                        kwargs["dropdown_year"],
                    )

                occupations = combinations.query(f"YEAR == {kwargs['store_year']}")[
                    "OCCP4D"
                ].unique()

                message = f"The currently selected occupations are not available for {kwargs['dropdown_year']}.\n\n Changing years will reset occupation selections to default values. Are you sure you want to continue?"

                return (
                    True,
                    message,
                    [{"label": x, "value": x} for x in np.sort(occupations)],
                    kwargs["checkbox_occupations"],
                    kwargs["store_year"],
                )

        elif changed_id == "confirm" or changed_id == "button_reset":
            occupations = combinations.query(f"YEAR == {kwargs['dropdown_year']}")[
                "OCCP4D"
            ].unique()
            return (
                False,
                "",
                [{"label": x, "value": x} for x in np.sort(occupations)],
                occs_default_selected,
                kwargs["dropdown_year"],
            )

    raise PreventUpdate


@app.callback(
    output=Output(component_id="dropdown_year", component_property="value"),
    inputs=[Input("confirm", "cancel_n_clicks")],
    state=[State("store_year", "data")],
    prevent_initial_call=True,
)
@dash_kwarg([Input("confirm", "cancel_n_clicks")] + [State("store_year", "data")])
def year_cancel(**kwargs):
    return kwargs["store_year"]


@app.callback(
    *(
        [Output("download_plot", "data"), Input("button_download", "n_clicks")]
        + graph_states
    ),
    prevent_initial_call=True,
)
def download_plot(button_nclicks, *args):

    fig = figure_dict(*args)

    w, h = 800, 600
    format = "png"

    img_bytes = go.Figure(fig).to_image(
        format=format,
        width=w,
        height=h,
        scale=1,
    )

    return dcc.send_bytes(img_bytes, filename="download.png")


if __name__ == "__main__":
    app.run_server(debug=True)
