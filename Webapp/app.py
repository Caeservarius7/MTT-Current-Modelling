######################## MTT Current Monitoring System Dashboard ########################
#
# A Dash built web application dashboard to import current data from AWS S3 and
# DynamoDB services and display in interactive figure widgets with manual date
# and hour datetime filtering linked to automatic re-plotting and gauge updates.
#
# Built by the Machine Tool Technologies UK IN4.0 Group Talent Academy team
# as part of the manufacturing industry 4.0 project placement. 
# Author: George Everiss
# Latest Revision: 19:45:07 02/12/2020
# 
# Contains:
# - AWS S3 and AWS Dynam0DB client creation with Boto3 library
# - Functions to read from both AWS S3 and AWS DynamoDB data sources
# - Figure creation with Plotly Express for current time series data from both AWS sources
# - Background data refresh using APS and Cron style scheduling
# - App using dash_html_components and dash_core_components to implement 2 figures,
#   2 gauges and and LED panel with date pickers and dropdown boxes as inputs
# - Callback functionality to filter S3 current data and replot figure, update peak current
#   and mean current gauges according to user inputs
# - Flask based application server hosting and running via Dash library

######################## Dependencies ########################

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import dash_daq as daq
import plotly.express as px
import plotly.graph_objs as go
import boto3
import pandas as pd
from dynamodb_json import json_util as json
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
import atexit

# Define Application
app = dash.Dash(__name__)

# S3 config - assuming credentials set up with AWS CLI, change bucket name from 'mtt-demo'
s3 = boto3.resource('s3')
my_bucket = s3.Bucket('mtt-demo')
s3data = pd.DataFrame()

# Dynamodb config - assuming credentials set up with AWS CLI, change region to match AWS service region
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
dbdata = pd.DataFrame()

# Function to read data from AWS DynamoDB
def read_dynamodb_data():
    # Create temp dataframe to store data
    temp = pd.DataFrame()
    # Define DynamoDB table *** change this for client deployment ***
    table = dynamodb.Table('sensor-sim')
    # Scan table for all entries
    response = table.scan()
    data = response['Items']
    # Scan function retuen limit of 1 MB so loop through keys and extend data
    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        data.extend(response['Items'])

    jsontable = json.loads(response['Items'])
    # Create data frame from data 
    df = pd.DataFrame.from_records(jsontable, columns=["current", "date", "time"])
    df["date"]= df["date"].astype(str)
    df["time"]= df["time"].astype(str)
    df['datetime'] = df.date+' '+df.time
    df['datetime'] = pd.to_datetime(df.datetime)
    # Clean data 
    del df['date']
    del df['time']

    temp = temp.append(df, ignore_index = True)
    
    return temp

# read data from s3 bucket and return all files in a df
def read_s3_data():
  # Create temp dataframe to store data
  temp = pd.DataFrame()

  # Loop through all object in defined S3 bucket
  for s3_object in my_bucket.objects.all():
      # Get each object and read contents 
      response = s3_object.get()    
      lines = response['Body'].read()
      # *** Data is cleaned here however this can be factored into AWS side upon
      # deployment ***
      stringlines = str(lines)
      stringlines = stringlines[2:-2]
      stringdata = '['+stringlines+']'
      # Create dataframe from json string data
      df = pd.read_json(stringdata)
      df["date"]= df["date"].astype(str)
      df["time"]= df["time"].astype(str)
      df['datetime'] = df.date+' '+df.time
      df['datetime'] = pd.to_datetime(df.datetime)
      # Clean dataframe
      del df['date']
      del df['time']
      temp = temp.append(df, ignore_index = True)
  return temp

# call function to read s3 bucket, dynamodb table and append to dfs
s3data = s3data.append(read_s3_data())
#s3data = s3data.append(read_s3_data())
dbdata = dbdata.append(read_dynamodb_data())

######################## Dynamodb Figure ########################

fig = px.scatter(x=dbdata.datetime,y=dbdata.current)
# Update plot parameters                                               
fig.update_layout(margin={'l': 40, 'b': 40, 't': 10, 'r': 0}, hovermode='closest',
    paper_bgcolor= 'rgba(0,0,0,0)', font = dict(color = "White"), autosize = True)

max_dbdata = max(dbdata.datetime)
fig.update_xaxes(title='Datetime', range = [max_dbdata - timedelta(hours = 5),max_dbdata]) 
                     
fig.update_yaxes(title='Current / A')

fig.update_traces(marker=dict(color='#6D6194') )


######################## S3 Figure ########################

