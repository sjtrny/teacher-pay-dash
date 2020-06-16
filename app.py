import ast
import io
from urllib.parse import urlencode
from shutil import which

import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import flask
import inflect
import numpy as np
import pandas as pd
import plotly.graph_objs as go
from dash.dependencies import Input, Output

from dash_util import parse_state, apply_default_value, dash_kwarg

import chart_studio
from chart_studio.plotly import image

chart_studio.tools.set_credentials_file(username='sjtrny', api_key='ElnyL3o3mKjqV61xlSHV')

p = inflect.engine()

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server
# from util import get_percentiles

# clean_data = pd.read_csv("../CLEAN_DATA.csv")
# pcnt_data = get_percentiles(clean_data)

pcnt_data = pd.read_csv("percentiles.csv")

# default_occs = [
#     'Accountants',
#     'Primary School Teachers',
#     'Secondary School Teachers',
#     'Medical Practitioners',
#     'Solicitors',
#     'Police Bachelor',
#     'Police assoc. diploma',
#     'Registered Nurses',
# ]

resolutions = [
    [1920, 1080],
    [2560, 1440],
    [3840, 2160],
    [5120, 2880],
    [7680, 4320],
    [19200, 10800],
]

resolution_dict = {r[0]: r for r in resolutions}

resolution_options = [
    {"label": f"{res[0]} x {res[1]}", "value": res[0]} for res in resolutions
]

scale_options = {
    'Annual': 52,
    'Weekly': 1
}

orca_available = True if which("orca") else False

def build_layout(params):

    return html.Div([
        dbc.Row([
            dbc.Col([
                apply_default_value(params)(dcc.Dropdown)(
                    id="download-resolution",
                    options=resolution_options,
                    value=1920,
                ),
            ], width=2),
            dbc.Col([
                apply_default_value(params)(dcc.Dropdown)(
                    id="download-format",
                    options=[
                        {"label": "PDF", "value": "pdf"},
                        {"label": "PNG", "value": "png"},
                    ] if orca_available else [
                        {"label": "PNG", "value": "png"},
                    ],
                    value="png"
                ),
            ], width=2),
            dbc.Col([
                html.A(
                    id="download-button",
                    children=dbc.Button("Download Plot"),
                    href="#",
                    style={"fontSize": 18},
                ),
            ], width=2)
        ]),
        html.Hr(),
        dbc.Row([
            dbc.Col([
                dbc.Form([
                    dbc.FormGroup([
                        dbc.Label("Percentile"),
                        apply_default_value(params)(dcc.Dropdown)(id='dropdown_percentile', value=80, clearable=False,
                                     options=[{"label": x, "value": x} for x in pcnt_data['PERCENTILE'].unique()]),
                    ]),
                    dbc.FormGroup([
                        dbc.Label("Year"),
                        apply_default_value(params)(dcc.Dropdown)(id='dropdown_year', value=pcnt_data['YEAR'].unique()[0], clearable=False,
                                     options=[{"label": x, "value": x} for x in pcnt_data['YEAR'].unique()]),
                    ]),
                    dbc.FormGroup([
                        dbc.Label("Scale"),
                        apply_default_value(params)(dcc.Dropdown)(id='dropdown_scale', value=list(scale_options.keys())[0], clearable=False,
                                     options=[{"label": x, "value": x} for x in scale_options.keys()]),
                    ]),
                    dbc.FormGroup([
                        dbc.Label("Occupations"),
                        apply_default_value(params)(dbc.Checklist)(id='checkbox_occupations',
                               options=[{"label": x, "value": x} for x in
                                        np.sort(pcnt_data['OCCUPATION'].unique())],
                               value=np.sort(pcnt_data['OCCUPATION'].unique()),
                               ),
                    ])
                ])
            ], width=4),
            dbc.Col(id="table", width=8),
        ]),
    ])

app.layout = html.Div([
    dcc.Location(id="url", refresh=False),
    dbc.Container([
        dbc.Row([
            dbc.Col([
                dcc.Graph(id='graph'),

            ], width=12)
        ]),
        html.Div(id="page-layout", children=build_layout([])),
    ])

])

