import streamlit as st
import logging
from oasislmf.platform_api.client import APIClient
from oasis_data_manager.errors import OasisException
from requests.exceptions import ConnectionError
import time
import os


LOG_LEVEL = logging.INFO
logger = logging.getLogger(__name__)
logging.basicConfig(level=LOG_LEVEL)

def parse_initialise_args(**kwargs):
    max_retries = 1
    if kwargs.get('retry'):
        max_retries = kwargs.get('max_retries')
        logger.info(f'max retries: {max_retries}')

    retry_interval = kwargs.get('retry_interval')

    return max_retries, retry_interval


def initialise_client(max_retries=1, retry_interval=5):
    '''
    Initialise APIClient with retries whilst waiting for the server to come online.
    '''
    logger.info("Initialising client")
    api_url = os.environ.get('API_URL', 'http://localhost:8000')
    user = st.secrets.get('user', 'admin')
    password = st.secrets.get('password', 'password')

    retry_count = 0

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

        time.sleep(retry_interval)

    return client
