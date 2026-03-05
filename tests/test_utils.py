import unittest
import os
import sys
from unittest.mock import patch

# Add project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api.utils import get_db_path, list_databases

class TestUtils(unittest.TestCase):
    @patch('api.utils.get_data_dir')
    def test_get_db_path_sanitization(self, mock_data_dir):
        mock_data_dir.return_value = '/mock/data/dir'
        
        # Default
        self.assertEqual(get_db_path(), '/mock/data/dir/migraine_log.db')
        
        # Valid custom DB
        self.assertEqual(get_db_path('custom.db'), '/mock/data/dir/custom.db')
        
        # Invalid extension fallback
        self.assertEqual(get_db_path('custom.csv'), '/mock/data/dir/migraine_log.db')
        
        # Path traversal mitigation
        self.assertEqual(get_db_path('../../etc/passwd.db'), '/mock/data/dir/passwd.db')

    @patch('api.utils.get_data_dir')
    @patch('os.path.isdir')
    @patch('os.listdir')
    @patch('os.path.getsize')
    def test_list_databases_excludes_empty(self, mock_getsize, mock_listdir, mock_isdir, mock_data_dir):
        mock_data_dir.return_value = '/mock/data/dir'
        mock_isdir.return_value = True
        
        # Simulate directory contents
        mock_listdir.return_value = [
            'migraine_log.db', 
            'empty_skeleton.db',
            'random.txt',
            'valid_import.db'
        ]
        
        # Mock file sizes
        def mock_size(path):
            sizes = {
                '/mock/data/dir/migraine_log.db': 15000,   # Valid size
                '/mock/data/dir/empty_skeleton.db': 2048,  # Below 4KB threshold (empty)
                '/mock/data/dir/random.txt': 50000,
                '/mock/data/dir/valid_import.db': 10240    # Valid size
            }
            return sizes.get(path, 0)
            
        mock_getsize.side_effect = mock_size
        
        dbs = list_databases()
        
        # Should only include .db files >= 4096 bytes
        self.assertEqual(len(dbs), 2)
        self.assertIn('migraine_log.db', dbs)
        self.assertIn('valid_import.db', dbs)
        self.assertNotIn('empty_skeleton.db', dbs)
        self.assertNotIn('random.txt', dbs)

if __name__ == '__main__':
    unittest.main()
