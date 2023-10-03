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

# PAGE 3


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
                    html.H1(children="Analysis of an institution"),
                    html.H3(children="Institution to analyse"),
                    dcc.Dropdown(id='ref3_institutions_dropdown', clearable=True, placeholder='Type at least 5 characters (for example "Stockholm Resilience Centre")',),
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


@app.callback(
    Output("ref3_institutions_dropdown", "options"),
    Input("ref3_institutions_dropdown", "search_value")
)
def update_options_ref3_institutions_dropdown(search_value):
    if not search_value or len(search_value) < 5:
        # return {}
        raise PreventUpdate
    search_value = search_value.lower()
    # return [o for o in OA_concepts.concepts_names_full if search_value in OA_concepts.concepts_names_full[o]]
    return {key: value for key, value in OA_concepts.institutions_names.items() if search_value in value.lower()}


