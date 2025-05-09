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

def add_piwind_small_alt(client):
    path = './OasisPiWind/'
    # Check if PiWind can be found
    if not os.path.exists(path):
        logger.error("PiWind not found")
        return 1

    input_path = os.path.join(path, 'tests/inputs')

    input_args = {
        'portfolio_name': 'piwind-small-alt',
        'location_f': os.path.join(input_path, 'SourceLocOEDPiWind10Alt.csv'),
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

def add_maeq(client):
    pname = 'maeq-test'
    path = '../models/MAEQ/1.0.0/'

    if not os.path.exists(path):
        logger.error(f"{pname} not found")
        return 1

    input_path = os.path.join(path, 'tests/')

    input_args = {
        'portfolio_name': pname,
        'location_f': os.path.join(input_path, 'MAEQ_100_oasis.csv'),
        'accounts_f': os.path.join(input_path, 'MAEQ_acc.csv'),
    }

    add_portfolio(client, input_args)

def add_trek(client):
    pname = 'treq-test'
    path = '../models/TREQ/1.0.0/'

    if not os.path.exists(path):
        print(path)
        logger.error(f"{pname} not found")
        return 1

    input_path = os.path.join(path, 'tests/')

    input_args = {
        'portfolio_name': pname,
        'location_f': os.path.join(input_path, 'TREQ_P_test_loc_100.csv'),
        'accounts_f': os.path.join(input_path, 'TREQ_acc.csv'),
    }

    add_portfolio(client, input_args)

def add_maeq_lat_long(client):
    pname = 'maeq-test-ll'
    path = '../models/MAEQ/1.0.0/'

    if not os.path.exists(path):
        logger.error(f"{pname} not found")
        return 1

    input_path = os.path.join(path, 'tests/')

    input_args = {
        'portfolio_name': pname,
        'location_f': os.path.join(input_path, 'MAEQ_100_oasis_lat_long.csv'),
        'accounts_f': os.path.join(input_path, 'MAEQ_acc.csv'),
    }

    add_portfolio(client, input_args)

def add_euws_lat_long(client):
    pname = 'euws-test-ll'
    path = '../models/EUWS/1.0.0/'

    if not os.path.exists(path):
        logger.error(f"{pname} not found")
        return 1

    input_path = os.path.join(path, 'tests/')

    input_args = {
        'portfolio_name': pname,
        'location_f': os.path.join(input_path, 'EUWS_200_oasis_lat_long.csv'),
        'accounts_f': os.path.join(input_path, 'EUWS_acc.csv'),
    }

    add_portfolio(client, input_args)

def add_euws(client):
    pname = 'euws-test'
    path = '../models/EUWS/1.0.0/'

    if not os.path.exists(path):
        logger.error(f"{pname} not found")
        return 1

    input_path = os.path.join(path, 'tests/')

    input_args = {
        'portfolio_name': pname,
        'location_f': os.path.join(input_path, 'EUWS_200_oasis.csv'),
        'accounts_f': os.path.join(input_path, 'EUWS_acc.csv'),
    }

    add_portfolio(client, input_args)

def add_phty_taiwan(client):
    pname = 'phty-taiwan'
    path = '../models/PHTY/tests/inputs/'

    if not os.path.exists(path):
        logger.error(f"{pname} not found")
        return 1

    input_args = {
        'portfolio_name': pname,
        'location_f': os.path.join(path, 'locationTW_diff3.csv')
    }

    add_portfolio(client, input_args)

def add_us_flat(client):
    pname = 'us-flat'
    path = '../models/US_Hurricane/tests/test_1/'

    if not os.path.exists(path):
        logger.error(f"{pname} not found")
        return 1

    input_args = {
        'portfolio_name': pname,
        'location_f': os.path.join(path, 'locationFlat.csv')
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
        'piwind-large': add_piwind_large,
        'piwind-small-alt': add_piwind_small_alt,
        'maeq': add_maeq,
        'maeq-ll': add_maeq_lat_long,
        'euws': add_euws,
        'euws-ll': add_euws_lat_long,
        'trek' : add_trek,
        'phty-tw': add_phty_taiwan,
        'us-flat': add_us_flat
    }

    for p in portfolios:
        assert p in function_map.keys(), 'Portfolio not found'
        function_map[p](client)
