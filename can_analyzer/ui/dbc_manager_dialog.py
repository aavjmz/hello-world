"""
DBC Manager Dialog

Dialog for managing loaded DBC database files
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QListWidget, QListWidgetItem, QGroupBox, QLabel,
    QFileDialog, QMessageBox, QSplitter, QTextEdit
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from typing import Optional
from utils.dbc_manager import DBCManager


class DBCManagerDialog(QDialog):
    """Dialog for managing DBC databases"""

    def __init__(self, dbc_manager: DBCManager, parent=None):
        super().__init__(parent)
        self.dbc_manager = dbc_manager
        self.setWindowTitle("DBC 数据库管理")
        self.setMinimumSize(800, 500)

        # Initialize UI
        self.init_ui()

        # Load current DBC list
        self.refresh_dbc_list()

    def init_ui(self):
        """Initialize the user interface"""
        layout = QHBoxLayout(self)

        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel - DBC list
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)

        # Right panel - DBC details
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)

        # Set splitter sizes (40% left, 60% right)
        splitter.setSizes([320, 480])

        layout.addWidget(splitter)

        # Bottom buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.close_btn = QPushButton("关闭")
        self.close_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.close_btn)

        layout.addLayout(button_layout)

    def create_left_panel(self) -> QGroupBox:
        """Create left panel with DBC list"""
        group = QGroupBox("已加载的 DBC 文件")
        layout = QVBoxLayout(group)

        # DBC list widget
        self.dbc_list = QListWidget()
        self.dbc_list.itemSelectionChanged.connect(self.on_selection_changed)
        layout.addWidget(self.dbc_list)

        # Buttons
        btn_layout = QHBoxLayout()

        self.add_btn = QPushButton("添加...")
        self.add_btn.clicked.connect(self.add_dbc)
        btn_layout.addWidget(self.add_btn)

        self.remove_btn = QPushButton("删除")
        self.remove_btn.clicked.connect(self.remove_dbc)
        self.remove_btn.setEnabled(False)
        btn_layout.addWidget(self.remove_btn)

        self.activate_btn = QPushButton("设为激活")
        self.activate_btn.clicked.connect(self.activate_dbc)
        self.activate_btn.setEnabled(False)
        btn_layout.addWidget(self.activate_btn)

        layout.addLayout(btn_layout)

        # Status label
        self.status_label = QLabel("未加载 DBC 文件")
        self.status_label.setStyleSheet("color: gray; font-style: italic;")
        layout.addWidget(self.status_label)

        return group

    def create_right_panel(self) -> QGroupBox:
        """Create right panel with DBC details"""
        group = QGroupBox("DBC 详细信息")
        layout = QVBoxLayout(group)

        # Info labels
        info_layout = QVBoxLayout()

        self.name_label = QLabel()
        self.name_label.setFont(QFont("", 12, QFont.Weight.Bold))
        info_layout.addWidget(self.name_label)

        self.path_label = QLabel()
        self.path_label.setWordWrap(True)
        info_layout.addWidget(self.path_label)

        self.status_info_label = QLabel()
        info_layout.addWidget(self.status_info_label)

        info_layout.addSpacing(10)

        # Statistics
        stats_group = QGroupBox("统计信息")
        stats_layout = QVBoxLayout(stats_group)

        self.message_count_label = QLabel()
        stats_layout.addWidget(self.message_count_label)

        self.node_count_label = QLabel()
        stats_layout.addWidget(self.node_count_label)

        self.signal_count_label = QLabel()
        stats_layout.addWidget(self.signal_count_label)

        info_layout.addWidget(stats_group)

        # Message list
        msg_group = QGroupBox("消息定义")
        msg_layout = QVBoxLayout(msg_group)

        self.message_text = QTextEdit()
        self.message_text.setReadOnly(True)
        self.message_text.setFont(QFont("Courier New", 9))
        msg_layout.addWidget(self.message_text)

        info_layout.addWidget(msg_group)

        layout.addLayout(info_layout)

        # Initially hide details
        self.clear_details()

        return group

    def refresh_dbc_list(self):
        """Refresh the DBC list"""
        self.dbc_list.clear()

        dbc_names = self.dbc_manager.list_dbc_names()
        active_dbc = self.dbc_manager.get_active()

        if not dbc_names:
            self.status_label.setText("未加载 DBC 文件")
            self.clear_details()
            return

        for name in dbc_names:
            item = QListWidgetItem(name)

            # Mark active DBC
            if active_dbc and active_dbc.name == name:
                item.setText(f"★ {name} (激活)")
                item.setFont(QFont("", -1, QFont.Weight.Bold))

            self.dbc_list.addItem(item)

        self.status_label.setText(f"已加载 {len(dbc_names)} 个 DBC 文件")

    def on_selection_changed(self):
        """Handle selection change"""
        selected_items = self.dbc_list.selectedItems()

        if not selected_items:
            self.remove_btn.setEnabled(False)
            self.activate_btn.setEnabled(False)
            self.clear_details()
            return

        self.remove_btn.setEnabled(True)
        self.activate_btn.setEnabled(True)

        # Get selected DBC name
        item_text = selected_items[0].text()
        # Remove "★ " and " (激活)" if present
        dbc_name = item_text.replace("★ ", "").replace(" (激活)", "")

        # Show details
        self.show_dbc_details(dbc_name)

    def show_dbc_details(self, dbc_name: str):
        """Show details for selected DBC"""
        dbc = self.dbc_manager.get_dbc(dbc_name)

        if not dbc:
            self.clear_details()
            return

        # Get DBC info
        info = self.dbc_manager.get_dbc_info(dbc_name)

        if not info:
            self.clear_details()
            return

        # Update labels
        self.name_label.setText(f"名称: {dbc_name}")
        self.path_label.setText(f"路径: {info['file_path']}")

        active_dbc = self.dbc_manager.get_active()
        is_active = active_dbc and active_dbc.name == dbc_name

        status_text = "状态: "
        if is_active:
            status_text += "★ 激活 (当前正在使用)"
            self.status_info_label.setStyleSheet("color: green; font-weight: bold;")
        else:
            status_text += "已加载"
            self.status_info_label.setStyleSheet("color: blue;")

        self.status_info_label.setText(status_text)

        # Update statistics
        self.message_count_label.setText(f"消息定义数: {info['message_count']}")
        self.node_count_label.setText(f"节点数: {info['node_count']}")

        # Calculate total signals
        total_signals = 0
        if dbc.is_loaded():
            for msg in dbc.db.messages:
                total_signals += len(msg.signals)

        self.signal_count_label.setText(f"信号总数: {total_signals}")

        # Show message list
        self.show_message_list(dbc)

    def show_message_list(self, dbc):
        """Show list of messages in DBC"""
        if not dbc.is_loaded():
            self.message_text.setPlainText("DBC 未加载")
            return

        lines = []
        lines.append(f"{'ID':<10} {'名称':<30} {'DLC':<5} {'信号数':<8}")
        lines.append("=" * 70)

        for msg in sorted(dbc.db.messages, key=lambda m: m.frame_id):
            msg_line = f"0x{msg.frame_id:03X}    {msg.name:<30} {msg.length:<5} {len(msg.signals):<8}"
            lines.append(msg_line)

            # Add signals
            for signal in msg.signals:
                unit_str = f" ({signal.unit})" if signal.unit else ""
                sig_line = f"  • {signal.name}{unit_str}"
                lines.append(sig_line)

        self.message_text.setPlainText("\n".join(lines))

    def clear_details(self):
        """Clear the details panel"""
        self.name_label.setText("未选择 DBC")
        self.path_label.setText("")
        self.status_info_label.setText("")
        self.message_count_label.setText("")
        self.node_count_label.setText("")
        self.signal_count_label.setText("")
        self.message_text.setPlainText("请从左侧列表选择一个 DBC 文件")

    def add_dbc(self):
        """Add a new DBC file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择 DBC 文件",
            "",
            "DBC 文件 (*.dbc);;所有文件 (*.*)"
        )

        if not file_path:
            return

        try:
            # Add DBC to manager
            db_name = self.dbc_manager.add_dbc(file_path, load=True)

            # Refresh list
            self.refresh_dbc_list()

            # Show success message
            QMessageBox.information(
                self,
                "添加成功",
                f"DBC 文件已成功加载:\n{db_name}"
            )

        except ImportError:
            QMessageBox.warning(
                self,
                "功能不可用",
                "DBC 解析需要 cantools 库支持。\n\n"
                "请安装: pip install cantools"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "添加失败",
                f"无法加载 DBC 文件:\n{file_path}\n\n"
                f"错误信息:\n{str(e)}"
            )

    def remove_dbc(self):
        """Remove selected DBC"""
        selected_items = self.dbc_list.selectedItems()

        if not selected_items:
            return

        # Get DBC name
        item_text = selected_items[0].text()
        dbc_name = item_text.replace("★ ", "").replace(" (激活)", "")

        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除 DBC 文件吗?\n\n{dbc_name}\n\n"
            "注意: 这只会从内存中卸载，不会删除原文件。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            # Check if it's the active DBC
            active_dbc = self.dbc_manager.get_active()
            is_active = active_dbc and active_dbc.name == dbc_name

            # Remove DBC
            self.dbc_manager.remove_dbc(dbc_name)

            # Refresh list
            self.refresh_dbc_list()

            # Show warning if it was active
            if is_active:
                QMessageBox.warning(
                    self,
                    "删除成功",
                    f"DBC 文件已删除: {dbc_name}\n\n"
                    "注意: 该文件是激活状态，信号解码功能将不可用。\n"
                    "请添加并激活一个新的 DBC 文件。"
                )
            else:
                QMessageBox.information(
                    self,
                    "删除成功",
                    f"DBC 文件已删除: {dbc_name}"
                )

        except Exception as e:
            QMessageBox.critical(
                self,
                "删除失败",
                f"无法删除 DBC 文件:\n\n错误信息:\n{str(e)}"
            )

    def activate_dbc(self):
        """Activate selected DBC"""
        selected_items = self.dbc_list.selectedItems()

        if not selected_items:
            return

        # Get DBC name
        item_text = selected_items[0].text()
        dbc_name = item_text.replace("★ ", "").replace(" (激活)", "")

        try:
            # Set as active
            self.dbc_manager.set_active(dbc_name)

            # Refresh list
            self.refresh_dbc_list()

            # Select the activated item
            for i in range(self.dbc_list.count()):
                item = self.dbc_list.item(i)
                if dbc_name in item.text():
                    self.dbc_list.setCurrentItem(item)
                    break

            QMessageBox.information(
                self,
                "激活成功",
                f"DBC 文件已设为激活:\n{dbc_name}\n\n"
                "该 DBC 将用于解析 CAN 报文信号。"
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "激活失败",
                f"无法激活 DBC 文件:\n\n错误信息:\n{str(e)}"
            )

    @staticmethod
    def manage_dbc(dbc_manager: DBCManager, parent=None):
        """
        Static method to show DBC manager dialog

        Args:
            dbc_manager: DBCManager instance
            parent: Parent widget

        Returns:
            None
        """
        dialog = DBCManagerDialog(dbc_manager, parent)
        dialog.exec()
