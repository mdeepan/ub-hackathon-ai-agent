"""
Tests for database connection management.

This module tests the DatabaseConnection class and related functionality
including connection management, query execution, and error handling.
"""

import pytest
import sqlite3
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from backend.database.connection import (
    DatabaseConnection, 
    get_database, 
    initialize_database, 
    reset_database
)


class TestDatabaseConnection:
    """Test cases for DatabaseConnection class."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Create a temporary database file for testing
        self.temp_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.temp_dir, "test.db")
        self.db = DatabaseConnection(self.test_db_path)
    
    def teardown_method(self):
        """Clean up after each test method."""
        # Remove temporary database file
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
        os.rmdir(self.temp_dir)
    
    def test_initialization_with_custom_path(self):
        """Test database initialization with custom path."""
        assert self.db.db_path == Path(self.test_db_path)
        assert self.db.db_path.parent.exists()
    
    def test_initialization_with_default_path(self):
        """Test database initialization with default path."""
        db = DatabaseConnection()
        expected_path = Path(__file__).parent.parent / "data" / "sqlite" / "pla.db"
        assert db.db_path == expected_path
        assert db.db_path.parent.exists()
    
    def test_ensure_db_directory_creation(self):
        """Test that database directory is created if it doesn't exist."""
        temp_dir = tempfile.mkdtemp()
        db_path = os.path.join(temp_dir, "nested", "dir", "test.db")
        
        try:
            db = DatabaseConnection(db_path)
            assert Path(db_path).parent.exists()
        finally:
            # Clean up
            import shutil
            shutil.rmtree(temp_dir)
    
    def test_connection_context_manager(self):
        """Test database connection context manager."""
        with self.db.get_connection() as conn:
            assert isinstance(conn, sqlite3.Connection)
            assert conn.row_factory == sqlite3.Row
        
        # Connection should be closed after context
        with pytest.raises(sqlite3.ProgrammingError):
            conn.execute("SELECT 1")
    
    def test_cursor_context_manager(self):
        """Test database cursor context manager."""
        with self.db.get_cursor() as cursor:
            assert isinstance(cursor, sqlite3.Cursor)
            cursor.execute("SELECT 1 as test")
            result = cursor.fetchone()
            assert result['test'] == 1
        
        # Cursor should be closed after context
        with pytest.raises(sqlite3.ProgrammingError):
            cursor.execute("SELECT 1")
    
    def test_execute_query_success(self):
        """Test successful query execution."""
        # Create a test table
        with self.db.get_connection() as conn:
            conn.execute("CREATE TABLE test (id INTEGER, name TEXT)")
            conn.execute("INSERT INTO test VALUES (1, 'test1'), (2, 'test2')")
            conn.commit()
        
        # Test query execution
        results = self.db.execute_query("SELECT * FROM test ORDER BY id")
        assert len(results) == 2
        assert results[0]['id'] == 1
        assert results[0]['name'] == 'test1'
        assert results[1]['id'] == 2
        assert results[1]['name'] == 'test2'
    
    def test_execute_query_with_params(self):
        """Test query execution with parameters."""
        # Create a test table
        with self.db.get_connection() as conn:
            conn.execute("CREATE TABLE test (id INTEGER, name TEXT)")
            conn.execute("INSERT INTO test VALUES (1, 'test1'), (2, 'test2')")
            conn.commit()
        
        # Test parameterized query
        results = self.db.execute_query("SELECT * FROM test WHERE id = ?", (1,))
        assert len(results) == 1
        assert results[0]['id'] == 1
        assert results[0]['name'] == 'test1'
    
    def test_execute_update_success(self):
        """Test successful update execution."""
        # Create a test table
        with self.db.get_connection() as conn:
            conn.execute("CREATE TABLE test (id INTEGER, name TEXT)")
            conn.execute("INSERT INTO test VALUES (1, 'test1')")
            conn.commit()
        
        # Test update execution
        affected_rows = self.db.execute_update(
            "UPDATE test SET name = ? WHERE id = ?", 
            ('updated', 1)
        )
        assert affected_rows == 1
        
        # Verify update
        results = self.db.execute_query("SELECT name FROM test WHERE id = 1")
        assert results[0]['name'] == 'updated'
    
    def test_execute_update_with_rollback(self):
        """Test update execution with rollback on error."""
        # Create a test table
        with self.db.get_connection() as conn:
            conn.execute("CREATE TABLE test (id INTEGER, name TEXT)")
            conn.execute("INSERT INTO test VALUES (1, 'test1')")
            conn.commit()
        
        # Test update with invalid query (should rollback)
        with pytest.raises(sqlite3.Error):
            self.db.execute_update("UPDATE test SET invalid_column = ? WHERE id = ?", ('value', 1))
        
        # Verify original data is unchanged
        results = self.db.execute_query("SELECT name FROM test WHERE id = 1")
        assert results[0]['name'] == 'test1'
    
    def test_execute_many_success(self):
        """Test successful batch execution."""
        # Create a test table
        with self.db.get_connection() as conn:
            conn.execute("CREATE TABLE test (id INTEGER, name TEXT)")
            conn.commit()
        
        # Test batch insert
        params_list = [(1, 'test1'), (2, 'test2'), (3, 'test3')]
        affected_rows = self.db.execute_many(
            "INSERT INTO test (id, name) VALUES (?, ?)", 
            params_list
        )
        assert affected_rows == 3
        
        # Verify all records were inserted
        results = self.db.execute_query("SELECT COUNT(*) as count FROM test")
        assert results[0]['count'] == 3
    
    def test_execute_many_with_rollback(self):
        """Test batch execution with rollback on error."""
        # Create a test table
        with self.db.get_connection() as conn:
            conn.execute("CREATE TABLE test (id INTEGER, name TEXT)")
            conn.commit()
        
        # Test batch insert with invalid SQL (should rollback)
        params_list = [(1, 'test1'), (2, 'test2'), (3, 'test3')]
        with pytest.raises(sqlite3.Error):
            self.db.execute_many("INSERT INTO test (id, name) VALUES (?, ?) INVALID_SQL", params_list)
        
        # Verify no records were inserted
        results = self.db.execute_query("SELECT COUNT(*) as count FROM test")
        assert results[0]['count'] == 0
    
    def test_get_database_info_empty_db(self):
        """Test database info for empty database."""
        # Create the database by executing a simple query
        self.db.execute_query("SELECT 1")
        
        info = self.db.get_database_info()
        
        assert info['path'] == str(self.test_db_path)
        assert info['exists'] is True
        assert info['size_bytes'] >= 0  # SQLite can have 0 bytes initially
        assert info['table_count'] == 0
        assert info['tables'] == []
    
    def test_get_database_info_with_tables(self):
        """Test database info with tables."""
        # Create test tables
        with self.db.get_connection() as conn:
            conn.execute("CREATE TABLE users (id INTEGER, name TEXT)")
            conn.execute("CREATE TABLE skills (id INTEGER, name TEXT)")
            conn.commit()
        
        info = self.db.get_database_info()
        
        assert info['table_count'] == 2
        assert 'users' in info['tables']
        assert 'skills' in info['tables']
        assert len(info['tables']) == 2
    
    def test_get_database_info_nonexistent_db(self):
        """Test database info for non-existent database."""
        nonexistent_path = os.path.join(self.temp_dir, "nonexistent.db")
        db = DatabaseConnection(nonexistent_path)
        
        info = db.get_database_info()
        
        assert info['path'] == nonexistent_path
        assert info['exists'] is False
        assert info['size_bytes'] == 0
        assert info['table_count'] == 0
        assert info['tables'] == []
    
    def test_connection_test_success(self):
        """Test successful connection test."""
        assert self.db.test_connection() is True
    
    def test_connection_test_failure(self):
        """Test connection test failure."""
        # Create a database with invalid permissions
        with patch('sqlite3.connect') as mock_connect:
            mock_connect.side_effect = sqlite3.Error("Connection failed")
            
            db = DatabaseConnection(self.test_db_path)
            assert db.test_connection() is False


