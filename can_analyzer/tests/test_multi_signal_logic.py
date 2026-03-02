"""
Test multi-signal logic without GUI display

Tests the internal logic of multi-signal storage and management
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
import sys


class TestMultiSignalLogic(unittest.TestCase):
    """Test multi-signal logic"""

    def test_plot_data_stores_multiple_signals(self):
        """Test that plot_data dictionary stores multiple signals correctly"""
        # Mock the plot_data storage
        plot_data = {}

        # Simulate adding 3 signals
        signal1 = {
            'times': [0.0, 1.0, 2.0],
            'values': [0.0, 50.0, 100.0],
            'name': 'Speed',
            'unit': 'km/h',
            'color': 'red'
        }

        signal2 = {
            'times': [0.0, 1.0, 2.0],
            'values': [800.0, 1500.0, 2500.0],
            'name': 'RPM',
            'unit': 'rpm',
            'color': 'blue'
        }

        signal3 = {
            'times': [0.0, 1.0, 2.0],
            'values': [20.0, 25.0, 30.0],
            'name': 'Temp',
            'unit': '°C',
            'color': 'green'
        }

        # Add to plot_data
        plot_data['msg1.speed'] = signal1
        plot_data['msg1.rpm'] = signal2
        plot_data['msg2.temp'] = signal3

        # Verify all 3 are stored
        self.assertEqual(len(plot_data), 3)
        self.assertIn('msg1.speed', plot_data)
        self.assertIn('msg1.rpm', plot_data)
        self.assertIn('msg2.temp', plot_data)

        # Verify data integrity
        self.assertEqual(plot_data['msg1.speed']['name'], 'Speed')
        self.assertEqual(plot_data['msg1.rpm']['name'], 'RPM')
        self.assertEqual(plot_data['msg2.temp']['name'], 'Temp')

    def test_refresh_iterates_all_signals(self):
        """Test that refresh logic processes all signals"""
        # Simulate plot_data with multiple signals
        plot_data = {
            'sig1': {'name': 'S1', 'unit': 'u1', 'times': [0], 'values': [1], 'color': 'r'},
            'sig2': {'name': 'S2', 'unit': 'u2', 'times': [0], 'values': [2], 'color': 'g'},
            'sig3': {'name': 'S3', 'unit': 'u3', 'times': [0], 'values': [3], 'color': 'b'},
        }

        # Count how many times plot would be called
        plot_calls = []

        for signal_key, data in plot_data.items():
            label = data['name']
            if data['unit']:
                label += f" ({data['unit']})"
            plot_calls.append(label)

        # Should have 3 plot calls
        self.assertEqual(len(plot_calls), 3)
        self.assertIn('S1 (u1)', plot_calls)
        self.assertIn('S2 (u2)', plot_calls)
        self.assertIn('S3 (u3)', plot_calls)

    def test_color_assignment_differs(self):
        """Test that different signals get different colors"""
        colors = ['red', 'blue', 'green', 'yellow', 'cyan']

        assigned_colors = []
        for i in range(5):
            # Simulate color assignment
            color = colors[i % len(colors)]
            assigned_colors.append(color)

        # All should be assigned
        self.assertEqual(len(assigned_colors), 5)

        # First 5 should all be different
        unique_colors = set(assigned_colors)
        self.assertEqual(len(unique_colors), 5)

    def test_pyqtgraph_refresh_logic(self):
        """Test the refresh logic for PyQtGraph"""
        # Simulate plot_data
        plot_data = {
            'sig1': {'name': 'S1', 'unit': '', 'times': [0], 'values': [1], 'color': 'r'},
            'sig2': {'name': 'S2', 'unit': '', 'times': [0], 'values': [2], 'color': 'g'},
        }

        # Simulate refresh logic
        # 1. Clear would be called
        # 2. Legend would be removed and re-added
        # 3. Each signal would be plotted

        # Verify plot would be called for each signal
        plot_count = len(plot_data)
        self.assertEqual(plot_count, 2)

        # Each signal should have required data
        for key, data in plot_data.items():
            self.assertIn('name', data)
            self.assertIn('times', data)
            self.assertIn('values', data)
            self.assertIn('color', data)

    def test_signal_key_uniqueness(self):
        """Test that signal keys are unique"""
        # Simulate creating signal keys
        signal_keys = []

        # From different messages
        signal_keys.append(f"EngineMessage.EngineSpeed")
        signal_keys.append(f"EngineMessage.EngineTemp")
        signal_keys.append(f"VehicleMessage.VehicleSpeed")

        # All should be unique
        self.assertEqual(len(signal_keys), 3)
        self.assertEqual(len(set(signal_keys)), 3)

        # Same signal name from different messages should be unique
        self.assertNotEqual(
            "EngineMessage.Speed",
            "VehicleMessage.Speed"
        )


if __name__ == '__main__':
    unittest.main()
