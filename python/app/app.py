import datetime as dt
import numpy    as np

import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly
from dash.dependencies import Input, Output
import socket
from scipy import interpolate
import os
import time
from ClassApp import *

#
# ps -fA | grep python
# kill -9 6702

import sys
if "C:\\bin" not in sys.path:
    sys.path.append("C:\\bin")

from trackerUtils     import *


def writeTCP(message):

    dataServer_IP = "127.0.0.1"
    portNum = 5555

    try:
        sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        sock.connect((dataServer_IP,portNum))
        sock.sendall(message)

        #-------------------------
        # Loop to recieve all data
        #-------------------------
        incommingTotal = ""
        while True:
            incommingPart = sock.recv(4096)
            if not incommingPart: break
            incommingTotal += incommingPart

        sock.close()
    except:
        print "Unable to connect to data server!!"
        incommingTotal = False

    return incommingTotal


#-------------------------------------------
# ***** Start ******
#-------------------------------------------
#logMeas                = readMeas('')
#logHK, obstimeHK       = readHK('')
#logMet, obstimeMet     = readMet('')

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

logMeas                = readMeas('')
#logHK, obstimeHK       = readHK('')
#logHK, obstimeHK       = readHKUpdate(logHK, obstimeHK)
#logMet, obstimeMet     = readMetUpdate(logMet, obstimeMet)


app.layout = html.Div(
    html.Div([
        html.H4('HR-FTIR Live Feed - Boulder'),
        html.Div(id='live-update-text-Now'),
        html.Div(id='live-update-text-Meas'),
        html.Div(id='live-update-text-bruker'),
        html.Div(id='live-update-text-opus'), 
        html.Div(id='live-update-text-atm'),        
        #html.Div(id='live-update-text-HK'),
        #html.Div(id='live-update-text-HK2'),
        dcc.Graph(id='live-update-graph-Meas'),
        #dcc.Graph(id='live-update-graph-HK'),
        dcc.Interval(
            id='interval-component',
            interval=5000, # in milliseconds
            n_intervals=0
        )
    ])
)

@app.callback(Output('live-update-text-Now', 'children'),
              [Input('interval-component', 'n_intervals')])
def update_metrics_Now(n):

    nowutc           = dt.datetime.utcnow()

    style = {'padding': '5px', 'fontSize': '16px'}
    
    return [
        html.Span('UT (Now):    {0:}\n'.format(nowutc), style=style),
    ]

@app.callback(Output('live-update-text-Meas', 'children'),
              [Input('interval-component', 'n_intervals')])
def update_metrics_Meas(n):

    style = {'padding': '5px', 'fontSize': '16px'}

    try:
        MeasSNR          = logMeas['SNR_RMS'][0][-1]
        MeasTime         = logMeas['Measurement_Time'][0][-1][0:8]
        File             = logMeas['Filename'][0][-1]

         
        return [
            html.Span('TIME_LAST_MEAS =     {0:}; '.format(MeasTime), style=style),
            #html.Span("{0:25s} = {1:<60}; ".format('Time-Meas', MeasTime), style=style),
            html.Span('SNR_RMS =       {0:.2f}; '.format(float(MeasSNR)), style=style),       
            html.Span('FILENAME =      {0:}; '.format(File), style=style),       
        ]

    except:
        return [
            html.Span('NO MEASUREMENT INFO AVAILABLE', style=style),
        ]    


@app.callback(Output('live-update-text-bruker', 'children'),
              [Input('interval-component', 'n_intervals')])
def update_metrics_bruker(n):

    style = {'padding': '5px', 'fontSize': '16px'}

    try: 
        ids = ['BRUKER_DETECTORS', 'BRUKER_LASER', 'BRUKER_INSTRUMENT_READY', 'BRUKER_IR_SOURCE', 'BRUKER_SCANNER']
       
        allParms = writeTCP("LISTALL")
        allParms = allParms.strip().split(";")

        allTS    = writeTCP("LISTALLTS")
        allTS    = allTS.strip().split(";")

       #-----------------------
       # Put data in dictionary
       #-----------------------
        data = {}
        for val in allParms:
            val = val.strip().split("=")
            data[val[0].strip()] = val[1].strip()

        TS = {}
        for val in allTS:
            val = val.strip().split("=")
            TS[val[0].strip()] = val[1].strip()

        # print '\n'
        # for key,val in sorted(data.items()):
        #     print "{0:25s} = {1:<60} {2:>25}".format(key,val,TS[key])
        
        d = []

        for key,val in sorted(data.items()):
            if key in ids:
                d.append("{0:25s} = {1:<60}; ".format(key,val))

        

        #key,val = data.items()[0]
        return [
            #for key,val in sorted(data.items()):
            #    html.Span("{0:25s} = {1:<60}".format(key,val), style=style)
            #html.Span("{0:25s} = {1:<60}".format(key,val), style=style), 
            html.Span(d, style=style ),    
        ]
    except:
        return [
            html.Span('NO BRUKER INFO AVAILABLE', style=style),
        ] 

