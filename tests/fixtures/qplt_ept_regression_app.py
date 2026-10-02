'''
Regression fixture: `generate_qplt_fragment` and `generate_ept_fragment`
rendered together for the same perspective. `generate_ept_fragment`
used to reuse QPLT's OED-field pills key (`qplt_{p}_group_field_pills`)
and had no key at all on its two EP Curve Type / Calculation Method
radios, so showing both QPLT and EPT for one perspective raised a
Streamlit duplicate-widget-key error.
'''
import pandas as pd

from modules.visualisation import OutputInterface
from pages.components.output import generate_qplt_fragment, generate_ept_fragment

plt_quantile_df = pd.DataFrame({
    'Quantile': [0.5, 0.5, 0.95, 0.95],
    'SummaryId': [1, 2, 1, 2],
    'Year': [2020, 2020, 2020, 2020],
    'Month': [1, 1, 1, 1],
    'Day': [1, 1, 1, 1],
    'Loss': [10.0, 20.0, 30.0, 40.0],
})

ept_df = pd.DataFrame({
    'EPType': [1, 1, 1, 1, 3, 3, 3, 3],
    'EPCalc': [1, 1, 2, 2, 1, 1, 2, 2],
    'SummaryId': [1, 2, 1, 2, 1, 2, 1, 2],
    'ReturnPeriod': [10, 10, 10, 10, 10, 10, 10, 10],
    'Loss': [50.0, 40.0, 55.0, 42.0, 500.0, 400.0, 505.0, 402.0],
})

summary_info_df = pd.DataFrame({
    'summary_id': [1, 2],
    'LocNumber': ['loc1', 'loc2'],
})

vis = OutputInterface({
    'gul_S1_qplt.csv': plt_quantile_df,
    'gul_S1_ept.csv': ept_df,
    'gul_S1_summary-info.csv': summary_info_df,
})
vis.set_oed_fields('gul', ['LocNumber'])

generate_qplt_fragment('gul', vis)
generate_ept_fragment('gul', vis)
