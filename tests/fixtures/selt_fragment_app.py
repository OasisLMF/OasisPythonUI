'''
Standalone script for AppTest coverage of `generate_selt_fragment`.

Builds a minimal `OutputInterface` around a synthetic `elt_sample`
(SELT) output file and renders the fragment for a single perspective,
so the fragment can be exercised without the full app/login stack.
'''
import pandas as pd

from modules.visualisation import OutputInterface
from pages.components.output import generate_selt_fragment

elt_sample_df = pd.DataFrame({
    'EventId': [1, 1, 1, 1, 2, 2, 2, 2],
    'SummaryId': [1, 1, 2, 2, 1, 1, 2, 2],
    'SampleId': [1, 2, 1, 2, 1, 2, 1, 2],
    'Loss': [100.0, 300.0, 50.0, 150.0, 20.0, 40.0, 10.0, 30.0],
})

summary_info_df = pd.DataFrame({
    'summary_id': [1, 2],
    'LocNumber': ['loc1', 'loc2'],
})

locations_df = pd.DataFrame({
    'LocNumber': ['loc1', 'loc2'],
    'Longitude': [-0.1, -0.2],
    'Latitude': [51.5, 51.6],
})

vis = OutputInterface({
    'gul_S1_selt.csv': elt_sample_df,
    'gul_S1_summary-info.csv': summary_info_df,
})
vis.set_oed_fields('gul', ['LocNumber'])

generate_selt_fragment('gul', vis, locations=locations_df)
