import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px

df_annuaire = pd.read_csv('./Data/annuaire-de-leducation.csv', sep=';')
df_resultats = pd.read_csv('./Data/fr-en-indicateurs-de-resultat-des-lycees-gt_v2.csv', sep=';')
df_all = df_annuaire.merge(df_resultats, left_on='Identifiant_de_l_etablissement', right_on='UAI', how='inner')
df_idf = df_all[df_all['Region'] == 'ILE-DE-FRANCE']

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])

sidebar = html.Div([
    html.H2('Filtre'),
    html.Div('Département'),
    dcc.Dropdown(
        id='departement-dropdown',
        options=[{'label': dep, 'value': dep} for dep in sorted(df_idf['Libelle_departement'].unique())],
        placeholder="Sélectionnez un département",
        multi=True
    ),
    html.Div('Commune'),
    dcc.Dropdown(
        id='commune-dropdown',
        placeholder="Sélectionnez une commune",
        multi=True
    ),
    html.Div('Etablissement'),
    dcc.Dropdown(
        id='etablissement-dropdown',
        placeholder="Sélectionnez un établissement",
        multi=True
    ),
])

content = html.Div([
    dbc.Row([
        dcc.Graph(id='heatmap-graph'),
    ]),
    dbc.Row([
        dcc.Graph(id='bac-performance-graph')
    ]),
])

@app.callback(
    [Output('commune-dropdown', 'options'),
     Output('etablissement-dropdown', 'options')],
    [Input('departement-dropdown', 'value')]
)
def update_filter_options(departement):
    filtered_df = df_idf
    if departement:
        filtered_df = filtered_df[filtered_df['Libelle_departement'].isin(departement)]
    communes = [{'label': comm, 'value': comm} for comm in sorted(filtered_df['Nom_commune'].unique())]
    etablissements = [{'label': etab, 'value': etab} for etab in sorted(filtered_df['Nom_etablissement'].unique())]
    return communes, etablissements

@app.callback(
    [Output('heatmap-graph', 'figure'),
     Output('bac-performance-graph', 'figure')],
    [Input('departement-dropdown', 'value'),
     Input('commune-dropdown', 'value'),
     Input('etablissement-dropdown', 'value')]
)
def update_graphs(departement, commune, etablissement):
    filtered_df = df_idf
    if departement:
        filtered_df = filtered_df[filtered_df['Libelle_departement'].isin(departement)]
    if commune:
        filtered_df = filtered_df[filtered_df['Nom_commune'].isin(commune)]
    if etablissement:
        filtered_df = filtered_df[filtered_df['Nom_etablissement'].isin(etablissement)]

    fig_map = px.scatter_mapbox(
        filtered_df,
        lat='latitude',
        lon='longitude',
        hover_name='Nom_etablissement',
        color='Taux de reussite - Toutes series', 
        size_max=15,
        zoom=8,
        mapbox_style="carto-positron"
    )
    
    if etablissement:
        fig_performance = px.bar(
            filtered_df,
            x='Nom_etablissement',
            y=['Taux de reussite - L', 'Taux de reussite - ES', 'Taux de reussite - S'],
            barmode='group',
            labels={'value': 'Taux de réussite', 'Nom_etablissement': 'Etablissement'},
            title="Résultats au Bac par Spécialité"
        )
        fig_performance.update_layout(xaxis={'automargin': True})
    else:
        fig_performance = px.bar(title="Sélectionnez un ou plusieurs établissements")
    
    return fig_map, fig_performance

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(sidebar, width=3, className='bg-success'),
        dbc.Col(content, width=9)
    ], style={"height": "100vh"}),
], fluid=True)

if __name__ == '__main__':
    app.run_server(debug=True)
