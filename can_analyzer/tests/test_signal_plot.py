"""
Test Signal Plot Widget

Tests signal plotting functionality with both backends
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from PyQt6.QtWidgets import QApplication
from views.signal_plot_widget import SignalPlotWidget
import numpy as np


def test_backend_detection():
    """Test that a backend is detected"""
    print("\n=== Test 1: Backend Detection ===")

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    widget = SignalPlotWidget()
    backend = widget.get_backend()

    print(f"Detected backend: {backend}")

    if backend is None:
        print("⚠ No plotting backend available")
        print("  Install: pip install pyqtgraph  (recommended)")
        print("  Or: pip install matplotlib")
        return False
    elif backend == 'pyqtgraph':
        print("✓ PyQtGraph backend available (preferred)")
        return True
    elif backend == 'matplotlib':
        print("✓ Matplotlib backend available")
        return True

    return False


def test_add_signal():
    """Test adding signals to plot"""
    print("\n=== Test 2: Add Signal ===")

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    widget = SignalPlotWidget()

    if not widget.is_available():
        print("⚠ Skipping test - no backend available")
        return True  # Not a failure, just skip

    # Generate test data
    times = np.linspace(0, 10, 100)
    values = np.sin(times)

    # Add signal
    widget.add_signal(
        signal_key="signal1",
        times=times.tolist(),
        values=values.tolist(),
        name="Test Signal",
        unit="V"
    )

    # Verify signal was added
    count = widget.get_signal_count()
    keys = widget.get_signal_keys()

    print(f"Signal count: {count}")
    print(f"Signal keys: {keys}")

    if count == 1 and "signal1" in keys:
        print("✓ Signal added successfully")
        return True
    else:
        print("✗ Signal add failed")
        return False


def test_multiple_signals():
    """Test adding multiple signals"""
    print("\n=== Test 3: Multiple Signals ===")

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    widget = SignalPlotWidget()

    if not widget.is_available():
        print("⚠ Skipping test - no backend available")
        return True

    # Generate test data for 3 signals
    times = np.linspace(0, 10, 100)

    widget.add_signal("sig1", times.tolist(), np.sin(times).tolist(),
                     "Sine", "V", "#1f77b4")
    widget.add_signal("sig2", times.tolist(), np.cos(times).tolist(),
                     "Cosine", "V", "#ff7f0e")
    widget.add_signal("sig3", times.tolist(), (np.sin(times) * 2).tolist(),
                     "Double Sine", "V", "#2ca02c")

    count = widget.get_signal_count()
    print(f"Added {count} signals")

    if count == 3:
        print("✓ Multiple signals added successfully")
        return True
    else:
        print(f"✗ Expected 3 signals, got {count}")
        return False


def test_remove_signal():
    """Test removing signals"""
    print("\n=== Test 4: Remove Signal ===")

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    widget = SignalPlotWidget()

    if not widget.is_available():
        print("⚠ Skipping test - no backend available")
        return True

    # Add signals
    times = [0, 1, 2, 3, 4]
    values = [0, 1, 4, 9, 16]

    widget.add_signal("sig1", times, values, "Signal 1")
    widget.add_signal("sig2", times, values, "Signal 2")

    initial_count = widget.get_signal_count()
    print(f"Initial count: {initial_count}")

    # Remove one signal
    widget.remove_signal("sig1")

    final_count = widget.get_signal_count()
    keys = widget.get_signal_keys()

    print(f"After removal: {final_count}")
    print(f"Remaining keys: {keys}")

    if final_count == 1 and "sig2" in keys and "sig1" not in keys:
        print("✓ Signal removed successfully")
        return True
    else:
        print("✗ Signal removal failed")
        return False


def test_clear_all():
    """Test clearing all signals"""
    print("\n=== Test 5: Clear All Signals ===")

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    widget = SignalPlotWidget()

    if not widget.is_available():
        print("⚠ Skipping test - no backend available")
        return True

    # Add some signals
    times = [0, 1, 2]
    values = [0, 1, 2]

    widget.add_signal("sig1", times, values)
    widget.add_signal("sig2", times, values)
    widget.add_signal("sig3", times, values)

    print(f"Before clear: {widget.get_signal_count()} signals")

    # Clear all
    widget.clear_all()

    count = widget.get_signal_count()
    print(f"After clear: {count} signals")

    if count == 0:
        print("✓ All signals cleared")
        return True
    else:
        print("✗ Clear all failed")
        return False


def test_color_cycling():
    """Test automatic color assignment"""
    print("\n=== Test 6: Color Cycling ===")

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    widget = SignalPlotWidget()

    if not widget.is_available():
        print("⚠ Skipping test - no backend available")
        return True

    # Add signals without specifying colors
    times = [0, 1, 2]
    values = [0, 1, 2]

    for i in range(5):
        widget.add_signal(f"sig{i}", times, values, f"Signal {i}")

    # Check that colors were assigned
    colors = [widget.plot_data[f"sig{i}"]["color"] for i in range(5)]
    print(f"Assigned colors: {colors}")

    # All colors should be different
    unique_colors = len(set(colors))

    if unique_colors == 5:
        print("✓ Unique colors assigned to each signal")
        return True
    else:
        print(f"✗ Expected 5 unique colors, got {unique_colors}")
        return False


def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("Signal Plot Widget - Test Suite")
    print("=" * 60)

    tests = [
        test_backend_detection,
        test_add_signal,
        test_multiple_signals,
        test_remove_signal,
        test_clear_all,
        test_color_cycling
    ]

    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"\n✗ Test failed with exception: {e}")
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
        print("✓ All tests passed!")
        return True
    else:
        print(f"✗ {total - passed} test(s) failed")
        return False


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
