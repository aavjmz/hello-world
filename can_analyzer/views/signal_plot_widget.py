"""
Signal Plot Widget for displaying signal curves

Supports both PyQtGraph (preferred) and Matplotlib (fallback) backends
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QMessageBox
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from typing import List, Dict, Optional, Tuple
import numpy as np


class SignalPlotWidget(QWidget):
    """Widget for plotting signal values over time"""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.plot_data: Dict[str, Dict] = {}  # signal_key -> {times, values, color}
        self.backend = None  # 'pyqtgraph' or 'matplotlib'
        self.plot_widget = None

        self.init_ui()
        self.detect_backend()

    def init_ui(self):
        """Initialize the user interface"""
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

    def detect_backend(self):
        """Detect which plotting backend is available"""
        # Try PyQtGraph first
        try:
            import pyqtgraph as pg
            self.backend = 'pyqtgraph'
            self.init_pyqtgraph()
            return
        except ImportError:
            pass

        # Try Matplotlib as fallback
        try:
            from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
            from matplotlib.figure import Figure
            self.backend = 'matplotlib'
            self.init_matplotlib()
            return
        except ImportError:
            pass

        # No backend available
        self.backend = None
        self.show_no_backend_message()

    def init_pyqtgraph(self):
        """Initialize PyQtGraph plot widget"""
        import pyqtgraph as pg

        # Configure font for Chinese characters
        font = QFont()
        # Try to use common Chinese fonts available on different platforms
        chinese_fonts = ['Microsoft YaHei', 'SimHei', 'STHeiti', 'PingFang SC', 'Arial Unicode MS', 'sans-serif']
        for font_name in chinese_fonts:
            font.setFamily(font_name)
            if font.family() == font_name or font.family() in chinese_fonts:
                break
        font.setPointSize(10)

        # Set default font for PyQtGraph
        pg.setConfigOptions(antialias=True)

        # Create plot widget
        self.plot_widget = pg.PlotWidget()

        # Configure plot
        self.plot_widget.setBackground('w')  # White background
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)

        # Set labels with font
        axis_font = QFont(font)
        axis_font.setPointSize(10)

        styles = {'color': 'black', 'font-size': '12pt', 'font-family': font.family()}
        self.plot_widget.setLabel('bottom', '时间 (s)', **styles)
        self.plot_widget.setLabel('left', '信号值', **styles)

        # Set title with font
        title_font = QFont(font)
        title_font.setPointSize(12)
        title_font.setBold(True)
        self.plot_widget.setTitle('信号曲线', color='black', size='14pt')

        # Enable mouse interaction
        self.plot_widget.setMouseEnabled(x=True, y=True)  # Enable pan
        self.plot_widget.enableAutoRange()

        # Add legend
        self.plot_widget.addLegend()

        self.layout.addWidget(self.plot_widget)

    def init_matplotlib(self):
        """Initialize Matplotlib plot widget"""
        from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT
        from matplotlib.figure import Figure
        import matplotlib.pyplot as plt
        import matplotlib

        # Configure matplotlib to use Chinese fonts
        # Try common Chinese fonts on different platforms
        chinese_fonts = ['Microsoft YaHei', 'SimHei', 'STHeiti', 'PingFang SC', 'Arial Unicode MS', 'DejaVu Sans']

        font_found = False
        for font_name in chinese_fonts:
            try:
                matplotlib.rcParams['font.sans-serif'] = [font_name] + matplotlib.rcParams['font.sans-serif']
                font_found = True
                break
            except:
                continue

        if not font_found:
            # Fallback: use default sans-serif and hope it supports Chinese
            matplotlib.rcParams['font.sans-serif'] = ['sans-serif']

        # Fix negative sign display issue
        matplotlib.rcParams['axes.unicode_minus'] = False

        # Create figure and canvas
        self.figure = Figure(figsize=(8, 6))
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.axes = self.figure.add_subplot(111)

        # Add toolbar
        self.toolbar = NavigationToolbar2QT(self.canvas, self)

        # Configure axes with Chinese labels
        self.axes.set_xlabel('时间 (s)', fontsize=10)
        self.axes.set_ylabel('信号值', fontsize=10)
        self.axes.set_title('信号曲线', fontsize=12, fontweight='bold')
        self.axes.grid(True, alpha=0.3)

        self.layout.addWidget(self.toolbar)
        self.layout.addWidget(self.canvas)

        self.plot_widget = self.canvas

    def show_no_backend_message(self):
        """Show message when no plotting backend is available"""
        label = QLabel()
        label.setText(
            "<h3>无可用的绘图库</h3>"
            "<p>请安装以下任一绘图库：</p>"
            "<ul>"
            "<li>PyQtGraph (推荐): <code>pip install pyqtgraph</code></li>"
            "<li>Matplotlib: <code>pip install matplotlib</code></li>"
            "</ul>"
        )
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setWordWrap(True)
        self.layout.addWidget(label)

    def add_signal(self, signal_key: str, times: List[float], values: List[float],
                  name: str = "", unit: str = "", color: Optional[str] = None):
        """
        Add a signal curve to the plot

        Args:
            signal_key: Unique key for this signal
            times: List of timestamps
            values: List of signal values
            name: Display name
            unit: Unit string
            color: Color for the curve (optional)
        """
        if self.backend is None:
            return

        # Generate color if not provided
        if color is None:
            color = self._get_next_color()

        # Store data
        self.plot_data[signal_key] = {
            'times': np.array(times),
            'values': np.array(values),
            'name': name,
            'unit': unit,
            'color': color
        }

        # Refresh plot
        self.refresh_plot()

    def remove_signal(self, signal_key: str):
        """Remove a signal from the plot"""
        if signal_key in self.plot_data:
            del self.plot_data[signal_key]
            self.refresh_plot()

    def clear_all(self):
        """Clear all signals"""
        self.plot_data.clear()
        self.refresh_plot()

    def refresh_plot(self):
        """Refresh the plot with current data"""
        if self.backend == 'pyqtgraph':
            self._refresh_pyqtgraph()
        elif self.backend == 'matplotlib':
            self._refresh_matplotlib()

    def _refresh_pyqtgraph(self):
        """Refresh PyQtGraph plot"""
        import pyqtgraph as pg

        # Clear existing plot items (but keep legend)
        self.plot_widget.getPlotItem().clearPlots()

        # Plot each signal
        for signal_key, data in self.plot_data.items():
            label = data['name']
            if data['unit']:
                label += f" ({data['unit']})"

            pen = pg.mkPen(color=data['color'], width=2)
            self.plot_widget.plot(
                data['times'],
                data['values'],
                pen=pen,
                name=label
            )

    def _refresh_matplotlib(self):
        """Refresh Matplotlib plot"""
        # Clear axes
        self.axes.clear()

        # Plot each signal
        for signal_key, data in self.plot_data.items():
            label = data['name']
            if data['unit']:
                label += f" ({data['unit']})"

            self.axes.plot(
                data['times'],
                data['values'],
                color=data['color'],
                linewidth=2,
                label=label
            )

        # Re-configure axes with Chinese labels
        self.axes.set_xlabel('时间 (s)', fontsize=10)
        self.axes.set_ylabel('信号值', fontsize=10)
        self.axes.set_title('信号曲线', fontsize=12, fontweight='bold')
        self.axes.grid(True, alpha=0.3)

        # Add legend if there are signals
        if self.plot_data:
            # Set legend with font properties
            self.axes.legend(prop={'size': 9})

        # Redraw
        self.canvas.draw()

    def _get_next_color(self) -> str:
        """Get next color from color cycle"""
        colors = [
            '#1f77b4',  # Blue
            '#ff7f0e',  # Orange
            '#2ca02c',  # Green
            '#d62728',  # Red
            '#9467bd',  # Purple
            '#8c564b',  # Brown
            '#e377c2',  # Pink
            '#7f7f7f',  # Gray
            '#bcbd22',  # Olive
            '#17becf',  # Cyan
        ]

        index = len(self.plot_data) % len(colors)
        return colors[index]

    def get_backend(self) -> Optional[str]:
        """Get the current backend name"""
        return self.backend

    def is_available(self) -> bool:
        """Check if plotting is available"""
        return self.backend is not None

    def zoom_to_fit(self):
        """Zoom to fit all data"""
        if self.backend == 'pyqtgraph':
            self.plot_widget.enableAutoRange()
        elif self.backend == 'matplotlib':
            self.axes.relim()
            self.axes.autoscale()
            self.canvas.draw()

    def set_title(self, title: str):
        """Set plot title"""
        if self.backend == 'pyqtgraph':
            self.plot_widget.setTitle(title)
        elif self.backend == 'matplotlib':
            self.axes.set_title(title)
            self.canvas.draw()

    def get_signal_count(self) -> int:
        """Get number of signals currently plotted"""
        return len(self.plot_data)

    def get_signal_keys(self) -> List[str]:
        """Get list of signal keys"""
        return list(self.plot_data.keys())
