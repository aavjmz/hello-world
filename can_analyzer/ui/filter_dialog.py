"""
Message Filter Dialog

Allows users to configure filters for CAN messages
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox,
    QCheckBox, QLineEdit, QLabel, QPushButton,
    QComboBox, QSpinBox, QDoubleSpinBox
)
from PyQt6.QtCore import Qt
from typing import Dict, List, Optional, Set
from utils.message_filter import MessageFilter


# Re-export MessageFilter for convenience
__all__ = ['MessageFilter', 'FilterDialog']


class FilterDialog(QDialog):
    """Dialog for configuring message filters"""

    def __init__(self, current_filter: Optional[MessageFilter] = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("配置报文过滤器")
        self.setMinimumWidth(500)

        # Initialize filter
        self.filter = current_filter if current_filter else MessageFilter()

        # Initialize UI
        self.init_ui()

        # Load current filter settings
        self.load_filter_settings()

    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)

        # CAN ID filter group
        can_id_group = self.create_can_id_group()
        layout.addWidget(can_id_group)

        # Direction filter group
        direction_group = self.create_direction_group()
        layout.addWidget(direction_group)

        # Time filter group
        time_group = self.create_time_group()
        layout.addWidget(time_group)

        # DLC filter group
        dlc_group = self.create_dlc_group()
        layout.addWidget(dlc_group)

        # Buttons
        button_layout = QHBoxLayout()

        self.clear_btn = QPushButton("清除所有")
        self.clear_btn.clicked.connect(self.clear_all_filters)
        button_layout.addWidget(self.clear_btn)

        button_layout.addStretch()

        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)

        self.apply_btn = QPushButton("应用")
        self.apply_btn.clicked.connect(self.apply_filter)
        self.apply_btn.setDefault(True)
        button_layout.addWidget(self.apply_btn)

        layout.addLayout(button_layout)

    def create_can_id_group(self) -> QGroupBox:
        """Create CAN ID filter group"""
        group = QGroupBox("CAN ID 过滤")
        layout = QVBoxLayout(group)

        # Enable checkbox
        self.can_id_enabled = QCheckBox("启用 CAN ID 过滤")
        layout.addWidget(self.can_id_enabled)

        # Mode selection
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("模式:"))

        self.can_id_mode = QComboBox()
        self.can_id_mode.addItems(["包含 (仅显示)", "排除 (不显示)"])
        mode_layout.addWidget(self.can_id_mode)
        mode_layout.addStretch()

        layout.addLayout(mode_layout)

        # ID input
        id_layout = QHBoxLayout()
        id_layout.addWidget(QLabel("ID列表 (十六进制，逗号分隔):"))

        self.can_id_input = QLineEdit()
        self.can_id_input.setPlaceholderText("例如: 123, 456, 0x789")
        id_layout.addWidget(self.can_id_input)

        layout.addLayout(id_layout)

        return group

    def create_direction_group(self) -> QGroupBox:
        """Create direction filter group"""
        group = QGroupBox("方向过滤")
        layout = QVBoxLayout(group)

        # Enable checkbox
        self.dir_enabled = QCheckBox("启用方向过滤")
        layout.addWidget(self.dir_enabled)

        # Direction checkboxes
        dir_layout = QHBoxLayout()
        dir_layout.addWidget(QLabel("显示:"))

        self.show_rx = QCheckBox("Rx (接收)")
        self.show_rx.setChecked(True)
        dir_layout.addWidget(self.show_rx)

        self.show_tx = QCheckBox("Tx (发送)")
        self.show_tx.setChecked(True)
        dir_layout.addWidget(self.show_tx)

        dir_layout.addStretch()

        layout.addLayout(dir_layout)

        return group

    def create_time_group(self) -> QGroupBox:
        """Create time filter group"""
        group = QGroupBox("时间范围过滤")
        layout = QVBoxLayout(group)

        # Enable checkbox
        self.time_enabled = QCheckBox("启用时间范围过滤")
        layout.addWidget(self.time_enabled)

        # Time range
        range_layout = QHBoxLayout()

        range_layout.addWidget(QLabel("起始时间 (秒):"))
        self.time_start = QDoubleSpinBox()
        self.time_start.setRange(0, 999999.999)
        self.time_start.setDecimals(3)
        self.time_start.setSingleStep(0.1)
        range_layout.addWidget(self.time_start)

        range_layout.addWidget(QLabel("结束时间 (秒):"))
        self.time_end = QDoubleSpinBox()
        self.time_end.setRange(0, 999999.999)
        self.time_end.setDecimals(3)
        self.time_end.setSingleStep(0.1)
        self.time_end.setValue(999999.999)
        range_layout.addWidget(self.time_end)

        layout.addLayout(range_layout)

        return group

    def create_dlc_group(self) -> QGroupBox:
        """Create DLC filter group"""
        group = QGroupBox("DLC (数据长度) 过滤")
        layout = QVBoxLayout(group)

        # Enable checkbox
        self.dlc_enabled = QCheckBox("启用 DLC 过滤")
        layout.addWidget(self.dlc_enabled)

        # DLC range
        range_layout = QHBoxLayout()

        range_layout.addWidget(QLabel("最小 DLC:"))
        self.dlc_min = QSpinBox()
        self.dlc_min.setRange(0, 8)
        self.dlc_min.setValue(0)
        range_layout.addWidget(self.dlc_min)

        range_layout.addWidget(QLabel("最大 DLC:"))
        self.dlc_max = QSpinBox()
        self.dlc_max.setRange(0, 8)
        self.dlc_max.setValue(8)
        range_layout.addWidget(self.dlc_max)

        range_layout.addStretch()

        layout.addLayout(range_layout)

        return group

    def load_filter_settings(self):
        """Load current filter settings into UI"""
        # CAN ID
        self.can_id_enabled.setChecked(self.filter.filter_by_can_id)
        self.can_id_mode.setCurrentIndex(0 if self.filter.can_id_mode == "include" else 1)
        if self.filter.can_id_list:
            id_strings = [f"0x{can_id:X}" for can_id in sorted(self.filter.can_id_list)]
            self.can_id_input.setText(", ".join(id_strings))

        # Direction
        self.dir_enabled.setChecked(self.filter.filter_by_direction)
        self.show_rx.setChecked(self.filter.show_rx)
        self.show_tx.setChecked(self.filter.show_tx)

        # Time
        self.time_enabled.setChecked(self.filter.filter_by_time)
        self.time_start.setValue(self.filter.time_start)
        self.time_end.setValue(self.filter.time_end)

        # DLC
        self.dlc_enabled.setChecked(self.filter.filter_by_dlc)
        self.dlc_min.setValue(self.filter.dlc_min)
        self.dlc_max.setValue(self.filter.dlc_max)

    def parse_can_ids(self, text: str) -> Set[int]:
        """
        Parse CAN IDs from text input

        Args:
            text: Comma-separated list of CAN IDs

        Returns:
            Set of parsed CAN IDs
        """
        ids = set()

        for part in text.split(','):
            part = part.strip()
            if not part:
                continue

            try:
                # Support both decimal and hex
                if part.startswith('0x') or part.startswith('0X'):
                    can_id = int(part, 16)
                else:
                    can_id = int(part, 16)  # Default to hex

                ids.add(can_id)
            except ValueError:
                # Skip invalid entries
                pass

        return ids

    def apply_filter(self):
        """Apply filter settings"""
        # CAN ID
        self.filter.filter_by_can_id = self.can_id_enabled.isChecked()
        self.filter.can_id_mode = "include" if self.can_id_mode.currentIndex() == 0 else "exclude"
        self.filter.can_id_list = self.parse_can_ids(self.can_id_input.text())

        # Direction
        self.filter.filter_by_direction = self.dir_enabled.isChecked()
        self.filter.show_rx = self.show_rx.isChecked()
        self.filter.show_tx = self.show_tx.isChecked()

        # Time
        self.filter.filter_by_time = self.time_enabled.isChecked()
        self.filter.time_start = self.time_start.value()
        self.filter.time_end = self.time_end.value()

        # DLC
        self.filter.filter_by_dlc = self.dlc_enabled.isChecked()
        self.filter.dlc_min = self.dlc_min.value()
        self.filter.dlc_max = self.dlc_max.value()

        self.accept()

    def clear_all_filters(self):
        """Clear all filters"""
        self.can_id_enabled.setChecked(False)
        self.can_id_input.clear()

        self.dir_enabled.setChecked(False)
        self.show_rx.setChecked(True)
        self.show_tx.setChecked(True)

        self.time_enabled.setChecked(False)
        self.time_start.setValue(0)
        self.time_end.setValue(999999.999)

        self.dlc_enabled.setChecked(False)
        self.dlc_min.setValue(0)
        self.dlc_max.setValue(8)

    def get_filter(self) -> MessageFilter:
        """Get the configured filter"""
        return self.filter

    @staticmethod
    def configure_filter(current_filter: Optional[MessageFilter] = None,
                        parent=None) -> Optional[MessageFilter]:
        """
        Static method to show filter dialog

        Args:
            current_filter: Current filter configuration
            parent: Parent widget

        Returns:
            MessageFilter if accepted, None if cancelled
        """
        dialog = FilterDialog(current_filter, parent)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            return dialog.get_filter()
        return None
