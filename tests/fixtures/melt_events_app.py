"""Standalone script: a MELT with two events and both Analytical (1) and Sample (2) rows."""
import pandas as pd

from modules.visualisation import OutputInterface
from pages.components.output import generate_melt_fragment

melt = pd.DataFrame({
    'EventId': [1, 1, 2, 2],
    'SummaryId': [1, 1, 1, 1],
    'SampleType': [1, 2, 1, 2],
    'EventRate': [0.0] * 4,
    'ChanceOfLoss': [1.0] * 4,
    'MeanLoss': [100.0, 110.0, 400.0, 420.0],
    'SDLoss': [0.0] * 4,
    'MaxLoss': [0.0] * 4,
    'FootprintExposure': [0.0] * 4,
    'MeanImpactedExposure': [0.0] * 4,
    'MaxImpactedExposure': [0.0] * 4,
})
generate_melt_fragment('gul', OutputInterface({'gul_S1_melt.csv': melt}))
