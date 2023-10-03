from openalex_analysis.plot import config, WorksPlot, get_info_about_entitie_from_api
from OA_entities_names import OA_entities_names
# from jupyter_dash import JupyterDash
import dash_bootstrap_components as dbc # dash app theme
import plotly.io as pio # plotly theme
from dash import Dash, dcc, html, Input, Output, State, ALL, MATCH, Patch, callback, dash_table, no_update
from dash.exceptions import PreventUpdate
import dash
import threading
# from flask import Flask
import time
import dash_loading_spinners
import os, sys
sys.path.append(os.path.abspath('../'))
import layout_parameters
import pandas as pd
import base64
import io
from furl import furl

# PAGE 4


dash.register_page(__name__)

app = dash.get_app()

# concept names and BD file names:
OA_concepts = OA_entities_names()

# openalex_analysis configuartion:
if os.path.exists("dash_app_configuration.py"):
    import dash_app_configuration as dash_app_config
    print('OK: Loadeded the configuration from "dash_app_configuration.py"')
else:
    import dash_app_configuration_template as dash_app_config
    print('WARNING: Loaded the default configuration, from the template file ("dash_app_configuration_template.py")')
    print('Please copy the template file, rename it "dash_app_configuration.py" and set the configuration in it')
config.email = dash_app_config.config_email
config.api_key = dash_app_config.config_api_key
config.openalex_url = dash_app_config.config_openalex_url
config.allow_automatic_download = dash_app_config.config_allow_automatic_download
config.disable_tqdm_loading_bar = dash_app_config.config_disable_tqdm_loading_bar
config.n_max_entities = dash_app_config.config_n_max_entities
config.project_datas_folder_path = dash_app_config.config_project_datas_folder_path
config.parquet_compression = dash_app_config.config_parquet_compression
config.max_storage_percent = dash_app_config.config_max_storage_percent
config.redis_enabled = dash_app_config.config_redis_enabled
config.redis_client = dash_app_config.config_redis_client
config.redis_cache = dash_app_config.config_redis_cache
print('OK: Configuration set')


works_infos = ["display_name", "author_citation_style", "publication_year", "doi"]

        
main_container = dbc.Container(className="container-app-references-analysis", id="container-app-references-analysis", fluid=True, children=[
    dbc.Row(justify="center", style={'margin': '1em 1em'}, children=
        [
            dbc.Col(
                [
                    html.H1(children="Analyse the citations comming from an institution of an article"),
                    html.H2(children="Parameters"),
                    html.H3(children="Concept"),
                    html.P(children="The analysis will use only the works of this concept to compute where does the citations come from:"),
                    dcc.Dropdown(id='ref4_concept_dropdown', clearable=True, placeholder='Type at least 3 characters (for example "Sustainability")',),
                    html.H3(children="Institution"),
                    html.P(children="The analysis will use only the works of this institution to compute where does the citations come from:"),
                    dcc.Dropdown(id='ref4_institution_dropdown', clearable=True, placeholder='Type at least 5 characters (for example "Stockholm Resilience Centre")',),
                    html.H3(children="Reference"),
                    html.P(children="The article cited on which we want to know who cited it:"),
                    dbc.Input(id="ref4_reference_dropdown", type="text", placeholder='Type the article OpenAlex ID (for example "W1999167944")'),

                    dcc.Location(id='url', refresh=False),
                    html.Div(id='content'),
                ],
                **layout_parameters.layout_dynamic_width,
            ),
        ],
    ), 
])


layout = html.Div(children=
    [
        html.Div(
            id="div-loading-references-analysis",
            children=
                [
                    dash_loading_spinners.ClimbingBox(#Pacman(
                        fullscreen=True, 
                        id="loading-app-references-analysis"
                    )
                ]
        ),
        main_container
    ]
)


@app.callback([
                Output('ref4_concept_dropdown', 'value'),
                Output('ref4_concept_dropdown', 'options'),
                Output('ref4_institution_dropdown', 'value'),
                Output('ref4_institution_dropdown', 'options'),
                Output('ref4_reference_dropdown', 'value')
              ],
              [
                Input('url', 'href'),
                Input('ref4_concept_dropdown', 'search_value'),
                Input('ref4_institution_dropdown', 'search_value')
              ],
              )
def _content(href: str, search_value_concept, search_value_institution):
    concept = no_update
    concept_options = no_update
    institution = no_update
    institution_options = no_update
    reference = no_update
    context = dash.callback_context.triggered[0]['prop_id']
    if context == ".":
        # intial callback
        f = furl(href)
        params = f.query.asdict()['params']
        params_dict = {}
        for param in params:
            params_dict[param[0]] = param[1]
        # concept
        concept = params_dict.get('concept')
        print(concept)
        concept_name = OA_concepts.concepts_names_full.get(concept)
        print(concept_name)
        if concept_name != None:
            concept_name = concept_name.lower()
            concept_options = {key: value for key, value in OA_concepts.concepts_names_full.items() if concept_name in value.lower()}
        # institution
        institution = params_dict.get('institution') 
        institution_name = OA_concepts.institutions_names.get(institution)
        if institution_name != None:
            institution_name = institution_name.lower()
            institution_options = {key: value for key, value in OA_concepts.institutions_names.items() if institution_name in value.lower()}
        reference = params_dict.get('reference')
    elif context == 'ref4_concept_dropdown':
        if not search_value_concept or len(search_value_concept) < 3:
            pass
        else:
            search_value_concept = search_value_concept.lower()
            concept_options = {key: value for key, value in OA_concepts.concepts_names_full.items() if search_value_concept in value.lower()}
    elif context == 'ref4_institution_dropdown':
        if not search_value_institution or len(search_value_institution) < 3:
            pass
        else:
            search_value_institution = search_value_institution.lower()
            institution_options = {key: value for key, value in OA_concepts.institutions_names.items() if search_value_institution in value.lower()}

    print(concept, concept_options, institution, institution_options, reference)
    return concept, concept_options, institution, institution_options, reference


