"""
Tests for FeatureEngine.select_features_by_correlation (Issue #59).
"""
import unittest
import pandas as pd
import numpy as np

from forecasting.feature_engine import FeatureEngine


class TestFeatureSelection(unittest.TestCase):
    """Validates the correlation-based feature selection filter."""

    def test_normal_uncorrelated_features(self):
        """Standard baseline: uncorrelated features (R < 0.90) are left alone."""
        np.random.seed(42)
        df = pd.DataFrame({
            "tmax": np.random.randn(50),
            "average_humidity": np.random.randn(50),
            "pressure_change": np.random.randn(50)
        })
        
        selected, dropped = FeatureEngine.select_features_by_correlation(df, threshold=0.90)
        
        self.assertEqual(dropped, [], "No features should be dropped when uncorrelated")
        self.assertEqual(len(selected), 3, "All 3 original features should remain")

    def test_perfectly_correlated_feature_is_dropped(self):
        """Simulation: Max Temp (tmax) and Sun Duration (tsun) correlate perfectly."""
        np.random.seed(42)
        temp_signal = np.random.randn(50)
        df = pd.DataFrame({
            "tmax": temp_signal,
            "tsun": temp_signal * 2.0, # mathematically perfect correlation
            "prcp": np.random.randn(50)
        })

        selected, dropped = FeatureEngine.select_features_by_correlation(df, threshold=0.90)

        self.assertEqual(len(dropped), 1, "Exactly one feature should be dropped")
        self.assertIn(dropped[0], ["tmax", "tsun"])
        self.assertEqual(len(selected), 2)
        self.assertIn("prcp", selected)

    def test_feature_with_more_nans_is_dropped(self):
        """Tiebreaker: between two correlated features, the one with more NaN values should go."""
        np.random.seed(42)
        temp_signal = np.random.randn(50)
        sun_signal = temp_signal * 2.0
        
        # Inject more NaNs into tsun than tmax
        tmax_with_nans = temp_signal.copy()
        tsun_with_nans = sun_signal.copy()
        tmax_with_nans[0] = np.nan           # tmax has 1 missing day
        tsun_with_nans[0:5] = np.nan         # tsun has 5 missing days

        df = pd.DataFrame({
            "tmax": tmax_with_nans, 
            "tsun": tsun_with_nans, 
            "Pain_Lag_1": np.random.randn(50)
        })

        selected, dropped = FeatureEngine.select_features_by_correlation(df, threshold=0.90)

        self.assertEqual(dropped, ["tsun"], "tsun should be dropped because it has more missing data")
        self.assertIn("tmax", selected)

    def test_alphabetical_tiebreak_is_deterministic(self):
        """When NaN counts are equal, the alphabetically-last column name is dropped."""
        np.random.seed(42)
        temp_signal = np.random.randn(50)
        
        # 'tsun' comes after 'tmax' alphabetically. Both have 0 missing values.
        df = pd.DataFrame({
            "tmax": temp_signal, 
            "tsun": temp_signal * 2.0, 
            "Pain_Lag_1": np.random.randn(50)
        })

        selected, dropped = FeatureEngine.select_features_by_correlation(df, threshold=0.90)

        self.assertEqual(dropped, ["tsun"], "tsun should be dropped (alphabetically after tmax)")
        self.assertIn("tmax", selected)
        self.assertIn("Pain_Lag_1", selected)

    def test_small_dataset_skips_filter(self):
        """With fewer than 30 rows (new user), no features should be dropped to avoid lucky noise."""
        np.random.seed(42)
        temp_signal = np.random.randn(10) # Only 10 days of data
        df = pd.DataFrame({
            "tmax": temp_signal, 
            "tsun": temp_signal * 2.0, 
            "pressure_change": np.random.randn(10)
        })

        selected, dropped = FeatureEngine.select_features_by_correlation(df, threshold=0.90)

        self.assertEqual(dropped, [], "No features should be dropped with N < 30")
        self.assertEqual(len(selected), 3)

    def test_nan_in_correlation_matrix_does_not_crash(self):
        """A numeric column with no variance produces NaN in the correlation matrix; this should not crash."""
        np.random.seed(42)
        df = pd.DataFrame({
            "tmax": np.random.randn(50),
            "tmin": np.random.randn(50),
            "Always_Zero_Padding": [0.0] * 50  # Zero variance → NaN correlations internally
        })

        selected, dropped = FeatureEngine.select_features_by_correlation(df, threshold=0.90)

        self.assertEqual(dropped, [], "No features should be dropped (none are truly correlated)")
        self.assertEqual(len(selected), 3)


if __name__ == "__main__":
    unittest.main()
