import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
from collections import Counter
import pandas as pd
import os
from main import fetch_tfl_disruptions  # Assuming main.py contains fetch_tfl_disruptions
import dash_bootstrap_components as dbc  # Assuming you have this installed for Bootstrap styles

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

    # Initialize the Dash app with Bootstrap styles
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

    # Define the layout combining HTML structure with Dash components
    app.layout = html.Div([
        html.Header(className='header', children=[
            html.H1('Urban Mobility Blog')
        ]),
        
        html.Nav(className='nav', children=[
            html.A('Home', href='#home'),
            html.A('About', href='#about'),
            html.A('Analysis', href='#analysis')
        ]),
        
        dbc.Container([
            dbc.Row([
                # Main Content
                dbc.Col([
                    html.Article(className='post', children=[
                        html.H2('Weekly Urban Mobility Analysis', id='analysis'),
                        html.P('Published on: 2025-01-23'),
                        
                        # Sections for content
                        html.Section([
                            html.H3('Introduction'),
                            html.P('Welcome to our weekly urban mobility analysis focusing on road disruptions in London. ...')
                        ]),
                        html.Section([
                            html.H3('Analysis Summary'),
                            html.P('**Severe disruptions:** There are 4 severe disruptions now.'),
                            html.Ul([html.Li('Disruption 1'), html.Li('Disruption 2'), ...])
                        ]),
                        html.Section([
                            html.H3('Dashboard'),
                            html.P('Explore our interactive dashboard for real-time disruption analysis:'),
                            dcc.Graph(id='severity-bar-chart'),
                            dcc.Graph(id='category-pie-chart'),
                            dcc.Graph(id='subcategory-bar-chart'),
                            html.Div([
                                html.H2('Current Status of Disruptions'),
                                html.P('All disruptions are currently: Active')
                            ], style={'textAlign': 'center'})
                        ]),
                        html.Section([
                            html.H3('Map of Road Disruptions in London'),
                            # html.Iframe(src='map.html', style={'width': '100%', 'height': '600px', 'border': 'none'})
                        ]),
                        html.Section([
                            html.H3('Visualizations'),
                            html.H4('Time Series of Disruptions'),
                            html.Img(src='assets/time_series_plot.png', width='100%')
                        ]),
                        html.Section([
                            html.H3('Conclusion'),
                            html.P('Based on the analysis, we observe that the majority of disruptions occur during peak hours, ...')
                        ])
                    ])
                ], width=8),
                
                # Sidebar
                dbc.Col([
                    html.H2('About This Blog'),
                    html.P('This blog provides weekly insights into urban mobility issues in London...'),
                    html.H2('Recent Posts'),
                    html.Ul([
                        html.Li(html.A('Last Week\'s Analysis', href='#post1')),
                        html.Li(html.A('Impact of Weather on Traffic', href='#post2')),
                        html.Li(html.A('Future of Urban Mobility', href='#post3'))
                    ]),
                    html.H2('Contact Us'),
                    html.P([
                        'For inquiries or to contribute, reach us at ',
                        html.A('urbanmobility@example.com', href='mailto:urbanmobility@example.com')
                    ])
                ], width=4)
            ])
        ]),
        
        html.Footer([
            html.P('Data sourced from Transport for London API. Last updated: 2025-01-23 17:53:33')
        ])
    ])

    # Callbacks to update graphs remain the same
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