"""Standalone script: results whose settings request an output the run didn't produce."""
import pandas as pd

from pages.components.results import render_results

settings = {'gul_output': True, 'gul_summaries': [{'id': 1, 'ord_output': {'alt_meanonly': True}}]}
render_results(settings, {'gul_S1_selt.csv': pd.DataFrame({'Loss': [1.0]})})
