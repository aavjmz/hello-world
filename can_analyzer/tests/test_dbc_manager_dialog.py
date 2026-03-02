"""
Test DBC Manager Dialog Logic

Tests the DBC manager functionality without GUI
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.dbc_manager import DBCManager


def test_add_multiple_dbc():
    """Test adding multiple DBC files"""
    print("\n=== Test 1: Add Multiple DBC Files ===")

    dbc_file = os.path.join(os.path.dirname(__file__), 'test_data.dbc')

    if not os.path.exists(dbc_file):
        print(f"✗ Test file not found: {dbc_file}")
        return False

    try:
        manager = DBCManager()

        # Add first DBC
        name1 = manager.add_dbc(dbc_file, load=True)
        print(f"✓ Added first DBC: {name1}")

        # Add same file again (should get different name)
        name2 = manager.add_dbc(dbc_file, load=True)
        print(f"✓ Added second DBC: {name2}")

        # Verify different names
        assert name1 != name2, "DBC names should be different"
        print(f"✓ Names are unique: {name1} vs {name2}")

        # List DBCs
        names = manager.list_dbc_names()
        print(f"✓ Total DBCs: {len(names)}")
        assert len(names) == 2, f"Expected 2 DBCs, got {len(names)}"

        return True

    except ImportError:
        print("⚠ cantools not available, skipping test")
        return True
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_get_dbc_info():
    """Test getting DBC information"""
    print("\n=== Test 2: Get DBC Information ===")

    dbc_file = os.path.join(os.path.dirname(__file__), 'test_data.dbc')

    if not os.path.exists(dbc_file):
        print(f"✗ Test file not found")
        return False

    try:
        manager = DBCManager()
        db_name = manager.add_dbc(dbc_file, load=True)

        # Get info
        info = manager.get_dbc_info(db_name)

        assert info is not None, "Info should not be None"
        print(f"✓ Got DBC info")

        # Check required fields
        assert 'file_path' in info, "Missing file_path"
        assert 'message_count' in info, "Missing message_count"
        assert 'node_count' in info, "Missing node_count"

        print(f"  File path: {info['file_path']}")
        print(f"  Messages: {info['message_count']}")
        print(f"  Nodes: {info['node_count']}")

        assert info['message_count'] > 0, "Should have messages"
        print(f"✓ Message count: {info['message_count']}")

        return True

    except ImportError:
        print("⚠ cantools not available, skipping test")
        return True
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False


def test_set_active_dbc():
    """Test setting active DBC"""
    print("\n=== Test 3: Set Active DBC ===")

    dbc_file = os.path.join(os.path.dirname(__file__), 'test_data.dbc')

    if not os.path.exists(dbc_file):
        print(f"✗ Test file not found")
        return False

    try:
        manager = DBCManager()

        # Add two DBCs
        name1 = manager.add_dbc(dbc_file, load=True)
        name2 = manager.add_dbc(dbc_file, load=True)

        print(f"Added DBCs: {name1}, {name2}")

        # Initially, first one should be active
        active = manager.get_active()
        assert active is not None, "Should have an active DBC"
        print(f"✓ Initial active DBC: {active.name}")

        # Set second as active
        manager.set_active(name2)
        active = manager.get_active()

        assert active.name == name2, f"Expected {name2}, got {active.name}"
        print(f"✓ Changed active to: {active.name}")

        # Set first as active
        manager.set_active(name1)
        active = manager.get_active()

        assert active.name == name1, f"Expected {name1}, got {active.name}"
        print(f"✓ Changed active to: {active.name}")

        return True

    except ImportError:
        print("⚠ cantools not available, skipping test")
        return True
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False


def test_remove_dbc():
    """Test removing DBC"""
    print("\n=== Test 4: Remove DBC ===")

    dbc_file = os.path.join(os.path.dirname(__file__), 'test_data.dbc')

    if not os.path.exists(dbc_file):
        print(f"✗ Test file not found")
        return False

    try:
        manager = DBCManager()

        # Add three DBCs
        name1 = manager.add_dbc(dbc_file, load=True)
        name2 = manager.add_dbc(dbc_file, load=True)
        name3 = manager.add_dbc(dbc_file, load=True)

        print(f"Added DBCs: {name1}, {name2}, {name3}")

        # Remove middle one
        manager.remove_dbc(name2)

        names = manager.list_dbc_names()
        assert len(names) == 2, f"Expected 2 DBCs, got {len(names)}"
        assert name2 not in names, f"{name2} should be removed"

        print(f"✓ Removed {name2}, remaining: {names}")

        # Remove first one
        manager.remove_dbc(name1)

        names = manager.list_dbc_names()
        assert len(names) == 1, f"Expected 1 DBC, got {len(names)}"
        assert name1 not in names, f"{name1} should be removed"

        print(f"✓ Removed {name1}, remaining: {names}")

        return True

    except ImportError:
        print("⚠ cantools not available, skipping test")
        return True
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False


def test_remove_active_dbc():
    """Test removing the active DBC"""
    print("\n=== Test 5: Remove Active DBC ===")

    dbc_file = os.path.join(os.path.dirname(__file__), 'test_data.dbc')

    if not os.path.exists(dbc_file):
        print(f"✗ Test file not found")
        return False

    try:
        manager = DBCManager()

        # Add two DBCs
        name1 = manager.add_dbc(dbc_file, load=True)
        name2 = manager.add_dbc(dbc_file, load=True)

        # Set first as active
        manager.set_active(name1)
        active = manager.get_active()
        assert active.name == name1, "First should be active"

        print(f"✓ Active DBC: {active.name}")

        # Remove the active DBC
        manager.remove_dbc(name1)

        # Active should now be None or the other DBC
        active = manager.get_active()

        if active is None:
            print(f"✓ Active DBC cleared after removal")
        else:
            print(f"✓ Active switched to: {active.name}")
            # If there's still an active, it should be name2
            assert active.name == name2, f"Expected {name2}, got {active.name}"

        return True

    except ImportError:
        print("⚠ cantools not available, skipping test")
        return True
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False


def test_list_empty():
    """Test listing when no DBCs loaded"""
    print("\n=== Test 6: List Empty ===")

    try:
        manager = DBCManager()

        names = manager.list_dbc_names()
        assert len(names) == 0, "Should be empty initially"

        print(f"✓ Empty list: {names}")

        active = manager.get_active()
        assert active is None, "Should have no active DBC"

        print(f"✓ No active DBC")

        return True

    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False


def test_count_signals_in_dbc():
    """Test counting total signals in a DBC"""
    print("\n=== Test 7: Count Signals ===")

    dbc_file = os.path.join(os.path.dirname(__file__), 'test_data.dbc')

    if not os.path.exists(dbc_file):
        print(f"✗ Test file not found")
        return False

    try:
        manager = DBCManager()
        db_name = manager.add_dbc(dbc_file, load=True)

        dbc = manager.get_dbc(db_name)

        if not dbc.is_loaded():
            print("✗ DBC not loaded")
            return False

        # Count total signals
        total_signals = 0
        for msg in dbc.db.messages:
            total_signals += len(msg.signals)

        print(f"✓ Total messages: {len(dbc.db.messages)}")
        print(f"✓ Total signals: {total_signals}")

        assert total_signals > 0, "Should have at least one signal"

        # Show breakdown
        for msg in dbc.db.messages:
            print(f"  • {msg.name} (0x{msg.frame_id:03X}): {len(msg.signals)} signals")

        return True

    except ImportError:
        print("⚠ cantools not available, skipping test")
        return True
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False


def test_get_nonexistent_dbc():
    """Test getting a non-existent DBC"""
    print("\n=== Test 8: Get Non-existent DBC ===")

    try:
        manager = DBCManager()

        dbc = manager.get_dbc("nonexistent")
        assert dbc is None, "Should return None for non-existent DBC"

        print(f"✓ Returns None for non-existent DBC")

        info = manager.get_dbc_info("nonexistent")
        assert info is None, "Info should be None for non-existent DBC"

        print(f"✓ Info returns None for non-existent DBC")

        return True

    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False


def run_all_tests():
    """Run all DBC manager tests"""
    print("=" * 60)
    print("DBC Manager Dialog - Logic Test Suite")
    print("=" * 60)

    tests = [
        test_add_multiple_dbc,
        test_get_dbc_info,
        test_set_active_dbc,
        test_remove_dbc,
        test_remove_active_dbc,
        test_list_empty,
        test_count_signals_in_dbc,
        test_get_nonexistent_dbc
    ]

    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append(result)
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
        print("\n✓✓✓ All DBC manager tests passed! ✓✓✓")
        return True
    else:
        print(f"\n✗ {total - passed} test(s) failed")
        return False


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