class TestGlobalDatabaseFunctions:
    """Test cases for global database functions."""
    
    def teardown_method(self):
        """Clean up after each test method."""
        reset_database()
    
    def test_get_database_creates_instance(self):
        """Test that get_database creates a new instance if none exists."""
        reset_database()
        db = get_database()
        assert isinstance(db, DatabaseConnection)
    
    def test_get_database_returns_same_instance(self):
        """Test that get_database returns the same instance."""
        db1 = get_database()
        db2 = get_database()
        assert db1 is db2
    
    def test_initialize_database(self):
        """Test database initialization."""
        temp_dir = tempfile.mkdtemp()
        test_db_path = os.path.join(temp_dir, "init_test.db")
        
        try:
            db = initialize_database(test_db_path)
            assert isinstance(db, DatabaseConnection)
            assert db.db_path == Path(test_db_path)
            
            # Verify global instance is set
            global_db = get_database()
            assert global_db is db
        finally:
            # Clean up
            if os.path.exists(test_db_path):
                os.remove(test_db_path)
            os.rmdir(temp_dir)
    
    def test_reset_database(self):
        """Test database reset."""
        # Get initial instance
        db1 = get_database()
        
        # Reset and get new instance
        reset_database()
        db2 = get_database()
        
        # Should be different instances
        assert db1 is not db2


class TestDatabaseErrorHandling:
    """Test cases for database error handling."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.temp_dir, "test.db")
        self.db = DatabaseConnection(self.test_db_path)
    
    def teardown_method(self):
        """Clean up after each test method."""
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
        os.rmdir(self.temp_dir)
    
    def test_connection_error_handling(self):
        """Test connection error handling."""
        with patch('sqlite3.connect') as mock_connect:
            mock_connect.side_effect = sqlite3.Error("Connection failed")
            
            with pytest.raises(sqlite3.Error):
                with self.db.get_connection():
                    pass
    
    def test_query_error_handling(self):
        """Test query error handling."""
        with pytest.raises(sqlite3.Error):
            self.db.execute_query("INVALID SQL QUERY")
    
    def test_update_error_handling(self):
        """Test update error handling."""
        with pytest.raises(sqlite3.Error):
            self.db.execute_update("INVALID SQL UPDATE")
    
    def test_batch_error_handling(self):
        """Test batch execution error handling."""
        with pytest.raises(sqlite3.Error):
            self.db.execute_many("INVALID SQL BATCH", [(1, 2), (3, 4)])


if __name__ == "__main__":
    pytest.main([__file__])
