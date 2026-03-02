"""
Message Search Dialog

Allows users to search for CAN messages by ID, data content, or signal values
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLineEdit, QLabel, QPushButton, QComboBox,
    QCheckBox, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from typing import Optional, List
from parsers.asc_parser import CANMessage


class SearchDialog(QDialog):
    """Dialog for searching CAN messages"""

    # Signal emitted when a search result is found
    # Parameters: row_index, message
    result_found = pyqtSignal(int, object)

    def __init__(self, messages: List[CANMessage], parent=None):
        super().__init__(parent)
        self.setWindowTitle("搜索报文")
        self.setMinimumWidth(450)

        # Store messages and search state
        self.messages = messages
        self.current_index = -1
        self.last_search_text = ""
        self.last_search_type = ""

        # Initialize UI
        self.init_ui()

    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)

        # Search criteria group
        search_group = self.create_search_group()
        layout.addWidget(search_group)

        # Status label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(self.status_label)

        # Buttons
        button_layout = QHBoxLayout()

        self.prev_btn = QPushButton("上一个 (Shift+F3)")
        self.prev_btn.clicked.connect(self.find_previous)
        self.prev_btn.setEnabled(False)
        button_layout.addWidget(self.prev_btn)

        self.next_btn = QPushButton("下一个 (F3)")
        self.next_btn.clicked.connect(self.find_next)
        self.next_btn.setEnabled(False)
        self.next_btn.setDefault(True)
        button_layout.addWidget(self.next_btn)

        button_layout.addStretch()

        self.close_btn = QPushButton("关闭")
        self.close_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.close_btn)

        layout.addLayout(button_layout)

    def create_search_group(self) -> QGroupBox:
        """Create search criteria group"""
        group = QGroupBox("搜索条件")
        layout = QVBoxLayout()

        # Search type
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("搜索类型:"))

        self.search_type_combo = QComboBox()
        self.search_type_combo.addItems([
            "CAN ID (十六进制)",
            "数据内容 (十六进制)",
            "信号值 (文本)"
        ])
        self.search_type_combo.currentTextChanged.connect(self.on_search_type_changed)
        type_layout.addWidget(self.search_type_combo, 1)

        layout.addLayout(type_layout)

        # Search input
        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("搜索内容:"))

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入搜索内容...")
        self.search_input.textChanged.connect(self.on_search_text_changed)
        self.search_input.returnPressed.connect(self.find_next)
        input_layout.addWidget(self.search_input, 1)

        layout.addLayout(input_layout)

        # Options
        options_layout = QHBoxLayout()

        self.case_sensitive_cb = QCheckBox("区分大小写")
        options_layout.addWidget(self.case_sensitive_cb)

        self.whole_word_cb = QCheckBox("全字匹配")
        options_layout.addWidget(self.whole_word_cb)

        options_layout.addStretch()

        layout.addLayout(options_layout)

        group.setLayout(layout)
        return group

    def on_search_type_changed(self, text: str):
        """Handle search type change"""
        # Update placeholder text based on search type
        if "CAN ID" in text:
            self.search_input.setPlaceholderText("例如: 123 或 0x123")
        elif "数据内容" in text:
            self.search_input.setPlaceholderText("例如: 01 02 03 或 010203")
        else:
            self.search_input.setPlaceholderText("例如: EngineSpeed 或 2000")

        # Reset search when type changes
        self.reset_search()

    def on_search_text_changed(self, text: str):
        """Handle search text change"""
        # Enable/disable buttons based on text
        has_text = len(text.strip()) > 0
        self.next_btn.setEnabled(has_text)
        self.prev_btn.setEnabled(has_text)

        # Reset search if text changed significantly
        if text != self.last_search_text:
            self.reset_search()

    def reset_search(self):
        """Reset search state"""
        self.current_index = -1
        self.status_label.setText("")

    def find_next(self):
        """Find next matching message"""
        search_text = self.search_input.text().strip()
        if not search_text:
            return

        search_type = self.search_type_combo.currentText()

        # Start from current position + 1
        start_index = self.current_index + 1
        if start_index >= len(self.messages):
            start_index = 0

        # Search forward
        for i in range(start_index, len(self.messages)):
            if self.message_matches(self.messages[i], search_text, search_type):
                self.current_index = i
                self.last_search_text = search_text
                self.last_search_type = search_type
                self.result_found.emit(i, self.messages[i])
                self.update_status(i + 1, len(self.messages))
                return

        # Wrap around to beginning
        for i in range(0, start_index):
            if self.message_matches(self.messages[i], search_text, search_type):
                self.current_index = i
                self.last_search_text = search_text
                self.last_search_type = search_type
                self.result_found.emit(i, self.messages[i])
                self.update_status(i + 1, len(self.messages), wrapped=True)
                return

        # No match found
        self.status_label.setText("未找到匹配项")
        QMessageBox.information(self, "搜索", "未找到匹配的报文")

    def find_previous(self):
        """Find previous matching message"""
        search_text = self.search_input.text().strip()
        if not search_text:
            return

        search_type = self.search_type_combo.currentText()

        # Start from current position - 1
        start_index = self.current_index - 1
        if start_index < 0:
            start_index = len(self.messages) - 1

        # Search backward
        for i in range(start_index, -1, -1):
            if self.message_matches(self.messages[i], search_text, search_type):
                self.current_index = i
                self.last_search_text = search_text
                self.last_search_type = search_type
                self.result_found.emit(i, self.messages[i])
                self.update_status(i + 1, len(self.messages))
                return

        # Wrap around to end
        for i in range(len(self.messages) - 1, start_index, -1):
            if self.message_matches(self.messages[i], search_text, search_type):
                self.current_index = i
                self.last_search_text = search_text
                self.last_search_type = search_type
                self.result_found.emit(i, self.messages[i])
                self.update_status(i + 1, len(self.messages), wrapped=True)
                return

        # No match found
        self.status_label.setText("未找到匹配项")
        QMessageBox.information(self, "搜索", "未找到匹配的报文")

    def message_matches(self, message: CANMessage, search_text: str, search_type: str) -> bool:
        """Check if a message matches the search criteria"""
        case_sensitive = self.case_sensitive_cb.isChecked()
        whole_word = self.whole_word_cb.isChecked()

        # Prepare search text
        if not case_sensitive:
            search_text = search_text.lower()

        if "CAN ID" in search_type:
            return self.match_can_id(message, search_text)
        elif "数据内容" in search_type:
            return self.match_data_content(message, search_text, case_sensitive)
        else:  # Signal value
            return self.match_signal_value(message, search_text, case_sensitive, whole_word)

    def match_can_id(self, message: CANMessage, search_text: str) -> bool:
        """Match CAN ID"""
        try:
            # Parse search text as hex (with or without 0x prefix)
            if search_text.startswith('0x') or search_text.startswith('0X'):
                search_id = int(search_text, 16)
            else:
                search_id = int(search_text, 16)

            return message.can_id == search_id
        except ValueError:
            return False

    def match_data_content(self, message: CANMessage, search_text: str, case_sensitive: bool) -> bool:
        """Match data content"""
        # Remove spaces from search text
        search_text = search_text.replace(' ', '').replace('0x', '').replace('0X', '')

        # Convert message data to hex string
        data_hex = ''.join(f'{b:02X}' for b in message.data)

        if not case_sensitive:
            data_hex = data_hex.lower()

        return search_text in data_hex

    def match_signal_value(self, message: CANMessage, search_text: str,
                          case_sensitive: bool, whole_word: bool) -> bool:
        """Match signal value (requires decoded signals)"""
        # This will be implemented when we have signal decoder access
        # For now, just check if message has signals attribute
        if not hasattr(message, 'signals') or not message.signals:
            return False

        # Check each signal
        for signal_name, signal_value in message.signals.items():
            signal_str = f"{signal_name}:{signal_value}"

            if not case_sensitive:
                signal_str = signal_str.lower()

            if whole_word:
                # Check for exact word match
                words = signal_str.split()
                if search_text in words:
                    return True
            else:
                # Check for substring match
                if search_text in signal_str:
                    return True

        return False

    def update_status(self, current: int, total: int, wrapped: bool = False):
        """Update status label"""
        status = f"找到匹配项: {current}/{total}"
        if wrapped:
            status += " (已循环)"
        self.status_label.setText(status)

    def update_messages(self, messages: List[CANMessage]):
        """Update the message list (when filter changes)"""
        self.messages = messages
        self.reset_search()

    def keyPressEvent(self, event):
        """Handle keyboard shortcuts"""
        if event.key() == Qt.Key.Key_F3:
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                self.find_previous()
            else:
                self.find_next()
            event.accept()
        elif event.key() == Qt.Key.Key_Escape:
            self.accept()
            event.accept()
        else:
            super().keyPressEvent(event)
