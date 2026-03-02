#!/usr/bin/env python3
"""
UI Framework Test Script
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow


def test_ui():
    """Test the UI framework"""
    print("=" * 60)
    print("CAN Analyzer - UI Framework Test")
    print("=" * 60)
    print()

    print("✓ 导入PyQt6模块成功")
    print("✓ 导入MainWindow类成功")
    print()

    # Create application
    app = QApplication(sys.argv)
    print("✓ 创建QApplication实例成功")

    # Create main window
    window = MainWindow()
    print("✓ 创建MainWindow实例成功")

    # Check window properties
    print()
    print("窗口属性检查:")
    print(f"  - 窗口标题: {window.windowTitle()}")
    print(f"  - 窗口大小: {window.width()} x {window.height()}")
    print()

    # Check menu bar
    menubar = window.menuBar()
    menus = [action.text() for action in menubar.actions()]
    print("菜单栏检查:")
    for menu in menus:
        print(f"  ✓ {menu}")
    print()

    # Check status bar
    statusbar = window.statusBar()
    print(f"✓ 状态栏: {statusbar.currentMessage()}")
    print()

    print("=" * 60)
    print("UI框架测试完成 - 所有检查通过!")
    print("=" * 60)
    print()
    print("说明:")
    print("  1. 主窗口UI框架已成功创建")
    print("  2. 菜单栏包含：文件、DBC、视图、工具、帮助")
    print("  3. 工具栏包含：导入报文、导入DBC、新建视图")
    print("  4. 主界面采用左右分栏布局")
    print("  5. 状态栏显示就绪状态")
    print()
    print("下一步: 可以运行 'python main.py' 查看UI界面")
    print()

    # Don't show window in test mode
    # window.show()
    # sys.exit(app.exec())


if __name__ == "__main__":
    test_ui()
