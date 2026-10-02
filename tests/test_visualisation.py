import pandas as pd
import pytest
from oasis_data_manager.errors import OasisException

from modules.visualisation import OutputInterface


class TestRequestToFname:
    @pytest.mark.parametrize("output_type, expected", [
        ("eltcalc", "gul_S1_eltcalc.csv"),
        ("aalcalc", "gul_S1_aalcalc.csv"),
        ("pltcalc", "gul_S1_pltcalc.csv"),
        ("elt_moment", "gul_S1_melt.csv"),
        ("elt_quantile", "gul_S1_qelt.csv"),
        ("elt_sample", "gul_S1_selt.csv"),
        ("plt_moment", "gul_S1_mplt.csv"),
        ("plt_quantile", "gul_S1_qplt.csv"),
        ("plt_sample", "gul_S1_splt.csv"),
        ("alt_meanonly", "gul_S1_altmeanonly.csv"),
        ("alt_period", "gul_S1_palt.csv"),
        ("alct_convergence", "gul_S1_alct.csv"),
        ("ept", "gul_S1_ept.csv"),
        ("psept", "gul_S1_psept.csv"),
    ])
    def test_fname_resolution(self, output_type, expected):
        assert OutputInterface._request_to_fname(1, "gul", output_type) == expected

    def test_leccalc_fname_includes_analysis_and_loss_type(self):
        fname = OutputInterface._request_to_fname(
            1, "il", "leccalc",
            analysis_type="full_uncertainty", loss_type="oep")
        assert fname == "il_S1_leccalc_full_uncertainty_oep.csv"

    def test_summary_level_and_perspective_are_used(self):
        assert OutputInterface._request_to_fname(2, "ri", "ept") == "ri_S2_ept.csv"


class TestGet:
    def test_unsupported_output_type_raises(self):
        vis = OutputInterface({})
        with pytest.raises(AssertionError):
            vis.get(1, "gul", "not_a_real_output")

    def test_invalid_perspective_raises(self):
        vis = OutputInterface({})
        with pytest.raises(AssertionError):
            vis.get(1, "not_a_perspective", "ept")

    def test_missing_file_raises_oasis_exception(self):
        vis = OutputInterface({})
        with pytest.raises(OasisException):
            vis.get(1, "gul", "ept")

    def test_returns_transformed_dataframe(self):
        ept_df = pd.DataFrame({
            "EPType": [1, 1],
            "EPCalc": [1, 1],
            "SummaryId": [1, 2],
            "ReturnPeriod": [10, 10],
            "Loss": [100.0, 50.0],
        })
        vis = OutputInterface({"gul_S1_ept.csv": ept_df})
        result = vis.get(1, "gul", "ept")
        pd.testing.assert_frame_equal(result, ept_df)

    def test_applies_oed_fields_join_on_summary_id(self):
        eltcalc_df = pd.DataFrame({
            "type": [1, 2],
            "summary_id": [1, 2],
            "mean": [10.0, 20.0],
        })
        summary_info_df = pd.DataFrame({
            "summary_id": [1, 2],
            "LocNumber": ["loc1", "loc2"],
        })
        vis = OutputInterface({
            "gul_S1_eltcalc.csv": eltcalc_df,
            "gul_S1_summary-info.csv": summary_info_df,
        })
        vis.set_oed_fields("gul", ["LocNumber"])

        result = vis.get(1, "gul", "eltcalc")
        assert result["LocNumber"].tolist() == ["loc1", "loc2"]

    def test_applies_oed_fields_join_on_pascalcase_summary_id(self):
        elt_sample_df = pd.DataFrame({
            "EventId": [1, 2],
            "SummaryId": [1, 2],
            "SampleId": [1, 1],
            "Loss": [10.0, 20.0],
        })
        summary_info_df = pd.DataFrame({
            "summary_id": [1, 2],
            "LocNumber": ["loc1", "loc2"],
        })
        vis = OutputInterface({
            "gul_S1_selt.csv": elt_sample_df,
            "gul_S1_summary-info.csv": summary_info_df,
        })
        vis.set_oed_fields("gul", ["LocNumber"])

        result = vis.get(1, "gul", "elt_sample")
        assert result["LocNumber"].tolist() == ["loc1", "loc2"]


class TestGenerateTransforms:
    @pytest.mark.parametrize("output_type, type_col", [
        ("eltcalc", "type"),
        ("aalcalc", "type"),
        ("pltcalc", "type"),
    ])
    def test_legacy_type_column_mapped_to_analytical_sample(self, output_type, type_col):
        df = pd.DataFrame({type_col: [1, 2]})
        result = getattr(OutputInterface, f"generate_{output_type}")(df.copy())
        assert result[type_col].tolist() == ["Analytical", "Sample"]

    @pytest.mark.parametrize("output_type", [
        "elt_moment", "plt_moment", "alt_meanonly", "alt_period",
    ])
    def test_ord_sample_type_column_mapped_to_analytical_sample(self, output_type):
        df = pd.DataFrame({"SampleType": [1, 2]})
        result = getattr(OutputInterface, f"generate_{output_type}")(df.copy())
        assert result["SampleType"].tolist() == ["Analytical", "Sample"]

    @pytest.mark.parametrize("output_type", [
        "elt_quantile", "elt_sample", "plt_sample", "plt_quantile",
        "alct_convergence", "ept", "psept",
    ])
    def test_passthrough_transforms_are_identity(self, output_type):
        df = pd.DataFrame({"Loss": [1.0, 2.0]})
        result = getattr(OutputInterface, f"generate_{output_type}")(df.copy())
        pd.testing.assert_frame_equal(result, df)

    def test_leccalc_only_maps_type_when_present(self):
        df = pd.DataFrame({"loss": [1.0, 2.0]})
        result = OutputInterface.generate_leccalc(df.copy())
        pd.testing.assert_frame_equal(result, df)
