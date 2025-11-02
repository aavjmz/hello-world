"""
Integration Test for Signal Plotting

Tests the complete workflow: Import → DBC → Signal Selection → Plotting
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def test_module_imports():
    """Test that all required modules can be imported"""
    print("\n=== Test 1: Module Imports ===")

    try:
        from ui.signal_selection_dialog import SignalSelectionDialog
        print("✓ SignalSelectionDialog imported")
    except Exception as e:
        print(f"✗ Failed to import SignalSelectionDialog: {e}")
        return False

    try:
        from views.signal_plot_widget import SignalPlotWidget
        print("✓ SignalPlotWidget imported")
    except Exception as e:
        print(f"✗ Failed to import SignalPlotWidget: {e}")
        return False

    try:
        from parsers.asc_parser import ASCParser
        print("✓ ASCParser imported")
    except Exception as e:
        print(f"✗ Failed to import ASCParser: {e}")
        return False

    try:
        from utils.dbc_manager import DBCManager
        print("✓ DBCManager imported")
    except Exception as e:
        print(f"✗ Failed to import DBCManager: {e}")
        return False

    try:
        from utils.signal_decoder import SignalDecoder
        print("✓ SignalDecoder imported")
    except Exception as e:
        print(f"✗ Failed to import SignalDecoder: {e}")
        return False

    return True


def test_data_workflow():
    """Test data extraction workflow"""
    print("\n=== Test 2: Data Extraction Workflow ===")

    from parsers.asc_parser import ASCParser
    from utils.dbc_manager import DBCManager
    from utils.signal_decoder import SignalDecoder

    # Paths
    asc_file = os.path.join(os.path.dirname(__file__), 'test_data.asc')
    dbc_file = os.path.join(os.path.dirname(__file__), 'test_data.dbc')

    # Check if test data exists
    if not os.path.exists(asc_file):
        print(f"✗ Test data not found: {asc_file}")
        return False

    if not os.path.exists(dbc_file):
        print(f"✗ DBC file not found: {dbc_file}")
        return False

    print(f"✓ Test data files found")

    # Parse ASC file
    try:
        parser = ASCParser()
        messages = parser.parse_file(asc_file)
        print(f"✓ Parsed {len(messages)} messages")
    except Exception as e:
        print(f"✗ Failed to parse ASC: {e}")
        return False

    # Load DBC
    try:
        dbc_manager = DBCManager()
        db_name = dbc_manager.add_dbc(dbc_file, load=True)
        print(f"✓ Loaded DBC: {db_name}")
    except Exception as e:
        print(f"✗ Failed to load DBC: {e}")
        return False

    # Create decoder
    try:
        decoder = SignalDecoder(dbc_manager)
        print(f"✓ SignalDecoder created")
    except Exception as e:
        print(f"✗ Failed to create decoder: {e}")
        return False

    # Extract signal data for EngineSpeed
    try:
        target_can_id = 0x123  # EngineData
        target_signal = "EngineSpeed"

        filtered_msgs = [msg for msg in messages if msg.can_id == target_can_id]
        print(f"✓ Found {len(filtered_msgs)} messages with ID 0x{target_can_id:03X}")

        times = []
        values = []

        for msg in filtered_msgs:
            decoded = decoder.decode_message(msg)
            if decoded and decoded.signals:
                for sig in decoded.signals.values():
                    if sig.name == target_signal:
                        times.append(msg.timestamp)
                        values.append(sig.value)
                        break

        if times and values:
            print(f"✓ Extracted {len(times)} data points for {target_signal}")
            print(f"  Time range: {min(times):.3f}s - {max(times):.3f}s")
            print(f"  Value range: {min(values):.1f} - {max(values):.1f}")
            return True
        else:
            print(f"✗ No data points extracted")
            return False

    except Exception as e:
        print(f"✗ Failed to extract signal data: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_signal_metadata():
    """Test signal metadata extraction"""
    print("\n=== Test 3: Signal Metadata Extraction ===")

    from utils.dbc_manager import DBCManager

    dbc_file = os.path.join(os.path.dirname(__file__), 'test_data.dbc')

    if not os.path.exists(dbc_file):
        print(f"✗ DBC file not found")
        return False

    try:
        dbc_manager = DBCManager()
        db_name = dbc_manager.add_dbc(dbc_file, load=True)

        # Get active database
        active_db = dbc_manager.get_active()
        if not active_db:
            print("✗ No active database")
            return False

        print(f"✓ Active database: {active_db.name}")

        # Get message by ID
        can_id = 0x123
        msg_def = active_db.get_message_by_id(can_id)

        if not msg_def:
            print(f"✗ Message 0x{can_id:03X} not found")
            return False

        print(f"✓ Message found: {msg_def.name}")
        print(f"  Signal count: {len(msg_def.signals)}")

        # Extract signal metadata
        for signal in msg_def.signals:
            print(f"  • {signal.name}")
            print(f"    Unit: {signal.unit if signal.unit else '(none)'}")
            print(f"    Min: {signal.minimum}, Max: {signal.maximum}")

        return True

    except Exception as e:
        print(f"✗ Failed: {e}")
        return False


def test_unique_can_ids():
    """Test extracting unique CAN IDs"""
    print("\n=== Test 4: Unique CAN ID Extraction ===")

    from parsers.asc_parser import ASCParser

    asc_file = os.path.join(os.path.dirname(__file__), 'test_data.asc')

    if not os.path.exists(asc_file):
        print(f"✗ Test data not found")
        return False

    try:
        parser = ASCParser()
        messages = parser.parse_file(asc_file)

        # Extract unique IDs (same logic as MainWindow)
        unique_ids = list(set(msg.can_id for msg in messages))
        unique_ids.sort()

        print(f"✓ Found {len(unique_ids)} unique CAN IDs:")
        for can_id in unique_ids:
            count = sum(1 for msg in messages if msg.can_id == can_id)
            print(f"  • 0x{can_id:03X}: {count} messages")

        return True

    except Exception as e:
        print(f"✗ Failed: {e}")
        return False


def test_signal_selection_logic():
    """Test signal selection dialog logic"""
    print("\n=== Test 5: Signal Selection Logic ===")

    from utils.dbc_manager import DBCManager

    dbc_file = os.path.join(os.path.dirname(__file__), 'test_data.dbc')

    if not os.path.exists(dbc_file):
        print(f"✗ DBC file not found")
        return False

    try:
        dbc_manager = DBCManager()
        dbc_manager.add_dbc(dbc_file, load=True)

        # Simulate collecting signals for CAN IDs
        can_ids = [0x123, 0x456]
        db = dbc_manager.get_active()

        signal_count = 0
        for can_id in can_ids:
            msg_def = db.get_message_by_id(can_id)
            if msg_def:
                print(f"✓ Message 0x{can_id:03X} ({msg_def.name}):")
                for signal in msg_def.signals:
                    signal_count += 1
                    display_text = f"{msg_def.name}.{signal.name}"
                    if signal.unit:
                        display_text += f" ({signal.unit})"
                    display_text += f" [ID: 0x{can_id:03X}]"
                    print(f"  • {display_text}")

        print(f"\n✓ Total signals available: {signal_count}")
        return True

    except Exception as e:
        print(f"✗ Failed: {e}")
        return False


def test_complete_workflow():
    """Test the complete end-to-end workflow"""
    print("\n=== Test 6: Complete Workflow Simulation ===")

    from parsers.asc_parser import ASCParser
    from utils.dbc_manager import DBCManager
    from utils.signal_decoder import SignalDecoder

    # File paths
    asc_file = os.path.join(os.path.dirname(__file__), 'test_data.asc')
    dbc_file = os.path.join(os.path.dirname(__file__), 'test_data.dbc')

    try:
        # Step 1: Import messages
        print("Step 1: Import messages")
        parser = ASCParser()
        messages = parser.parse_file(asc_file)
        print(f"  ✓ Loaded {len(messages)} messages")

        # Step 2: Import DBC
        print("Step 2: Import DBC")
        dbc_manager = DBCManager()
        db_name = dbc_manager.add_dbc(dbc_file, load=True)
        print(f"  ✓ Loaded DBC: {db_name}")

        # Step 3: Get unique CAN IDs
        print("Step 3: Get unique CAN IDs")
        unique_ids = list(set(msg.can_id for msg in messages))
        unique_ids.sort()
        print(f"  ✓ Found {len(unique_ids)} unique IDs")

        # Step 4: Simulate signal selection
        print("Step 4: Simulate signal selection")
        db = dbc_manager.get_active()
        selected_signals = []

        # Select first signal from first message
        can_id = 0x123
        msg_def = db.get_message_by_id(can_id)
        if msg_def and msg_def.signals:
            signal = msg_def.signals[0]
            selected_signals.append({
                'can_id': can_id,
                'message_name': msg_def.name,
                'signal_name': signal.name,
                'unit': signal.unit
            })
            print(f"  ✓ Selected: {msg_def.name}.{signal.name}")

        # Step 5: Extract signal data
        print("Step 5: Extract signal data")
        decoder = SignalDecoder(dbc_manager)

        for signal_info in selected_signals:
            can_id = signal_info['can_id']
            signal_name = signal_info['signal_name']

            # Filter messages
            filtered_msgs = [msg for msg in messages if msg.can_id == can_id]

            times = []
            values = []

            for msg in filtered_msgs:
                decoded = decoder.decode_message(msg)
                if decoded and decoded.signals:
                    for sig_val in decoded.signals.values():
                        if sig_val.name == signal_name:
                            times.append(msg.timestamp)
                            values.append(sig_val.value)
                            break

            if times and values:
                print(f"  ✓ Extracted {len(times)} points: {signal_name}")
                print(f"    Range: [{min(values):.1f}, {max(values):.1f}]")
            else:
                print(f"  ✗ No data for {signal_name}")
                return False

        print("\n✓ Complete workflow successful!")
        return True

    except Exception as e:
        print(f"\n✗ Workflow failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all integration tests"""
    print("=" * 60)
    print("Signal Plotting - Integration Test Suite")
    print("=" * 60)

    tests = [
        test_module_imports,
        test_data_workflow,
        test_signal_metadata,
        test_unique_can_ids,
        test_signal_selection_logic,
        test_complete_workflow
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
        print("\n✓✓✓ All integration tests passed! ✓✓✓")
        print("\nValidated complete workflow:")
        print("  1. Import CAN messages from ASC file")
        print("  2. Load DBC database")
        print("  3. Extract unique CAN IDs")
        print("  4. Get signal metadata from DBC")
        print("  5. Decode messages and extract signal values")
        print("  6. Prepare data for plotting")
        return True
    else:
        print(f"\n✗ {total - passed} test(s) failed")
        return False


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
