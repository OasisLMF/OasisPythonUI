'''
Standalone script for AppTest coverage of `generate_psept_fragment`.

Includes ktools' reserved `SampleId == -1` ("mean_idx") row per
summary/return-period group, matching a real PSEPT file. Its Loss
value is deliberately a huge outlier so a test can assert it was
excluded from the per-sample min/mean/max stats this fragment
computes across the *real* samples.
'''
import pandas as pd

from modules.visualisation import OutputInterface
from pages.components.output import generate_psept_fragment

psept_df = pd.DataFrame({
    'EPType': [1] * 12,
    'SummaryId': [1, 1, 1, 2, 2, 2, 1, 1, 1, 2, 2, 2],
    'SampleId': [1, 2, -1, 1, 2, -1, 1, 2, -1, 1, 2, -1],
    'ReturnPeriod': [10, 10, 10, 10, 10, 10, 100, 100, 100, 100, 100, 100],
    'Loss': [50.0, 60.0, 999.0, 40.0, 45.0, 999.0, 500.0, 600.0, 9999.0, 400.0, 450.0, 9999.0],
})

vis = OutputInterface({
    'gul_S1_psept.csv': psept_df,
})

generate_psept_fragment('gul', vis)
