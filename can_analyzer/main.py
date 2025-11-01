#!/usr/bin/env python3
"""
CAN Analyzer - Main Entry Point
"""

import sys
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName("CAN Analyzer")
    app.setOrganizationName("CAN Tools")

    # Create and show main window
    window = MainWindow()
    window.show()

    # Start event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
