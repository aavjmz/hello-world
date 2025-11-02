"""
Test Message Filter

Tests the message filtering functionality
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.message_filter import MessageFilter
from parsers.asc_parser import CANMessage


def create_test_message(timestamp=0.0, can_id=0x123, direction="Rx", dlc=8, data=None, channel=1):
    """Helper to create test messages"""
    if data is None:
        data = bytes([0x00] * dlc)
    return CANMessage(timestamp, can_id, direction, data, channel)


def test_can_id_filter():
    """Test CAN ID filtering"""
    print("\n=== Test 1: CAN ID Filter ===")

    # Create test messages
    msg1 = create_test_message(can_id=0x123)
    msg2 = create_test_message(can_id=0x456)
    msg3 = create_test_message(can_id=0x789)

    # Test include mode
    filter_obj = MessageFilter()
    filter_obj.filter_by_can_id = True
    filter_obj.can_id_mode = "include"
    filter_obj.can_id_list = {0x123, 0x456}

    assert filter_obj.matches(msg1) == True, "Should include 0x123"
    assert filter_obj.matches(msg2) == True, "Should include 0x456"
    assert filter_obj.matches(msg3) == False, "Should exclude 0x789"

    print("✓ Include mode works correctly")

    # Test exclude mode
    filter_obj.can_id_mode = "exclude"

    assert filter_obj.matches(msg1) == False, "Should exclude 0x123"
    assert filter_obj.matches(msg2) == False, "Should exclude 0x456"
    assert filter_obj.matches(msg3) == True, "Should include 0x789"

    print("✓ Exclude mode works correctly")

    return True


def test_direction_filter():
    """Test direction filtering"""
    print("\n=== Test 2: Direction Filter ===")

    msg_rx = create_test_message(direction="Rx")
    msg_tx = create_test_message(direction="Tx")

    filter_obj = MessageFilter()
    filter_obj.filter_by_direction = True

    # Show only Rx
    filter_obj.show_rx = True
    filter_obj.show_tx = False

    assert filter_obj.matches(msg_rx) == True, "Should show Rx"
    assert filter_obj.matches(msg_tx) == False, "Should hide Tx"

    print("✓ Rx-only filter works")

    # Show only Tx
    filter_obj.show_rx = False
    filter_obj.show_tx = True

    assert filter_obj.matches(msg_rx) == False, "Should hide Rx"
    assert filter_obj.matches(msg_tx) == True, "Should show Tx"

    print("✓ Tx-only filter works")

    # Show both
    filter_obj.show_rx = True
    filter_obj.show_tx = True

    assert filter_obj.matches(msg_rx) == True, "Should show Rx"
    assert filter_obj.matches(msg_tx) == True, "Should show Tx"

    print("✓ Show-all works")

    return True


def test_time_filter():
    """Test time range filtering"""
    print("\n=== Test 3: Time Range Filter ===")

    msg1 = create_test_message(timestamp=0.5)
    msg2 = create_test_message(timestamp=5.0)
    msg3 = create_test_message(timestamp=10.5)

    filter_obj = MessageFilter()
    filter_obj.filter_by_time = True
    filter_obj.time_start = 1.0
    filter_obj.time_end = 10.0

    assert filter_obj.matches(msg1) == False, "Should exclude 0.5s (too early)"
    assert filter_obj.matches(msg2) == True, "Should include 5.0s"
    assert filter_obj.matches(msg3) == False, "Should exclude 10.5s (too late)"

    print("✓ Time range filter works correctly")

    return True


def test_dlc_filter():
    """Test DLC filtering"""
    print("\n=== Test 4: DLC Filter ===")

    msg1 = create_test_message(dlc=2)
    msg2 = create_test_message(dlc=4)
    msg3 = create_test_message(dlc=8)

    filter_obj = MessageFilter()
    filter_obj.filter_by_dlc = True
    filter_obj.dlc_min = 3
    filter_obj.dlc_max = 6

    assert filter_obj.matches(msg1) == False, "Should exclude DLC=2 (too small)"
    assert filter_obj.matches(msg2) == True, "Should include DLC=4"
    assert filter_obj.matches(msg3) == False, "Should exclude DLC=8 (too large)"

    print("✓ DLC filter works correctly")

    return True


def test_combined_filters():
    """Test multiple filters combined"""
    print("\n=== Test 5: Combined Filters ===")

    msg1 = create_test_message(timestamp=5.0, can_id=0x123, direction="Rx", dlc=8)
    msg2 = create_test_message(timestamp=5.0, can_id=0x456, direction="Rx", dlc=8)
    msg3 = create_test_message(timestamp=5.0, can_id=0x123, direction="Tx", dlc=8)
    msg4 = create_test_message(timestamp=15.0, can_id=0x123, direction="Rx", dlc=8)
    msg5 = create_test_message(timestamp=5.0, can_id=0x123, direction="Rx", dlc=4)

    filter_obj = MessageFilter()

    # Enable all filters
    filter_obj.filter_by_can_id = True
    filter_obj.can_id_list = {0x123}
    filter_obj.can_id_mode = "include"

    filter_obj.filter_by_direction = True
    filter_obj.show_rx = True
    filter_obj.show_tx = False

    filter_obj.filter_by_time = True
    filter_obj.time_start = 1.0
    filter_obj.time_end = 10.0

    filter_obj.filter_by_dlc = True
    filter_obj.dlc_min = 6
    filter_obj.dlc_max = 8

    # msg1 should pass all filters
    assert filter_obj.matches(msg1) == True, "msg1 should pass all filters"

    # msg2 fails CAN ID filter
    assert filter_obj.matches(msg2) == False, "msg2 should fail CAN ID filter"

    # msg3 fails direction filter
    assert filter_obj.matches(msg3) == False, "msg3 should fail direction filter"

    # msg4 fails time filter
    assert filter_obj.matches(msg4) == False, "msg4 should fail time filter"

    # msg5 fails DLC filter
    assert filter_obj.matches(msg5) == False, "msg5 should fail DLC filter"

    print("✓ Combined filters work correctly")
    print(f"  msg1 (all match): {filter_obj.matches(msg1)}")
    print(f"  msg2 (wrong ID): {filter_obj.matches(msg2)}")
    print(f"  msg3 (wrong dir): {filter_obj.matches(msg3)}")
    print(f"  msg4 (wrong time): {filter_obj.matches(msg4)}")
    print(f"  msg5 (wrong DLC): {filter_obj.matches(msg5)}")

    return True


def test_is_active():
    """Test is_active method"""
    print("\n=== Test 6: is_active() Method ===")

    filter_obj = MessageFilter()

    # No filters active
    assert filter_obj.is_active() == False, "Should be inactive with no filters"
    print("✓ Correctly reports inactive when no filters set")

    # Activate CAN ID filter
    filter_obj.filter_by_can_id = True
    assert filter_obj.is_active() == True, "Should be active with CAN ID filter"
    print("✓ Correctly reports active when CAN ID filter set")

    # Clear and activate direction filter
    filter_obj.filter_by_can_id = False
    filter_obj.filter_by_direction = True
    assert filter_obj.is_active() == True, "Should be active with direction filter"
    print("✓ Correctly reports active when direction filter set")

    return True


def test_description():
    """Test get_description method"""
    print("\n=== Test 7: get_description() Method ===")

    filter_obj = MessageFilter()

    # No filters
    desc = filter_obj.get_description()
    assert desc == "无过滤条件", f"Expected '无过滤条件', got '{desc}'"
    print(f"✓ No filters: '{desc}'")

    # CAN ID filter
    filter_obj.filter_by_can_id = True
    filter_obj.can_id_list = {0x123, 0x456, 0x789}
    filter_obj.can_id_mode = "include"
    desc = filter_obj.get_description()
    assert "CAN ID 包含: 3个" in desc, f"Expected CAN ID description, got '{desc}'"
    print(f"✓ CAN ID filter: '{desc}'")

    # Add direction filter
    filter_obj.filter_by_direction = True
    filter_obj.show_rx = True
    filter_obj.show_tx = False
    desc = filter_obj.get_description()
    assert "CAN ID" in desc and "方向" in desc, f"Expected both filters, got '{desc}'"
    print(f"✓ Multiple filters: '{desc}'")

    return True


def test_real_world_scenario():
    """Test realistic filtering scenario"""
    print("\n=== Test 8: Real-World Scenario ===")

    # Create realistic test data
    messages = [
        create_test_message(0.010, 0x123, "Rx", 8),
        create_test_message(0.020, 0x456, "Tx", 8),
        create_test_message(0.030, 0x123, "Rx", 8),
        create_test_message(0.040, 0x789, "Rx", 4),
        create_test_message(0.050, 0x123, "Tx", 8),
        create_test_message(0.060, 0x456, "Rx", 8),
        create_test_message(0.070, 0x123, "Rx", 8),
        create_test_message(0.080, 0x123, "Rx", 2),
        create_test_message(0.090, 0x456, "Rx", 8),
        create_test_message(0.100, 0x123, "Rx", 8),
    ]

    print(f"Total messages: {len(messages)}")

    # Filter: Only show Rx messages from ID 0x123 with DLC=8
    filter_obj = MessageFilter()

    filter_obj.filter_by_can_id = True
    filter_obj.can_id_list = {0x123}
    filter_obj.can_id_mode = "include"

    filter_obj.filter_by_direction = True
    filter_obj.show_rx = True
    filter_obj.show_tx = False

    filter_obj.filter_by_dlc = True
    filter_obj.dlc_min = 8
    filter_obj.dlc_max = 8

    # Apply filter
    filtered = [msg for msg in messages if filter_obj.matches(msg)]

    print(f"Filtered messages: {len(filtered)}")
    print(f"Filter description: {filter_obj.get_description()}")

    # Expected: messages at indices 0, 2, 6, 9 (4 messages)
    assert len(filtered) == 4, f"Expected 4 filtered messages, got {len(filtered)}"

    for msg in filtered:
        assert msg.can_id == 0x123, "All should be ID 0x123"
        assert msg.direction == "Rx", "All should be Rx"
        assert msg.dlc == 8, "All should have DLC=8"

    print("✓ Real-world filtering scenario works correctly")

    return True


def run_all_tests():
    """Run all filter tests"""
    print("=" * 60)
    print("Message Filter - Test Suite")
    print("=" * 60)

    tests = [
        test_can_id_filter,
        test_direction_filter,
        test_time_filter,
        test_dlc_filter,
        test_combined_filters,
        test_is_active,
        test_description,
        test_real_world_scenario
    ]

    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append(result)
        except AssertionError as e:
            print(f"\n✗ Assertion failed: {e}")
            results.append(False)
        except Exception as e:
            print(f"\n✗ Test crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    passed = sum(results)
    total = len(results)

    print(f"Passed: {passed}/{total}")

    for i, (test_func, result) in enumerate(zip(tests, results), 1):
        status = "✓" if result else "✗"
        print(f"{status} Test {i}: {test_func.__name__}")

    print("=" * 60)

    if passed == total:
        print("\n✓✓✓ All filter tests passed! ✓✓✓")
        return True
    else:
        print(f"\n✗ {total - passed} test(s) failed")
        return False


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
