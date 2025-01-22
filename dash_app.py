# dash_app.py

import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
from collections import Counter
import pandas as pd
import os
from main import fetch_tfl_disruptions  # Assuming main.py contains fetch_tfl_disruptions

# Fetching the disruptions data
disruptions = fetch_tfl_disruptions()

if not disruptions:
    print("No disruption data available or there was an error in fetching data.")
else:
    # Extract data for severity, category, and subcategory
    severity_counts = Counter(d['severity'] for d in disruptions if 'severity' in d)
    category_counts = Counter(d['category'] for d in disruptions if 'category' in d)
    subcategory_counts = Counter(d['subCategory'] for d in disruptions if 'subCategory' in d)

    # Create DataFrames for easier manipulation
    df_severity = pd.DataFrame.from_dict(severity_counts, orient='index', columns=['count']).reset_index()
    df_severity = df_severity.rename(columns={'index': 'severity'})
    
    df_category = pd.DataFrame.from_dict(category_counts, orient='index', columns=['count']).reset_index()
    df_category = df_category.rename(columns={'index': 'category'})
    
    df_subcategory = pd.DataFrame.from_dict(subcategory_counts, orient='index', columns=['count']).reset_index()
    df_subcategory = df_subcategory.rename(columns={'index': 'subCategory'})

    # Map severity descriptions
    severity_dict = {
        'Serious': 'Serious',
        'Moderate': 'Moderate',
        'Minimal': 'Minimal',
        'No impact': 'No Impact'
    }
    df_severity['description'] = df_severity['severity'].map(severity_dict)

    # Initialize the Dash app
    app = dash.Dash(__name__)

    # Define the layout
    app.layout = html.Div([
        html.H1('TfL Road Disruption Dashboard'),
        
        html.Div([
            html.H2('Severity of Disruptions'),
            dcc.Graph(id='severity-bar-chart'),
        ], style={'width': '33%', 'display': 'inline-block'}),
        
        html.Div([
            html.H2('Disruption Categories'),
            dcc.Graph(id='category-pie-chart'),
        ], style={'width': '33%', 'display': 'inline-block'}),
        
        html.Div([
            html.H2('Disruption Subcategories'),
            dcc.Graph(id='subcategory-bar-chart'),
        ], style={'width': '33%', 'display': 'inline-block'}),
        
        html.Div([
            html.H2('Current Status of Disruptions'),
            html.P('All disruptions are currently: Active')
        ], style={'width': '100%', 'display': 'inline-block', 'textAlign': 'center'})
    ])

    # Callbacks to update graphs
    @app.callback(
        Output('severity-bar-chart', 'figure'),
        [Input('severity-bar-chart', 'id')]
    )
    def update_severity_graph(input_id):
        fig = px.bar(df_severity, x='description', y='count', title='Road Disruption Severities - TfL Data',
                     labels={'description': 'Severity', 'count': 'Number of Disruptions'})
        fig.update_layout(yaxis_title='Number of Disruptions', xaxis_title='Severity')
        for i, count in enumerate(df_severity['count']):
            fig.add_annotation(x=df_severity['description'][i], y=count, 
                               text=str(count), showarrow=False, yshift=10)
        return fig

    @app.callback(
        Output('category-pie-chart', 'figure'),
        [Input('category-pie-chart', 'id')]
    )
    def update_category_graph(input_id):
        fig = px.pie(df_category, values='count', names='category', title='Distribution of Disruption Categories')
        return fig

    @app.callback(
        Output('subcategory-bar-chart', 'figure'),
        [Input('subcategory-bar-chart', 'id')]
    )
    def update_subcategory_graph(input_id):
        fig = px.bar(df_subcategory, x='subCategory', y='count', title='Disruption Subcategories',
                     labels={'subCategory': 'Subcategory', 'count': 'Number of Disruptions'})
        fig.update_layout(yaxis_title='Number of Disruptions', xaxis_title='Subcategory')
        fig.update_xaxes(tickangle=45)
        return fig

    # Run the app
    if __name__ == '__main__':
        app.run_server(debug=True)