@app.callback(Output('live-update-text-opus', 'children'),
              [Input('interval-component', 'n_intervals')])
def update_metrics_opus(n):

    style = {'padding': '5px', 'fontSize': '16px'}

    try:
    
        ids = ['OPUS_CMND', 'OPUS_STATUS']
       
        allParms = writeTCP("LISTALL")
        allParms = allParms.strip().split(";")

        allTS    = writeTCP("LISTALLTS")
        allTS    = allTS.strip().split(";")

       #-----------------------
       # Put data in dictionary
       #-----------------------
        data = {}
        for val in allParms:
            val = val.strip().split("=")
            data[val[0].strip()] = val[1].strip()

        TS = {}
        for val in allTS:
            val = val.strip().split("=")
            TS[val[0].strip()] = val[1].strip()
       
        d = []

        for key,val in sorted(data.items()):
            if key in ids:
                d.append("{0:25s} = {1:<60}; ".format(key,val))

        

        #key,val = data.items()[0]
        return [
            #for key,val in sorted(data.items()):
            #    html.Span("{0:25s} = {1:<60}".format(key,val), style=style)
            #html.Span("{0:25s} = {1:<60}".format(key,val), style=style), 
            html.Span(d,style=style ),    
        ]

    except:
        return [
            html.Span('NO OPUS INFO AVAILABLE', style=style),
        ]


@app.callback(Output('live-update-text-atm', 'children'),
              [Input('interval-component', 'n_intervals')])
def update_metrics_ATM(n):

    style = {'padding': '5px', 'fontSize': '16px'}

    try:
    
        ids = ['MET_WIND_SPEED', 'MET_PEAK_GUST']
       
        allParms = writeTCP("LISTALL")
        allParms = allParms.strip().split(";")

        allTS    = writeTCP("LISTALLTS")
        allTS    = allTS.strip().split(";")

       #-----------------------
       # Put data in dictionary
       #-----------------------
        data = {}
        for val in allParms:
            val = val.strip().split("=")
            data[val[0].strip()] = val[1].strip()

        TS = {}
        for val in allTS:
            val = val.strip().split("=")
            TS[val[0].strip()] = val[1].strip()
       
        d = []

        for key,val in sorted(data.items()):
            if key in ids:
                d.append("{0:25s} = {1:<60}; ".format(key,val))

        

        #key,val = data.items()[0]
        return [
            #for key,val in sorted(data.items()):
            #    html.Span("{0:25s} = {1:<60}".format(key,val), style=style)
            #html.Span("{0:25s} = {1:<60}".format(key,val), style=style), 
            html.Span(d,style=style ),    
        ]

    except:
        return [
            html.Span('NO MET INFO AVAILABLE', style=style),
        ]

# @app.callback(Output('live-update-text-HK', 'children'),
#               [Input('interval-component', 'n_intervals')])
# def update_metrics_HK(n):

#     #logHK, obstime      = readHK('')
#     MetWindSpeed         = logMet['Atm_Wind_Speed'][-1]
#     MetWindGust          = logMet['Atm_Wind_Gust'][-1]
#     MetWindGust          = logMet['Atm_Wind_Gust'][-1]
#     MetTemp              = logMet['Atm_Temperature'][-1]
#     Metrh                = logMet['Atm_Rel_Humidity'][-1]
#     MetTime              = obstimeMet[-1].time()
  

#     style = {'padding': '5px', 'fontSize': '16px'}
    
#     return [
#         html.Span('Time-HK:    {0:}\n'.format(MetTime), style=style),
#         html.Span('Wind Speed [m/s]: {0:.2f}\n'.format(float(MetWindSpeed)), style=style), 
#         html.Span('Wind Gust: {0:.2f}\n'.format(float(MetWindGust)), style=style),  
#         html.Span('Temperature [C]: {0:.2f}\n'.format(float(MetTemp)), style=style), 
#         html.Span('RH [%]: {0:.2f}\n'.format(float(Metrh)), style=style),             
#     ]

# @app.callback(Output('live-update-text-HK2', 'children'),
#               [Input('interval-component', 'n_intervals')])
# def update_metrics_HK2(n):

