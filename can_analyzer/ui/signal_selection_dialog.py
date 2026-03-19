"""
Signal Selection Dialog for choosing signals to plot
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QListWidget, QListWidgetItem, QLabel, QGroupBox,
    QAbstractItemView, QLineEdit
)
from PyQt6.QtCore import Qt
from typing import List, Dict, Set
from utils.dbc_manager import DBCManager


class SignalSelectionDialog(QDialog):
    """Dialog for selecting signals to plot"""

    def __init__(self, dbc_manager: DBCManager, can_ids: List[int], parent=None):
        super().__init__(parent)
        self.dbc_manager = dbc_manager
        self.can_ids = can_ids
        self.selected_signals: List[Dict] = []
        self._all_items: List[tuple] = []  # (text, data_dict)

        self.setWindowTitle("选择信号")
        self.setMinimumSize(600, 400)

        self.init_ui()
        self.load_signals()

    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)

        # Instructions
        info_label = QLabel("选择要绘制的信号（可多选）：")
        layout.addWidget(info_label)

        # Signal list
        list_group = QGroupBox("可用信号")
        list_layout = QVBoxLayout(list_group)

        # Search bar
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索信号名或消息ID（支持模糊搜索）")
        self.search_input.textChanged.connect(self.apply_filter)
        list_layout.addWidget(self.search_input)

        self.signal_list = QListWidget()
        self.signal_list.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        list_layout.addWidget(self.signal_list)

        layout.addWidget(list_group)

        # Statistics label
        self.stats_label = QLabel()
        layout.addWidget(self.stats_label)

        # Buttons
        button_layout = QHBoxLayout()

        self.select_all_btn = QPushButton("全选")
        self.select_all_btn.clicked.connect(self.select_all)
        button_layout.addWidget(self.select_all_btn)

        self.clear_btn = QPushButton("清空")
        self.clear_btn.clicked.connect(self.clear_selection)
        button_layout.addWidget(self.clear_btn)

        button_layout.addStretch()

        self.ok_btn = QPushButton("确定")
        self.ok_btn.clicked.connect(self.accept)
        self.ok_btn.setDefault(True)
        button_layout.addWidget(self.ok_btn)

        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)

        layout.addLayout(button_layout)

        # Connect selection changed signal
        self.signal_list.itemSelectionChanged.connect(self.on_selection_changed)

    def load_signals(self):
        """Load available signals from DBC"""
        self.signal_list.clear()
        self._all_items = []

        # Get active DBC
        db = self.dbc_manager.get_active()
        if not db or not db.is_loaded():
            self.stats_label.setText("未加载DBC文件")
            return

        # Collect all signals from the CAN IDs
        for can_id in self.can_ids:
            msg_def = db.get_message_by_id(can_id)
            if not msg_def:
                continue

            # Add signals from this message
            for signal in msg_def.signals:
                # Format: "MessageName.SignalName (unit) [ID: 0x123]"
                text = f"{msg_def.name}.{signal.name}"
                if signal.unit:
                    text += f" ({signal.unit})"
                text += f" [ID: 0x{can_id:03X}]"

                data = {
                    'can_id': can_id,
                    'message_name': msg_def.name,
                    'signal_name': signal.name,
                    'unit': signal.unit
                }
                self._all_items.append((text, data))

                item = QListWidgetItem(text)
                item.setData(Qt.ItemDataRole.UserRole, data)
                self.signal_list.addItem(item)

        self.update_stats()

    def _fuzzy_match(self, pattern: str, text: str) -> bool:
        """字符序列匹配：pattern 的所有字符按顺序出现在 text 中即命中"""
        it = iter(text)
        return all(c in it for c in pattern)

    def apply_filter(self, text: str):
        """Filter signal list based on search text"""
        query = text.strip().lower()

        self.signal_list.clear()

        for item_text, data in self._all_items:
            if not query:
                match = True
            else:
                can_id = data['can_id']
                # Match against signal/message name (fuzzy)
                name_text = f"{data['message_name']}.{data['signal_name']}".lower()
                name_match = self._fuzzy_match(query, name_text)
                # Match against message ID (hex and decimal substring)
                id_hex = f"0x{can_id:03x}"
                id_dec = str(can_id)
                id_match = query in id_hex or query in id_dec
                match = name_match or id_match

            if match:
                item = QListWidgetItem(item_text)
                item.setData(Qt.ItemDataRole.UserRole, data)
                self.signal_list.addItem(item)

        self.update_stats()

    def select_all(self):
        """Select all signals"""
        self.signal_list.selectAll()

    def clear_selection(self):
        """Clear all selections"""
        self.signal_list.clearSelection()

    def on_selection_changed(self):
        """Handle selection change"""
        self.update_stats()

    def update_stats(self):
        """Update statistics label"""
        total = self.signal_list.count()
        selected = len(self.signal_list.selectedItems())

        self.stats_label.setText(f"总共 {total} 个信号，已选择 {selected} 个")

        # Enable/disable OK button
        self.ok_btn.setEnabled(selected > 0)

    def get_selected_signals(self) -> List[Dict]:
        """
        Get list of selected signals

        Returns:
            List of dicts with signal info
        """
        selected = []
        for item in self.signal_list.selectedItems():
            signal_info = item.data(Qt.ItemDataRole.UserRole)
            if signal_info:
                selected.append(signal_info)
        return selected

    def accept(self):
        """Handle OK button"""
        self.selected_signals = self.get_selected_signals()
        super().accept()

    @staticmethod
    def select_signals(dbc_manager: DBCManager, can_ids: List[int],
                      parent=None) -> List[Dict]:
        """
        Static method to show dialog and get selected signals

        Args:
            dbc_manager: DBC manager instance
            can_ids: List of CAN IDs to show signals from
            parent: Parent widget

        Returns:
            List of selected signal dicts, or empty list if cancelled
        """
        dialog = SignalSelectionDialog(dbc_manager, can_ids, parent)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            return dialog.selected_signals
        return []
