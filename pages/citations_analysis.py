from openalex_analysis.plot import config, WorksPlot, get_info_about_entitie_from_api, check_if_entity_exists_from_api
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
                    dcc.Dropdown(id='4_concept_dropdown', clearable=True, placeholder='Type at least 3 characters (for example "Sustainability")',),
                    html.H3(children="Institution"),
                    html.P(children="The analysis will use only the works of this institution to compute where does the citations come from:"),
                    dcc.Dropdown(id='4_institution_dropdown', clearable=True, placeholder='Type at least 5 characters (for example "Stockholm Resilience Centre")',),
                    html.H3(children="Reference"),
                    html.P(children="The article cited on which we want to know who cited it:"),
                    dbc.Row(
                        [
                            dbc.Col(
                                dbc.Input(id="4_reference_text",
                                          type="text",
                                          placeholder='Type the article OpenAlex ID (for example "W1999167944")',
                                          pattern=u"W\d+$",
                                         ),
                                sm = 10, md = 8
                            ),
                            dbc.Col(dbc.Button(id="4_btn_validate_reference_text",
                                children="Validate this reference",
                                disabled=False,
                            )),
                        ]
                    ),
                    dcc.Location(id='url', refresh=False),
                    dbc.Alert(id='4_reference_description', color="danger"),
                    dcc.Store(id='4_reference'),
                    "",
                    html.H2(children="Analysis"),
                    dbc.Button(id='4_start_analysis_btn',
                        children="Start the analysis",
                        disabled=True,),
                ],
                **layout_parameters.layout_dynamic_width,
            ),
        ],
    ),
    dbc.Row(justify="center", style={'margin': '1em 1em'}, children=
        [
            dbc.Col(
                [
                    html.H3(children="Works citing the reference"),
                    html.Div(id='4_div_table_works', children=dash_table.DataTable(id='4_table_works')),
                    html.Br(),
                    html.H3(children="Authors using the reference"),
                    html.Div(id='4_div_table_authors', children=dash_table.DataTable(id='4_table_authors')),
                ]
            )
        ]
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
                Output('4_concept_dropdown', 'value'),
                Output('4_concept_dropdown', 'options'),
                Output('4_institution_dropdown', 'value'),
                Output('4_institution_dropdown', 'options'),
                Output('4_reference_text', 'value')
              ],
              [
                Input('url', 'href'),
                Input('4_concept_dropdown', 'search_value'),
                Input('4_institution_dropdown', 'search_value')
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
        concept_name = OA_concepts.concepts_names_full.get(concept)
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
    elif context == '4_concept_dropdown.search_value':
        if not search_value_concept or len(search_value_concept) < 3:
            pass
        else:
            search_value_concept = search_value_concept.lower()
            concept_options = {key: value for key, value in OA_concepts.concepts_names_full.items() if search_value_concept in value.lower()}
    elif context == '4_institution_dropdown.search_value':
        if not search_value_institution or len(search_value_institution) < 3:
            pass
        else:
            search_value_institution = search_value_institution.lower()
            institution_options = {key: value for key, value in OA_concepts.institutions_names.items() if search_value_institution in value.lower()}

    return concept, concept_options, institution, institution_options, reference




@app.callback(
    Output('4_btn_validate_reference_text', 'disabled'),
    [
        Input('4_reference_text', 'value'),
        Input('4_btn_validate_reference_text', 'n_clicks'),
    ],
)
def update_button_validate_reference(reference, n_clicks):
    context = dash.callback_context.triggered[0]['prop_id']
    if context == '4_btn_validate_reference_text.n_clicks':
        return True
    else:
        return False


@app.callback(
    [
        Output('4_reference_description', 'children'),
        Output('4_reference_description', 'color'),
        Output('4_reference', 'data'),
    ],
    Input('4_btn_validate_reference_text', 'n_clicks'),
    State('4_reference_text', 'value'),
    prevent_initial_call=True,
)
def update_reference_description(n_clicks, reference):
    print("##################################")
    print("ref", reference)
    reference_exists = check_if_entity_exists_from_api(reference)
    print(reference_exists)
    if reference_exists == False:
        return "The reference doesn't exists", "danger", None
    reference_info = get_info_about_entitie_from_api(reference, infos = works_infos, return_as_pd_serie = False)
    print(reference_info['doi'])
    div_children = [
                html.A(reference_info['display_name'], href=reference_info['doi'], target="_blank"),
                html.Br(),
                reference_info['author_citation_style'],
                html.Br(),
                "Publication year: "+str(reference_info['publication_year']),
            ]
    
    return div_children, "success", reference


@app.callback(
    Output('4_start_analysis_btn', 'disabled'),
    [
        Input('4_concept_dropdown', 'value'),
        Input('4_institution_dropdown', 'value'),
        Input('4_reference', 'data'),
    ],
    prevent_initial_call=True,
)
def update_button_start_references_analysis_disabled_status(concept, institution, reference):
    disabled_download_btn = True
    if concept != None and institution != None and reference != None:
        disabled_download_btn = False
    return disabled_download_btn


def get_dash_table_works_citing(wplt):
    df = wplt.entities_df[['id', 'doi', 'display_name', 'author_citation_style', 'publication_year']].copy()
    # sort by publication date:
    df = df.sort_values(by=['publication_year'], ascending=False)
    # reordre the columns:
    df = df[['display_name', 'author_citation_style', 'publication_year', 'doi', 'id']]
    df = df.rename(columns={
        'display_name': 'Title',
        'author_citation_style': 'Authors',
        'publication_year': 'Year',
        'doi': 'DOI',
        'id': 'OpenAlex ID',
    })
    table = dash_table.DataTable(
        df.to_dict('records', index = True),
        [{"name": i, "id": i} for i in df.columns],
        id = '4_table_works',
        style_cell = layout_parameters.dash_table_style_cell,
        # style_data_conditional = dash_table_ref_conditional_style,
        style_data_conditional = [
            {
                'if': {'column_id': c},
                'width': '170px'
            } for c in df.columns
        ] + [
            {
                'if': {'column_id': 'Title'},
                 'width': '350px'
            },
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': 'rgb(240, 240, 240)',
            },
        ],
        style_header = layout_parameters.dash_table_style_header,
        # fixed_columns={'headers': True, 'data': 1},
        style_table={'minWidth': '100%', 'overflowX': 'auto'},
        page_size=20,
    )
    return table