#     #logHK, obstime      = readHK('')
#     ERad         = logHK['Extern_E_Radiance'][-1]
#     ERads        = logHK['Extern_E_RadianceS'][-1]
#     WRad         = logHK['Extern_W_Radiance'][-1]
#     WRads        = logHK['Extern_W_RadianceS'][-1]

#     style = {'padding': '5px', 'fontSize': '16px'}
    
#     return [
#         html.Span('ERad:    {0:}\n'.format(ERad), style=style),
#         html.Span('ERadS: {0:.2f}\n'.format(float(ERads)), style=style), 
#         html.Span('WRad: {0:.2f}\n'.format(float(WRad)), style=style),  
#         html.Span('WRadS: {0:.2f}\n'.format(float(WRads)), style=style),            
#    ]

# Multiple components can update everytime interval gets fired.
@app.callback(Output('live-update-graph-Meas', 'figure'),
              [Input('interval-component', 'n_intervals')])
def update_graph_live_Meas(n):

    fig = plotly.tools.make_subplots(rows=2, cols=1, vertical_spacing=0.2)
    fig['layout']['margin'] = {
        'l': 40, 'r': 20, 'b': 60, 't': 60
    }
    fig['layout']['legend'] = {'x': 0, 'y': 1, 'xanchor': 'left'}
    

    try:

        fig['layout']['title']  = "Log - Measurements"

        #logMeas     = readMeas('')
        MeasSNR     = logMeas['SNR_RMS'][0]
        MeasTime    = logMeas['Measurement_Time'][0]
        MeaspAmp    = logMeas['Peak_Amplitude'][0]
        SignalGain  = logMeas['Signal_Gain'][0]
        File        = logMeas['Filename'][0]
        PreAmpGain  = logMeas['Pre_Amp_Gain'][0]

        MeasTime     = [t[0:8] for t in MeasTime]
        MeasTime     = MeasTime
        # Create the graph with subplots
        

        fig.append_trace({
            'x': MeasTime,
            'y': MeasSNR,
            'text': File,
            'name': 'SNR-RMS',
            'mode': 'lines+markers',
            'type': 'scatter'
        }, 1, 1)
        fig.append_trace({
            'x': MeasTime,
            'y': MeaspAmp,
            'text': PreAmpGain,
            'name': 'peakAmp',
            'mode': 'lines+markers',
            'type': 'scatter'
        }, 2, 1)

        return fig
    except:

        fig['layout']['title']  = "Log - Measurements - Error or not found"

        return fig

#@app.callback(Output('live-update-graph-HK', 'figure'),
#             [Input('interval-component', 'n_intervals')])
# def update_graph_live_HK(n):

#     MetWindSpeed  = logMet['Atm_Wind_Speed']
#     MetTemp       = logMet['Atm_Temperature']
#     ERad         = logHK['Extern_E_Radiance']
#     ERads        = logHK['Extern_E_RadianceS']
    
#     HKTime       = [t.time() for t in obstimeHK]
#     HKTime       = HKTime

#     MetTime       = [t.time() for t in obstimeMet]
#     MetTime       = MetTime


#     # Create the graph with subplots
#     fig = plotly.tools.make_subplots(rows=2, cols=2, vertical_spacing=0.2)
#     fig['layout']['margin'] = {
#         'l': 40, 'r': 20, 'b': 60, 't': 40
#     }
#     fig['layout']['legend'] = {'x': 0, 'y': 1, 'xanchor': 'left'}
#     fig['layout']['title']  = "Log - HK"

#     fig.append_trace({
#         'x': MetTime,
#         'y': MetWindSpeed,
#         'name': 'Wind Speed [m/s]',
#         'mode': 'lines+markers',
#         'type': 'scatter'
#     }, 1, 1)
#     fig.append_trace({
#         'x': MetTime,
#         'y': MetTemp,
#         'text': MetTime,
#         'name': 'Temperature [C]',
#         'mode': 'lines+markers',
#         'type': 'scatter'
#     }, 1, 2)
#     fig.append_trace({
#         'x': HKTime,
#         'y': ERad,
#         'text': HKTime,
#         'name': 'ERad',
#         'mode': 'lines+markers',
#         'type': 'scatter'
#     }, 2, 1)
#     fig.append_trace({
#         'x': HKTime,
#         'y': ERads,
#         'text': HKTime,
#         'name': 'ERads',
#         'mode': 'lines+markers',
#         'type': 'scatter'
#     }, 2, 2)
    
#     return fig

if __name__ == '__main__':
    host = socket.gethostbyname(socket.gethostname())
    app.run_server(debug=True,  host=host, port = 5050)