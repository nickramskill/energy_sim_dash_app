import os
from config import config
import copy

import dash
import dash_core_components as dcc
import dash_html_components as html

from dash.dependencies import Input, Output, State
import dash_table

import datetime as dt
import numpy as np
import pandas as pd
import plotly.express as px

import psycopg2

devel = 0

if devel == 1:
    
    params = config()
    conn = psycopg2.connect(**params)

else:
    
    DATABASE_URL = 'xxxxxxxxxxxxx'
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')

sql_int = "select * from interval_data;"
#sql_int = "select * from tfrsjb_interval_data;"
df_int = pd.read_sql_query(sql_int, conn)
df_int = df_int.set_index('interval_start')
df_int = df_int.resample('30min').mean() / 10**3
df_int['doy'] = df_int.index.dayofyear
df_int = df_int[0:1400]

sql_pv = "select * from solar_sim_ref;"
df_pv = pd.read_sql_query(sql_pv, conn)
df_pv = df_pv[0:1400]
df_pv = df_pv.set_index(df_int.index)
df_pv['doy'] = df_pv.index.dayofyear

df_fc = pd.DataFrame()
df_fc = pd.DataFrame(1, index=df_int.index, columns=['fc_gen'])
df_fc['dow'] = df_fc.index.dayofweek
df_fc['doy'] = df_fc.index.dayofyear

locations = ['California']

conn = None

app = dash.Dash(__name__)

server = app.server

layout = dict(
    autosize=True,
    automargin=True,
    margin=dict(l=30, r=30, b=20, t=40),
    hovermode="closest",
    plot_bgcolor="#F9F9F9",
    paper_bgcolor="#F9F9F9",
    legend=dict(font=dict(size=10), orientation="h"),
)

# Create app layout
app.layout = html.Div(
    [
        dcc.Store(id="aggregate_data"),
        # empty Div to trigger javascript file for graph resizing
        html.Div(id="output-clientside"),
        html.Div(
            [
                html.Div(
                    [
                        html.Img(
                            src=app.get_asset_url("sun.png"),
                            id="plotly-image",
                            style={
                                "height": "150px",
                                "width": "auto",
                                "margin-bottom": "10px",
                            },
                        )
                    ],
                    className="one-third column",
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.H3(
                                    "Energy Simulation",
                                    style={"margin-bottom": "0px"},
                                ),
                                html.H5(
                                    "Alternative Energy Microgrid Design Toolkit", style={"margin-top": "0px"}
                                ),
                            ]
                        )
                    ],
                    className="one-half column",
                    id="title",
                ),
                html.Div(
                    [
                        html.A(
                            html.Button("Learn More", id="learn-more-button"),
                            href="https://www.nrel.gov/research/re-solar.html",
                        )
                    ],
                    className="one-third column",
                    id="button",
                ),
            ],
            id="header",
            className="row flex-display",
            style={"margin-bottom": "10px"},
        ),
        html.Div(
            [
                html.Div(
                    [
                        html.H6("Simulation Parameters"),
                        html.P(
                            "Select location and specify properties of solar and fuel cell systems of interest",
                            className="control_label",
                        ),
                        html.Br(),
                        html.Label("Select Location"),
                        dcc.Dropdown(
                            id="location",
                            options=[{'label': i, 'value': i} for i in locations],
                            multi=False,
                            value='Factory 1',
                            className="dcc_control",
                        ),
                        html.Br(),
                        html.Label("Solar Capacity [MW]"),
                        dcc.Slider(
                            id='pv--slider',
                            min=0,
                            max=8,
                            value=0,
                            step=0.5,
                            marks={i: '{}'.format(i) if i == 0 else str(i) for i in range(0, 9)},
                            className="dcc_control",
                        ),
                        html.Br(),
                        html.Br(),
                        html.Label("Fuel Cell Capacity [MW]"),
                        dcc.Slider(
                            id='fc--slider',
                            min=0,
                            max=8,
                            value=0,
                            step=0.5,
                            marks={i: '{}'.format(i) if i == 0 else str(i) for i in range(0, 9)},
                            className="dcc_control",
                        ),
                        html.Br(),
                        dcc.RadioItems(
                            id='modulate',
                            options=[{'label': i, 'value': i} for i in ['Constant Output', 'Modulate']],
                            value='Constant Output',
                            className="dcc_control",
                        ),
                        html.Br(),
                        html.Label("Select Date Range"),
                        dcc.RangeSlider(
                            id="day_slider",
                            min=df_fc['doy'].min(),
                            max=df_fc['doy'].max(),
                            value=[df_fc['doy'].min(), df_fc['doy'].max()],
                            className="dcc_control",
                        ),
                    ],
                    className="pretty_container four columns",
                    id="cross-filter-options",
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.Div(
                                    [html.H6(id="import_text"), html.P("Import MWh")],
                                    id="wells",
                                    className="mini_container",
                                ),
                                html.Div(
                                    [html.H6(id="export_text"), html.P("Export MWh")],
                                    id="gas",
                                    className="mini_container",
                                ),
                                html.Div(
                                    [html.H6(id="solar_text"), html.P("Solar MWh")],
                                    id="oil",
                                    className="mini_container",
                                ),
                                html.Div(
                                    [html.H6(id="fc_text"), html.P("Fuel Cell MWh")],
                                    id="water",
                                    className="mini_container",
                                ),
                            ],
                            id="info-container",
                            className="row container-display",
                        ),
                        html.Div(
                            [dcc.Graph(id="int_graph")],
                            id="intGraphContainer",
                            className="pretty_container",
                        ),
                    ],
                    id="right-column",
                    className="eight columns",
                ),
            ],
            className="row flex-display",
        ),
        html.Div(
            [
                html.Div(
                    [dcc.Graph(id="pv_graph")],
                    className="pretty_container six columns",
                ),
                html.Div(
                    [dcc.Graph(id="fc_graph")],
                    className="pretty_container six columns",
                ),
            ],
            className="row flex-display",
        ),
    ],
    id="mainContainer",
    style={"display": "flex", "flex-direction": "column"},
)

