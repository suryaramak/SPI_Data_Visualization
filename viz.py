# Import necessary libraries
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
import plotly.graph_objects as go

# Load your data

spi_data = pd.read_csv('22_23_spi_data.csv')
salary_data = pd.read_csv('nba_salaries.csv')
salary_data = salary_data[['Player Name', 'Salary']]

# Combine SPI and salary data
df_combined = pd.merge(salary_data, spi_data, left_on="Player Name", right_on="Player", how='left')

# Set valid teams to unique since some players were traded 
valid_teams = spi_data['Team'].dropna().unique()

# Colors that are being used

good_color = '#008000'  # Green
bad_color = '#FF0000'   # Red
offense_color = '#0000FF'  # Blue
defense_color = '#2f4f4f'  # Grey


# Initialize the Dash app
app = dash.Dash(__name__)

# Define the font style
font_family = "Futura, Arial, sans-serif"


# Define the app layout 
app.layout =  html.Div([
    # Text Paragraph at the Top
    html.Div([
        html.H1("Stable Player Impact Visualization", style={'font-family': font_family, 'textAlign': 'center', 'color': '#000000'}),
        html.P(
            "Stable Player Impact (SPI) is a basketball metric assessing a player's overall impact on their team, "
            "merging box score data and luck-adjusted on-off statistics. It quantifies both offensive and defensive contributions, "
            "offering a comprehensive numerical value to reflect a player's effectiveness on the court."
        ),
        html.A("Click here for more information", href="https://nbacouchside.net/2022/11/05/introducing-nba-stable-player-impact-spi/", target="_blank",
    )], style={'font-family': font_family, 'textAlign': 'center', 'margin': '10px', 'color': '#555'}), 
    # First Visualization
    html.Div([
        html.Label("Select a Team:", style={'font-family': font_family}),
        dcc.Dropdown(
            id='team-dropdown',  
            options=[{'label': 'All Teams', 'value': 'ALL'}] + 
                    [{'label': team, 'value': team} for team in valid_teams],
            value='ALL',
            multi=False,
            placeholder="Select a team...",
            style={'font-family': font_family}
        ),
        html.Label("Select an Offensive Archetype:", style={'font-family': font_family}),
        dcc.Dropdown(
            id='archetype-dropdown',
            options=[{'label': archetype, 'value': archetype} for archetype in spi_data['Offensive Archetype'].unique()],
            value=spi_data['Offensive Archetype'].unique(),
            multi=True,
            placeholder="Select an offensive archetype...",
            style={'font-family': font_family}
        ),
        html.Label("Select Age Range:", style={'font-family': font_family}),
        dcc.RangeSlider(
            id='age-slider',
            min=spi_data['Age'].min(),
            max=spi_data['Age'].max(),
            value=[spi_data['Age'].min(), spi_data['Age'].max()],
            marks={str(age): {'label': str(age), 'style': {'font-family': font_family}} for age in range(spi_data['Age'].min(), spi_data['Age'].max() + 1)},
            step=1,
            tooltip={"placement": "bottom", "always_visible": True}
        ),
        html.Div(
        dcc.Graph(id='spi-scatter'),
        style={'display': 'flex', 'justifyContent': 'center', 'alignItems': 'center'})
    ], style={'font-family': font_family, 'height': '600px', 'width': '100%',}),

    html.Div(style={'marginTop': '500px'}),

    # Second Visualization
    html.Div([
        html.H1("Stable Player Impact vs (Log Transformed) Salary", style={'textAlign': 'center'}),
        dcc.Dropdown(
            id='dropdown-metric',
            options=[
                {'label': 'O-SPI vs Salary', 'value': 'O-SPI'},
                {'label': 'D-SPI vs Salary', 'value': 'D-SPI'},
                {'label': 'SPI vs Salary', 'value': 'SPI'}
            ],
            value='O-SPI',
            style={'width': '50%'}
        ),
        dcc.Graph(id='scatter-plot')
    ])
], style={'font-family': font_family})

# Callback for first viz
@app.callback(
    Output('spi-scatter', 'figure'),
    [Input('team-dropdown', 'value'),
     Input('archetype-dropdown', 'value'),
     Input('age-slider', 'value')]
)

# Update for first viz
def update_graph(selected_team, selected_archetypes, age_range):
    # Filter data by selected team, archetypes, and age range
    if selected_team == 'ALL':
        filtered_data = spi_data[
            (spi_data['Offensive Archetype'].isin(selected_archetypes)) &
            (spi_data['Age'] >= age_range[0]) &
            (spi_data['Age'] <= age_range[1])
        ]
    else:
        filtered_data = spi_data[
            (spi_data['Team'] == selected_team) &
            (spi_data['Offensive Archetype'].isin(selected_archetypes)) &
            (spi_data['Age'] >= age_range[0]) &
            (spi_data['Age'] <= age_range[1])
        ]
    
    fig = px.scatter(
        filtered_data,
        x='O-SPI',
        y='D-SPI',
        hover_name='Player',
        hover_data=['Pos', 'Age', 'Value Added'],
        labels={'O-SPI': 'Offensive Stable Player Impact', 'D-SPI': 'Defensive Stable Player Impact'},
        template="plotly_white"
    )
    
    # Set aspect ratio to make the plot square and font to Futura
    fig.update_layout(
        autosize=True,
        width=800,  # Width in pixels
        height=800,  # Height in pixels
        font=dict(family=font_family),
        xaxis=dict(scaleanchor="y"),
        yaxis=dict(range=[-5, 5])

    )
    
    return fig

# Callback for the second visualization (SPI Stats vs Salary)
@app.callback(
    Output('scatter-plot', 'figure'),
    [Input('dropdown-metric', 'value'),
     Input('team-dropdown', 'value'),
     Input('archetype-dropdown', 'value'),
     Input('age-slider', 'value')]
)
def update_scatter_plot(selected_metric, selected_team, selected_archetypes, age_range):
    # Apply filters to the combined dataset
    filtered_data = df_combined[
        (df_combined['Team'] == selected_team if selected_team != 'ALL' else True) &
        (df_combined['Offensive Archetype'].isin(selected_archetypes)) &
        (df_combined['Age'] >= age_range[0]) &
        (df_combined['Age'] <= age_range[1])
    ]

    # Determine the color for the regression line
    if selected_metric == 'SPI vs Salary':
        trendline_color = good_color
    elif selected_metric == 'O-SPI vs Salary':
        trendline_color = offense_color
    else:
        trendline_color = defense_color

    # Create the scatter plot
    fig = px.scatter(filtered_data, x=selected_metric, y='Salary',
                     hover_name='Player',
                     hover_data=['O-SPI','D-SPI', 'Salary', 'Pos', 'Age'],
                     labels={selected_metric: f'{selected_metric}'
                      })

    # Add trendline manually
    trendline = px.scatter(filtered_data, x=selected_metric, y='Salary',
                           trendline='ols',
                           trendline_options=dict(log_y=True))
    trendline_line = trendline['data'][1]
    fig.add_traces([go.Scatter(x=trendline_line.x, y=trendline_line.y, mode='lines', line=dict(color=trendline_color))])

    return fig


# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
