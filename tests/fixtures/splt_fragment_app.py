'''
Standalone script for AppTest coverage of `generate_splt_fragment`.
'''
import pandas as pd

from modules.visualisation import OutputInterface
from pages.components.output import generate_splt_fragment

plt_sample_df = pd.DataFrame({
    'SummaryId': [1, 1, 2, 2, 1, 1, 2, 2],
    'SampleId': [1, 2, 1, 2, 1, 2, 1, 2],
    'Year': [2020, 2020, 2020, 2020, 2021, 2021, 2021, 2021],
    'Month': [1, 1, 1, 1, 6, 6, 6, 6],
    'Day': [1, 1, 1, 1, 15, 15, 15, 15],
    'Loss': [10.0, 20.0, 15.0, 25.0, 5.0, 8.0, 6.0, 9.0],
})

summary_info_df = pd.DataFrame({
    'summary_id': [1, 2],
    'LocNumber': ['loc1', 'loc2'],
})

vis = OutputInterface({
    'gul_S1_splt.csv': plt_sample_df,
    'gul_S1_summary-info.csv': summary_info_df,
})
vis.set_oed_fields('gul', ['LocNumber'])

generate_splt_fragment('gul', vis)
