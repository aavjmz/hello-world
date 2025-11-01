"""
Main Window UI for CAN Analyzer
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QMenuBar, QToolBar, QStatusBar,
    QTabWidget, QTableWidget, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QIcon


class MainWindow(QMainWindow):
    """Main application window"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("CAN Analyzer - CAN Bus Message Analysis Tool")
        self.setGeometry(100, 100, 1400, 800)

        # Initialize UI components
        self.init_ui()

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

        # Left panel - Message table placeholder
        self.message_table = QTableWidget()
        self.message_table.setColumnCount(5)
        self.message_table.setHorizontalHeaderLabels([
            "时间戳", "CAN ID", "方向", "数据", "信号值"
        ])
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

    # Slot methods (placeholders for now)
    def import_messages(self):
        """Import CAN messages from file"""
        QMessageBox.information(self, "导入报文", "导入报文功能即将实现")
        self.statusBar().showMessage("导入报文功能即将实现", 3000)

    def import_dbc(self):
        """Import DBC file"""
        QMessageBox.information(self, "导入DBC", "导入DBC功能即将实现")
        self.statusBar().showMessage("导入DBC功能即将实现", 3000)

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
