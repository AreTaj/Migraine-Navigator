import unittest
from services.entry_service import EntryService

class TestEntrySanitization(unittest.TestCase):
    
    def test_key_remapping(self):
        # Test mapping Pain_Level to Pain Level and Physical_Activity to Physical Activity
        data = {
            'Pain_Level': 7,
            'Physical_Activity': 'Moderate',
            'Notes': 'Test'
        }
        sanitized = EntryService.sanitize_entry(data)
        self.assertIn('Pain Level', sanitized)
        self.assertEqual(sanitized['Pain Level'], 7)
        self.assertNotIn('Pain_Level', sanitized)
        
        self.assertIn('Physical Activity', sanitized)
        self.assertEqual(sanitized['Physical Activity'], 'Moderate')
        self.assertNotIn('Physical_Activity', sanitized)
        self.assertEqual(sanitized['Notes'], 'Test')

    def test_legacy_key_remapping(self):
        # Test weather_pressure remapping
        data = {
            'weather_pressure': 1012.5,
            'Pain Level': 5
        }
        sanitized = EntryService.sanitize_entry(data)
        self.assertIn('pressure', sanitized)
        self.assertEqual(sanitized['pressure'], 1012.5)
        self.assertNotIn('weather_pressure', sanitized)

    def test_geodata_patching_unknown(self):
        # Test that 'Unknown' or empty geodata becomes None
        data = {
            'Latitude': 'Unknown',
            'Longitude': 'unknown',
            'Pain Level': 3
        }
        sanitized = EntryService.sanitize_entry(data)
        self.assertIsNone(sanitized['Latitude'])
        self.assertIsNone(sanitized['Longitude'])
        self.assertEqual(sanitized['Pain Level'], 3)

    def test_geodata_patching_empty_string(self):
        data = {
            'Latitude': '',
            'Longitude': '   ',
            'Pain Level': 3
        }
        sanitized = EntryService.sanitize_entry(data)
        self.assertIsNone(sanitized['Latitude'])
        self.assertIsNone(sanitized['Longitude'])

    def test_geodata_patching_empty_array_string(self):
        data = {
            'Latitude': '[]',
            'Longitude': '[]',
            'Pain Level': 3
        }
        sanitized = EntryService.sanitize_entry(data)
        self.assertIsNone(sanitized['Latitude'])
        self.assertIsNone(sanitized['Longitude'])

    def test_geodata_valid_values_preserved(self):
        # Valid values should not be touched by the sanitizer
        # (they get cast to floats later in add_entry persistence or schema if needed)
        data = {
            'Latitude': 34.05,
            'Longitude': -118.24,
            'Pain Level': 3
        }
        sanitized = EntryService.sanitize_entry(data)
        self.assertEqual(sanitized['Latitude'], 34.05)
        self.assertEqual(sanitized['Longitude'], -118.24)

if __name__ == '__main__':
    unittest.main()
