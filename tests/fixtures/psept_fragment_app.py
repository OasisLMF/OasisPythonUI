'''
Standalone script for AppTest coverage of `generate_psept_fragment`.
'''
import pandas as pd

from modules.visualisation import OutputInterface
from pages.components.output import generate_psept_fragment

psept_df = pd.DataFrame({
    'EPType': [1] * 8,
    'SummaryId': [1, 1, 2, 2, 1, 1, 2, 2],
    'SampleId': [1, 2, 1, 2, 1, 2, 1, 2],
    'ReturnPeriod': [10, 10, 10, 10, 100, 100, 100, 100],
    'Loss': [50.0, 60.0, 40.0, 45.0, 500.0, 600.0, 400.0, 450.0],
})

vis = OutputInterface({
    'gul_S1_psept.csv': psept_df,
})

generate_psept_fragment('gul', vis)
