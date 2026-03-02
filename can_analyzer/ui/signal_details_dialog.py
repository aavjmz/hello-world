"""
Signal Details Dialog - Display detailed information about decoded signals
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QDialogButtonBox, QLabel
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from typing import Optional
from parsers.asc_parser import CANMessage
from utils.signal_decoder import SignalDecoder, DecodedMessage


class SignalDetailsDialog(QDialog):
    """Dialog showing detailed information about all signals in a message"""

    def __init__(self, message: CANMessage, decoder: SignalDecoder, parent=None):
        super().__init__(parent)
        self.message = message
        self.decoder = decoder

        self.setWindowTitle("信号详情")
        self.resize(800, 500)

        self.setup_ui()
        self.load_signal_details()

    def setup_ui(self):
        """Setup the dialog UI"""
        layout = QVBoxLayout(self)

        # Header info
        header_label = QLabel()
        header_label.setFont(QFont("", 10, QFont.Weight.Bold))
        layout.addWidget(header_label)
        self.header_label = header_label

        # Signal details table
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "信号名", "物理值", "单位", "原始值", "最小值", "最大值", "Bit位置", "长度(bit)"
        ])

        # Set column properties
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # 信号名
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # 物理值
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # 单位
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # 原始值
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # 最小值
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # 最大值
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)  # Bit位置
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Stretch)           # 长度

        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        layout.addWidget(self.table)

        # Button box
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(self.close)
        layout.addWidget(button_box)

    def load_signal_details(self):
        """Load and display signal details"""
        # Decode the message
        decoded = self.decoder.decode_message(self.message)

        if not decoded or not decoded.signals:
            self.header_label.setText(
                f"CAN ID: 0x{self.message.can_id:03X} - 无法解码信号"
            )
            return

        # Update header
        self.header_label.setText(
            f"消息: {decoded.message_name} (ID: 0x{decoded.can_id:03X}) - "
            f"共 {len(decoded.signals)} 个信号"
        )

        # Get DBC database for signal definitions
        db = self.decoder.dbc_manager.get_active()
        if not db:
            return

        msg_def = db.get_message_by_id(self.message.can_id)
        if not msg_def:
            return

        # Populate table
        self.table.setRowCount(len(decoded.signals))

        row = 0
        for signal_name, signal_value in decoded.signals.items():
            # Find signal definition
            signal_def = None
            for sig in msg_def.signals:
                if sig.name == signal_name:
                    signal_def = sig
                    break

            if not signal_def:
                continue

            # Column 0: Signal name
            item = QTableWidgetItem(signal_name)
            item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 0, item)

            # Column 1: Physical value (formatted)
            physical_value = signal_value.value
            item = QTableWidgetItem(str(physical_value))
            item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 1, item)

            # Column 2: Unit
            unit = signal_value.unit or "-"
            item = QTableWidgetItem(unit)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 2, item)

            # Column 3: Raw value
            raw_value = signal_value.raw_value
            # Handle NamedSignalValue
            if hasattr(raw_value, 'value'):
                raw_display = f"{raw_value.value} ({raw_value.name})" if hasattr(raw_value, 'name') else str(raw_value.value)
            else:
                raw_display = str(raw_value)
            item = QTableWidgetItem(raw_display)
            item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 3, item)

            # Column 4: Minimum value
            min_val = signal_def.minimum if signal_def.minimum is not None else "-"
            item = QTableWidgetItem(str(min_val))
            item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 4, item)

            # Column 5: Maximum value
            max_val = signal_def.maximum if signal_def.maximum is not None else "-"
            item = QTableWidgetItem(str(max_val))
            item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 5, item)

            # Column 6: Bit position (start bit)
            bit_pos = f"{signal_def.start}"
            item = QTableWidgetItem(bit_pos)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 6, item)

            # Column 7: Bit length
            bit_len = str(signal_def.length)
            item = QTableWidgetItem(bit_len)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 7, item)

            row += 1
