"""
Test Signal Plot Widget Logic (Non-GUI)

Validates the signal plot widget structure and logic without GUI
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def test_file_structure():
    """Test that signal plot widget file exists and has correct structure"""
    print("\n=== Test 1: File Structure ===")

    filepath = os.path.join(os.path.dirname(__file__), '..', 'views', 'signal_plot_widget.py')

    if not os.path.exists(filepath):
        print("✗ Signal plot widget file not found")
        return False

    print(f"✓ File exists: {filepath}")

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check for required class
    if 'class SignalPlotWidget' not in content:
        print("✗ SignalPlotWidget class not found")
        return False

    print("✓ SignalPlotWidget class found")

    # Check for required methods
    required_methods = [
        'def __init__',
        'def init_ui',
        'def detect_backend',
        'def init_pyqtgraph',
        'def init_matplotlib',
        'def add_signal',
        'def remove_signal',
        'def clear_all',
        'def refresh_plot',
        'def zoom_to_fit',
        'def get_backend',
        'def is_available'
    ]

    missing_methods = []
    for method in required_methods:
        if method not in content:
            missing_methods.append(method)

    if missing_methods:
        print(f"✗ Missing methods: {missing_methods}")
        return False

    print(f"✓ All {len(required_methods)} required methods found")

    # Check for backend support
    backends = ['pyqtgraph', 'matplotlib']
    for backend in backends:
        if backend not in content:
            print(f"✗ Backend '{backend}' not mentioned")
            return False

    print(f"✓ Both backends (PyQtGraph, Matplotlib) supported")

    return True


def test_selection_dialog_structure():
    """Test signal selection dialog structure"""
    print("\n=== Test 2: Signal Selection Dialog Structure ===")

    filepath = os.path.join(os.path.dirname(__file__), '..', 'ui', 'signal_selection_dialog.py')

    if not os.path.exists(filepath):
        print("✗ Signal selection dialog file not found")
        return False

    print(f"✓ File exists: {filepath}")

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check for required class
    if 'class SignalSelectionDialog' not in content:
        print("✗ SignalSelectionDialog class not found")
        return False

    print("✓ SignalSelectionDialog class found")

    # Check for required methods
    required_methods = [
        'def __init__',
        'def init_ui',
        'def load_signals',
        'def select_all',
        'def clear_selection',
        'def get_selected_signals',
        '@staticmethod',
        'def select_signals'
    ]

    missing_methods = []
    for method in required_methods:
        if method not in content:
            missing_methods.append(method)

    if missing_methods:
        print(f"✗ Missing methods: {missing_methods}")
        return False

    print(f"✓ All {len(required_methods)} required methods/decorators found")

    # Check for UI elements
    ui_elements = [
        'QListWidget',
        'QPushButton',
        'MultiSelection',
        '全选',
        '清空',
        '确定',
        '取消'
    ]

    missing_elements = []
    for element in ui_elements:
        if element not in content:
            missing_elements.append(element)

    if missing_elements:
        print(f"✗ Missing UI elements: {missing_elements}")
        return False

    print(f"✓ All UI elements found")

    return True


def test_integration_points():
    """Test integration points with existing modules"""
    print("\n=== Test 3: Integration Points ===")

    plot_file = os.path.join(os.path.dirname(__file__), '..', 'views', 'signal_plot_widget.py')

    with open(plot_file, 'r', encoding='utf-8') as f:
        plot_content = f.read()

    # Check imports
    required_imports = [
        'from PyQt6.QtWidgets import',
        'from PyQt6.QtCore import',
        'from typing import',
        'import numpy'
    ]

    for imp in required_imports:
        if imp not in plot_content:
            print(f"✗ Missing import: {imp}")
            return False

    print("✓ Required imports found")

    # Check data structures
    if 'self.plot_data' not in plot_content:
        print("✗ plot_data structure not found")
        return False

    print("✓ Data storage structure found")

    # Check for color support
    if 'color' not in plot_content or '_get_next_color' not in plot_content:
        print("✗ Color management not found")
        return False

    print("✓ Color management found")

    return True


def test_backend_fallback():
    """Test backend fallback logic"""
    print("\n=== Test 4: Backend Fallback Logic ===")

    filepath = os.path.join(os.path.dirname(__file__), '..', 'views', 'signal_plot_widget.py')

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check for try-except blocks for backend detection
    if content.count('try:') < 2:
        print("✗ Not enough try-except blocks for backend fallback")
        return False

    if 'except ImportError:' not in content:
        print("✗ ImportError handling not found")
        return False

    print("✓ Exception handling for backend detection found")

    # Check for fallback message
    if 'show_no_backend_message' not in content:
        print("✗ No backend message function not found")
        return False

    if '无可用的绘图库' not in content or 'pip install pyqtgraph' not in content:
        print("✗ User-friendly error message not found")
        return False

    print("✓ Fallback message with installation instructions found")

    return True


def test_api_consistency():
    """Test API method signatures"""
    print("\n=== Test 5: API Consistency ===")

    filepath = os.path.join(os.path.dirname(__file__), '..', 'views', 'signal_plot_widget.py')

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check add_signal signature
    if 'def add_signal(self, signal_key: str, times: List[float], values: List[float]' not in content:
        print("✗ add_signal method signature incorrect")
        return False

    print("✓ add_signal signature correct")

    # Check remove_signal signature
    if 'def remove_signal(self, signal_key: str)' not in content:
        print("✗ remove_signal method signature incorrect")
        return False

    print("✓ remove_signal signature correct")

    # Check utility methods
    utility_methods = [
        'def get_signal_count',
        'def get_signal_keys',
        'def set_title'
    ]

    for method in utility_methods:
        if method not in content:
            print(f"✗ Utility method missing: {method}")
            return False

    print("✓ All utility methods present")

    return True


def test_documentation():
    """Test that code has proper documentation"""
    print("\n=== Test 6: Documentation ===")

    filepath = os.path.join(os.path.dirname(__file__), '..', 'views', 'signal_plot_widget.py')

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check for module docstring
    if '"""' not in content[:500]:
        print("✗ Module docstring missing")
        return False

    print("✓ Module docstring found")

    # Check for class docstring
    lines = content.split('\n')
    class_line_found = False
    docstring_after_class = False

    for i, line in enumerate(lines):
        if 'class SignalPlotWidget' in line:
            class_line_found = True
            # Check next few lines for docstring
            if i + 1 < len(lines) and '"""' in lines[i + 1]:
                docstring_after_class = True
                break

    if not class_line_found:
        print("✗ Class definition not found")
        return False

    if not docstring_after_class:
        print("✗ Class docstring missing")
        return False

    print("✓ Class docstring found")

    # Check for method docstrings (at least for add_signal)
    if 'def add_signal' in content:
        add_signal_idx = content.index('def add_signal')
        next_section = content[add_signal_idx:add_signal_idx + 500]
        if '"""' in next_section or "'''" in next_section:
            print("✓ Method docstrings found")
        else:
            print("⚠ Method docstrings could be improved")

    return True


def run_all_tests():
    """Run all logic validation tests"""
    print("=" * 60)
    print("Signal Plot Widget - Logic Validation Suite")
    print("=" * 60)

    tests = [
        test_file_structure,
        test_selection_dialog_structure,
        test_integration_points,
        test_backend_fallback,
        test_api_consistency,
        test_documentation
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
        print("\n✓✓✓ All validation tests passed! ✓✓✓")
        print("\nValidated:")
        print("  • SignalPlotWidget structure and methods")
        print("  • SignalSelectionDialog structure and UI")
        print("  • Backend detection and fallback logic")
        print("  • API consistency and method signatures")
        print("  • Integration points with existing modules")
        print("  • Documentation quality")
        return True
    else:
        print(f"\n✗ {total - passed} validation(s) failed")
        return False


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
