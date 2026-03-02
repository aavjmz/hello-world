"""
Export Dialog

Allows users to export CAN messages to various formats
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QPushButton, QComboBox, QCheckBox,
    QRadioButton, QButtonGroup, QFileDialog, QMessageBox, QProgressDialog
)
from PyQt6.QtCore import Qt
from typing import List, Optional
from parsers.asc_parser import CANMessage
from utils.data_exporter import DataExporter
from utils.timestamp_formatter import TimestampFormatter
from utils.signal_decoder import SignalDecoder


class ExportDialog(QDialog):
    """Dialog for exporting CAN messages"""

    def __init__(self, messages: List[CANMessage],
                 timestamp_formatter: Optional[TimestampFormatter] = None,
                 signal_decoder: Optional[SignalDecoder] = None,
                 parent=None):
        super().__init__(parent)
        self.setWindowTitle("导出报文数据")
        self.setMinimumWidth(500)

        # Store parameters
        self.all_messages = messages
        self.selected_messages = messages  # Will be updated based on scope selection
        self.timestamp_formatter = timestamp_formatter
        self.signal_decoder = signal_decoder

        # Initialize exporter
        self.exporter = DataExporter(timestamp_formatter, signal_decoder)

        # Initialize UI
        self.init_ui()

        # Update statistics
        self.update_statistics()

    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)

        # Export format group
        format_group = self.create_format_group()
        layout.addWidget(format_group)

        # Export scope group
        scope_group = self.create_scope_group()
        layout.addWidget(scope_group)

        # Options group
        options_group = self.create_options_group()
        layout.addWidget(options_group)

        # Statistics label
        self.stats_label = QLabel("")
        self.stats_label.setStyleSheet("color: #666; font-style: italic; padding: 10px;")
        layout.addWidget(self.stats_label)

        # Buttons
        button_layout = QHBoxLayout()

        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)

        button_layout.addStretch()

        self.export_btn = QPushButton("导出")
        self.export_btn.clicked.connect(self.export_data)
        self.export_btn.setDefault(True)
        button_layout.addWidget(self.export_btn)

        layout.addLayout(button_layout)

    def create_format_group(self) -> QGroupBox:
        """Create export format selection group"""
        group = QGroupBox("导出格式")
        layout = QVBoxLayout()

        self.format_group = QButtonGroup(self)

        self.csv_radio = QRadioButton("CSV (逗号分隔值)")
        self.csv_radio.setToolTip("适合在Excel、Numbers等软件中打开")
        self.csv_radio.setChecked(True)
        self.format_group.addButton(self.csv_radio, 0)
        layout.addWidget(self.csv_radio)

        self.excel_radio = QRadioButton("Excel (*.xlsx)")
        self.excel_radio.setToolTip("Excel格式，带格式化样式（需要openpyxl库）")
        self.format_group.addButton(self.excel_radio, 1)
        layout.addWidget(self.excel_radio)

        self.json_radio = QRadioButton("JSON (JavaScript对象表示法)")
        self.json_radio.setToolTip("适合编程处理和数据交换")
        self.format_group.addButton(self.json_radio, 2)
        layout.addWidget(self.json_radio)

        group.setLayout(layout)
        return group

    def create_scope_group(self) -> QGroupBox:
        """Create export scope selection group"""
        group = QGroupBox("导出范围")
        layout = QVBoxLayout()

        self.scope_group = QButtonGroup(self)

        self.all_scope_radio = QRadioButton("导出所有报文")
        self.all_scope_radio.setChecked(True)
        self.all_scope_radio.toggled.connect(self.on_scope_changed)
        self.scope_group.addButton(self.all_scope_radio, 0)
        layout.addWidget(self.all_scope_radio)

        self.filtered_scope_radio = QRadioButton("仅导出当前过滤后的报文")
        self.filtered_scope_radio.setToolTip("如果应用了过滤器，只导出符合条件的报文")
        self.filtered_scope_radio.toggled.connect(self.on_scope_changed)
        self.scope_group.addButton(self.filtered_scope_radio, 1)
        layout.addWidget(self.filtered_scope_radio)

        group.setLayout(layout)
        return group

    def create_options_group(self) -> QGroupBox:
        """Create export options group"""
        group = QGroupBox("导出选项")
        layout = QVBoxLayout()

        self.include_signals_cb = QCheckBox("包含信号解码值")
        self.include_signals_cb.setToolTip("如果有DBC数据库，包含解码后的信号值")
        self.include_signals_cb.setChecked(True)
        self.include_signals_cb.setEnabled(self.signal_decoder is not None)
        layout.addWidget(self.include_signals_cb)

        self.pretty_json_cb = QCheckBox("格式化JSON输出（更易读但文件更大）")
        self.pretty_json_cb.setToolTip("添加缩进和换行使JSON更易读")
        self.pretty_json_cb.setChecked(True)
        layout.addWidget(self.pretty_json_cb)

        group.setLayout(layout)
        return group

    def on_scope_changed(self):
        """Handle export scope change"""
        # Update selected messages based on scope
        # This will be set by the parent (MainWindow) based on current filter
        self.update_statistics()

    def set_filtered_messages(self, messages: List[CANMessage]):
        """
        Set the filtered messages list

        Args:
            messages: List of filtered messages
        """
        self.selected_messages = messages
        self.update_statistics()

    def update_statistics(self):
        """Update statistics display"""
        # Determine which messages to show stats for
        messages = self.all_messages if self.all_scope_radio.isChecked() else self.selected_messages

        stats = self.exporter.get_export_statistics(messages)

        stats_text = (
            f"将导出 {stats['total_messages']} 条报文 | "
            f"唯一ID数: {stats['unique_ids']} | "
            f"Rx: {stats['rx_count']}, Tx: {stats['tx_count']} | "
            f"时间跨度: {stats['time_span']:.3f}秒"
        )

        self.stats_label.setText(stats_text)

    def export_data(self):
        """Perform the export operation"""
        # Determine export format
        if self.csv_radio.isChecked():
            format_name = "CSV"
            file_filter = "CSV Files (*.csv);;All Files (*)"
            default_ext = ".csv"
        elif self.excel_radio.isChecked():
            format_name = "Excel"
            file_filter = "Excel Files (*.xlsx);;All Files (*)"
            default_ext = ".xlsx"
        else:  # JSON
            format_name = "JSON"
            file_filter = "JSON Files (*.json);;All Files (*)"
            default_ext = ".json"

        # Get file path from user
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            f"导出为{format_name}",
            f"can_messages{default_ext}",
            file_filter
        )

        if not file_path:
            return  # User cancelled

        # Determine which messages to export
        messages = self.all_messages if self.all_scope_radio.isChecked() else self.selected_messages

        if not messages:
            QMessageBox.warning(
                self,
                "无数据",
                "没有可导出的报文数据。"
            )
            return

        # Get export options
        include_signals = self.include_signals_cb.isChecked() and self.signal_decoder is not None

        # Show progress dialog
        progress = QProgressDialog(f"正在导出到 {format_name}...", "取消", 0, 100, self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(10)

        # Perform export
        try:
            success = False

            if self.csv_radio.isChecked():
                progress.setValue(30)
                success = self.exporter.export_to_csv(messages, file_path, include_signals)

            elif self.excel_radio.isChecked():
                progress.setValue(30)
                success = self.exporter.export_to_excel(messages, file_path, include_signals)

            else:  # JSON
                pretty = self.pretty_json_cb.isChecked()
                progress.setValue(30)
                success = self.exporter.export_to_json(messages, file_path, include_signals, pretty)

            progress.setValue(100)

            if success:
                QMessageBox.information(
                    self,
                    "导出成功",
                    f"已成功导出 {len(messages)} 条报文到:\n{file_path}"
                )
                self.accept()
            else:
                QMessageBox.critical(
                    self,
                    "导出失败",
                    f"导出数据时发生错误。\n\n请检查:\n"
                    f"1. 文件路径是否有效\n"
                    f"2. 是否有写入权限\n"
                    f"3. 如果导出Excel格式，是否已安装 openpyxl 库"
                )

        except Exception as e:
            progress.setValue(100)
            QMessageBox.critical(
                self,
                "导出错误",
                f"导出过程中发生异常:\n\n{str(e)}"
            )

    @staticmethod
    def export_messages(messages: List[CANMessage],
                       timestamp_formatter: Optional[TimestampFormatter] = None,
                       signal_decoder: Optional[SignalDecoder] = None,
                       filtered_messages: Optional[List[CANMessage]] = None,
                       parent=None) -> bool:
        """
        Static method to show export dialog

        Args:
            messages: All messages
            timestamp_formatter: Timestamp formatter
            signal_decoder: Signal decoder
            filtered_messages: Currently filtered messages (optional)
            parent: Parent widget

        Returns:
            True if export was performed, False if cancelled
        """
        dialog = ExportDialog(messages, timestamp_formatter, signal_decoder, parent)

        if filtered_messages and len(filtered_messages) != len(messages):
            dialog.set_filtered_messages(filtered_messages)
            # Enable the filtered scope option
            dialog.filtered_scope_radio.setEnabled(True)
        else:
            dialog.filtered_scope_radio.setEnabled(False)

        result = dialog.exec()
        return result == QDialog.DialogCode.Accepted