#--> Helper Function
            
def calc_solar(pv_value, day_slider):
    
    df_pv_s = df_pv.copy()
    df_pv_s["yr_2020"] = df_pv["yr_2020"] * pv_value / 2
    
    df_pv_s = df_pv_s[(df_pv_s['doy'] > day_slider[0]) & (df_pv_s['doy'] < day_slider[1])]
    
    return df_pv_s

def calc_fc(fc_value, day_slider):
    
    df_fc_s = df_fc.copy()
    
    df_fc_s["fc_gen"] = fc_value
    
    df_fc_s = df_fc_s[(df_fc_s['doy'] > day_slider[0]) & (df_fc_s['doy'] < day_slider[1])]
    
    return df_fc_s

def calc_net(pv_value, fc_value, day_slider):
    
    df_net = df_int.copy()
    df_sl = calc_solar(pv_value, day_slider)
    df_fc = calc_fc(fc_value, day_slider)
    
    df_net['peak_demand_kw'] = df_net['peak_demand_kw'] - (df_sl['yr_2020'] + df_fc['fc_gen'])
    
    df_net = df_net[(df_net['doy'] > day_slider[0]) & (df_net['doy'] < day_slider[1])]
    
    return df_net

@app.callback(
    [
        Output("import_text", "children"),
        Output("export_text", "children"),
        Output("solar_text", "children"),
        Output("fc_text", "children"),
    ],
    [
        Input("pv--slider", "value"),
        Input("fc--slider", "value"),
        Input("day_slider", "value")
    ],
    )
def calc_stats(pv_value, fc_value, day_slider):
    
    df_net = df_int.copy()
    df_sl = calc_solar(pv_value, day_slider)
    df_fc = calc_fc(fc_value, day_slider)
    
    df_net['peak_demand_kw'] = df_net['peak_demand_kw'] - (df_sl['yr_2020'] + df_fc['fc_gen'])
    
    df_net = df_net[(df_net['doy'] > day_slider[0]) & (df_net['doy'] < day_slider[1])]
    
    imprt = np.round(df_net[df_net["peak_demand_kw"] > 0]["peak_demand_kw"].sum()/2)
    exprt = -np.round(df_net[df_net["peak_demand_kw"] < 0]["peak_demand_kw"].sum()/2)
    slr_gen = np.round(df_sl['yr_2020'].sum()/2)
    fc_gen = np.round(df_fc['fc_gen'].sum()/2)
    
    return imprt, exprt, slr_gen, fc_gen

#--> Interval Figure
@app.callback(
    Output("int_graph", "figure"),
    [
        Input("pv--slider", "value"),
        Input("fc--slider", "value"),
        Input("day_slider", "value")
    ],
)
def make_int_figure(pv_value, fc_value, day_slider):

    layout_int = copy.deepcopy(layout)
    
    df_net = calc_net(pv_value, fc_value, day_slider)
    
    data = [
        dict(
            type="line",
            x=df_net[df_net["peak_demand_kw"] < 0].index,
            y=df_net[df_net["peak_demand_kw"] < 0]["peak_demand_kw"],
            name="Interval",
            line=dict(color="#fac1b7")
        ),
        dict(
            type="line",
            x=df_net[df_net["peak_demand_kw"] > 0].index,
            y=df_net[df_net["peak_demand_kw"] > 0]["peak_demand_kw"],
            name="Interval",
            line=dict(color="#92d8d8")
        ),
    ]

    layout_int["title"] = "Net Grid Demand [MW]"
    layout_int["dragmode"] = "select"
    layout_int["showlegend"] = False
    layout_int["autosize"] = True

    figure = dict(data=data, layout=layout_int)
    return figure

#--> Solar Figure
@app.callback(
    Output("pv_graph", "figure"),
    [
        Input("pv--slider", "value"),
        Input("day_slider", "value")
    ],
)
def make_solar_figure(pv_value, day_slider):

    layout_pv = copy.deepcopy(layout)
    
    df = calc_solar(pv_value, day_slider)
    
    data = [
        dict(
            type="bar",
            x=df.index,
            y=df["yr_2020"],
            name="Solar",
            marker=dict(color="#FFEDA0"),
        ),
    ]

    layout_pv["title"] = "Solar Generation [MW]"
    layout_pv["dragmode"] = "select"
    layout_pv["showlegend"] = False
    layout_pv["autosize"] = True

    figure = dict(data=data, layout=layout_pv)
    return figure

#--> Fuel Cell Figure
@app.callback(
    Output("fc_graph", "figure"),
    [
        Input("fc--slider", "value"),
        Input("modulate", "value"),
        Input("day_slider", "value")
    ],
)
def make_fc_figure(fc_value, modulate, day_slider):

    layout_fc = copy.deepcopy(layout)
    
    df = calc_fc(fc_value, day_slider)
    
    data = [
        dict(
            type="bar",
            x=df.index,
            y=df["fc_gen"],
            name="FC",
            marker=dict(color="#BFD3E6"),
        ),
    ]

    layout_fc["title"] = "Fuel Cell Generation [MW]"
    layout_fc["dragmode"] = "select"
    layout_fc["showlegend"] = False
    layout_fc["autosize"] = True

    figure = dict(data=data, layout=layout_fc)
    return figure

if __name__ == '__main__':
    app.run_server(debug=True)