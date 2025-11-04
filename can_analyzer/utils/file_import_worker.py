"""
File Import Worker for background file parsing

Provides QThread-based worker for non-blocking file import
"""

from PyQt6.QtCore import QThread, pyqtSignal
from typing import List, Optional
from parsers.asc_parser import CANMessage


class FileImportWorker(QThread):
    """Worker thread for importing CAN message files in background"""

    # Signals
    progress_updated = pyqtSignal(str)  # Progress message
    import_finished = pyqtSignal(list, dict)  # messages, statistics
    import_failed = pyqtSignal(str)  # error message

    def __init__(self, message_parser, file_path: str):
        """
        Initialize worker

        Args:
            message_parser: MessageParser instance
            file_path: Path to file to import
        """
        super().__init__()
        self.message_parser = message_parser
        self.file_path = file_path
        self._is_cancelled = False

    def run(self):
        """Run the import task in background thread"""
        try:
            # Emit progress update
            self.progress_updated.emit("正在读取文件...")

            # Check if cancelled
            if self._is_cancelled:
                return

            # Parse file
            self.progress_updated.emit("正在解析报文...")
            messages = self.message_parser.parse_file(self.file_path)

            # Check if cancelled
            if self._is_cancelled:
                return

            # Get statistics
            self.progress_updated.emit("正在生成统计信息...")
            parser = self.message_parser.get_parser()
            stats = {}
            if parser:
                stats = parser.get_statistics()

            # Emit success signal
            self.import_finished.emit(messages, stats)

        except Exception as e:
            # Emit error signal
            self.import_failed.emit(str(e))

    def cancel(self):
        """Cancel the import operation"""
        self._is_cancelled = True