fig1 = px.scatter(x=s3data.datetime, y=s3data.current)
# Update plot parameters                     
fig1.update_layout(margin={'l': 40, 'b': 40, 't': 10, 'r': 0}, hovermode='closest',
    paper_bgcolor= 'rgba(0,0,0,0)', font = dict(color = "White"), autosize = True)

fig1.update_xaxes(title='Datetime') 

fig1.update_yaxes(title='Current / A') 

fig1.update_traces(marker=dict(color='#6D6194'))

######################## Update Scheduling ########################

# Define scheduler and add jobs for data refresh
scheduler = BackgroundScheduler()
# Cron style scheduling set to every day for S3 and every minute for DynamoDB as default
scheduler.add_job(func=read_s3_data, trigger ='cron', day= '1')
scheduler.add_job(func=read_dynamodb_data, trigger ='cron', minute=1)
# Start scheduling
scheduler.start() 

######################## App Head ########################

app.head = [html.Title('MTT Current Monitoring Dashboard')]
                                          
######################## App Layout ########################
                      
app.layout = html.Div(
    id="big-app-container",
    children=[
    # Banner with logo creation
         html.Div(
        id="banner",
        className="banner",
        children=[
            html.Div(
                id="banner-text",
                children=[
                    html.H5("Machine Tool Technologies"),
                    html.H6("Current Monitoring System Dashboard"),
                ],
            ),
            html.Div(
                id="banner-logo",
                children=[
                    
                    html.Img(id="logo", src=app.get_asset_url("MTT2.png"),style={'height':'30%', 'width':'30%'}),
                ],
            ),
        ],
    ),
        # Create stats container for: LED panel tool ID, start date picker, end date picker,
        # start hour dropdown, end hour dropdown, mean current gauge (linked to S3 data) and
        # peak current gauge (linked to S3 data)
        html.Div(
            id="status-container",
            children=[
                 html.Div(
        id="quick-stats",
        className="row",
        children=[
            html.Div(
                id="card-1",
                children=[
                    html.P("Machine Tool ID"),
                    daq.LEDDisplay(
                        id="tool-id-led",
                        value="0001",
                        color="#78C4BE",
                        backgroundColor="#242633",
                        size=50,
                    ),
                ],
            ),
            

    html.Div(children = [
        html.P("Select Start Date:"),
        dcc.DatePickerSingle(
        id='my-date-picker-single-start',
        min_date_allowed=min(s3data.datetime).date(),
        max_date_allowed=max(s3data.datetime).date(),
        initial_visible_month=min(s3data.datetime).date(),
        date=min(s3data.datetime).date(),
        day_size = 50

    ),
        html.P("Select End Date:"),
    dcc.DatePickerSingle(
        id='my-date-picker-single-end',
        min_date_allowed=min(s3data.datetime).date(),
        max_date_allowed=max(s3data.datetime).date(),
        initial_visible_month=max(s3data.datetime).date(),
        date=max(s3data.datetime).date(),
        day_size = 50
        
    )]
),
           
            html.Div(
                id="start-time-selector",
                children=[
                    html.P("Select Start Hour:"),
                    dcc.Dropdown(
                id='start-dropdown',
                options=[
                  
                  {'label': '0', 'value': 0},
                    {'label': '1', 'value': 1},
                    {'label': '2', 'value': 2},
                    {'label': '3', 'value': 3},
                    {'label': '4', 'value': 4},
                    {'label': '5', 'value': 5},
                    {'label': '6', 'value': 6},
                    {'label': '7', 'value': 7},
                    {'label': '8', 'value': 8},
                    {'label': '9', 'value': 9},
                    {'label': '10', 'value': 10},
                    {'label': '11', 'value': 11},
                    {'label': '12', 'value': 12},
                    {'label': '13', 'value': 13},
                    {'label': '14', 'value': 14},
                    {'label': '15', 'value': 15},
                    {'label': '16', 'value': 16},
                    {'label': '17', 'value': 17},
                    {'label': '18', 'value': 18},
                    {'label': '19', 'value': 19},
                    {'label': '20', 'value': 20},
                    {'label': '21', 'value': 21},
                    {'label': '22', 'value': 22},
                    {'label': '23', 'value': 23}
                    
                ],
                placeholder='End hour',
                value='0'
            ),
                ],
            ),
            html.Div(
                id="end-time-selector",
                children=[
                    html.P("Select End Hour:"),
                    dcc.Dropdown(
                id='end-dropdown',
                options=[
                  
                  {'label': '0', 'value': 0},
                    {'label': '1', 'value': 1},
                    {'label': '2', 'value': 2},
                    {'label': '3', 'value': 3},
                    {'label': '4', 'value': 4},
                    {'label': '5', 'value': 5},
                    {'label': '6', 'value': 6},
                    {'label': '7', 'value': 7},
                    {'label': '8', 'value': 8},
                    {'label': '9', 'value': 9},
                    {'label': '10', 'value': 10},
                    {'label': '11', 'value': 11},
                    {'label': '12', 'value': 12},
                    {'label': '13', 'value': 13},
                    {'label': '14', 'value': 14},
                    {'label': '15', 'value': 15},
                    {'label': '16', 'value': 16},
                    {'label': '17', 'value': 17},
                    {'label': '18', 'value': 18},
                    {'label': '19', 'value': 19},
                    {'label': '20', 'value': 20},
                    {'label': '21', 'value': 21},
                    {'label': '22', 'value': 22},
                    {'label': '23', 'value': 23}
                    
                ],
                placeholder='End hour',
                value='23'
            
            ),
                ],
            ),
            html.Div(
                id="peak-gauge",
                children=[
                    html.P([html.Br(),"Peak Current - Selected Region"]),
                    daq.Gauge(
                        id="peak-current-gauge",
                        max=100,
                        min=0,
                        value = 79.4,
                        units = "Amps",
                        showCurrentValue=True,
                        size=170, # default size 200 pixel
                        color = "#78C4BE"
                    ),
            ],
    ),
            html.Div(
                id="average-gauge",
                children=[
                    html.P("Mean Current - Selected Region"),
                    daq.Gauge(
                        id="average-current-gauge",
                        max=100,
                        min=0,
                        value = 37.7,
                        units = "Amps",
                        showCurrentValue=True,
                        size=170,
                        color = "#78C4BE"  # default size 200 pixel
                    ),
                ],
            )
        ]
    ),          
                # Create chart container for figure items
                html.Div(
                    id="graphs-container",
                    children=[html.Div(
                    id="chart-container",
                    className="row",
                    children=[

            # Create chart session using 12 columns of grid structure as width 
            html.Div(
                id="chart-session",
                className="twelve columns",
                children=[
                    html.P([html.Br(),"Selected Timeframe Current Data "]),
                    # Add S3 data figure to html item
                    html.Div(dcc.Graph(id='S3data-graphic', figure=fig1)),
                    html.P("Previous 5 Hours Current Data"),
                    # Add DynamoDB data figure to html item         
                    html.Div( dcc.Graph(figure = fig))
                                                
                    ] 
                )
            ]      

                ),
            ],
        )   
    ],

        )
    ]
)

     
###################### Callback Function #########################
# Define outputs as S3 figure and display gauges 
# Define inputs as the four user datetime inputs 

