from oasis_data_manager.errors import OasisException
from oasislmf.platform_api.client import APIClient
from requests.exceptions import ConnectionError
import os
import logging
from requests.exceptions import HTTPError
import streamlit as st
import argparse
from pathlib import Path
import json
import time

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def add_portfolio(client, input_args):
    existing_names = [r['name'] for r in client.portfolios.get().json()]
    logger.info('Adding portfolios...')

    if input_args.get('portfolio_name') in existing_names:
        logger.info(f'Skipping {input_args["portfolio_name"]}')
    else:
        logger.info(f'Adding {input_args["portfolio_name"]}')
        client.upload_inputs(**input_args)

def main():
    parser = argparse.ArgumentParser(description='Script to add portfolios')
    parser.add_argument('-c', '--config', default='./portfolios.json',
                        help='Path to portfolios config file.', type=Path)
    parser.add_argument('-p', '--portfolios', nargs='+', default=None,
                        help='Portfolio(s) to add as described by config file. By default adds all portfolios')
    parser.add_argument('-r', '--retry', action='store_true',
                        help='Retry initialising client')
    parser.add_argument('-m', '--max-retries', default=10, type=int,
                        help='Max number of retries')
    parser.add_argument('-i', '--interval-retries', default=10, type=int,
                        help='Interval between retries in seconds.')

    logger.info("Initialising client")
    api_url = os.environ.get('API_URL', 'http://localhost:8000')
    user = st.secrets.get('user', 'admin')
    password = st.secrets.get('password', 'password')

    args = vars(parser.parse_args())

    retry_count = 0
    if args.get('retry'):
        max_retries = args.get('max_retries')
        logger.info(f'max retries: {max_retries}')
    else:
        logger.info('No retries')
        max_retries = 1

    while True:
        try:
            client =  APIClient(api_url=api_url, username=user, password=password)
            break
        except (ConnectionError, OasisException) as e:
            logger.error(f'Retry: {retry_count+1}/{max_retries}.\nFailed to load client: {e}')

        retry_count += 1

        if max_retries <= retry_count:
            print('Failed to load client.')
            return

        time.sleep(args.get('interval_retries'))


    with open(args['config'], 'r') as f:
        config = json.load(f)

    portfolios = args['portfolios']

    if portfolios is None:
        portfolios = list(config.keys())

    if not all([p in config.keys() for p in portfolios]):
        logger.error(f'Config portfolios: {list(config.keys())}  Selected portfolios: {portfolios}')
        raise Exception('Selected portfolio not in config')

    for p in portfolios:
        input_args = config[p]
        add_portfolio(client, input_args)

if __name__=="__main__":
    main()
