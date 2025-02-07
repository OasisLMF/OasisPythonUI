from pathlib import Path
import re

def get_analyses_settings(defaults_path=None, model_id=None, model_name_id=None,
                          supplier_id=None):
    if defaults_path is None:
        defaults_path = 'defaults/'

    defaults_path = Path(defaults_path)

    if model_id is None:
        model_id = r'\d+'
    if model_name_id is None:
        model_name_id = r'[\w-]+'
    if supplier_id is None:
        supplier_id = r'[\w-]+'

    # Format model name and supplier name
    model_name_id = model_name_id.replace(' ', '-')
    supplier_id = supplier_id.replace(' ', '-')

    settings_pattern = f'{model_id}_{model_name_id}_{supplier_id}' + r'-analysis_settings\.json'

    settings_files = [str(p) for p in defaults_path.iterdir() if re.search(settings_pattern, str(p), re.IGNORECASE)]

    return settings_files
