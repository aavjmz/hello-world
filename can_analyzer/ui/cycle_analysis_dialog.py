"""
Message cycle analysis dialog

Lists the actual cycle of each CAN ID, lets the user set an expected cycle
and plots the actual interval curve against the expected cycle.
"""

from contextlib import contextmanager
from typing import Dict, Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QSplitter, QTableWidget,
    QTableWidgetItem, QHeaderView, QLabel, QDoubleSpinBox, QPushButton,
    QAbstractItemView, QMessageBox, QFileDialog
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from utils.cycle_report import export_csv, export_html
from utils.cycle_analyzer import CycleAnalyzer, CycleStats, GroupKey

COLUMNS = ["CAN ID", "通道", "方向", "报文数", "平均(ms)", "中位数(ms)", "最小(ms)", "最大(ms)",
           "标准差(ms)", "预期周期(ms)", "平均偏差(%)", "超差次数"]
COL_EXPECTED = 9


class NumericItem(QTableWidgetItem):
    """Table item that sorts by a numeric value"""

    def __init__(self, text: str, value: float):
        super().__init__(text)
        self._value = value
        self.setFlags(self.flags() & ~Qt.ItemFlag.ItemIsEditable)

    def __lt__(self, other):
        if isinstance(other, NumericItem):
            return self._value < other._value
        return super().__lt__(other)


