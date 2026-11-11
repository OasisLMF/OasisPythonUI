'''
Standalone script for AppTest coverage of `generate_alt_fragment` with
a numeric breakdown field (PiWind's `LocNumber` is an integer).
'''
import pandas as pd

from modules.visualisation import OutputInterface
from pages.components.output import generate_alt_fragment

palt_df = pd.DataFrame({
    'SummaryId': [1, 2, 3, 1, 2, 3],
    'SampleType': [1, 1, 1, 2, 2, 2],
    'MeanLoss': [10.0, 20.0, 30.0, 11.0, 21.0, 31.0],
    'SDLoss': [1.0] * 6,
})

summary_info_df = pd.DataFrame({
    'summary_id': [1, 2, 3],
    'LocNumber': [2, 10, 1],
})

vis = OutputInterface({
    'gul_S1_palt.csv': palt_df,
    'gul_S1_summary-info.csv': summary_info_df,
})
vis.set_oed_fields('gul', ['LocNumber'])

generate_alt_fragment('gul', vis, 'alt_period')
