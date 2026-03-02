"""
Test Search Dialog
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from parsers.asc_parser import CANMessage


def test_can_id_matching():
    """Test CAN ID search matching"""
    from ui.search_dialog import SearchDialog

    # Create test messages
    messages = [
        CANMessage(0.1, 'CAN1', 0x123, 'Rx', 8, bytes([0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08])),
        CANMessage(0.2, 'CAN1', 0x456, 'Tx', 8, bytes([0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17, 0x18])),
        CANMessage(0.3, 'CAN1', 0x789, 'Rx', 8, bytes([0x21, 0x22, 0x23, 0x24, 0x25, 0x26, 0x27, 0x28])),
    ]

    dialog = SearchDialog(messages, None)

    # Test exact match (hex without 0x)
    assert dialog.match_can_id(messages[0], '123') == True
    assert dialog.match_can_id(messages[1], '456') == True

    # Test with 0x prefix
    assert dialog.match_can_id(messages[0], '0x123') == True
    assert dialog.match_can_id(messages[2], '0x789') == True

    # Test case insensitivity (handled by int() parsing)
    assert dialog.match_can_id(messages[0], '0X123') == True

    # Test no match
    assert dialog.match_can_id(messages[0], 'ABC') == False

    print("✓ CAN ID matching tests passed")
    return True


def test_data_content_matching():
    """Test data content search matching"""
    from ui.search_dialog import SearchDialog

    messages = [
        CANMessage(0.1, 'CAN1', 0x123, 'Rx', 8, bytes([0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08])),
        CANMessage(0.2, 'CAN1', 0x456, 'Tx', 8, bytes([0xAB, 0xCD, 0xEF, 0x12, 0x34, 0x56, 0x78, 0x90])),
        CANMessage(0.3, 'CAN1', 0x789, 'Rx', 4, bytes([0xFF, 0xFF, 0x00, 0x00])),
    ]

    dialog = SearchDialog(messages, None)

    # Test exact byte sequence
    assert dialog.match_data_content(messages[0], '0102', False) == True
    assert dialog.match_data_content(messages[0], '01020304', False) == True

    # Test with spaces
    assert dialog.match_data_content(messages[0], '01 02 03', False) == True

    # Test case insensitivity
    assert dialog.match_data_content(messages[1], 'abcd', False) == True
    assert dialog.match_data_content(messages[1], 'ABCD', False) == True
    assert dialog.match_data_content(messages[1], 'AbCd', False) == True

    # Test partial match
    assert dialog.match_data_content(messages[2], 'FF', False) == True
    assert dialog.match_data_content(messages[2], 'FFFF', False) == True

    # Test no match
    assert dialog.match_data_content(messages[0], 'ZZ', False) == False

    print("✓ Data content matching tests passed")
    return True


def test_search_state_management():
    """Test search state management"""
    from ui.search_dialog import SearchDialog

    messages = [
        CANMessage(0.1, 'CAN1', 0x123, 'Rx', 8, bytes([0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08])),
        CANMessage(0.2, 'CAN1', 0x456, 'Tx', 8, bytes([0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17, 0x18])),
        CANMessage(0.3, 'CAN1', 0x123, 'Rx', 8, bytes([0x21, 0x22, 0x23, 0x24, 0x25, 0x26, 0x27, 0x28])),
    ]

    dialog = SearchDialog(messages, None)

    # Test initial state
    assert dialog.current_index == -1
    assert dialog.last_search_text == ""

    # Test reset search
    dialog.current_index = 5
    dialog.last_search_text = "test"
    dialog.reset_search()
    assert dialog.current_index == -1
    assert dialog.status_label.text() == ""

    print("✓ Search state management tests passed")
    return True


def test_message_update():
    """Test updating messages in search dialog"""
    from ui.search_dialog import SearchDialog

    messages1 = [
        CANMessage(0.1, 'CAN1', 0x123, 'Rx', 8, bytes([0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08])),
    ]

    dialog = SearchDialog(messages1, None)
    assert len(dialog.messages) == 1

    messages2 = [
        CANMessage(0.1, 'CAN1', 0x123, 'Rx', 8, bytes([0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08])),
        CANMessage(0.2, 'CAN1', 0x456, 'Tx', 8, bytes([0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17, 0x18])),
    ]

    dialog.update_messages(messages2)
    assert len(dialog.messages) == 2
    assert dialog.current_index == -1  # Should reset search

    print("✓ Message update tests passed")
    return True


def test_placeholder_text():
    """Test placeholder text changes based on search type"""
    from ui.search_dialog import SearchDialog
    from PyQt6.QtWidgets import QApplication

    # Need QApplication for widgets
    if not QApplication.instance():
        app = QApplication(sys.argv)

    messages = [CANMessage(0.1, 'CAN1', 0x123, 'Rx', 8, bytes([0x01, 0x02, 0x03, 0x04]))]

    dialog = SearchDialog(messages, None)

    # Test CAN ID placeholder
    dialog.search_type_combo.setCurrentIndex(0)  # CAN ID
    assert "123" in dialog.search_input.placeholderText()

    # Test Data content placeholder
    dialog.search_type_combo.setCurrentIndex(1)  # Data content
    assert "01 02 03" in dialog.search_input.placeholderText() or "010203" in dialog.search_input.placeholderText()

    # Test Signal value placeholder
    dialog.search_type_combo.setCurrentIndex(2)  # Signal value
    assert "EngineSpeed" in dialog.search_input.placeholderText() or "2000" in dialog.search_input.placeholderText()

    print("✓ Placeholder text tests passed")
    return True


def run_all_tests():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("Running Search Dialog Tests")
    print("=" * 60 + "\n")

    tests = [
        test_can_id_matching,
        test_data_content_matching,
        test_search_state_management,
        test_message_update,
        test_placeholder_text,
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ {test.__name__} failed: {e}")
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
