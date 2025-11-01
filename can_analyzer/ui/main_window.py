"""
Main Window UI for CAN Analyzer
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QMenuBar, QToolBar, QStatusBar,
    QTabWidget, QMessageBox, QFileDialog
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QIcon
from ui.message_table import MessageTableWidget
from parsers.message_parser import MessageParser
from utils.dbc_manager import DBCManager
from utils.signal_decoder import SignalDecoder


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

        # View Menu
        view_menu = menubar.addMenu("视图(&V)")

        new_view_action = QAction("新建视图(&N)", self)
        new_view_action.setShortcut("Ctrl+T")
        new_view_action.setStatusTip("创建新的信号曲线视图")
        new_view_action.triggered.connect(self.create_new_view)
        view_menu.addAction(new_view_action)

        # Tools Menu
        tools_menu = menubar.addMenu("工具(&T)")

        filter_action = QAction("过滤器(&F)...", self)
        filter_action.setStatusTip("配置报文过滤器")
        filter_action.triggered.connect(self.configure_filter)
        tools_menu.addAction(filter_action)

        # Help Menu
        help_menu = menubar.addMenu("帮助(&H)")

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
        """Import CAN messages from file"""
        # Open file dialog
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "导入CAN报文文件",
            "",
            "CAN文件 (*.asc *.blf *.log);;ASC文件 (*.asc);;BLF文件 (*.blf);;所有文件 (*.*)"
        )

        if not file_path:
            return

        try:
            self.statusBar().showMessage(f"正在解析文件: {file_path}...")

            # Parse file
            messages = self.message_parser.parse_file(file_path)
            self.current_messages = messages

            # Display messages in table
            self.message_table.set_messages(messages)

            # Get statistics
            parser = self.message_parser.get_parser()
            if parser:
                stats = parser.get_statistics()
                msg = (f"导入成功! "
                       f"共 {stats['total_messages']} 条报文, "
                       f"时间范围: {stats['duration']:.3f}s, "
                       f"唯一ID: {stats['unique_ids']} 个")
                self.statusBar().showMessage(msg, 5000)

                # Show summary dialog
                QMessageBox.information(
                    self,
                    "导入成功",
                    f"文件: {file_path}\n\n"
                    f"总报文数: {stats['total_messages']}\n"
                    f"时间范围: {stats['time_range'][0]:.6f}s - {stats['time_range'][1]:.6f}s\n"
                    f"持续时间: {stats['duration']:.3f}s\n"
                    f"唯一CAN ID数: {stats['unique_ids']}\n"
                    f"接收报文: {stats['rx_count']}\n"
                    f"发送报文: {stats['tx_count']}"
                )

        except Exception as e:
            QMessageBox.critical(
                self,
                "导入失败",
                f"无法解析文件:\n{file_path}\n\n错误信息:\n{str(e)}"
            )
            self.statusBar().showMessage("导入失败", 3000)

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

                # Show summary
                QMessageBox.information(
                    self,
                    "DBC导入成功",
                    f"数据库名称: {db_name}\n"
                    f"文件路径: {info['file_path']}\n"
                    f"报文定义数: {info['message_count']}\n"
                    f"节点数: {info['node_count']}"
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
        QMessageBox.information(self, "管理DBC", "DBC管理功能即将实现")
        self.statusBar().showMessage("DBC管理功能即将实现", 3000)

    def create_new_view(self):
        """Create a new signal view"""
        QMessageBox.information(self, "新建视图", "新建视图功能即将实现")
        self.statusBar().showMessage("新建视图功能即将实现", 3000)

    def configure_filter(self):
        """Configure message filter"""
        QMessageBox.information(self, "过滤器", "过滤器配置功能即将实现")
        self.statusBar().showMessage("过滤器配置功能即将实现", 3000)

    def close_view_tab(self, index):
        """Close a view tab"""
        self.view_tabs.removeTab(index)

    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            "关于 CAN Analyzer",
            "<h2>CAN Analyzer v0.1.0</h2>"
            "<p>CAN总线报文分析工具</p>"
            "<p>功能特性：</p>"
            "<ul>"
            "<li>支持ASC、BLF格式报文解析</li>"
            "<li>DBC文件管理（增删改查）</li>"
            "<li>信号曲线可视化</li>"
            "<li>支持曲线缩放和平移</li>"
            "</ul>"
        )
