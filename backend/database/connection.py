"""
Database connection management for the Personal Learning Agent.

This module provides SQLite database connection management with proper
error handling, connection pooling, and configuration management.
"""

import sqlite3
import os
from pathlib import Path
from typing import Optional, Dict, Any
from contextlib import contextmanager
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseConnection:
    """
    SQLite database connection manager with connection pooling and error handling.
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize database connection manager.
        
        Args:
            db_path: Path to SQLite database file. If None, uses default path.
        """
        if db_path is None:
            # Default to data/sqlite/pla.db
            project_root = Path(__file__).parent.parent.parent
            db_path = project_root / "data" / "sqlite" / "pla.db"
        
        self.db_path = Path(db_path)
        self._ensure_db_directory()
        
        # Connection configuration
        self.connection_config = {
            'check_same_thread': False,
            'timeout': 30.0,
            'isolation_level': None  # Autocommit mode
        }
        
        logger.info(f"Database connection initialized: {self.db_path}")
    
    def _ensure_db_directory(self) -> None:
        """Ensure the database directory exists."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"Database directory ensured: {self.db_path.parent}")
    
    @contextmanager
    def get_connection(self):
        """
        Context manager for database connections.
        
        Yields:
            sqlite3.Connection: Database connection
            
        Raises:
            sqlite3.Error: If connection fails
        """
        connection = None
        try:
            connection = sqlite3.connect(str(self.db_path), **self.connection_config)
            connection.row_factory = sqlite3.Row  # Enable dict-like access
            logger.debug("Database connection established")
            yield connection
        except sqlite3.Error as e:
            logger.error(f"Database connection error: {e}")
            if connection:
                connection.rollback()
            raise
        finally:
            if connection:
                connection.close()
                logger.debug("Database connection closed")
    
    @contextmanager
    def get_cursor(self):
        """
        Context manager for database cursors.
        
        Yields:
            sqlite3.Cursor: Database cursor
            
        Raises:
            sqlite3.Error: If connection or cursor creation fails
        """
        with self.get_connection() as connection:
            cursor = connection.cursor()
            try:
                yield cursor
            except sqlite3.Error as e:
                logger.error(f"Database cursor error: {e}")
                connection.rollback()
                raise
            finally:
                cursor.close()
    
    def execute_query(self, query: str, params: tuple = ()) -> list:
        """
        Execute a SELECT query and return results.
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            list: Query results as list of Row objects
            
        Raises:
            sqlite3.Error: If query execution fails
        """
        with self.get_cursor() as cursor:
            logger.debug(f"Executing query: {query[:100]}...")
            cursor.execute(query, params)
            results = cursor.fetchall()
            logger.debug(f"Query returned {len(results)} rows")
            return results
    
    def execute_update(self, query: str, params: tuple = ()) -> int:
        """
        Execute an INSERT, UPDATE, or DELETE query.
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            int: Number of affected rows
            
        Raises:
            sqlite3.Error: If query execution fails
        """
        with self.get_connection() as connection:
            cursor = connection.cursor()
            try:
                logger.debug(f"Executing update: {query[:100]}...")
                cursor.execute(query, params)
                connection.commit()
                affected_rows = cursor.rowcount
                logger.debug(f"Update affected {affected_rows} rows")
                return affected_rows
            except sqlite3.Error as e:
                logger.error(f"Update query error: {e}")
                connection.rollback()
                raise
            finally:
                cursor.close()
    
    def execute_many(self, query: str, params_list: list) -> int:
        """
        Execute a query multiple times with different parameters.
        
        Args:
            query: SQL query string
            params_list: List of parameter tuples
            
        Returns:
            int: Total number of affected rows
            
        Raises:
            sqlite3.Error: If query execution fails
        """
        with self.get_connection() as connection:
            cursor = connection.cursor()
            try:
                logger.debug(f"Executing batch update: {query[:100]}...")
                cursor.executemany(query, params_list)
                connection.commit()
                affected_rows = cursor.rowcount
                logger.debug(f"Batch update affected {affected_rows} rows")
                return affected_rows
            except sqlite3.Error as e:
                logger.error(f"Batch update error: {e}")
                connection.rollback()
                raise
            finally:
                cursor.close()
    
    def get_database_info(self) -> Dict[str, Any]:
        """
        Get database information and statistics.
        
        Returns:
            dict: Database information including path, size, and table count
        """
        info = {
            'path': str(self.db_path),
            'exists': self.db_path.exists(),
            'size_bytes': 0,
            'table_count': 0,
            'tables': []
        }
        
        if self.db_path.exists():
            info['size_bytes'] = self.db_path.stat().st_size
            
            try:
                with self.get_cursor() as cursor:
                    # Get table count
                    cursor.execute("""
                        SELECT COUNT(*) as count 
                        FROM sqlite_master 
                        WHERE type='table' AND name NOT LIKE 'sqlite_%'
                    """)
                    result = cursor.fetchone()
                    info['table_count'] = result['count'] if result else 0
                    
                    # Get table names
                    cursor.execute("""
                        SELECT name 
                        FROM sqlite_master 
                        WHERE type='table' AND name NOT LIKE 'sqlite_%'
                        ORDER BY name
                    """)
                    tables = cursor.fetchall()
                    info['tables'] = [table['name'] for table in tables]
                    
            except sqlite3.Error as e:
                logger.warning(f"Could not get database info: {e}")
        
        return info
    
    def test_connection(self) -> bool:
        """
        Test database connection and basic functionality.
        
        Returns:
            bool: True if connection test passes, False otherwise
        """
        try:
            with self.get_cursor() as cursor:
                cursor.execute("SELECT 1 as test")
                result = cursor.fetchone()
                return result['test'] == 1
        except sqlite3.Error as e:
            logger.error(f"Connection test failed: {e}")
            return False


# Global database instance
_db_instance: Optional[DatabaseConnection] = None


def get_database() -> DatabaseConnection:
    """
    Get the global database connection instance.
    
    Returns:
        DatabaseConnection: Global database instance
    """
    global _db_instance
    if _db_instance is None:
        _db_instance = DatabaseConnection()
    return _db_instance


def initialize_database(db_path: Optional[str] = None) -> DatabaseConnection:
    """
    Initialize the global database connection.
    
    Args:
        db_path: Path to SQLite database file
        
    Returns:
        DatabaseConnection: Initialized database instance
    """
    global _db_instance
    _db_instance = DatabaseConnection(db_path)
    return _db_instance


def reset_database() -> None:
    """Reset the global database instance (useful for testing)."""
    global _db_instance
    _db_instance = None
