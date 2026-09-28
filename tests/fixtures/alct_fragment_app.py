'''
Standalone script for AppTest coverage of `generate_alct_fragment`.
'''
import pandas as pd

from modules.visualisation import OutputInterface
from pages.components.output import generate_alct_fragment

alct_df = pd.DataFrame({
    'SummaryId': [1, 2],
    'SampleSize': [1000, 1000],
    'MeanLoss': [123.45, 67.89],
    'SEMean': [1.23, 0.98],
    'VarianceLoss': [45.6, 12.3],
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
