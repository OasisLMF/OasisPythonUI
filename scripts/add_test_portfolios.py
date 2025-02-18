from oasislmf.platform_api.client import APIClient
import os
import logging
import sys
import streamlit as st

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def add_portfolio(client, input_args):
    existing_names = [r['name'] for r in client.portfolios.get().json()]
    logger.info('Adding portfolios...')

    if input_args.get('name') and input_args.get('name') in existing_names:
        logger.info(f'Skipping {input_args["name"]}')
    else:
        logger.info(f'Adding {input_args["portfolio_name"]}')
        client.upload_inputs(**input_args)


def add_piwind_small(client):
    path = './OasisPiWind/'
    # Check if PiWind can be found
    if not os.path.exists(path):
        logger.error("PiWind not found")
        return 1

    input_path = os.path.join(path, 'tests/inputs')

    input_args = {
        'portfolio_name': 'piwind-small',
        'location_f': os.path.join(input_path, 'SourceLocOEDPiWind10.csv'),
        'accounts_f': os.path.join(input_path, 'SourceAccOEDPiWind.csv'),
        'ri_info_f': os.path.join(input_path, 'SourceReinsInfoOEDPiWind.csv'),
        'ri_scope_f': os.path.join(input_path, 'SourceReinsScopeOEDPiWind.csv'),
    }

    add_portfolio(client, input_args)


def add_piwind_large(client):
    path = './OasisPiWind/'
    # Check if PiWind can be found
    if not os.path.exists(path):
        logger.error("PiWind not found")
        return 1

    input_path = os.path.join(path, 'tests/inputs')

    input_args = {
        'portfolio_name': 'piwind-large',
        'location_f': os.path.join(input_path, 'SourceLocOEDPiWind.csv'),
        'accounts_f': os.path.join(input_path, 'SourceAccOEDPiWind.csv'),
        'ri_info_f': os.path.join(input_path, 'SourceReinsInfoOEDPiWind.csv'),
        'ri_scope_f': os.path.join(input_path, 'SourceReinsScopeOEDPiWind.csv'),
    }

    add_portfolio(client, input_args)

if __name__=="__main__":
    logger.info("Initialising client")
    api_url = os.environ.get('API_URL', 'http://localhost:8000')
    user = st.secrets.get('user', 'admin')
    password = st.secrets.get('password', 'password')
    client =  APIClient(api_url=api_url, username=user, password=password)
    if len(sys.argv) > 1:
        portfolios = sys.argv[1:]
    else:
        portfolios = ['piwind-small', 'piwind-large']

    function_map = {
        'piwind-small':  add_piwind_small,
        'piwind-large': add_piwind_large
    }

    for p in portfolios:
        assert p in function_map.keys(), 'Portfolio not found'
        function_map[p](client)
