import os
from config import config

import dash
import dash_core_components as dcc
import dash_html_components as html

from dash.dependencies import Input, Output, State
import dash_table

import pandas as pd
import plotly.express as px

import psycopg2

devel = 0

if devel == 1:
    
    params = config()
    conn = psycopg2.connect(**params)

else:
    
    DATABASE_URL = 'postgres://kdlcfrvcmbzozv:1dbdbbde75d4f5191b002f970d6d55f2a670c27da5aec4ca1320acad3922f8e6@ec2-3-231-194-96.compute-1.amazonaws.com:5432/dd5o6tm4njut7v'
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')

sql = "select * from interval_data;"
df = pd.read_sql_query(sql, conn)
conn = None

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

server = app.server

fig = px.line(df, x="interval_start", y="peak_demand_kw")

# Create app layout
app.layout = html.Div([

        html.Div(
            [  
                html.Div(
                    [
                        html.Div(
                            [
                                html.H3(
                                    "Taylor Farms Energy Analysis",
                                    style={"margin-bottom": "0px"},
                                ),
                            ]
                        )
                    ],
                    className="one-half column",
                    id="title",
                )         
            ],
            id="header",
            className="row flex-display",
            style={"margin-bottom": "25px"},
        ),
        
        html.Div(
            [
                html.Div(
                    [
                        html.H6('Location'),
                        dcc.Dropdown(
                            options=[
                                {'label': 'San Juan Bautista', 'value': 'tfrsjb'}
                            ],
                            value='tfrsjb'
                        ),    
                        html.H6(
                            "Fuel Cell Parameters:",
                            className="control_label",
                        ),
                        html.P('Fuel Cell Capacity [MW]'),
                        dcc.Slider(
                            min=0,
                            max=8,
                            marks={i: '{}'.format(i) if i == 1 else str(i) for i in range(1, 9)},
                            value=5,
                        ),
                        html.Br(),
                        html.Label('Fuel Cell Modulation'),
                        dcc.RadioItems(
                            options=[
                                {'label': 'None', 'value': 'none'},
                                {'label': 'Sundays', 'value': 'sun'},
                                {'label': 'Sundays + Holidays', 'value': 'sun_hol'}
                            ],
                            value='sun'
                        ),
                        html.H6(
                            "PV System Parameters:",
                            className="control_label",
                        ),
                        html.P('PV System Capacity [MW]'),
                        dcc.Slider(
                            min=0,
                            max=8,
                            marks={i: '{}'.format(i) if i == 1 else str(i) for i in range(1, 9)},
                            value=5,
                        ),
                    ],
                    className="pretty_container four columns",
                    id="cross-filter-options",
                    ),
                        
                html.Div(
                    [
                        html.Div(
                            [dcc.Graph(id="count_graph",figure=fig)],
                            id="countGraphContainer",
                            className="pretty_container",
                        ),
                    ],
                    id="right-column",
                    className="eight columns",
                ),
            ],
            className="row flex-display",
        )
        
        ])

if __name__ == '__main__':
    app.run_server(debug=True)