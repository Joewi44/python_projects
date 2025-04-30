# Import required libraries
import pandas as pd
import dash
from dash import html
from dash import dcc
from dash.dependencies import Input, Output
import plotly.express as px

# Read the airline data into pandas dataframe

spacex_df = pd.read_csv("coursera/Falcon9/spacex_launch_dash.csv")
max_payload = spacex_df['Payload Mass (kg)'].max()
min_payload = spacex_df['Payload Mass (kg)'].min()

# Create a dash application
app = dash.Dash(__name__)

# Create an app layout
app.layout = html.Div(children=[
    html.H1('SpaceX Launch Records Dashboard',
            style={'textAlign': 'center', 'color': '#503D36','font-size': 40}),
                                # TASK 1: Add a dropdown list to enable Launch Site selection
                                # The default select value is for ALL sites
                                # dcc.Dropdown(id='site-dropdown',...)
    html.Div([
        html.H2('Select Site', style={'margin-right': '2em'}),
        dcc.Dropdown(
            id='site-dropdown',
            options=[{'label': 'All Sites', 'value': 'ALL'}] +
                    [{'label': site, 'value': site} for site in spacex_df['Launch Site'].unique()],
            value='ALL',
            placeholder="Select a Launch Site",
            searchable=True
            )]),
    html.Br(),

                                # TASK 2: Add a pie chart to show the total successful launches count for all sites
                                # If a specific launch site was selected, show the Success vs. Failed counts for the site
    html.Div(dcc.Graph(id='success-pie-chart')),
    html.Br(),

    html.P("Payload range (Kg):"),
    dcc.RangeSlider(id='payload-slider',
                    min=0, max=10000, step=1000,
                    value=[min_payload, max_payload]),
                                # TASK 3: Add a slider to select payload range
                                #dcc.RangeSlider(id='payload-slider',...)

                                # TASK 4: Add a scatter chart to show the correlation between payload and launch success
    html.Div(dcc.Graph(id='success-payload-scatter-chart')),
    ])

# TASK 2:
# Add a callback function for `site-dropdown` as input, `success-pie-chart` as output
@app.callback(Output(component_id='success-pie-chart', component_property='figure'),
              Input(component_id='site-dropdown', component_property='value'))
def get_pie_chart(entered_site):
    if entered_site == 'ALL':
        fig = px.pie(spacex_df, 
                    values='class', 
                    names='Launch Site', 
                    title='Total Success Launches By Site'
                    )
    else:
        filtered_df = spacex_df[spacex_df['Launch Site'] == entered_site]
        fig = px.pie(filtered_df,
                    names=filtered_df['class'].map({1: 'succes', 0:'Failure'}),
                    title=f'Total Success Launches for site {entered_site}',
                    color=filtered_df['class'],
                    color_discrete_map={0: 'red', 1:'green'}
                    )

    return fig

# TASK 4:
# Add a callback function for `site-dropdown` and `payload-slider` as inputs, `success-payload-scatter-chart` as output
@app.callback(Output(component_id='success-payload-scatter-chart', component_property='figure'),
              Input(component_id='site-dropdown', component_property='value'),
              Input(component_id='payload-slider', component_property='value'))

def get_scatter_plot(entered_site, payload_value):
    low, high = payload_value
    scatter_data = spacex_df[(spacex_df['Payload Mass (kg)'] > low) & (spacex_df['Payload Mass (kg)'] < high)]
    if entered_site == 'ALL':
        fig = px.scatter(scatter_data,
               x='Payload Mass (kg)',
               y='class',
               color='Booster Version Category',
               title='Correlation between Payload and Success for all Sites'
               )
    else:
        fig = px.scatter(scatter_data[scatter_data['Launch Site'] == entered_site],
               x='Payload Mass (kg)',
               y='class',
               color='Booster Version Category',
               title=f'Correlation between Payload and Success for {entered_site} Sites'
        )

    return fig

# Run the app
if __name__ == '__main__':
    app.run()
