from oasislmf.platform_api.client import APIClient
import os
import datetime
import argparse
import logging
from requests import HTTPError

logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(prog='analysis-prune',
                                     description='Script to delete old analyses.')

    parser.add_argument('-f', '--force', help='Skip confirmation before deleting.',
                        default=False, action=argparse.BooleanOptionalAction)

    parser.add_argument('-d', '--days', help='Number of days of history to preserve (default 7).',
                        default=7, type=int)

    args = parser.parse_args()

    week_ago = datetime.datetime.today() - datetime.timedelta(days=args.days)
    week_ago = week_ago.strftime('%Y-%m-%d')

    print('Pruning analyses created before: ', week_ago)

    client = APIClient()
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
