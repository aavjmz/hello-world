"""
DBC Database Manager

Manages DBC files for CAN signal decoding
"""

import os
from typing import List, Dict, Optional, Any
from pathlib import Path


class DBCDatabase:
    """DBC database representation"""

    def __init__(self, file_path: str, name: Optional[str] = None):
        self.file_path = file_path
        self.name = name or os.path.basename(file_path)
        self.db = None
        self._loaded = False
        self._cantools_available = False
        self._check_cantools()

    def _check_cantools(self):
        """Check if cantools is available"""
        try:
            import cantools
            self._cantools_available = True
        except ImportError:
            self._cantools_available = False

    def load(self):
        """Load the DBC file"""
        if not self._cantools_available:
            raise ImportError(
                "cantools library is required for DBC parsing. "
                "Install it with: pip install cantools"
            )

        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"DBC file not found: {self.file_path}")

        try:
            import cantools
            self.db = cantools.database.load_file(self.file_path)
            self._loaded = True
        except Exception as e:
            raise Exception(f"Error loading DBC file: {str(e)}")

    def is_loaded(self) -> bool:
        """Check if DBC is loaded"""
        return self._loaded

    def get_messages(self) -> List:
        """Get all messages defined in DBC"""
        if not self._loaded or self.db is None:
            return []
        return list(self.db.messages)

    def get_message_count(self) -> int:
        """Get total number of messages"""
        return len(self.get_messages())

    def get_message_by_id(self, can_id: int):
        """Get message by CAN ID"""
        if not self._loaded or self.db is None:
            return None
        try:
            return self.db.get_message_by_frame_id(can_id)
        except KeyError:
            return None

    def get_message_by_name(self, name: str):
        """Get message by name"""
        if not self._loaded or self.db is None:
            return None
        try:
            return self.db.get_message_by_name(name)
        except KeyError:
            return None

    def decode_message(self, can_id: int, data: bytes) -> Dict[str, Any]:
        """
        Decode a CAN message using DBC definition

        Args:
            can_id: CAN ID
            data: Message data bytes

        Returns:
            Dictionary of signal name -> value
        """
        if not self._loaded or self.db is None:
            return {}

        try:
            message = self.db.get_message_by_frame_id(can_id)
            return message.decode(data)
        except (KeyError, Exception):
            return {}

    def get_info(self) -> Dict:
        """Get DBC database information"""
        if not self._loaded or self.db is None:
            return {
                'name': self.name,
                'file_path': self.file_path,
                'loaded': False,
                'message_count': 0,
                'node_count': 0
            }

        return {
            'name': self.name,
            'file_path': self.file_path,
            'loaded': True,
            'message_count': len(self.db.messages),
            'node_count': len(self.db.nodes) if hasattr(self.db, 'nodes') else 0,
            'version': getattr(self.db, 'version', 'Unknown')
        }


class DBCManager:
    """Manager for multiple DBC databases"""

    def __init__(self):
        self.databases: Dict[str, DBCDatabase] = {}
        self._active_db: Optional[str] = None

    def add_dbc(self, file_path: str, name: Optional[str] = None, load: bool = True) -> str:
        """
        Add a DBC file

        Args:
            file_path: Path to DBC file
            name: Optional custom name for the database
            load: Whether to load the database immediately

        Returns:
            Database ID (name)
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"DBC file not found: {file_path}")

        # Generate unique name if not provided
        if name is None:
            name = os.path.splitext(os.path.basename(file_path))[0]

        # Make name unique
        original_name = name
        counter = 1
        while name in self.databases:
            name = f"{original_name}_{counter}"
            counter += 1

        # Create database object
        db = DBCDatabase(file_path, name)

        # Load if requested
        if load:
            db.load()

        # Add to databases
        self.databases[name] = db

        # Set as active if it's the first database
        if self._active_db is None:
            self._active_db = name

        return name

    def remove_dbc(self, name: str) -> bool:
        """
        Remove a DBC database

        Args:
            name: Database name

        Returns:
            True if removed successfully
        """
        if name not in self.databases:
            return False

        del self.databases[name]

        # Update active database if removed
        if self._active_db == name:
            if self.databases:
                self._active_db = next(iter(self.databases))
            else:
                self._active_db = None

        return True

    def get_dbc(self, name: str) -> Optional[DBCDatabase]:
        """Get a DBC database by name"""
        return self.databases.get(name)

    def list_dbcs(self) -> List[str]:
        """List all loaded DBC database names"""
        return list(self.databases.keys())

    def list_dbc_names(self) -> List[str]:
        """Alias for list_dbcs() - List all loaded DBC database names"""
        return self.list_dbcs()

    def get_dbc_info(self, name: str) -> Optional[Dict]:
        """Get information about a DBC database"""
        db = self.databases.get(name)
        if db is None:
            return None
        return db.get_info()

    def get_all_info(self) -> List[Dict]:
        """Get information about all loaded DBC databases"""
        return [db.get_info() for db in self.databases.values()]

    def set_active(self, name: str) -> bool:
        """
        Set active DBC database

        Args:
            name: Database name

        Returns:
            True if set successfully
        """
        if name not in self.databases:
            return False
        self._active_db = name
        return True

    def get_active(self) -> Optional[DBCDatabase]:
        """Get the active DBC database"""
        if self._active_db is None:
            return None
        return self.databases.get(self._active_db)

    def get_active_name(self) -> Optional[str]:
        """Get the active DBC database name"""
        return self._active_db

    def decode_message(self, can_id: int, data: bytes, db_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Decode a CAN message

        Args:
            can_id: CAN ID
            data: Message data bytes
            db_name: Optional specific database name (uses active if not specified)

        Returns:
            Dictionary of signal name -> value
        """
        # Get database to use
        if db_name is not None:
            db = self.databases.get(db_name)
        else:
            db = self.get_active()

        if db is None or not db.is_loaded():
            return {}

        return db.decode_message(can_id, data)

    def clear(self):
        """Clear all DBC databases"""
        self.databases.clear()
        self._active_db = None

    def count(self) -> int:
        """Get total number of loaded databases"""
        return len(self.databases)

    @staticmethod
    def is_dbc_file(file_path: str) -> bool:
        """Check if file is a DBC file based on extension"""
        return file_path.lower().endswith('.dbc')
