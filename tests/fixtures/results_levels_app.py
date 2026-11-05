'''
Standalone script for AppTest coverage of summary level selection in
`render_results`: two GUL summary levels, each with an EPT whose losses
identify the level (level 1 losses are 100s, level 2 losses are 200s).
'''
import pandas as pd

from pages.components.results import render_results


def ept(base):
    return pd.DataFrame({
        'SummaryId': [1] * 4,
        'EPCalc': [2, 2, 1, 1],
        'EPType': [1, 1, 1, 1],
        'ReturnPeriod': [10.0, 100.0, 10.0, 100.0],
        'Loss': [base + 1, base + 2, base + 3, base + 4],
    })


settings = {
    'gul_output': True,
    'gul_summaries': [
        {'id': 1, 'ord_output': {'ept_full_uncertainty_aep': True}},
        {'id': 2, 'oed_fields': ['LocNumber'], 'ord_output': {'ept_full_uncertainty_aep': True}},
    ],
}
outputs = {
    'gul_S1_ept.csv': ept(100),
    'gul_S2_ept.csv': ept(200),
    'gul_S2_summary-info.csv': pd.DataFrame({'summary_id': [1], 'LocNumber': ['loc-1']}),
}
render_results(settings, outputs)
