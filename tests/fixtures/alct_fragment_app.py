'''
Standalone script for AppTest coverage of `generate_alct_fragment`.
'''
import pandas as pd

from modules.visualisation import OutputInterface
from pages.components.output import generate_alct_fragment

# Columns as written by oasislmf 2.5's aalpy (-c): one row per sample size
alct_df = pd.DataFrame({
    'SummaryId': [1, 1, 1, 2, 2, 2],
    'MeanLoss': [100.0, 110.0, 105.0, 50.0, 55.0, 52.0],
    'SDLoss': [10.0, 9.0, 8.0, 5.0, 4.5, 4.0],
    'SampleSize': [1, 2, 4, 1, 2, 4],
    'LowerCI': [0.0, 100.0, 101.0, 0.0, 50.0, 50.5],
    'UpperCI': [0.0, 120.0, 109.0, 0.0, 60.0, 53.5],
    'StandardError': [0.0, 5.0, 2.0, 0.0, 2.5, 0.75],
    'RelativeError': [0.0, 0.045, 0.019, 0.0, 0.045, 0.014],
})

summary_info_df = pd.DataFrame({
    'summary_id': [1, 2],
    'LocNumber': ['loc1', 'loc2'],
})

vis = OutputInterface({
    'gul_S1_alct.csv': alct_df,
    'gul_S1_summary-info.csv': summary_info_df,
})
vis.set_oed_fields('gul', ['LocNumber'])

generate_alct_fragment('gul', vis)
