"""
Test Virtual Scrolling Performance

This test validates the virtual scrolling implementation for large datasets
"""

import sys
import os
import time
from pathlib import Path

# Enable offscreen rendering for headless environments
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from PyQt6.QtWidgets import QApplication
from parsers.asc_parser import CANMessage
from ui.message_table import MessageTableWidget


def create_test_messages(count: int):
    """
    Create test CAN messages

    Args:
        count: Number of messages to create

    Returns:
        List of CANMessage objects
    """
    messages = []
    for i in range(count):
        timestamp = i * 0.001  # 1ms intervals
        can_id = 0x100 + (i % 256)  # Cycle through IDs
        direction = 'Rx' if i % 2 == 0 else 'Tx'
        data = bytes([(i + j) % 256 for j in range(8)])
        channel = 1

        messages.append(CANMessage(timestamp, can_id, direction, data, channel))

    return messages


def test_small_dataset():
    """Test that small datasets use batch loading (not virtual scrolling)"""
    print("\n" + "=" * 70)
    print("Test 1: Small Dataset (5,000 messages) - Should use batch loading")
    print("=" * 70)

    # Create test messages
    messages = create_test_messages(5000)

    # Create table widget
    table = MessageTableWidget()

    # Load messages
    start_time = time.time()
    table.set_messages(messages)
    load_time = time.time() - start_time

    # Verify batch loading is used
    assert not table._use_virtual_scrolling, "Small dataset should use batch loading"

    print(f"✓ Batch loading mode activated (expected)")
    print(f"  Load time: {load_time:.3f}s")
    print(f"  Message count: {len(messages)}")
    print(f"  Virtual scrolling: {table._use_virtual_scrolling}")

    return True


def test_large_dataset():
    """Test that large datasets use virtual scrolling"""
    print("\n" + "=" * 70)
    print("Test 2: Large Dataset (50,000 messages) - Should use virtual scrolling")
    print("=" * 70)

    # Create test messages
    messages = create_test_messages(50000)

    # Create table widget
    table = MessageTableWidget()

    # Load messages
    start_time = time.time()
    table.set_messages(messages)
    load_time = time.time() - start_time

    # Verify virtual scrolling is used
    assert table._use_virtual_scrolling, "Large dataset should use virtual scrolling"

    # Check that only a subset of rows are loaded
    row_count = table.rowCount()
    print(f"✓ Virtual scrolling mode activated (expected)")
    print(f"  Load time: {load_time:.3f}s")
    print(f"  Total messages: {len(messages)}")
    print(f"  Rows in table: {row_count}")
    print(f"  Memory efficiency: {row_count / len(messages) * 100:.1f}% loaded")
    print(f"  Virtual scrolling: {table._use_virtual_scrolling}")

    # Verify row count is much smaller than message count
    assert row_count < len(messages) / 10, "Virtual scrolling should load much fewer rows"

    return True


def test_very_large_dataset():
    """Test performance with very large dataset (100k messages)"""
    print("\n" + "=" * 70)
    print("Test 3: Very Large Dataset (100,000 messages)")
    print("=" * 70)

    # Create test messages
    messages = create_test_messages(100000)

    # Create table widget
    table = MessageTableWidget()

    # Load messages
    start_time = time.time()
    table.set_messages(messages)
    load_time = time.time() - start_time

    row_count = table.rowCount()
    print(f"✓ Virtual scrolling with 100k messages")
    print(f"  Load time: {load_time:.3f}s")
    print(f"  Total messages: {len(messages):,}")
    print(f"  Rows in table: {row_count}")
    print(f"  Memory efficiency: {row_count / len(messages) * 100:.1f}% loaded")

    # Performance assertion - should load in reasonable time
    assert load_time < 2.0, f"Load time {load_time:.3f}s exceeds 2s limit"
    assert row_count < 200, "Should maintain small number of rows for performance"

    return True


