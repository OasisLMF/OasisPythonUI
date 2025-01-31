from oasislmf.platform_api.client import APIClient
import os
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def main():
    # Initialise client
    logger.info("Initialising client")
    api_url = os.environ.get('API_URL', 'http://localhost:8000')
    username = "admin"
    password = "password"
    client = APIClient(username=username, password=password, api_url=api_url)


    logger.info("Finding PiWind...")
    # Get portfolio files
    piwind_path = './OasisPiWind/'

    # Check if PiWind can be found
    if not os.path.exists(piwind_path):

        logger.error("PiWind not found")
        return 1

    input_path = os.path.join(piwind_path, 'tests/inputs')

    piwind_small_args = {
        'portfolio_name': 'piwind-small',
        'location_f': os.path.join(input_path, 'SourceLocOEDPiWind10.csv'),
        'accounts_f': os.path.join(input_path, 'SourceAccOEDPiWind.csv'),
        'ri_info_f': os.path.join(input_path, 'SourceReinsInfoOEDPiWind.csv'),
        'ri_scope_f': os.path.join(input_path, 'SourceReinsScopeOEDPiWind.csv'),
    }

    piwind_large_args = piwind_small_args.copy()
    piwind_large_args['portfolio_name'] = 'piwind-large'
    piwind_large_args['location_f'] = os.path.join(input_path, 'SourceLocOEDPiWind.csv')

    existing_names = [r['name'] for r in client.portfolios.get().json()]
    logger.info('Adding portfolios...')
    if piwind_small_args['portfolio_name'] in existing_names:
        logger.info(f'Skipping {piwind_small_args["portfolio_name"]}')
    else:
        logger.info(f'Adding {piwind_small_args["portfolio_name"]}')
        client.upload_inputs(**piwind_small_args)
    if piwind_large_args['portfolio_name'] in existing_names:
        logger.info(f'Skipping {piwind_large_args["portfolio_name"]}')
    else:
        logger.info(f'Adding {piwind_large_args["portfolio_name"]}')
        client.upload_inputs(**piwind_large_args)

if __name__=="__main__":
    main()