def get_dash_table_authors_citing(wplt):
    df = wplt.get_authors_count()
    # reordre the columns:
    df = df[['author.display_name', 'count', 'raw_affiliation_string', 'author.orcid', 'author.id']]
    df = df.rename(columns={
        'author.display_name': 'Authors',
        'count': 'Count',
        'raw_affiliation_string': 'Affiliation',
        'author.orcid': 'ORCID',
        'author.id': 'OpenAlex ID',
    })
    table = dash_table.DataTable(
        df.to_dict('records', index = True),
        [{"name": i, "id": i} for i in df.columns],
        id = '4_table_authors',
        style_cell = layout_parameters.dash_table_style_cell,
        # style_data_conditional = dash_table_ref_conditional_style,
        style_data_conditional = [
            {
                'if': {'column_id': c},
                'width': '170px'
            } for c in df.columns
        ] + [
            {
                'if': {'column_id': 'Authors'},
                 'width': '350px'
            },
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': 'rgb(240, 240, 240)',
            },
        ],
        style_header = layout_parameters.dash_table_style_header,
        # fixed_columns={'headers': True, 'data': 1},
        style_table={'minWidth': '100%', 'overflowX': 'auto'},
        page_size=20,
    )
    print("coucou")
    return table


@app.callback(
    [
        Output('4_div_table_works', 'children'),
        Output('4_div_table_authors', 'children'),
    ],
    Input('4_start_analysis_btn', 'n_clicks'),
    State('4_concept_dropdown', 'value'),
    State('4_institution_dropdown', 'value'),
    State('4_reference', 'data'),
    prevent_initial_call=True,
)
def analyse_reference_citations(n_clicks, concept, institution, reference):
    extra_filters = {
        'cites':reference,
        'institutions':{'id':institution},
    }
    wplt = WorksPlot(concept, extra_filters = extra_filters)
    wplt.add_authorships_citation_style()
    table_works = get_dash_table_works_citing(wplt)
    table_authors = get_dash_table_authors_citing(wplt)
    
    return table_works, table_authors