@app.callback(
    [Output('S3data-graphic', 'figure'),
     Output('peak-current-gauge', 'value'),
     Output('average-current-gauge', 'value')],
    [Input('my-date-picker-single-start', 'date'),
     Input('my-date-picker-single-end', 'date'),
     Input('start-dropdown', 'value'),
     Input('end-dropdown', 'value')
     ])

# Function taking four user app inputs as args, filters dataframe between these input times,
# calculate the new peak current value, mean current and plot as anee figure and return
# these three items 
def update_graph(start_date, end_date, start_hour, end_hour):
    
    # Compile dates and times to form Pandas datetime objects
    start_date_string = str(start_date)
    start_total = start_date_string[0:10:1] + ' ' + str(start_hour)+':00:00.00'  
    start_date_time_obj = pd.to_datetime(start_total)    
    end_date_string = str(end_date)
    end_total = end_date_string[0:10:1] + ' ' + str(end_hour)+':00:00.00'  
    end_date_time_obj = pd.to_datetime(end_total)
    
    # Create new temp dataframe
    dff = pd.DataFrame()

    # Filter full dataset between start and end times 
    # *** To provide quicker re-plotting here filtering can be avoided and new x axis limits
    # returned to the existing figure if instant response is required by client ***
    dff = s3data[s3data.datetime.between(start_date_time_obj, end_date_time_obj)]
    peak = max(dff.current)
    mean = dff['current'].mean()

    # Create new figure from filtered dataframe
    fig = px.scatter(x=dff.datetime, y=dff.current)                 
    fig.update_layout(margin={'l': 40, 'b': 40, 't': 10, 'r': 0}, hovermode='closest',
     paper_bgcolor= 'rgba(0,0,0,0)', font = dict(color = "White"), autosize = True)
    fig.update_xaxes(title='Datetime') 
    fig.update_yaxes(title='Current / A') 
    fig.update_traces(marker=dict(color='#6D6194'))

    return fig, peak, mean

# Run application
if __name__ == '__main__':
    # Debugging mode set to False for deployment
    app.run_server(debug=False)

# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown()) 
