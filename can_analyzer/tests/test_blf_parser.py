"""
Tests for BLF Parser

Tests the BLF file parser functionality
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from parsers.blf_parser import BLFParser
from parsers.asc_parser import CANMessage


class TestBLFParser(unittest.TestCase):
    """Test cases for BLF Parser"""

    def setUp(self):
        """Set up test fixtures"""
        self.parser = BLFParser()

    def test_parser_initialization(self):
        """Test parser initializes correctly"""
        self.assertIsNotNone(self.parser)
        self.assertEqual(len(self.parser.messages), 0)

    def test_check_dependencies(self):
        """Test dependency checking"""
        # This will be True if python-can is installed, False otherwise
        is_available = BLFParser.is_available()
        self.assertIsInstance(is_available, bool)

    @patch('can.BLFReader')
    def test_parse_with_is_rx_attribute(self, mock_reader):
        """Test parsing messages with is_rx attribute"""
        # Create mock messages with is_rx attribute
        mock_msg1 = Mock()
        mock_msg1.timestamp = 1.0
        mock_msg1.arbitration_id = 0x123
        mock_msg1.data = [0x01, 0x02, 0x03]
        mock_msg1.is_rx = True
        mock_msg1.channel = 1

        mock_msg2 = Mock()
        mock_msg2.timestamp = 2.0
        mock_msg2.arbitration_id = 0x456
        mock_msg2.data = [0x04, 0x05, 0x06]
        mock_msg2.is_rx = False  # This should be Tx
        mock_msg2.channel = 1

        # Configure mock reader
        mock_reader.return_value.__enter__.return_value = [mock_msg1, mock_msg2]

        # Check if python-can is available
        if not self.parser._can_available:
            self.skipTest("python-can not available")

        # Parse file
        messages = self.parser.parse_file("dummy.blf")

        # Verify results
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0].direction, 'Rx')
        self.assertEqual(messages[1].direction, 'Tx')

    @patch('can.BLFReader')
    def test_parse_without_is_rx_attribute(self, mock_reader):
        """Test parsing messages without is_rx attribute (fallback)"""
        # Create mock message without is_rx attribute
        mock_msg = Mock(spec=['timestamp', 'arbitration_id', 'data', 'channel'])
        mock_msg.timestamp = 1.0
        mock_msg.arbitration_id = 0x123
        mock_msg.data = [0x01, 0x02, 0x03]
        mock_msg.channel = 1
        # Note: is_rx attribute is NOT set

        # Configure mock reader
        mock_reader.return_value.__enter__.return_value = [mock_msg]

        # Check if python-can is available
        if not self.parser._can_available:
            self.skipTest("python-can not available")

        # Parse file
        messages = self.parser.parse_file("dummy.blf")

        # Verify fallback to 'Rx'
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].direction, 'Rx')

    def test_get_statistics_empty(self):
        """Test statistics with no messages"""
        stats = self.parser.get_statistics()
        self.assertEqual(stats['total_messages'], 0)
        self.assertEqual(stats['unique_ids'], 0)

    @patch('can.BLFReader')
    def test_parse_with_relative_timestamps(self, mock_reader):
        """Test that timestamps are relative to first message"""
        # Create mock messages
        mock_msg1 = Mock()
        mock_msg1.timestamp = 10.5
        mock_msg1.arbitration_id = 0x123
        mock_msg1.data = [0x01, 0x02]
        mock_msg1.is_rx = True
        mock_msg1.channel = 1

        mock_msg2 = Mock()
        mock_msg2.timestamp = 12.0
        mock_msg2.arbitration_id = 0x456
        mock_msg2.data = [0x03, 0x04]
        mock_msg2.is_rx = True
        mock_msg2.channel = 1

        # Configure mock reader
        mock_reader.return_value.__enter__.return_value = [mock_msg1, mock_msg2]

        # Check if python-can is available
        if not self.parser._can_available:
            self.skipTest("python-can not available")

        # Parse file
        messages = self.parser.parse_file("dummy.blf")

        # Verify relative timestamps
        self.assertEqual(len(messages), 2)
        self.assertAlmostEqual(messages[0].timestamp, 0.0)
        self.assertAlmostEqual(messages[1].timestamp, 1.5)

    @patch('can.BLFReader')
    def test_parse_with_missing_channel(self, mock_reader):
        """Test parsing messages without channel attribute"""
        # Create mock message without channel
        mock_msg = Mock(spec=['timestamp', 'arbitration_id', 'data', 'is_rx'])
        mock_msg.timestamp = 1.0
        mock_msg.arbitration_id = 0x123
        mock_msg.data = [0x01, 0x02, 0x03]
        mock_msg.is_rx = True

        # Configure mock reader
        mock_reader.return_value.__enter__.return_value = [mock_msg]

        # Check if python-can is available
        if not self.parser._can_available:
            self.skipTest("python-can not available")

        # Parse file
        messages = self.parser.parse_file("dummy.blf")

        # Verify default channel is 1
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].channel, 1)

    def test_import_error_handling(self):
        """Test handling when python-can is not available"""
        # Create parser instance and force unavailable state
        parser = BLFParser()
        parser._can_available = False

        # Try to parse file
        with self.assertRaises(ImportError) as context:
            parser.parse_file("dummy.blf")

        self.assertIn("python-can", str(context.exception))

    def test_file_not_found_error(self):
        """Test handling of missing file"""
        if not self.parser._can_available:
            self.skipTest("python-can not available")

        with self.assertRaises(FileNotFoundError):
            self.parser.parse_file("/nonexistent/file.blf")


if __name__ == '__main__':
    unittest.main()
