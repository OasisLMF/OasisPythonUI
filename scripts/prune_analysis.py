import os
import datetime
import argparse
import logging
from requests import HTTPError

from utils import initialise_client


def main():
    parser = argparse.ArgumentParser(prog='analysis-prune',
                                     description='Script to delete old analyses.')

    parser.add_argument('-f', '--force', help='Skip confirmation before deleting.',
                        default=False, action=argparse.BooleanOptionalAction)

    parser.add_argument('-d', '--days', help='Number of days of history to preserve (default 7).',
                        default=7, type=int)

    parser.add_argument('--user', help='Username (simple auth). Default: OASIS_SERVICE_USERNAME_OR_ID, '
                        'then .streamlit/secrets.toml.', default=None)

    parser.add_argument('--password', help='Password (simple auth). Prefer OASIS_SERVICE_PASSWORD_OR_SECRET, '
                        'which keeps it out of the process list.', default=None)

    parser.add_argument('--keep-tag', action='append', default=[],
                        help='Never delete analyses whose name ends with this tag, e.g. "[showcase]". '
                             'Can be given more than once.')

    parser.add_argument('--log', help='Set logging level.', default='WARNING')
    parser.add_argument('--retry_time', help='Time between retries (s).', default=60, type=int)
    parser.add_argument('--n_retries', help='Number of retries.', default=30, type=int)

    args = parser.parse_args()

    logging.basicConfig(level=args.log.upper())
    logger = logging.getLogger(__name__)

    week_ago = datetime.datetime.today() - datetime.timedelta(days=args.days)
    week_ago = week_ago.strftime('%Y-%m-%d')

    print('Pruning analyses created before: ', week_ago, flush=True)

    # Same service-account login as the other scripts (env vars, then secrets.toml)
    if args.user:
        os.environ['OASIS_SERVICE_USERNAME_OR_ID'] = args.user
    if args.password:
        os.environ['OASIS_SERVICE_PASSWORD_OR_SECRET'] = args.password
    os.environ.setdefault('API_URL', 'http://localhost:8000')
    client = initialise_client(max_retries=args.n_retries + 1, retry_interval=args.retry_time)
    if client is None:
        logger.error('Failed to create client.')
        print('Client initialisation failed.', flush=True)
        return

    old_analyses = client.analyses.search(metadata={'created__lt': week_ago}).json()
    old_analyses = [a for a in old_analyses if not any(a['name'].endswith(t) for t in args.keep_tag)]
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


if __name__ == "__main__":
    main()
