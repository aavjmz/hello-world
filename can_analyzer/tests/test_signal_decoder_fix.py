"""
Test signal decoder NamedSignalValue fix

Verifies that NamedSignalValue objects from cantools are handled correctly
"""

import unittest
from unittest.mock import Mock
from utils.signal_decoder import SignalDecoder, SignalValue, DecodedMessage
from utils.dbc_manager import DBCManager


class MockNamedSignalValue:
    """Mock class simulating cantools NamedSignalValue"""
    def __init__(self, value):
        self.value = value


class TestSignalDecoderFix(unittest.TestCase):
    """Test cases for NamedSignalValue handling"""

    def setUp(self):
        """Set up test fixtures"""
        self.dbc_manager = Mock(spec=DBCManager)
        self.decoder = SignalDecoder(self.dbc_manager)

    def test_format_named_signal_value_float(self):
        """Test formatting NamedSignalValue with float"""
        # Create mock NamedSignalValue
        named_value = MockNamedSignalValue(12.5)

        # Format it
        result = self.decoder._format_signal_value(named_value)

        # Should extract the value
        self.assertEqual(result, 12.5)

    def test_format_named_signal_value_int(self):
        """Test formatting NamedSignalValue with int-like float"""
        # Create mock NamedSignalValue
        named_value = MockNamedSignalValue(100.0)

        # Format it
        result = self.decoder._format_signal_value(named_value)

        # Should convert to int
        self.assertEqual(result, 100)
        self.assertIsInstance(result, int)

    def test_format_regular_float(self):
        """Test formatting regular float (backward compatibility)"""
        result = self.decoder._format_signal_value(25.75)
        self.assertEqual(result, 25.75)

    def test_format_regular_int_float(self):
        """Test formatting int-like float"""
        result = self.decoder._format_signal_value(50.0)
        self.assertEqual(result, 50)
        self.assertIsInstance(result, int)

    def test_format_string_value(self):
        """Test formatting string value (passthrough)"""
        result = self.decoder._format_signal_value("test")
        self.assertEqual(result, "test")

    def test_format_named_signal_value_with_rounding(self):
        """Test formatting NamedSignalValue with rounding"""
        # Create mock NamedSignalValue with many decimals
        named_value = MockNamedSignalValue(12.3456789)

        # Format it
        result = self.decoder._format_signal_value(named_value)

        # Should round to 2 decimals
        self.assertEqual(result, 12.35)

    def test_hasattr_check_on_regular_value(self):
        """Test that regular values without 'value' attribute still work"""
        # Regular numeric value
        result = self.decoder._format_signal_value(42)
        self.assertEqual(result, 42)

        # Regular string
        result = self.decoder._format_signal_value("normal")
        self.assertEqual(result, "normal")

    def test_nested_named_signal_value(self):
        """Test that we only extract one level"""
        # Create nested object
        inner = MockNamedSignalValue(99.99)

        # Format it
        result = self.decoder._format_signal_value(inner)

        # Should extract value (already rounded to 2 decimals)
        self.assertEqual(result, 99.99)


if __name__ == '__main__':
    unittest.main()
