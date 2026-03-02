"""
Test Data Exporter
"""

import sys
import os
import json
import csv
import tempfile
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from parsers.asc_parser import CANMessage
from utils.data_exporter import DataExporter
from utils.timestamp_formatter import TimestampFormatter, TimestampFormat


def test_csv_export():
    """Test CSV export functionality"""
    # Create test messages
    messages = [
        CANMessage(0.1, 0x123, 'Rx', bytes([0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08]), 1),
        CANMessage(0.2, 0x456, 'Tx', bytes([0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17, 0x18]), 1),
        CANMessage(0.3, 0x789, 'Rx', bytes([0x21, 0x22, 0x23, 0x24]), 1),
    ]

    exporter = DataExporter()

    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmpfile:
        csv_path = tmpfile.name

    try:
        # Export to CSV
        success = exporter.export_to_csv(messages, csv_path, include_signals=False)
        assert success, "CSV export failed"

        # Verify file exists
        assert os.path.exists(csv_path), "CSV file was not created"

        # Read and verify content
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            rows = list(reader)

            # Check header
            assert len(rows) > 0, "CSV is empty"
            assert '序号' in rows[0], "Header missing"
            assert 'CAN ID' in rows[0], "CAN ID column missing"

            # Check data rows
            assert len(rows) == 4, f"Expected 4 rows (1 header + 3 data), got {len(rows)}"

            # Verify first data row
            assert rows[1][0] == '1', "序号 incorrect"
            assert '0x123' in rows[1][3], "CAN ID incorrect"
            assert rows[1][4] == 'Rx', "Direction incorrect"

        print("✓ CSV export test passed")
        return True

    finally:
        # Clean up
        if os.path.exists(csv_path):
            os.remove(csv_path)


def test_json_export():
    """Test JSON export functionality"""
    messages = [
        CANMessage(0.1, 0x123, 'Rx', bytes([0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08]), 1),
        CANMessage(0.2, 0x456, 'Tx', bytes([0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17, 0x18]), 1),
    ]

    exporter = DataExporter()

    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmpfile:
        json_path = tmpfile.name

    try:
        # Export to JSON
        success = exporter.export_to_json(messages, json_path, include_signals=False, pretty=True)
        assert success, "JSON export failed"

        # Verify file exists
        assert os.path.exists(json_path), "JSON file was not created"

        # Read and verify content
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

            # Check metadata
            assert 'metadata' in data, "Metadata missing"
            assert data['metadata']['total_messages'] == 2, "Total messages incorrect"

            # Check messages
            assert 'messages' in data, "Messages array missing"
            assert len(data['messages']) == 2, "Message count incorrect"

            # Verify first message
            msg1 = data['messages'][0]
            assert msg1['can_id'] == '0x123', "CAN ID incorrect"
            assert msg1['direction'] == 'Rx', "Direction incorrect"
            assert msg1['dlc'] == 8, "DLC incorrect"
            assert 'data_hex' in msg1, "Data hex missing"
            assert 'data_bytes' in msg1, "Data bytes missing"

        print("✓ JSON export test passed")
        return True

    finally:
        # Clean up
        if os.path.exists(json_path):
            os.remove(json_path)


def test_export_statistics():
    """Test export statistics calculation"""
    messages = [
        CANMessage(0.1, 0x123, 'Rx', bytes([0x01, 0x02, 0x03, 0x04]), 1),
        CANMessage(0.2, 0x456, 'Tx', bytes([0x11, 0x12, 0x13, 0x14]), 1),
        CANMessage(0.3, 0x123, 'Rx', bytes([0x21, 0x22, 0x23, 0x24]), 1),  # Duplicate ID
        CANMessage(0.5, 0x789, 'Tx', bytes([0x31, 0x32, 0x33, 0x34]), 1),
    ]

    exporter = DataExporter()
    stats = exporter.get_export_statistics(messages)

    assert stats['total_messages'] == 4, "Total messages incorrect"
    assert stats['unique_ids'] == 3, "Unique IDs incorrect (should be 0x123, 0x456, 0x789)"
    assert stats['rx_count'] == 2, "Rx count incorrect"
    assert stats['tx_count'] == 2, "Tx count incorrect"
    assert abs(stats['time_span'] - 0.4) < 0.001, "Time span incorrect"
    assert abs(stats['start_time'] - 0.1) < 0.001, "Start time incorrect"
    assert abs(stats['end_time'] - 0.5) < 0.001, "End time incorrect"

    print("✓ Export statistics test passed")
    return True


def test_empty_messages():
    """Test export with empty message list"""
    exporter = DataExporter()
    stats = exporter.get_export_statistics([])

    assert stats['total_messages'] == 0, "Total messages should be 0"
    assert stats['unique_ids'] == 0, "Unique IDs should be 0"
    assert stats['rx_count'] == 0, "Rx count should be 0"
    assert stats['tx_count'] == 0, "Tx count should be 0"
    assert stats['time_span'] == 0.0, "Time span should be 0"

    print("✓ Empty messages test passed")
    return True


def test_timestamp_formats():
    """Test export with different timestamp formats"""
    messages = [
        CANMessage(1.234567, 0x123, 'Rx', bytes([0x01, 0x02, 0x03, 0x04]), 1),
    ]

    # Test with different formats
    formatter = TimestampFormatter(TimestampFormat.MILLISECONDS)
    exporter = DataExporter(timestamp_formatter=formatter)

    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmpfile:
        csv_path = tmpfile.name

    try:
        success = exporter.export_to_csv(messages, csv_path, include_signals=False)
        assert success, "CSV export with timestamp format failed"

        # Verify timestamp formatting
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            rows = list(reader)
            # Check that timestamp is formatted (should contain '1234' for milliseconds)
            assert '1234' in rows[1][1] or '1235' in rows[1][1], "Timestamp not formatted correctly"

        print("✓ Timestamp formats test passed")
        return True

    finally:
        if os.path.exists(csv_path):
            os.remove(csv_path)


def run_all_tests():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("Running Data Exporter Tests")
    print("=" * 60 + "\n")

    tests = [
        test_csv_export,
        test_json_export,
        test_export_statistics,
        test_empty_messages,
        test_timestamp_formats,
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ {test.__name__} failed: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)

    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Test Results: {passed}/{total} passed")

    if passed == total:
        print("✅ All tests passed!")
    else:
        print(f"❌ {total - passed} test(s) failed")

    print("=" * 60 + "\n")

    return all(results)


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