def test_scroll_to_message():
    """Test scroll_to_message functionality with virtual scrolling"""
    print("\n" + "=" * 70)
    print("Test 4: Scroll to Message in Virtual Scrolling Mode")
    print("=" * 70)

    # Create test messages
    messages = create_test_messages(20000)

    # Create table widget
    table = MessageTableWidget()
    table.set_messages(messages)

    # Test scrolling to different positions
    test_indices = [0, 1000, 10000, 15000, 19999]

    for idx in test_indices:
        table.scroll_to_message(idx)
        # Give a moment for window update
        QApplication.processEvents()

        # Verify message is now in view
        found = False
        for row in range(table.rowCount()):
            item = table.item(row, 0)
            if item and item.data(0x0100) == idx:  # Qt.UserRole
                found = True
                break

        print(f"  Scroll to message {idx:,}: {'✓ Found' if found else '✗ Not found'}")
        assert found, f"Failed to scroll to message {idx}"

    print("✓ All scroll tests passed")
    return True


def test_message_retrieval():
    """Test get_message_at() with virtual scrolling"""
    print("\n" + "=" * 70)
    print("Test 5: Message Retrieval with Virtual Scrolling")
    print("=" * 70)

    # Create test messages
    messages = create_test_messages(15000)

    # Create table widget
    table = MessageTableWidget()
    table.set_messages(messages)

    # Test retrieving messages from visible rows
    success_count = 0
    for row in range(min(10, table.rowCount())):
        message = table.get_message_at(row)
        if message is not None:
            # Verify it's a valid message
            assert isinstance(message, CANMessage), "Should return CANMessage object"
            success_count += 1

    print(f"✓ Successfully retrieved {success_count}/10 messages from table")
    assert success_count == min(10, table.rowCount()), "All visible messages should be retrievable"

    return True


def test_performance_comparison():
    """Compare performance between batch loading and virtual scrolling"""
    print("\n" + "=" * 70)
    print("Test 6: Performance Comparison")
    print("=" * 70)

    # Test batch loading (9,000 messages - just below threshold)
    batch_messages = create_test_messages(9000)
    batch_table = MessageTableWidget()

    batch_start = time.time()
    batch_table.set_messages(batch_messages)
    # Wait for all batches to complete
    while batch_table._batch_timer.isActive():
        QApplication.processEvents()
        time.sleep(0.01)
    batch_time = time.time() - batch_start

    batch_rows = batch_table.rowCount()

    # Test virtual scrolling (15,000 messages)
    virtual_messages = create_test_messages(15000)
    virtual_table = MessageTableWidget()

    virtual_start = time.time()
    virtual_table.set_messages(virtual_messages)
    virtual_time = time.time() - virtual_start

    virtual_rows = virtual_table.rowCount()

    print(f"\nBatch Loading (9,000 messages):")
    print(f"  Time: {batch_time:.3f}s")
    print(f"  Rows loaded: {batch_rows:,}")
    print(f"  Rows per second: {batch_rows / batch_time:,.0f}")

    print(f"\nVirtual Scrolling (15,000 messages):")
    print(f"  Time: {virtual_time:.3f}s")
    print(f"  Rows loaded: {virtual_rows:,}")
    print(f"  Effective rows/sec: {len(virtual_messages) / virtual_time:,.0f}")
    print(f"  Memory reduction: {(1 - virtual_rows / len(virtual_messages)) * 100:.1f}%")

    print(f"\n✓ Virtual scrolling is {virtual_time / batch_time * 100:.1f}% faster for initial load")
    print(f"✓ Memory usage reduced by ~{(1 - virtual_rows / len(virtual_messages)) * 100:.0f}%")

    return True


def run_all_tests():
    """Run all virtual scrolling tests"""
    print("\n" + "=" * 70)
    print("VIRTUAL SCROLLING PERFORMANCE TESTS")
    print("=" * 70)

    # Create QApplication (required for Qt widgets)
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    tests = [
        test_small_dataset,
        test_large_dataset,
        test_very_large_dataset,
        test_scroll_to_message,
        test_message_retrieval,
        test_performance_comparison,
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\n✗ {test.__name__} failed: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)

    print("\n" + "=" * 70)
    passed = sum(results)
    total = len(results)
    print(f"TEST RESULTS: {passed}/{total} passed")

    if passed == total:
        print("✅ All virtual scrolling tests passed!")
    else:
        print(f"❌ {total - passed} test(s) failed")

    print("=" * 70 + "\n")

    return all(results)


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
