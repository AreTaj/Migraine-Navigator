import unittest
import pandas as pd
import numpy as np
from forecasting.train_model import ModelConfig, TrainingManager

class TestTrainingManager(unittest.TestCase):

    def test_model_config_defaults(self):
        """Test that configuration initializes with expected shape without executing logic."""
        config = ModelConfig()
        self.assertIn('max_iter', config.clf_params)
        self.assertEqual(config.tscv_splits, 5)
        self.assertEqual(config.recent_data_weight, 3.0)
        self.assertIn('Pain Level', config.exclude_cols)

    def test_custom_config_injection(self):
        """Test that we can inject a custom config to modify the engine's behavior."""
        custom_config = ModelConfig()
        custom_config.tscv_splits = 2
        custom_config.clf_params['max_iter'] = 10
        
        manager = TrainingManager(config=custom_config)
        self.assertEqual(manager.config.tscv_splits, 2)
        # Verify the classifier inherited the config
        self.assertEqual(manager.clf.max_iter, 10)

    def test_cross_validation_logic_isolation(self):
        """Test the cross-validation logic can run without hitting the DB or load scripts."""
        config = ModelConfig()
        config.tscv_splits = 2 # Minimal splits for speed
        manager = TrainingManager(config=config)
        
        # Create a synthetic dataset
        dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
        
        X = pd.DataFrame({
            'Feature_1': np.random.rand(100),
            'Feature_2': np.random.rand(100)
        })
        
        # Binary target (0 or 1)
        y_bin = pd.Series(np.random.randint(0, 2, 100))
        
        # Regression target (float values)
        y_reg = pd.Series(np.random.rand(100) * 5)
        
        # Uniform weights for simplicity
        sample_weights = np.ones(100)
        
        # Execute cross-validation in pure isolation
        acc_scores, split_mae_scores = manager.run_cross_validation(
            X=X, 
            y_bin=y_bin, 
            y_reg=y_reg, 
            sample_weights=sample_weights
        )
        
        # Verify it ran the correct number of splits and returned metrics
        self.assertEqual(len(acc_scores), 2)
        self.assertEqual(len(split_mae_scores), 2)
        
if __name__ == '__main__':
    unittest.main()
