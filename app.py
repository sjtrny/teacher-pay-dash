import ast
import io
import itertools
from shutil import which
from urllib.parse import urlencode

import chart_studio
import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import flask
import inflect
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd
import plotly.graph_objs as go
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

from dash_util import parse_state, apply_default_value, dash_kwarg

chart_studio.tools.set_credentials_file(username='sjtrny', api_key='ElnyL3o3mKjqV61xlSHV')

p = inflect.engine()

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "NSW Teacher Pay"
server = app.server

pcnt_data = pd.read_csv("data/percentiles.csv")

scale_options = {
    'Annual': 52,
    'Weekly': 1
}

occs_2016 = pcnt_data.query("YEAR == 2016")['OCCP4D'].unique()

occs_default_selected = [
    'Secondary School Teachers',
    'Primary School Teachers',
    # 'Accountants',
    # 'Solicitors',
    # 'Police',
    # 'Management and Organisation Analysts',
    # 'Registered Nurses'
]

orca_available = True if which("orca") else False


def build_layout(params):
    return html.Div([
        dcc.Store(id='store_year', data=2016 if 'dropdown_year' not in params else params['dropdown_year']),
        dcc.ConfirmDialog(
            id='confirm',
            message='Changing years will reset occupation selections to default values. Are you sure you want to continue?',
        ),
        html.Hr(),
        dbc.Row([
            dbc.Col([
                html.A(
                    id="download-button",
                    children=dbc.Button("Download", color='primary'),
                    href="#",
                    style={"fontSize": 18},
                ),
            ], width={'size': 2, 'offset': 10})
        ]),
        html.Hr(),
        dbc.Row([
            dbc.Col([
                dbc.Form([
                    dbc.FormGroup([
                        dbc.Label("State"),
                        apply_default_value(params)(dcc.Dropdown)(id='dropdown_state', value="Total", clearable=False,
                                                                  options=[{"label": x, "value": x} for x in
                                                                           pcnt_data['STATE'].unique()]),
                    ]),

                    dbc.FormGroup([
                        dbc.Label("Percentile"),
                        apply_default_value(params)(dcc.Dropdown)(id='dropdown_percentile', value=80, clearable=False,
                                                                  options=[{"label": x, "value": x} for x in
                                                                           pcnt_data['PERCENTILE'].unique()]),
                    ]),
                    dbc.FormGroup([
                        dbc.Label("Scale"),
                        apply_default_value(params)(dcc.Dropdown)(id='dropdown_scale',
                                                                  value=list(scale_options.keys())[0], clearable=False,
                                                                  options=[{"label": x, "value": x} for x in
                                                                           scale_options.keys()]),
                    ]),
                    dbc.FormGroup([
                        dbc.Label("Year"),
                        apply_default_value(params)(dcc.Dropdown)(id='dropdown_year',
                                                                  value=pcnt_data['YEAR'].unique()[0], clearable=False,
                                                                  options=[{"label": x, "value": x} for x in
                                                                           pcnt_data['YEAR'].unique()]),
                    ]),
                    dbc.FormGroup([
                        dbc.Label("Occupations"),
                        dbc.Button(id="button_clear", children="Clear Occupations", color='danger', size='sm', block=True, style={'margin-bottom': '8px'}),
                        apply_default_value(params)(dbc.Checklist)(id='checkbox_occupations',
                                                                   options=[{"label": x, "value": x} for x in
                                                                            np.sort(occs_2016)],
                                                                   value=occs_default_selected,
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

components = [
    Input("dropdown_state", "value"),
    Input("dropdown_percentile", "value"),
    Input("store_year", "data"),
    Input("dropdown_scale", "value"),
    Input("checkbox_occupations", "value"),
]

graph_inputs = [
    Input("dropdown_state", "value"),
    Input("dropdown_percentile", "value"),
    Input("store_year", "data"),
    Input("dropdown_scale", "value"),
    Input("checkbox_occupations", "value"),
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
    inputs=components,
)
# Add dash kward arg here
@dash_kwarg(components)
def update_url_state(**kwargs):
    state = urlencode(kwargs)
    return f"?{state}"


def figure_dict(state, percentile, year, scale, occupations):
    plot_list = []

    occs = np.sort(occupations)

    for occ in occs:
        line_data = pcnt_data.query(f"STATE == '{state}' and PERCENTILE == {percentile} and OCCP4D == '{occ}' and YEAR == {year}").sort_values(
            "AGE10P")

        plot_list.append(
            go.Scatter(
                x=line_data['AGE10P'],
                y=line_data['PERCENTILE_VALUE'] * scale_options[scale],
                name=occ
            )
        )

    layout = go.Layout(
        height=800,
        # title=f"{year} Estimate of Annual Income of {p.ordinal(percentile)} Percentile<br> Full Time Workers in Occupations Holding Bachelor Degrees",
        title=f"Estimated {scale} Income of Full Time Employees<br>{year} - {p.ordinal(percentile)} Percentile",
        yaxis={'title': f"{scale} Income (Estimated)"},
        xaxis={'title': "Age Group (AGE10P)"},
        showlegend=True,
        legend_title_text="Occupation (4-digit)"
    )

    return {
        "data": plot_list,
        "layout": layout
    }


@app.callback(
    Output(component_id='graph', component_property='figure'),
    inputs=graph_inputs,
)
def update_graph(*args):
    return figure_dict(*args)

@app.callback(
    output=[
        Output('confirm', 'displayed'),
        Output('confirm', 'message'),
        Output(component_id='checkbox_occupations', component_property='options'),
        Output(component_id='checkbox_occupations', component_property='value'),
        Output(component_id='store_year', component_property='data')
    ],
    inputs=[
        Input('dropdown_year', 'value'),
        Input('confirm', "submit_n_clicks"),
        Input('button_clear', "n_clicks"),
    ],
    state=[
        State('store_year', 'data'),
        State('checkbox_occupations', 'value')
    ],
    prevent_initial_call=True
)
@dash_kwarg(
    [
        Input('dropdown_year', 'value'),
        Input('confirm', "submit_n_clicks"),
        Input('button_clear', "n_clicks"),
        State('store_year', 'value'),
        State('checkbox_occupations', 'value')
    ]
)
def year_change(**kwargs):

    ctx = dash.callback_context

    if ctx.triggered:

        changed_id = ctx.triggered[0]['prop_id'].split('.')[0]

        # First the year dropdown gets changed
        if changed_id == 'dropdown_year':
            if kwargs['dropdown_year'] != kwargs['store_year']:

                # Check if changing years will cause issues with occupations
                occs_selected_set = set(kwargs['checkbox_occupations'])
                occs_year_set = set(pcnt_data.query(f"YEAR == {kwargs['dropdown_year']}")['OCCP4D'].unique())

                if occs_selected_set.issubset(occs_year_set):

                    occupations = pcnt_data.query(f"YEAR == {kwargs['dropdown_year']}")['OCCP4D'].unique()

                    return False, "", [{"label": x, "value": x} for x in np.sort(occupations)], kwargs['checkbox_occupations'], kwargs['dropdown_year']

                occupations = pcnt_data.query(f"YEAR == {kwargs['store_year']}")['OCCP4D'].unique()

                return True, "Changing years will reset occupation selections to default values. Are you sure you want to continue?", \
                        [{"label": x, "value": x} for x in np.sort(occupations)], kwargs['checkbox_occupations'], kwargs[
                            'store_year']

        elif changed_id == 'confirm':
            occupations = pcnt_data.query(f"YEAR == {kwargs['dropdown_year']}")['OCCP4D'].unique()
            return False, "", [{"label": x, "value": x} for x in np.sort(occupations)], occs_default_selected, kwargs['dropdown_year']
        elif changed_id == 'button_clear':
            occupations = pcnt_data.query(f"YEAR == {kwargs['dropdown_year']}")['OCCP4D'].unique()
            return False, "", [{"label": x, "value": x} for x in np.sort(occupations)], [], kwargs['dropdown_year']

    raise PreventUpdate


@app.callback(
    output=Output(component_id='dropdown_year', component_property='value'),
    inputs=[Input('confirm', "cancel_n_clicks")],
    state=[State('store_year', 'data')],
    prevent_initial_call=True
)
@dash_kwarg([Input('confirm', "cancel_n_clicks")] + [State('store_year', 'data')])
def year_cancel(**kwargs):
    return kwargs['store_year']

@app.callback(
    Output(component_id='table', component_property='children'),
    inputs=graph_inputs,
)
@dash_kwarg(graph_inputs)
def update_table(**kwargs):
    occs = np.sort(kwargs['checkbox_occupations'])

    if len(occs) > 0:

        lines = []

        for occ in occs:
            line_data = pcnt_data.query(
                f"STATE == '{kwargs['dropdown_state']}' and PERCENTILE == {kwargs['dropdown_percentile']} and OCCP4D == '{occ}' and YEAR == {kwargs['store_year']}").sort_values(
                "AGE10P")
            lines.append(line_data)

        final_data = pd.concat(lines, axis=0)

        final_data = final_data.rename(columns={
            'PERCENTILE': 'Percentile',
            'PERCENTILE_VALUE': 'Income',
            'YEAR': 'Year',
            'OCCP4D': 'Occupation',
            'AGE10P': 'Age',
            'STATE': 'State'
        })

        final_data = final_data[[
            "Income",
            "Age",
            "Occupation",
            "State",
            "Year",
            "Percentile"
        ]]

        return dbc.Table.from_dataframe(final_data.round(2))

    return dbc.Table.from_dataframe(pd.DataFrame())


@app.callback(
    Output(component_id="download-button", component_property="href"),
    components,
)
@dash_kwarg(components)
def set_download_link(**kwargs):
    state = urlencode(kwargs)
    return f"download/?{state}"


def matplot_figure(state, percentile, year, scale, occupations):
    marker = itertools.cycle((',', '+', '.', 'o', '*'))

    fig = plt.figure(figsize=(12, 7), dpi=300)
    ax = plt.gca()

    for occ in occupations:
        line_data = pcnt_data.query(f"STATE == '{state}' and PERCENTILE == {percentile} and OCCP4D == '{occ}' and YEAR == {year}") \
            .sort_values("AGE10P")

        plt.plot(
            line_data['AGE10P'],
            line_data['PERCENTILE_VALUE'] * scale_options[scale],
            marker=next(marker),
            label=occ
        )

    tick = mtick.StrMethodFormatter('${x:,.0f}')
    ax.yaxis.set_major_formatter(tick)

    plt.legend(
        loc='upper center',
        bbox_to_anchor=(0.5, -0.1),
        fontsize=6,
        frameon=False,
        ncol=4
    )

    ax.set_ylabel(f"{scale} Income (Estimated)", fontsize=7, rotation=0, ha='left')
    ax.yaxis.set_label_coords(-0.13, 1.02)

    # remove left/right margin
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)

    ax.tick_params(axis=u'y', which=u'both', length=0)

    plt.grid(which='major', axis='y')

    return fig


@app.server.route(
    f"/download/",
    endpoint=f"serve_figure",
)
def serve_figure():
    inputs = []

    component_ids = [x.component_id for x in components]
    graph_input_ids = [x.component_id for x in graph_inputs]

    for x in component_ids:
        original = flask.request.args[x]

        try:
            val = ast.literal_eval(original)
        except Exception:
            val = original

        inputs.append(val)

    input_dict = dict(zip(component_ids, inputs))

    fig = matplot_figure(
        *[v for k, v in input_dict.items() if k in graph_input_ids]
    )

    mem = io.BytesIO()

    fig.savefig(mem, format='pdf', dpi=300, bbox_inches="tight")
    mem.seek(0)

    return flask.send_file(
        mem,
        attachment_filename=f"plot.pdf",
        as_attachment=True,
        cache_timeout=0,
    )


if __name__ == '__main__':
    app.run_server(debug=True)
