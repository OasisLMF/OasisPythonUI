import sys
from pathlib import Path

# Allow `python scripts/<script>.py` to import the UI's modules package
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from modules.credentials import service_client_kwargs  # noqa: E402
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
    """Initialise APIClient with retries whilst waiting for the server to come online."""
    logger.info("Initialising client")
    api_url = os.environ.get('API_URL', 'http://ui.oasis.local/api')
    credentials = service_client_kwargs()

    retry_count = 0

    while True:
        try:
            client = APIClient(api_url=api_url, **credentials)
            break
        except (ConnectionError, OasisException) as e:
            logger.error(f'Retry: {retry_count + 1}/{max_retries}.\nFailed to load client: {e}')

        retry_count += 1

        if max_retries <= retry_count:
            print('Failed to load client.')
            return

        time.sleep(retry_interval)

    return client
