from oasislmf.platform_api.client import APIClient
from oasis_data_manager.errors import OasisException
import time
import os
import datetime
import argparse
import logging
from requests import HTTPError



def main():
    parser = argparse.ArgumentParser(prog='analysis-prune',
                                     description='Script to delete old analyses.')

    parser.add_argument('-f', '--force', help='Skip confirmation before deleting.',
                        default=False, action=argparse.BooleanOptionalAction)

    parser.add_argument('-d', '--days', help='Number of days of history to preserve (default 7).',
                        default=7, type=int)

    parser.add_argument('--user', help='Username for oasislmf client.',
                        default='admin')

    parser.add_argument('--password', help='Password for oasislmf client.',
                        default='password')

    parser.add_argument('--log', help='Set logging level.', default='WARNING')
    parser.add_argument('--retry_time', help='Time between retries (s).', default=60, type=int)
    parser.add_argument('--n_retries', help='Number of retries.', default=30, type=int)

    args = parser.parse_args()

    logging.basicConfig(level=args.log.upper())
    logger = logging.getLogger(__name__)

    week_ago = datetime.datetime.today() - datetime.timedelta(days=args.days)
    week_ago = week_ago.strftime('%Y-%m-%d')

    print('Pruning analyses created before: ', week_ago)

    api_url = os.environ.get('API_URL', 'http://localhost:8000')
    retries = 0
    while True:
        if retries > args.n_retries:
            logger.error(f'Failed to create client. No. of retries: {retries}')
            print('Client intialisation failed.')
            return
        try:
            client = APIClient(username=args.user,
                               password=args.password,
                               api_url=api_url)
            break
        except OasisException:
            logger.debug(f'Client initialisation failed. Attempt {retries}/{args.n_retries}')
            retries += 1
            time.sleep(args.retry_time)

    old_analyses = client.analyses.search(metadata={'created__lt': week_ago}).json()
    analysis_ids = [a['id'] for a in old_analyses]

    confirmed = 'n'
    if not args.force:
        print('Deleting the following analyses: ')
        for analysis in old_analyses:
            print(f"{analysis['id']} : {analysis['name']}")

        while True:
            try:
                confirmed = input('Confirm deletion [y/n]: ')
                if confirmed not in ['y', 'n', 'Y', 'N']:
                    raise ValueError
                break
            except ValueError:
                print('Invalid input. Please enter y/n')

    if args.force or confirmed in ['y', 'Y']:
        for id in analysis_ids:
            try:
                client.analyses.delete(id)
                print(f'Anlaysis #{id} deleted.')
            except HTTPError:
                logger.error(f'Failed to delete: {id}.')

if __name__=="__main__":
    main()
