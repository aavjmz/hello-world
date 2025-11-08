"""
Main Window UI for CAN Analyzer
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QMenuBar, QToolBar, QStatusBar,
    QTabWidget, QMessageBox, QFileDialog, QProgressDialog
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QIcon
from ui.message_table import MessageTableWidget
from ui.signal_selection_dialog import SignalSelectionDialog
from ui.filter_dialog import FilterDialog, MessageFilter
from ui.dbc_manager_dialog import DBCManagerDialog
from ui.search_dialog import SearchDialog
from ui.export_dialog import ExportDialog
from views.signal_plot_widget import SignalPlotWidget
from parsers.message_parser import MessageParser
from utils.dbc_manager import DBCManager
from utils.signal_decoder import SignalDecoder
from utils.file_import_worker import FileImportWorker


class MainWindow(QMainWindow):
    """Main application window"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("CAN Analyzer - CAN Bus Message Analysis Tool")
        self.setGeometry(100, 100, 1400, 800)

        # Initialize data managers
        self.message_parser = MessageParser()
        self.dbc_manager = DBCManager()
        self.signal_decoder = SignalDecoder(self.dbc_manager)
        self.current_messages = []
        self.current_filter = None

        # Background import worker
        self.import_worker = None
        self.import_progress_dialog = None

        # Initialize UI components
        self.init_ui()

        # Set signal decoder to message table
        self.message_table.set_signal_decoder(self.signal_decoder)

    def init_ui(self):
        """Initialize the user interface"""
        # Create menu bar
        self.create_menu_bar()

        # Create tool bar
        self.create_tool_bar()

        # Create main layout
        self.create_main_layout()

        # Create status bar
        self.create_status_bar()

    def create_menu_bar(self):
        """Create the menu bar"""
        menubar = self.menuBar()

        # File Menu
        file_menu = menubar.addMenu("文件(&F)")

        import_action = QAction("导入报文(&I)...", self)
        import_action.setShortcut("Ctrl+I")
        import_action.setStatusTip("导入ASC或BLF格式的CAN报文文件")
        import_action.triggered.connect(self.import_messages)
        file_menu.addAction(import_action)

        export_action = QAction("导出报文(&E)...", self)
        export_action.setShortcut("Ctrl+E")
        export_action.setStatusTip("导出报文到CSV、Excel或JSON格式")
        export_action.triggered.connect(self.export_messages)
        file_menu.addAction(export_action)

        file_menu.addSeparator()

        exit_action = QAction("退出(&X)", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.setStatusTip("退出应用程序")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # DBC Menu
        dbc_menu = menubar.addMenu("DBC(&D)")

        dbc_import_action = QAction("导入DBC(&I)...", self)
        dbc_import_action.setStatusTip("导入DBC数据库文件")
        dbc_import_action.triggered.connect(self.import_dbc)
        dbc_menu.addAction(dbc_import_action)

        dbc_manage_action = QAction("管理DBC(&M)...", self)
        dbc_manage_action.setStatusTip("管理已加载的DBC文件")
        dbc_manage_action.triggered.connect(self.manage_dbc)
        dbc_menu.addAction(dbc_manage_action)

        dbc_menu.addSeparator()

        refresh_decode_action = QAction("刷新解码(&R)", self)
        refresh_decode_action.setShortcut("F5")
        refresh_decode_action.setStatusTip("使用当前激活的DBC重新解码所有报文")
        refresh_decode_action.triggered.connect(self.refresh_message_decode)
        dbc_menu.addAction(refresh_decode_action)

        # View Menu
        view_menu = menubar.addMenu("视图(&V)")

        new_view_action = QAction("新建视图(&N)", self)
        new_view_action.setShortcut("Ctrl+T")
        new_view_action.setStatusTip("创建新的信号曲线视图")
        new_view_action.triggered.connect(self.create_new_view)
        view_menu.addAction(new_view_action)

        # Tools Menu
        tools_menu = menubar.addMenu("工具(&T)")

        search_action = QAction("搜索报文(&S)...", self)
        search_action.setShortcut("Ctrl+F")
        search_action.setStatusTip("搜索CAN报文")
        search_action.triggered.connect(self.show_search_dialog)
        tools_menu.addAction(search_action)

        tools_menu.addSeparator()

        filter_action = QAction("过滤器(&F)...", self)
        filter_action.setStatusTip("配置报文过滤器")
        filter_action.triggered.connect(self.configure_filter)
        tools_menu.addAction(filter_action)

        # Help Menu
        help_menu = menubar.addMenu("帮助(&H)")

        manual_action = QAction("用户手册(&M)", self)
        manual_action.setShortcut("F1")
        manual_action.setStatusTip("查看用户手册")
        manual_action.triggered.connect(self.show_user_manual)
        help_menu.addAction(manual_action)

        help_menu.addSeparator()

        about_action = QAction("关于(&A)", self)
        about_action.setStatusTip("关于CAN Analyzer")
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def create_tool_bar(self):
        """Create the tool bar"""
        toolbar = QToolBar("主工具栏")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        # Import messages button
        import_btn = QAction("导入报文", self)
        import_btn.setStatusTip("导入CAN报文文件")
        import_btn.triggered.connect(self.import_messages)
        toolbar.addAction(import_btn)

        toolbar.addSeparator()

        # Import DBC button
        dbc_btn = QAction("导入DBC", self)
        dbc_btn.setStatusTip("导入DBC文件")
        dbc_btn.triggered.connect(self.import_dbc)
        toolbar.addAction(dbc_btn)

        toolbar.addSeparator()

        # New view button
        view_btn = QAction("新建视图", self)
        view_btn.setStatusTip("创建新的曲线视图")
        view_btn.triggered.connect(self.create_new_view)
        toolbar.addAction(view_btn)

    def create_main_layout(self):
        """Create the main layout with splitter"""
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QHBoxLayout(central_widget)

        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel - Message table
        self.message_table = MessageTableWidget()
        splitter.addWidget(self.message_table)

        # Right panel - Tab widget for views
        self.view_tabs = QTabWidget()
        self.view_tabs.setTabsClosable(True)
        self.view_tabs.tabCloseRequested.connect(self.close_view_tab)

        # Add a welcome tab
        welcome_widget = QWidget()
        welcome_layout = QVBoxLayout(welcome_widget)
        welcome_layout.addStretch()
        splitter.addWidget(self.view_tabs)

        # Set splitter sizes (30% left, 70% right)
        splitter.setSizes([400, 1000])

        main_layout.addWidget(splitter)

    def create_status_bar(self):
        """Create the status bar"""
        self.statusBar().showMessage("就绪")

    # Slot methods
    def import_messages(self):
        """Import CAN messages from file (async with progress dialog)"""
        # Open file dialog
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "导入CAN报文文件",
            "",
            "CAN文件 (*.asc *.blf *.log);;ASC文件 (*.asc);;BLF文件 (*.blf);;所有文件 (*.*)"
        )

        if not file_path:
            return

        # Create and start worker thread
        self.import_worker = FileImportWorker(self.message_parser, file_path)

        # Connect signals
        self.import_worker.progress_updated.connect(self._on_import_progress)
        self.import_worker.import_finished.connect(self._on_import_finished)
        self.import_worker.import_failed.connect(self._on_import_failed)

        # Create progress dialog with real progress bar (0-100)
        self.import_progress_dialog = QProgressDialog(
            "正在导入文件...",
            "取消",
            0, 100,  # Progress from 0 to 100%
            self
        )
        self.import_progress_dialog.setWindowTitle("导入报文")
        self.import_progress_dialog.setWindowModality(Qt.WindowModality.NonModal)  # Allow main window interaction
        self.import_progress_dialog.setMinimumDuration(0)  # Show immediately
        self.import_progress_dialog.setValue(0)  # Start at 0%
        self.import_progress_dialog.canceled.connect(self._on_import_cancelled)
        self.import_progress_dialog.show()  # Show explicitly for NonModal

        # Store file path for error reporting
        self.current_import_file = file_path

        # Start import
        self.statusBar().showMessage(f"正在导入文件: {file_path}...")
        self.import_worker.start()

    def _on_import_progress(self, message: str, percentage: int):
        """Handle progress update from worker"""
        if self.import_progress_dialog:
            self.import_progress_dialog.setLabelText(message)
            self.import_progress_dialog.setValue(percentage)

    def _on_import_finished(self, messages: list, stats: dict):
        """Handle successful import completion"""
        # Close progress dialog
        if self.import_progress_dialog:
            self.import_progress_dialog.close()
            self.import_progress_dialog = None

        # Store messages
        self.current_messages = messages

        # Display messages in table
        self.message_table.set_messages(messages)

        # Update status bar
        if stats:
            msg = (f"导入成功! "
                   f"共 {stats['total_messages']} 条报文, "
                   f"时间范围: {stats['duration']:.3f}s, "
                   f"唯一ID: {stats['unique_ids']} 个")
            self.statusBar().showMessage(msg, 5000)

            # Show summary dialog
            QMessageBox.information(
                self,
                "导入成功",
                f"文件: {self.current_import_file}\n\n"
                f"总报文数: {stats['total_messages']}\n"
                f"时间范围: {stats['time_range'][0]:.6f}s - {stats['time_range'][1]:.6f}s\n"
                f"持续时间: {stats['duration']:.3f}s\n"
                f"唯一CAN ID数: {stats['unique_ids']}\n"
                f"接收报文: {stats['rx_count']}\n"
                f"发送报文: {stats['tx_count']}"
            )
        else:
            self.statusBar().showMessage(f"导入成功! 共 {len(messages)} 条报文", 5000)

        # Clean up worker
        self.import_worker = None

    def _on_import_failed(self, error_message: str):
        """Handle import failure"""
        # Close progress dialog
        if self.import_progress_dialog:
            self.import_progress_dialog.close()
            self.import_progress_dialog = None

        # Show error message
        QMessageBox.critical(
            self,
            "导入失败",
            f"无法解析文件:\n{self.current_import_file}\n\n错误信息:\n{error_message}"
        )
        self.statusBar().showMessage("导入失败", 3000)

        # Clean up worker
        self.import_worker = None

    def _on_import_cancelled(self):
        """Handle import cancellation"""
        if self.import_worker:
            self.import_worker.cancel()
            self.import_worker.wait()  # Wait for thread to finish
            self.import_worker = None

        self.statusBar().showMessage("导入已取消", 3000)

    def import_dbc(self):
        """Import DBC file"""
        # Open file dialog
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "导入DBC文件",
            "",
            "DBC文件 (*.dbc);;所有文件 (*.*)"
        )

        if not file_path:
            return

        try:
            self.statusBar().showMessage(f"正在加载DBC: {file_path}...")

            # Add DBC to manager
            db_name = self.dbc_manager.add_dbc(file_path, load=True)

            # Get info
            info = self.dbc_manager.get_dbc_info(db_name)

            if info:
                self.statusBar().showMessage(
                    f"DBC加载成功: {db_name} ({info['message_count']} 个报文定义)",
                    5000
                )

                # Refresh message table to decode with new DBC
                if self.current_messages:
                    self.message_table.refresh_display()
                    decoded_count = sum(1 for msg in self.current_messages
                                      if self.signal_decoder.decode_message(msg) is not None)
                    refresh_msg = f"\n\n已刷新报文表格，成功解码 {decoded_count} 条报文"
                else:
                    refresh_msg = ""

                # Show summary
                QMessageBox.information(
                    self,
                    "DBC导入成功",
                    f"数据库名称: {db_name}\n"
                    f"文件路径: {info['file_path']}\n"
                    f"报文定义数: {info['message_count']}\n"
                    f"节点数: {info['node_count']}"
                    f"{refresh_msg}"
                )
        except ImportError as e:
            QMessageBox.warning(
                self,
                "DBC功能不可用",
                "DBC解析需要cantools库支持。\n\n"
                "请安装: pip install cantools"
            )
            self.statusBar().showMessage("DBC功能不可用", 3000)
        except Exception as e:
            QMessageBox.critical(
                self,
                "导入失败",
                f"无法加载DBC文件:\n{file_path}\n\n错误信息:\n{str(e)}"
            )
            self.statusBar().showMessage("DBC导入失败", 3000)

    def manage_dbc(self):
        """Manage loaded DBC files"""
        DBCManagerDialog.manage_dbc(self.dbc_manager, self)

        # Refresh message table in case active DBC changed
        if self.current_messages:
            self.message_table.refresh_display()

            # Count decoded messages
            decoded_count = sum(1 for msg in self.current_messages
                              if self.signal_decoder.decode_message(msg) is not None)

            if decoded_count > 0:
                self.statusBar().showMessage(
                    f"已刷新报文表格，成功解码 {decoded_count} 条报文",
                    5000
                )

    def refresh_message_decode(self):
        """Refresh message table to re-decode all messages with current active DBC"""
        # Check if messages are loaded
        if not self.current_messages:
            QMessageBox.information(
                self,
                "无报文数据",
                "当前没有已加载的报文。\n\n请先导入CAN报文文件。"
            )
            return

        # Check if DBC is loaded
        if not self.dbc_manager.has_active_dbc():
            QMessageBox.information(
                self,
                "无激活的DBC",
                "当前没有激活的DBC数据库。\n\n"
                "请先导入并激活DBC文件。"
            )
            return

        # Refresh display
        self.message_table.refresh_display()

        # Count decoded messages
        decoded_count = sum(1 for msg in self.current_messages
                          if self.signal_decoder.decode_message(msg) is not None)

        # Show result
        QMessageBox.information(
            self,
            "刷新完成",
            f"已使用当前激活的DBC重新解码所有报文。\n\n"
            f"总报文数: {len(self.current_messages)}\n"
            f"成功解码: {decoded_count} 条\n"
            f"解码率: {decoded_count * 100 // len(self.current_messages)}%"
        )

        self.statusBar().showMessage(
            f"刷新完成: 成功解码 {decoded_count}/{len(self.current_messages)} 条报文",
            5000
        )

    def create_new_view(self):
        """Create a new signal view"""
        # Check if messages are loaded
        if not self.current_messages:
            QMessageBox.warning(
                self,
                "无报文数据",
                "请先导入CAN报文文件。"
            )
            return

        # Check if DBC is loaded
        active_dbc = self.dbc_manager.get_active()
        if not active_dbc or not active_dbc.is_loaded():
            QMessageBox.warning(
                self,
                "未加载DBC",
                "请先导入DBC文件以解析信号。"
            )
            return

        # Get unique CAN IDs from messages
        unique_ids = list(set(msg.can_id for msg in self.current_messages))
        unique_ids.sort()

        # Show signal selection dialog
        selected_signals = SignalSelectionDialog.select_signals(
            self.dbc_manager,
            unique_ids,
            self
        )

        if not selected_signals:
            return  # User cancelled or no signals selected

        # Create plot widget
        plot_widget = SignalPlotWidget()

        if not plot_widget.is_available():
            QMessageBox.warning(
                self,
                "绘图功能不可用",
                "未找到可用的绘图库。\n\n"
                "请安装以下任一库：\n"
                "• PyQtGraph (推荐): pip install pyqtgraph\n"
                "• Matplotlib: pip install matplotlib"
            )
            return

        # Extract and plot signal data
        self.statusBar().showMessage("正在提取信号数据...", 0)

        try:
            for signal_info in selected_signals:
                can_id = signal_info['can_id']
                signal_name = signal_info['signal_name']
                message_name = signal_info['message_name']
                unit = signal_info.get('unit', '')

                # Filter messages by CAN ID
                filtered_msgs = [msg for msg in self.current_messages if msg.can_id == can_id]

                if not filtered_msgs:
                    continue

                # Extract times and values
                times = []
                values = []

                for msg in filtered_msgs:
                    # Decode message
                    decoded = self.signal_decoder.decode_message(msg)
                    if decoded and decoded.signals:
                        # Find the signal
                        for sig_val in decoded.signals.values():
                            if sig_val.name == signal_name:
                                times.append(msg.timestamp)
                                values.append(sig_val.value)
                                break

                if times and values:
                    # Create signal key
                    signal_key = f"{message_name}.{signal_name}"

                    # Add to plot
                    plot_widget.add_signal(
                        signal_key=signal_key,
                        times=times,
                        values=values,
                        name=signal_name,
                        unit=unit
                    )

            # Check if any signals were added
            if plot_widget.get_signal_count() == 0:
                QMessageBox.warning(
                    self,
                    "无信号数据",
                    "未能从所选信号中提取数据。"
                )
                self.statusBar().showMessage("就绪")
                return

            # Set plot title
            signal_count = plot_widget.get_signal_count()
            plot_widget.set_title(f"信号曲线 ({signal_count} 个信号)")

            # Auto-fit view
            plot_widget.zoom_to_fit()

            # Add as new tab
            tab_name = f"视图 {self.view_tabs.count() + 1}"
            self.view_tabs.addTab(plot_widget, tab_name)
            self.view_tabs.setCurrentWidget(plot_widget)

            self.statusBar().showMessage(
                f"视图创建成功 ({signal_count} 个信号)",
                3000
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "创建视图失败",
                f"无法创建信号视图。\n\n错误信息:\n{str(e)}"
            )
            self.statusBar().showMessage("创建视图失败", 3000)

    def configure_filter(self):
        """Configure message filter"""
        # Check if messages are loaded
        if not self.current_messages:
            QMessageBox.warning(
                self,
                "无报文数据",
                "请先导入CAN报文文件。"
            )
            return

        # Show filter dialog
        new_filter = FilterDialog.configure_filter(self.current_filter, self)

        if new_filter is not None:
            # Apply filter
            self.current_filter = new_filter
            self.message_table.set_filter(new_filter)

            # Update status bar
            if new_filter.is_active():
                filtered_count = self.message_table.get_filtered_count()
                total_count = self.message_table.get_message_count()
                filter_desc = new_filter.get_description()

                self.statusBar().showMessage(
                    f"过滤器已应用: {filter_desc} | "
                    f"显示 {filtered_count}/{total_count} 条报文",
                    5000
                )
            else:
                self.statusBar().showMessage("过滤器已清除", 3000)

    def show_search_dialog(self):
        """Show search dialog"""
        # Check if messages are loaded
        if not self.current_messages:
            QMessageBox.warning(
                self,
                "无报文数据",
                "请先导入CAN报文文件。"
            )
            return

        # Get currently displayed messages (considering filter)
        displayed_messages = self.message_table.get_displayed_messages()

        if not displayed_messages:
            QMessageBox.warning(
                self,
                "无可搜索的报文",
                "当前没有可搜索的报文。如果已应用过滤器，请检查过滤条件。"
            )
            return

        # Create and show search dialog
        search_dialog = SearchDialog(displayed_messages, self)

        # Connect result signal to highlight row
        search_dialog.result_found.connect(self.on_search_result_found)

        # Show dialog
        search_dialog.exec()

    def on_search_result_found(self, displayed_index: int, message):
        """
        Handle search result found

        Args:
            displayed_index: Index in the displayed messages list
            message: The found message
        """
        # Clear previous highlight
        self.message_table.clear_highlight()

        # Find the actual message index in the full messages list
        try:
            message_index = self.current_messages.index(message)
        except ValueError:
            # Message not found (shouldn't happen)
            return

        # Scroll to the message (handles virtual scrolling automatically)
        self.message_table.scroll_to_message(message_index)

        # Find the row in the current table view and highlight it
        for row in range(self.message_table.rowCount()):
            item = self.message_table.item(row, 0)
            if item and item.data(Qt.ItemDataRole.UserRole) == message_index:
                self.message_table.highlight_row(row)
                break

        # Update status bar
        self.statusBar().showMessage(
            f"找到匹配项: 第{message_index + 1}行 | ID: 0x{message.can_id:03X}",
            5000
        )

    def export_messages(self):
        """Export messages to file"""
        # Check if messages are loaded
        if not self.current_messages:
            QMessageBox.warning(
                self,
                "无报文数据",
                "请先导入CAN报文文件。"
            )
            return

        # Get currently displayed messages (considering filter)
        filtered_messages = self.message_table.get_displayed_messages()

        # Show export dialog
        ExportDialog.export_messages(
            messages=self.current_messages,
            timestamp_formatter=self.message_table.timestamp_formatter,
            signal_decoder=self.message_table.signal_decoder,
            filtered_messages=filtered_messages,
            parent=self
        )

    def close_view_tab(self, index):
        """Close a view tab"""
        self.view_tabs.removeTab(index)

    def show_user_manual(self):
        """Show user manual"""
        import webbrowser
        import os

        # Get manual path
        manual_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'docs',
            'USER_MANUAL.md'
        )

        if os.path.exists(manual_path):
            # Try to open in default markdown viewer or browser
            try:
                webbrowser.open('file://' + os.path.abspath(manual_path))
                self.statusBar().showMessage("用户手册已在浏览器中打开", 3000)
            except Exception as e:
                QMessageBox.information(
                    self,
                    "用户手册",
                    f"用户手册位置:\n{manual_path}\n\n"
                    f"请使用Markdown阅读器或文本编辑器打开。"
                )
        else:
            QMessageBox.warning(
                self,
                "用户手册",
                f"未找到用户手册文件。\n\n期望位置:\n{manual_path}"
            )

    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            "关于 CAN Analyzer",
            "<h2>CAN Analyzer v0.9.0</h2>"
            "<p>CAN总线报文分析工具</p>"
            "<p><b>核心功能：</b></p>"
            "<ul>"
            "<li>✅ 支持ASC、BLF、LOG格式报文解析</li>"
            "<li>✅ DBC文件管理与信号解码</li>"
            "<li>✅ 多信号曲线可视化</li>"
            "<li>✅ 报文过滤与搜索 (Ctrl+F)</li>"
            "<li>✅ 数据导出 (CSV/Excel/JSON)</li>"
            "<li>✅ 后台导入，UI流畅响应</li>"
            "</ul>"
            "<p><b>v0.9.0 新功能：</b></p>"
            "<ul>"
            "<li>🎉 报文搜索功能 (Ctrl+F)</li>"
            "<li>🎉 数据导出功能 (Ctrl+E)</li>"
            "<li>📖 完整用户手册 (F1)</li>"
            "</ul>"
            "<p style='margin-top:10px;'>"
            "<b>技术栈：</b> Python 3.11+ | PyQt6 | cantools | PyQtGraph"
            "</p>"
        )