class CycleAnalysisDialog(QDialog):
    """Dialog for CAN message cycle analysis"""

    def __init__(self, messages, parent=None, source: str = ""):
        super().__init__(parent)
        self.source = source
        self.setWindowTitle("报文周期分析")
        self.resize(1100, 750)

        self.stats: Dict[GroupKey, CycleStats] = CycleAnalyzer.analyze(messages)
        self.expected: Dict[GroupKey, float] = {}  # (can_id, channel, direction) -> expected cycle (ms)
        self._updating = False

        self._init_ui()
        self._populate_table()

    # ------------------------------------------------------------------ UI
    def _init_ui(self):
        layout = QVBoxLayout(self)

        # Top bar: tolerance + helpers
        bar = QHBoxLayout()
        bar.addWidget(QLabel("容差:"))
        self.tolerance_spin = QDoubleSpinBox()
        self.tolerance_spin.setRange(0.1, 100.0)
        self.tolerance_spin.setValue(10.0)
        self.tolerance_spin.setSuffix(" %")
        self.tolerance_spin.valueChanged.connect(self._on_tolerance_changed)
        bar.addWidget(self.tolerance_spin)

        median_btn = QPushButton("预期周期=实测中位数")
        median_btn.setToolTip("将所有ID的预期周期设为实测中位数")
        median_btn.clicked.connect(self._fill_expected_with_median)
        bar.addWidget(median_btn)

        clear_btn = QPushButton("清除预期周期")
        clear_btn.clicked.connect(self._clear_expected)
        bar.addWidget(clear_btn)

        export_btn = QPushButton("导出报告...")
        export_btn.setToolTip("导出HTML(含周期曲线)或CSV报告")
        export_btn.clicked.connect(self._export_report)
        bar.addWidget(export_btn)

        bar.addStretch()
        bar.addWidget(QLabel("提示: 双击“预期周期”列可编辑; 选中行查看周期曲线"))
        layout.addLayout(bar)

        splitter = QSplitter(Qt.Orientation.Vertical)

        self.table = QTableWidget(0, len(COLUMNS))
        self.table.setHorizontalHeaderLabels(COLUMNS)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.itemChanged.connect(self._on_item_changed)
        self.table.itemSelectionChanged.connect(self._update_plot)
        splitter.addWidget(self.table)

        self.plot_widget = self._create_plot()
        splitter.addWidget(self.plot_widget)
        splitter.setSizes([300, 450])
        layout.addWidget(splitter)

    def _create_plot(self):
        try:
            import pyqtgraph as pg
        except ImportError:
            label = QLabel("未安装 pyqtgraph，无法绘制周期曲线\npip install pyqtgraph")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            return label

        self._pg = pg
        plot = pg.PlotWidget()
        plot.setBackground('w')
        plot.showGrid(x=True, y=True, alpha=0.3)
        plot.setLabel('bottom', '时间 (s)')
        plot.setLabel('left', '报文周期 (ms)')
        plot.addLegend()
        return plot

    # ----------------------------------------------------------- table data
    @contextmanager
    def _sorting_paused(self):
        """Keep row indices stable while cells are rewritten"""
        self.table.setSortingEnabled(False)
        try:
            yield
        finally:
            self.table.setSortingEnabled(True)

    def _populate_table(self):
        self._updating = True
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(self.stats))
        for row, key in enumerate(sorted(self.stats)):
            s = self.stats[key]
            cells = [
                NumericItem(f"0x{s.can_id:03X}", s.can_id),
                NumericItem(str(s.channel), s.channel),
                NumericItem(s.direction, 0),
                NumericItem(str(s.count), s.count),
                NumericItem(f"{s.mean:.3f}", s.mean),
                NumericItem(f"{s.median:.3f}", s.median),
                NumericItem(f"{s.min:.3f}", s.min),
                NumericItem(f"{s.max:.3f}", s.max),
                NumericItem(f"{s.std:.3f}", s.std),
            ]
            for col, item in enumerate(cells):
                self.table.setItem(row, col, item)
            expected_item = QTableWidgetItem("")
            expected_item.setData(Qt.ItemDataRole.UserRole, key)
            self.table.setItem(row, COL_EXPECTED, expected_item)
            self.table.setItem(row, COL_EXPECTED + 1, NumericItem("-", 0))
            self.table.setItem(row, COL_EXPECTED + 2, NumericItem("-", 0))
        self.table.setSortingEnabled(True)
        self._updating = False

    def _refresh_row(self, row: int):
        """Recompute expected-dependent columns of one row"""
        key = self.table.item(row, COL_EXPECTED).data(Qt.ItemDataRole.UserRole)
        expected = self.expected.get(key)
        s = self.stats[key]
        self._updating = True
        if expected and s.intervals.size:
            dev = s.deviation_pct(expected)
            bad = s.out_of_tolerance(expected, self.tolerance_spin.value())
            dev_item = NumericItem(f"{dev:+.2f}", dev)
            bad_item = NumericItem(str(bad), bad)
            if bad:
                bad_item.setBackground(QColor(255, 200, 200))
            if abs(dev) > self.tolerance_spin.value():
                dev_item.setBackground(QColor(255, 200, 200))
        else:
            dev_item, bad_item = NumericItem("-", 0), NumericItem("-", 0)
        self.table.setItem(row, COL_EXPECTED + 1, dev_item)
        self.table.setItem(row, COL_EXPECTED + 2, bad_item)
        self._updating = False

    def _set_expected_cell(self, row: int, value: Optional[float]):
        key = self.table.item(row, COL_EXPECTED).data(Qt.ItemDataRole.UserRole)
        if value:
            self.expected[key] = value
        else:
            self.expected.pop(key, None)
        self._updating = True
        self.table.item(row, COL_EXPECTED).setText("" if not value else f"{value:g}")
        self._updating = False
        self._refresh_row(row)

    # -------------------------------------------------------------- events
    def _on_item_changed(self, item: QTableWidgetItem):
        if self._updating or item.column() != COL_EXPECTED:
            return
        text = item.text().strip()
        value = None
        if text:
            try:
                value = float(text)
                if value <= 0:
                    raise ValueError
            except ValueError:
                QMessageBox.warning(self, "输入无效", "预期周期必须为大于0的数值(ms)")
                value = None
        with self._sorting_paused():
            self._set_expected_cell(item.row(), value)
        self._update_plot()

    def _on_tolerance_changed(self, _value):
        with self._sorting_paused():
            for row in range(self.table.rowCount()):
                self._refresh_row(row)
        self._update_plot()

    def _fill_expected_with_median(self):
        with self._sorting_paused():
            for row in range(self.table.rowCount()):
                key = self.table.item(row, COL_EXPECTED).data(Qt.ItemDataRole.UserRole)
                median = self.stats[key].median
                self._set_expected_cell(row, round(median, 3) if median > 0 else None)
        self._update_plot()

    def _clear_expected(self):
        with self._sorting_paused():
            for row in range(self.table.rowCount()):
                self._set_expected_cell(row, None)
        self._update_plot()

    def _export_report(self):
        path, selected = QFileDialog.getSaveFileName(
            self, "导出分析报告", "cycle_report.html",
            "HTML 报告 (*.html);;CSV 表格 (*.csv)")
        if not path:
            return
        try:
            if path.lower().endswith(".csv") or "CSV" in selected and not path.lower().endswith(".html"):
                export_csv(path, self.stats, self.expected, self.tolerance_spin.value())
            else:
                export_html(path, self.stats, self.expected,
                            self.tolerance_spin.value(), self.source)
        except OSError as e:
            QMessageBox.critical(self, "导出失败", str(e))
            return
        QMessageBox.information(self, "导出成功", f"报告已保存到:\n{path}")

    # ---------------------------------------------------------------- plot
    def _update_plot(self):
        if not hasattr(self, '_pg'):
            return
        pg = self._pg
        plot = self.plot_widget
        plot.clear()

        rows = self.table.selectionModel().selectedRows()
        if not rows:
            plot.setTitle("请在上方选择一个CAN ID", color='k')
            return
        key = self.table.item(rows[0].row(), COL_EXPECTED).data(Qt.ItemDataRole.UserRole)
        s = self.stats[key]
        plot.setTitle(f"CAN ID 0x{s.can_id:03X} / 通道{s.channel} / {s.direction} 报文周期曲线",
                      color='k')
        if not s.intervals.size:
            return

        plot.plot(s.times, s.intervals, pen=pg.mkPen('#1f77b4', width=1.5),
                  symbol='o', symbolSize=3, symbolBrush='#1f77b4',
                  name="实际周期")

        expected = self.expected.get(key)
        if not expected:
            return
        tol = self.tolerance_spin.value()
        plot.addItem(pg.InfiniteLine(pos=expected, angle=0,
                                     pen=pg.mkPen('#2ca02c', width=2),
                                     label=f"预期 {expected:g}ms"))
        for bound in (expected * (1 + tol / 100), expected * (1 - tol / 100)):
            plot.addItem(pg.InfiniteLine(pos=bound, angle=0,
                                         pen=pg.mkPen('#ff7f0e', width=1,
                                                      style=Qt.PenStyle.DashLine)))
        # Legend entries for the reference lines
        plot.plot([], [], pen=pg.mkPen('#2ca02c', width=2), name=f"预期周期 {expected:g}ms")
        plot.plot([], [], pen=pg.mkPen('#ff7f0e', style=Qt.PenStyle.DashLine),
                  name=f"容差 ±{tol:g}%")

        mask = s.violation_mask(expected, tol)
        if mask.any():
            plot.plot(s.times[mask], s.intervals[mask], pen=None, symbol='o',
                      symbolSize=7, symbolBrush='#d62728', name=f"超差点 ({int(mask.sum())})")
