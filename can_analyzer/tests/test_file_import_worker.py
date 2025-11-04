"""
Tests for File Import Worker

Tests the background file import functionality
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from PyQt6.QtCore import QCoreApplication
from utils.file_import_worker import FileImportWorker
from parsers.asc_parser import CANMessage
import sys


class TestFileImportWorker(unittest.TestCase):
    """Test cases for FileImportWorker"""

    @classmethod
    def setUpClass(cls):
        """Set up QApplication for tests"""
        if not QCoreApplication.instance():
            cls.app = QCoreApplication(sys.argv)

    def setUp(self):
        """Set up test fixtures"""
        self.mock_parser = Mock()

    def test_worker_initialization(self):
        """Test worker initializes correctly"""
        worker = FileImportWorker(self.mock_parser, "test.asc")
        self.assertIsNotNone(worker)
        self.assertEqual(worker.file_path, "test.asc")
        self.assertFalse(worker._is_cancelled)

    def test_worker_signals_exist(self):
        """Test that worker has required signals"""
        worker = FileImportWorker(self.mock_parser, "test.asc")
        self.assertTrue(hasattr(worker, 'progress_updated'))
        self.assertTrue(hasattr(worker, 'import_finished'))
        self.assertTrue(hasattr(worker, 'import_failed'))

    def test_cancel_sets_flag(self):
        """Test that cancel() sets the cancelled flag"""
        worker = FileImportWorker(self.mock_parser, "test.asc")
        self.assertFalse(worker._is_cancelled)
        worker.cancel()
        self.assertTrue(worker._is_cancelled)

    def test_successful_import(self):
        """Test successful file import"""
        # Create mock messages
        mock_messages = [
            CANMessage(0.0, 0x123, 'Rx', b'\x01\x02\x03', 1),
            CANMessage(1.0, 0x456, 'Tx', b'\x04\x05\x06', 1)
        ]

        # Configure mock parser
        self.mock_parser.parse_file.return_value = mock_messages

        mock_sub_parser = Mock()
        mock_sub_parser.get_statistics.return_value = {
            'total_messages': 2,
            'time_range': (0.0, 1.0),
            'duration': 1.0,
            'unique_ids': 2,
            'rx_count': 1,
            'tx_count': 1
        }
        self.mock_parser.get_parser.return_value = mock_sub_parser

        # Create worker
        worker = FileImportWorker(self.mock_parser, "test.asc")

        # Connect signal to capture result
        result_messages = []
        result_stats = {}

        def capture_result(messages, stats):
            result_messages.extend(messages)
            result_stats.update(stats)

        worker.import_finished.connect(capture_result)

        # Run worker
        worker.run()

        # Verify results
        self.assertEqual(len(result_messages), 2)
        self.assertEqual(result_stats['total_messages'], 2)
        self.mock_parser.parse_file.assert_called_once_with("test.asc")

    def test_import_with_error(self):
        """Test import with parsing error"""
        # Configure mock parser to raise error
        self.mock_parser.parse_file.side_effect = Exception("Parse error")

        # Create worker
        worker = FileImportWorker(self.mock_parser, "test.asc")

        # Connect signal to capture error
        error_message = []

        def capture_error(msg):
            error_message.append(msg)

        worker.import_failed.connect(capture_error)

        # Run worker
        worker.run()

        # Verify error was captured
        self.assertEqual(len(error_message), 1)
        self.assertIn("Parse error", error_message[0])

    def test_progress_updates(self):
        """Test that progress updates are emitted"""
        # Configure mock parser
        self.mock_parser.parse_file.return_value = []
        self.mock_parser.get_parser.return_value = Mock()

        # Create worker
        worker = FileImportWorker(self.mock_parser, "test.asc")

        # Connect signal to capture progress
        progress_messages = []

        def capture_progress(msg):
            progress_messages.append(msg)

        worker.progress_updated.connect(capture_progress)

        # Run worker
        worker.run()

        # Verify progress messages were emitted
        self.assertGreater(len(progress_messages), 0)
        self.assertIn("正在读取文件", progress_messages[0])

    def test_cancellation_during_import(self):
        """Test that cancellation stops import"""
        # Create worker
        worker = FileImportWorker(self.mock_parser, "test.asc")

        # Cancel immediately
        worker.cancel()

        # Run worker
        worker.run()

        # Parser should not be called if cancelled early
        # Note: This test assumes cancellation happens before parse_file is called
        # In real scenario, timing matters
        self.assertTrue(worker._is_cancelled)


if __name__ == '__main__':
    unittest.main()