component_ids = [
    "dropdown_percentile",
    "dropdown_year",
    "dropdown_scale",
    "checkbox_occupations",
    "download-resolution",
    "download-format",
]

graph_inputs = [
    "dropdown_percentile",
    "dropdown_year",
    "dropdown_scale",
    "checkbox_occupations",
]

@app.callback(
    Output("page-layout", "children"), inputs=[Input("url", "href")],
)
def page_load(href):
    if not href:
        return []
    state = parse_state(href)
    return build_layout(state)

@app.callback(
    Output("url", "search"),
    inputs=[Input(i, "value") for i in component_ids],
)
def update_url_state(*values):
    state = urlencode(dict(zip(component_ids, values)))
    return f"?{state}"

def figure_dict(percentile, year, scale, occupations):

    plot_list = []

    occs = np.sort(occupations)

    for occ in occs:
        line_data = pcnt_data.query(f"PERCENTILE == {percentile} and OCCUPATION == '{occ}' and YEAR == {year}").sort_values("AGE_GROUP")

        plot_list.append(
            go.Scatter(
                x=line_data['AGE_GROUP'],
                y=line_data['PERCENTILE_VALUE'] * scale_options[scale],
                name=occ
            )
        )

    layout = go.Layout(
        height=800,
        # title=f"{year} Estimate of Annual Income of {p.ordinal(percentile)} Percentile<br> Full Time Workers in Occupations Holding Bachelor Degrees",
        title=f"{year} Estimate of Annual Income of {p.ordinal(percentile)} Percentile",
        yaxis={'title': f"{scale} Income"},
        xaxis={'title': "Age Group (AGE10P)"}
    )

    return {
        "data": plot_list,
        "layout": layout
    }

@app.callback(
    Output(component_id='graph', component_property='figure'),
    inputs=[Input(i, "value") for i in graph_inputs],
)
def update_graph(*args):
    return figure_dict(*args)

@app.callback(
    Output(component_id='table', component_property='children'),
    inputs=[Input(i, "value") for i in graph_inputs],
)
@dash_kwarg([Input(i, "value") for i in graph_inputs])
def update_table(**kwargs):

    occs = np.sort(kwargs['checkbox_occupations'])

    lines = []

    for occ in occs:
        line_data = pcnt_data.query(f"PERCENTILE == {kwargs['dropdown_percentile']} and OCCUPATION == '{occ}' and YEAR == {kwargs['dropdown_year']}").sort_values("AGE_GROUP")
        lines.append(line_data)

    final_data = pd.concat(lines, axis=0)

    return dbc.Table.from_dataframe(final_data.round(2))


@app.callback(
    Output(component_id="download-button", component_property="href"),
    [Input(i, "value") for i in component_ids],
)
def set_download_link(*values):
    state = urlencode(dict(zip(component_ids, values)))
    return f"download/?{state}"

@app.server.route(
        f"/download/",
        endpoint=f"serve_figure",
)
def serve_figure():

    inputs = []
    for x in component_ids:
        original = flask.request.args[x]

        try:
            val = ast.literal_eval(original)
        except Exception:
            val = original

        inputs.append(val)

    input_dict = dict(zip(component_ids, inputs))

    fig_dict = figure_dict(
        *[v for k, v in input_dict.items() if k in graph_inputs]
    )

    w, h = resolution_dict[input_dict["download-resolution"]]

    if orca_available:
        img_bytes = go.Figure(fig_dict).to_image(
            format=input_dict["download-format"], width=w, height=h
        )
    else:
        img_bytes = image.get(fig_dict, format = input_dict["download-format"], width = w, height = h)

    mem = io.BytesIO()
    mem.write(img_bytes)
    mem.seek(0)

    return flask.send_file(
        mem,
        attachment_filename=f"plot.{input_dict['download-format']}",
        as_attachment=True,
        cache_timeout=0,
    )


if __name__ == '__main__':
    app.run_server(debug=True)