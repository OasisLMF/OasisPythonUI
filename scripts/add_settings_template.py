import argparse
import logging
from pathlib import Path
import json

from utils import initialise_client, parse_initialise_args
from utils import LOG_LEVEL

logger = logging.getLogger(__name__)
logging.basicConfig(level=LOG_LEVEL)

def add_model_analysis_settings(client, model_id, analysis_settings_path):
    models = client.models.search({'model_id': str(model_id)}).json()
    if not models:
        logger.warning(f"model id: {model_id} not found")
        return

    analysis_settings_path = Path(analysis_settings_path)
    if not analysis_settings_path.is_file():
        logger.warning(f"analysis settings file for model_id {model_id} not found")
        return

    with open(analysis_settings_path, "r") as f:
        analysis_settings_json = json.load(f)

    # send post to make template
    model_pk = models[0]["id"]
    data = {"name": f"{model_id}_default_settings"}
    resp = client.models.setting_templates.post(model_pk, data=data).json()
    template_id = resp["id"]

    # send post with content
    logger.info(f"[ ] Uploading analysis settings template for {model_id}...")
    resp = client.models.setting_templates.content.post(model_pk, ID=template_id,
                                                        data=analysis_settings_json).json()
    logger.info("[✓] Uploaded")


def main():
    parser = argparse.ArgumentParser(description='Script to add analysis settings template to portfolios')
    parser.add_argument('-c', '--config', default='./a_settings.json',
                        help='Path to analysis settings config file', type=Path)
    parser.add_argument('-r', '--retry', action='store_true',
                        help='Retry initialising client')
    parser.add_argument('-m', '--max-retries', default=10, type=int,
                        help='Max number of retries')
    parser.add_argument('-i', '--retry_interval', default=10, type=int,
                        help='Interval between retries in seconds.')

    args = vars(parser.parse_args())

    # Set up client
    max_retries, retry_interval = parse_initialise_args(**args)
    client = initialise_client(max_retries, retry_interval)

    with open(args['config'], 'r') as f:
        config = json.load(f)

    for model_analysis_config in config:
        add_model_analysis_settings(client, model_analysis_config["model_name_id"],
                                    model_analysis_config["settings_path"])


if __name__=="__main__":
    main()
