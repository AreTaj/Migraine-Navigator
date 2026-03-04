import pytest
import os
import glob
import time
import joblib
from unittest.mock import patch, MagicMock

import forecasting.train_model as tm
import forecasting.inference as inf

# Add project root to path (handled implicitly in pytest if run from root)

@pytest.fixture
def mock_model_dir(tmp_path):
    """
    Fixture to mock MODEL_DIR so we don't pollute the real models directory.
    """
    model_dir = tmp_path / "mock_models"
    os.makedirs(model_dir, exist_ok=True)
    
    # We need to temporarily override the constants in both modules
    original_tm_model_dir = tm.MODEL_DIR
    original_inf_model_dir = inf.MODEL_DIR
    original_tm_clf_path = tm.MODEL_CLF_PATH
    original_tm_reg_path = tm.MODEL_REG_PATH
    original_inf_clf_path = inf.MODEL_CLF_PATH
    original_inf_reg_path = inf.MODEL_REG_PATH
    
    tm.MODEL_DIR = str(model_dir)
    inf.MODEL_DIR = str(model_dir)
    tm.MODEL_CLF_PATH = str(model_dir / 'best_model_clf.pkl')
    tm.MODEL_REG_PATH = str(model_dir / 'best_model_reg.pkl')
    inf.MODEL_CLF_PATH = str(model_dir / 'best_model_clf.pkl')
    inf.MODEL_REG_PATH = str(model_dir / 'best_model_reg.pkl')
    
    yield str(model_dir)
    
    # Teardown
    tm.MODEL_DIR = original_tm_model_dir
    inf.MODEL_DIR = original_inf_model_dir
    tm.MODEL_CLF_PATH = original_tm_clf_path
    tm.MODEL_REG_PATH = original_tm_reg_path
    inf.MODEL_CLF_PATH = original_inf_clf_path
    inf.MODEL_REG_PATH = original_inf_reg_path

def test_model_versioning_and_cleanup(mock_model_dir):
    """
    Test that train_model saves versioned files, updates the pointer, and retains only 2 newest.
    """
    # Use the extracted TrainingManager instead of duplicated logic
    from forecasting.train_model import TrainingManager
    manager = TrainingManager()
    
    # Mock the fit calls so we only test file operations
    manager.clf.fit = MagicMock()
    manager.reg.fit = MagicMock()
    
    # We must actually create files on disk so glob can find them for cleanup testing
    def dummy_dump(model, path):
        with open(path, 'w') as f:
            f.write("dummy")

    import pandas as pd
    import numpy as np
    X_dummy = pd.DataFrame({"A": [1, 2], "B": [3, 4]})
    y_dummy_clf = pd.Series([0, 1])
    y_dummy_reg = pd.Series([5.0, 6.0])
    weights_dummy = np.array([1.0, 1.0])

    with patch('forecasting.train_model.joblib.dump', side_effect=dummy_dump):
        # Simulate saving multiple times to test cleanup
        for _ in range(3):
            # We must sleep briefly because the timestamp is in seconds, 
            # and running it instantly would yield the exact same filename.
            time.sleep(1)
            manager.train_final_and_save(X_dummy, y_dummy_clf, y_dummy_reg, weights_dummy)
                
    # After 3 saves, exactly 2 versions should remain
    clf_files = glob.glob(os.path.join(mock_model_dir, 'best_model_clf_*.pkl'))
    assert len(clf_files) == 2
    
@patch('joblib.load')
@patch('os.path.exists')
@patch('glob.glob')
def test_inference_cache_invalidation(mock_glob, mock_exists, mock_load):
    """
    Test that inference.py clears its cache when a new model version is detected.
    """
    # Setup mock file existence
    mock_exists.return_value = True
    mock_glob.return_value = [os.path.join(inf.MODEL_DIR, 'best_model_clf_2000.pkl')]
    
    # Reset inference globals for clean state
    inf._prediction_cache = {"some_date": "cached_result"}
    inf._clf_model = "old_model"
    inf._reg_model = "old_model"
    inf._loaded_model_version = "1000"
    
    inf.load_models(tester_mode=False)
        
    # Cache should be cleared
    assert len(inf._prediction_cache) == 0
    # Models should be loaded from the "2000" path
    assert inf._loaded_model_version == "2000"
    # joblib.load should have been called twice (clf and reg)
    assert mock_load.call_count == 2
    
    # Check the args passed to joblib.load
    args, kwargs = mock_load.call_args
    # Verify mmap_mode='r' was passed
    assert kwargs.get('mmap_mode') == 'r'

