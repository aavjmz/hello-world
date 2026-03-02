"""
Test for multi-signal display in SignalPlotWidget

Tests that multiple signals can be added and displayed correctly
"""

import unittest
from unittest.mock import Mock, patch
import sys

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


class TestMultiSignalDisplay(unittest.TestCase):
    """Test cases for multi-signal display functionality"""

    def setUp(self):
        """Set up test fixtures"""
        # Import here to handle missing dependencies
        try:
            from PyQt6.QtWidgets import QApplication
            from views.signal_plot_widget import SignalPlotWidget

            if not QApplication.instance():
                self.app = QApplication(sys.argv)

            self.widget = SignalPlotWidget()
            self.has_pyqt = True
        except ImportError:
            self.has_pyqt = False

    def test_add_multiple_signals(self):
        """Test adding multiple signals to plot"""
        if not self.has_pyqt:
            self.skipTest("PyQt6 not available")

        if not self.widget.is_available():
            self.skipTest("No plotting backend available")

        # Add first signal
        times1 = [0.0, 1.0, 2.0, 3.0]
        values1 = [0.0, 10.0, 20.0, 30.0]
        self.widget.add_signal(
            signal_key="signal1",
            times=times1,
            values=values1,
            name="Speed",
            unit="km/h"
        )

        # Add second signal
        times2 = [0.0, 1.0, 2.0, 3.0]
        values2 = [0.0, 5.0, 10.0, 15.0]
        self.widget.add_signal(
            signal_key="signal2",
            times=times2,
            values=values2,
            name="Temperature",
            unit="°C"
        )

        # Add third signal
        times3 = [0.0, 1.0, 2.0, 3.0]
        values3 = [100.0, 90.0, 80.0, 70.0]
        self.widget.add_signal(
            signal_key="signal3",
            times=times3,
            values=values3,
            name="Battery",
            unit="%"
        )

        # Verify all signals are stored
        self.assertEqual(self.widget.get_signal_count(), 3)
        self.assertIn("signal1", self.widget.plot_data)
        self.assertIn("signal2", self.widget.plot_data)
        self.assertIn("signal3", self.widget.plot_data)

    def test_signal_data_integrity(self):
        """Test that signal data is stored correctly"""
        if not self.has_pyqt:
            self.skipTest("PyQt6 not available")

        if not self.widget.is_available():
            self.skipTest("No plotting backend available")

        # Add signals
        times1 = [0.0, 1.0, 2.0]
        values1 = [10.0, 20.0, 30.0]
        self.widget.add_signal(
            signal_key="sig1",
            times=times1,
            values=values1,
            name="Signal1",
            unit="V"
        )

        times2 = [0.0, 1.0, 2.0]
        values2 = [5.0, 10.0, 15.0]
        self.widget.add_signal(
            signal_key="sig2",
            times=times2,
            values=values2,
            name="Signal2",
            unit="A"
        )

        # Verify data integrity
        self.assertEqual(self.widget.plot_data["sig1"]["name"], "Signal1")
        self.assertEqual(self.widget.plot_data["sig1"]["unit"], "V")

        if HAS_NUMPY:
            np.testing.assert_array_equal(self.widget.plot_data["sig1"]["times"], times1)
            np.testing.assert_array_equal(self.widget.plot_data["sig1"]["values"], values1)
            np.testing.assert_array_equal(self.widget.plot_data["sig2"]["times"], times2)
            np.testing.assert_array_equal(self.widget.plot_data["sig2"]["values"], values2)
        else:
            # Basic list comparison
            self.assertEqual(list(self.widget.plot_data["sig1"]["times"]), times1)
            self.assertEqual(list(self.widget.plot_data["sig1"]["values"]), values1)
            self.assertEqual(list(self.widget.plot_data["sig2"]["times"]), times2)
            self.assertEqual(list(self.widget.plot_data["sig2"]["values"]), values2)

        self.assertEqual(self.widget.plot_data["sig2"]["name"], "Signal2")
        self.assertEqual(self.widget.plot_data["sig2"]["unit"], "A")

    def test_remove_signal_keeps_others(self):
        """Test that removing one signal keeps others intact"""
        if not self.has_pyqt:
            self.skipTest("PyQt6 not available")

        if not self.widget.is_available():
            self.skipTest("No plotting backend available")

        # Add three signals
        for i in range(3):
            self.widget.add_signal(
                signal_key=f"sig{i}",
                times=[0, 1, 2],
                values=[i, i+1, i+2],
                name=f"Signal{i}"
            )

        # Remove middle signal
        self.widget.remove_signal("sig1")

        # Verify count and remaining signals
        self.assertEqual(self.widget.get_signal_count(), 2)
        self.assertIn("sig0", self.widget.plot_data)
        self.assertNotIn("sig1", self.widget.plot_data)
        self.assertIn("sig2", self.widget.plot_data)

    def test_clear_all_signals(self):
        """Test clearing all signals"""
        if not self.has_pyqt:
            self.skipTest("PyQt6 not available")

        if not self.widget.is_available():
            self.skipTest("No plotting backend available")

        # Add multiple signals
        for i in range(5):
            self.widget.add_signal(
                signal_key=f"sig{i}",
                times=[0, 1, 2],
                values=[i, i+1, i+2],
                name=f"Signal{i}"
            )

        self.assertEqual(self.widget.get_signal_count(), 5)

        # Clear all
        self.widget.clear_all()

        # Verify all cleared
        self.assertEqual(self.widget.get_signal_count(), 0)
        self.assertEqual(len(self.widget.plot_data), 0)

    def test_different_colors_assigned(self):
        """Test that different signals get different colors"""
        if not self.has_pyqt:
            self.skipTest("PyQt6 not available")

        if not self.widget.is_available():
            self.skipTest("No plotting backend available")

        # Add multiple signals
        colors = []
        for i in range(5):
            self.widget.add_signal(
                signal_key=f"sig{i}",
                times=[0, 1],
                values=[0, 1],
                name=f"Signal{i}"
            )
            colors.append(self.widget.plot_data[f"sig{i}"]["color"])

        # Verify colors are assigned and different (at least first few)
        self.assertEqual(len(colors), 5)
        self.assertNotEqual(colors[0], colors[1])
        self.assertNotEqual(colors[1], colors[2])


if __name__ == '__main__':
    unittest.main()
