import ast
import io
from shutil import which
from urllib.parse import urlencode

import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import flask
import inflect
import numpy as np
import pandas as pd
import plotly.graph_objs as go
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

from dash_util import parse_state, apply_default_value, dash_kwarg

p = inflect.engine()

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "NSW Teacher Pay"
server = app.server

pcnt_data = pd.read_csv("data/percentiles.csv")

pcnt_data.loc[pcnt_data['STATE'] == "Total", 'STATE'] = "All"

states_australia = [
    'All',
    'New South Wales',
    'Victoria',
    'Queensland',
    'Western Australia',
    'South Australia',
    'Tasmania',
    'Australian Capital Territory',
    'Northern Territory',
]

scale_options = {
    'Annual': 52,
    'Weekly': 1
}

occs_2016 = pcnt_data.query("YEAR == 2016")['OCCP4D'].unique()

occs_default_selected = [
    'Secondary School Teachers',
    'Primary School Teachers',
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
        dbc.Form([
            dbc.Row([
                dbc.Col([
                    dbc.FormGroup([
                        dbc.Label("Occupations", style={'font-size': 22}),
                        apply_default_value(params)(dcc.Dropdown)(id='checkbox_occupations',
                                                                  options=[{"label": x, "value": x} for x in
                                                                           np.sort(occs_2016)],
                                                                  value=occs_default_selected,
                                                                  multi=True,
                                                                  ),

                    ]),
                ], width=9),
                dbc.Col([
                    dbc.Button(id="button_reset", children="Reset Occupations", color='danger',
                               className='float-right align-text-bottom', style={'margin-top': '41px'})
                ], width=3),
            ]),
            dbc.Row([
                dbc.Col([
                    dbc.FormGroup([
                        dbc.Label("Percentile", style={'font-size': 22}),
                        apply_default_value(params)(dcc.Dropdown)(id='dropdown_percentile', value=80, clearable=False,
                                                                  options=[{"label": x, "value": x} for x in
                                                                           np.arange(10, 100, 10)]),
                    ])
                ], width=2),
                dbc.Col([
                    dbc.FormGroup([
                        dbc.Label("Year", style={'font-size': 22}),
                        apply_default_value(params)(dcc.Dropdown)(id='dropdown_year',
                                                                  value=pcnt_data['YEAR'].unique()[0], clearable=False,
                                                                  options=[{"label": x, "value": x} for x in
                                                                           pcnt_data['YEAR'].unique()]),
                    ])
                ], width=2),
                dbc.Col([
                    dbc.FormGroup([
                        dbc.Label("Scale", style={'font-size': 22}),
                        apply_default_value(params)(dcc.Dropdown)(id='dropdown_scale',
                                                                  value=list(scale_options.keys())[0], clearable=False,
                                                                  options=[{"label": x, "value": x} for x in
                                                                           scale_options.keys()]),
                    ]),
                ], width=2),
                dbc.Col([
                    dbc.FormGroup([
                        dbc.Label("State or Territory", style={'font-size': 22}),
                        apply_default_value(params)(dcc.Dropdown)(id='dropdown_state', value="All", clearable=False,
                                                                  options=[{"label": x, "value": x} for x in
                                                                           states_australia]),
                    ])
                ], width=6),

            ]),
        ]),
        html.Hr(),
        dbc.Row([
            dbc.Col([
                dcc.Markdown(
                    '''
                    #### About
                    
                    This dashboard was developed as part of the "*NSW Teachers’
                    Pay: How it has changed and how it compares*" report.

                    This report was prepared for the Commission of Inquiry into
                    Work Value of NSW Public School Teachers by the NSW
                    Teachers Federation.
                    
                    #### Authors
                    
                    Professor John Buchanan (corresponding author)  
                    Dr Huon Curtis  
                    Ron Callus  
                    Dr Stephen Tierney (programming and statistical analysis)
                    
                    #### Source and Data
                    
                    https://github.com/sjtrny/teacher_pay_dash
                    
                    #### Acknowledgements
                    
                    This project was funded by the NSW Teachers’ Federation.
                    '''

                )
            ], width=6)
        ]),
    ], style={'margin-bottom': '250px'})


app.layout = html.Div([
    dcc.Location(id="url", refresh=False),
    dbc.Container([
        dbc.Row([
            dbc.Col([
                dcc.Graph(
                    id='graph',
                    config={
                        'displayModeBar': False,
                        'staticPlot': False,
                        'responsive': True,
                    }
                ),

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
        line_data = pcnt_data.query(
            f"STATE == '{state}' and PERCENTILE == {percentile} and OCCP4D == '{occ}' and YEAR == {year}").sort_values(
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
        title=dict(
            text=f"Estimated {scale} Income of Full Time Employees<br>{year} - {p.ordinal(percentile)} Percentile",
            font_size=24
        ),
        yaxis={'title': f"{scale} Income (Estimated)", "title_font_size": 18, 'fixedrange': True},
        xaxis={'fixedrange': True},
        legend=dict(orientation="h", title_text="Occupation", title_side="top", title_font_size=18, font_size=16),
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
        Input('button_reset', "n_clicks"),
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
        Input('button_reset', "n_clicks"),
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

                    return False, "", [{"label": x, "value": x} for x in np.sort(occupations)], kwargs[
                        'checkbox_occupations'], kwargs['dropdown_year']

                occupations = pcnt_data.query(f"YEAR == {kwargs['store_year']}")['OCCP4D'].unique()

                return True, "Changing years will reset occupation selections to default values. Are you sure you want to continue?", \
                       [{"label": x, "value": x} for x in np.sort(occupations)], kwargs['checkbox_occupations'], kwargs[
                           'store_year']

        elif changed_id == 'confirm' or changed_id == 'button_reset':
            occupations = pcnt_data.query(f"YEAR == {kwargs['dropdown_year']}")['OCCP4D'].unique()
            return False, "", [{"label": x, "value": x} for x in np.sort(occupations)], occs_default_selected, kwargs[
                'dropdown_year']

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

    fig_dict = figure_dict(
        *[v for k, v in input_dict.items() if k in graph_input_ids]
    )

    w, h = 800, 600
    format = 'png'

    img_bytes = go.Figure(fig_dict).to_image(
        format=format, width=w, height=h, scale=1,
    )

    mem = io.BytesIO()
    mem.write(img_bytes)
    mem.seek(0)

    return flask.send_file(
        mem,
        attachment_filename=f"plot.{format}",
        as_attachment=True,
        cache_timeout=0,
    )


if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0')
