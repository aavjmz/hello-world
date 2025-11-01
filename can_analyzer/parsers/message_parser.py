"""
Unified Message Parser

Automatically detects file format and uses appropriate parser
"""

import os
from typing import List, Optional
from parsers.asc_parser import ASCParser, CANMessage
from parsers.blf_parser import BLFParser


class MessageParser:
    """Unified parser for CAN message files"""

    SUPPORTED_FORMATS = {
        '.asc': 'ASC',
        '.blf': 'BLF',
        '.log': 'ASC'  # Some ASC files use .log extension
    }

    def __init__(self):
        self.current_parser = None
        self.file_format = None

    def parse_file(self, file_path: str, format_hint: Optional[str] = None) -> List[CANMessage]:
        """
        Parse a CAN message file

        Args:
            file_path: Path to the file
            format_hint: Optional format hint ('ASC' or 'BLF')

        Returns:
            List of CANMessage objects
        """
        # Check if file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        # Determine file format
        if format_hint:
            self.file_format = format_hint.upper()
        else:
            self.file_format = self._detect_format(file_path)

        # Select appropriate parser
        if self.file_format == 'ASC':
            self.current_parser = ASCParser()
            return self.current_parser.parse_file(file_path)
        elif self.file_format == 'BLF':
            self.current_parser = BLFParser()
            if not BLFParser.is_available():
                raise ImportError(
                    "python-can library is required for BLF parsing. "
                    "Install it with: pip install python-can"
                )
            return self.current_parser.parse_file(file_path)
        else:
            raise ValueError(f"Unsupported file format: {self.file_format}")

    def _detect_format(self, file_path: str) -> str:
        """
        Detect file format from extension

        Args:
            file_path: Path to the file

        Returns:
            Format string ('ASC' or 'BLF')
        """
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()

        if ext in self.SUPPORTED_FORMATS:
            return self.SUPPORTED_FORMATS[ext]
        else:
            raise ValueError(
                f"Unknown file extension: {ext}. "
                f"Supported extensions: {list(self.SUPPORTED_FORMATS.keys())}"
            )

    def get_parser(self):
        """Get the current parser instance"""
        return self.current_parser

    def get_format(self) -> Optional[str]:
        """Get the detected file format"""
        return self.file_format

    @staticmethod
    def get_supported_formats() -> dict:
        """Get dictionary of supported file formats"""
        return MessageParser.SUPPORTED_FORMATS.copy()

    @staticmethod
    def is_format_supported(file_path: str) -> bool:
        """Check if file format is supported"""
        _, ext = os.path.splitext(file_path)
        return ext.lower() in MessageParser.SUPPORTED_FORMATS
