"""
Database initialization and schema setup for the Personal Learning Agent.

This module creates all necessary database tables for user profiles, learning data,
skills assessment, and progress tracking.
"""

import sqlite3
import json
from pathlib import Path
from typing import Optional, Dict, Any
import logging

from .connection import get_database

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseInitializer:
    """Database initialization and schema management."""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize database initializer.
        
        Args:
            db_path: Path to SQLite database file. If None, uses default path.
        """
        self.db = get_database()
        logger.info("Database initializer created")
    
    def create_user_tables(self) -> None:
        """Create user-related database tables."""
        logger.info("Creating user tables...")
        
        # User profiles table
        user_profiles_sql = """
        CREATE TABLE IF NOT EXISTS user_profiles (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            job_role TEXT NOT NULL,
            experience_summary TEXT,
            personal_goals TEXT,  -- JSON array
            team_info TEXT,       -- JSON object
            project_info TEXT,    -- JSON object
            connections TEXT,     -- JSON object
            preferences TEXT,     -- JSON object
            skill_gaps TEXT,      -- JSON array
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        # User tasks table
        user_tasks_sql = """
        CREATE TABLE IF NOT EXISTS user_tasks (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'pending',
            priority TEXT DEFAULT 'medium',
            due_date DATE,
            completed_date DATE,
            estimated_hours REAL,
            actual_hours REAL,
            skills_used TEXT,     -- JSON array
            skills_learned TEXT,  -- JSON array
            project_context TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES user_profiles (id) ON DELETE CASCADE
        )
        """
        
        # User skills table
        user_skills_sql = """
        CREATE TABLE IF NOT EXISTS user_skills (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            skill_name TEXT NOT NULL,
            category TEXT,
            level TEXT DEFAULT 'beginner',
            source TEXT DEFAULT 'self_declared',
            confidence_score REAL,
            last_used_date DATE,
            last_assessed_date DATE,
            evidence_count INTEGER DEFAULT 0,
            learning_priority TEXT,
            target_level TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES user_profiles (id) ON DELETE CASCADE,
            UNIQUE(user_id, skill_name)
        )
        """
        
        # User context table
        user_context_sql = """
        CREATE TABLE IF NOT EXISTS user_context (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            current_focus_areas TEXT,  -- JSON array
            recent_work_summary TEXT,
            upcoming_priorities TEXT,  -- JSON array
            learning_goals TEXT,       -- JSON array
            skill_gaps TEXT,           -- JSON array
            context_summary TEXT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES user_profiles (id) ON DELETE CASCADE
        )
        """
        
        # Execute table creation
        self.db.execute_update(user_profiles_sql)
        self.db.execute_update(user_tasks_sql)
        self.db.execute_update(user_skills_sql)
        self.db.execute_update(user_context_sql)
        
        logger.info("User tables created successfully")
    
    def create_learning_tables(self) -> None:
        """Create learning-related database tables."""
        logger.info("Creating learning tables...")
        
        # Learning content table
        learning_content_sql = """
        CREATE TABLE IF NOT EXISTS learning_content (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT,
            content_type TEXT DEFAULT 'article',
            difficulty TEXT DEFAULT 'beginner',
            estimated_duration INTEGER,
            skills_covered TEXT,      -- JSON array
            prerequisites TEXT,       -- JSON array
            learning_objectives TEXT, -- JSON array
            content_url TEXT,
            content_text TEXT,
            tags TEXT,                -- JSON array
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        # Learning paths table
        learning_paths_sql = """
        CREATE TABLE IF NOT EXISTS learning_paths (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT,
            target_skills TEXT,       -- JSON array
            difficulty TEXT DEFAULT 'beginner',
            estimated_duration INTEGER,
            content_sequence TEXT,    -- JSON array
            prerequisites TEXT,       -- JSON array
            learning_objectives TEXT, -- JSON array
            tags TEXT,                -- JSON array
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        # Learning progress table
        learning_progress_sql = """
        CREATE TABLE IF NOT EXISTS learning_progress (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            content_id TEXT,
            learning_path_id TEXT,
            status TEXT DEFAULT 'not_started',
            completion_percentage REAL DEFAULT 0.0,
            time_spent INTEGER,
            quiz_score REAL,
            started_at TIMESTAMP,
            completed_at TIMESTAMP,
            last_accessed_at TIMESTAMP,
            notes TEXT,
            skills_gained TEXT,       -- JSON array
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES user_profiles (id) ON DELETE CASCADE,
            FOREIGN KEY (content_id) REFERENCES learning_content (id) ON DELETE SET NULL,
            FOREIGN KEY (learning_path_id) REFERENCES learning_paths (id) ON DELETE SET NULL
        )
        """
        
        # Execute table creation
        self.db.execute_update(learning_content_sql)
        self.db.execute_update(learning_paths_sql)
        self.db.execute_update(learning_progress_sql)
        
        logger.info("Learning tables created successfully")
    
    def create_skills_tables(self) -> None:
        """Create skills assessment database tables."""
        logger.info("Creating skills assessment tables...")
        
        # Skills assessments table
        skills_assessments_sql = """
        CREATE TABLE IF NOT EXISTS skills_assessments (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            assessment_type TEXT DEFAULT 'artifact_analysis',
            status TEXT DEFAULT 'pending',
            title TEXT NOT NULL,
            description TEXT,
            artifacts_analyzed TEXT,  -- JSON array
            skills_evaluated TEXT,    -- JSON array
            overall_score REAL,
            confidence_level REAL,
            assessment_data TEXT,     -- JSON object
            recommendations TEXT,     -- JSON array
            started_at TIMESTAMP,
            completed_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES user_profiles (id) ON DELETE CASCADE
        )
        """
        
        # Skill gaps table
        skill_gaps_sql = """
        CREATE TABLE IF NOT EXISTS skill_gaps (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            skill_name TEXT NOT NULL,
            category TEXT,
            current_level TEXT,
            target_level TEXT,
            gap_size TEXT,
            priority TEXT DEFAULT 'medium',
            urgency TEXT DEFAULT 'medium',
            business_impact TEXT,
            learning_effort TEXT,
            evidence_sources TEXT,    -- JSON array
            recommended_actions TEXT, -- JSON array
            related_skills TEXT,      -- JSON array
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES user_profiles (id) ON DELETE CASCADE
        )
        """
        
        # Skills taxonomy table
        skills_taxonomy_sql = """
        CREATE TABLE IF NOT EXISTS skills_taxonomy (
            id TEXT PRIMARY KEY,
            skill_name TEXT UNIQUE NOT NULL,
            category TEXT NOT NULL,
            subcategory TEXT,
            description TEXT,
            proficiency_levels TEXT,  -- JSON array
            related_skills TEXT,      -- JSON array
            prerequisites TEXT,       -- JSON array
            typical_use_cases TEXT,   -- JSON array
            industry_relevance TEXT,  -- JSON array
            learning_resources TEXT,  -- JSON array
            assessment_methods TEXT,  -- JSON array
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        # Execute table creation
        self.db.execute_update(skills_assessments_sql)
        self.db.execute_update(skill_gaps_sql)
        self.db.execute_update(skills_taxonomy_sql)
        
        logger.info("Skills assessment tables created successfully")
    
    def create_indexes(self) -> None:
        """Create database indexes for better performance."""
        logger.info("Creating database indexes...")
        
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_user_tasks_user_id ON user_tasks(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_user_tasks_status ON user_tasks(status)",
            "CREATE INDEX IF NOT EXISTS idx_user_tasks_due_date ON user_tasks(due_date)",
            "CREATE INDEX IF NOT EXISTS idx_user_skills_user_id ON user_skills(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_user_skills_category ON user_skills(category)",
            "CREATE INDEX IF NOT EXISTS idx_user_skills_level ON user_skills(level)",
            "CREATE INDEX IF NOT EXISTS idx_learning_progress_user_id ON learning_progress(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_learning_progress_status ON learning_progress(status)",
            "CREATE INDEX IF NOT EXISTS idx_learning_progress_content_id ON learning_progress(content_id)",
            "CREATE INDEX IF NOT EXISTS idx_skills_assessments_user_id ON skills_assessments(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_skills_assessments_status ON skills_assessments(status)",
            "CREATE INDEX IF NOT EXISTS idx_skill_gaps_user_id ON skill_gaps(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_skill_gaps_priority ON skill_gaps(priority)",
            "CREATE INDEX IF NOT EXISTS idx_skills_taxonomy_category ON skills_taxonomy(category)",
            "CREATE INDEX IF NOT EXISTS idx_skills_taxonomy_skill_name ON skills_taxonomy(skill_name)"
        ]
        
        for index_sql in indexes:
            self.db.execute_update(index_sql)
        
        logger.info("Database indexes created successfully")
    
    def create_triggers(self) -> None:
        """Create database triggers for automatic timestamp updates."""
        logger.info("Creating database triggers...")
        
        triggers = [
            # User profiles update trigger
            """
            CREATE TRIGGER IF NOT EXISTS update_user_profiles_timestamp 
            AFTER UPDATE ON user_profiles
            BEGIN
                UPDATE user_profiles SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
            END
            """,
            
            # User tasks update trigger
            """
            CREATE TRIGGER IF NOT EXISTS update_user_tasks_timestamp 
            AFTER UPDATE ON user_tasks
            BEGIN
                UPDATE user_tasks SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
            END
            """,
            
            # User skills update trigger
            """
            CREATE TRIGGER IF NOT EXISTS update_user_skills_timestamp 
            AFTER UPDATE ON user_skills
            BEGIN
                UPDATE user_skills SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
            END
            """,
            
            # Learning content update trigger
            """
            CREATE TRIGGER IF NOT EXISTS update_learning_content_timestamp 
            AFTER UPDATE ON learning_content
            BEGIN
                UPDATE learning_content SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
            END
            """,
            
            # Learning paths update trigger
            """
            CREATE TRIGGER IF NOT EXISTS update_learning_paths_timestamp 
            AFTER UPDATE ON learning_paths
            BEGIN
                UPDATE learning_paths SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
            END
            """,
            
            # Learning progress update trigger
            """
            CREATE TRIGGER IF NOT EXISTS update_learning_progress_timestamp 
            AFTER UPDATE ON learning_progress
            BEGIN
                UPDATE learning_progress SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
            END
            """,
            
            # Skills assessments update trigger
            """
            CREATE TRIGGER IF NOT EXISTS update_skills_assessments_timestamp 
            AFTER UPDATE ON skills_assessments
            BEGIN
                UPDATE skills_assessments SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
            END
            """,
            
            # Skill gaps update trigger
            """
            CREATE TRIGGER IF NOT EXISTS update_skill_gaps_timestamp 
            AFTER UPDATE ON skill_gaps
            BEGIN
                UPDATE skill_gaps SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
            END
            """,
            
            # Skills taxonomy update trigger
            """
            CREATE TRIGGER IF NOT EXISTS update_skills_taxonomy_timestamp 
            AFTER UPDATE ON skills_taxonomy
            BEGIN
                UPDATE skills_taxonomy SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
            END
            """
        ]
        
        for trigger_sql in triggers:
            self.db.execute_update(trigger_sql)
        
        logger.info("Database triggers created successfully")
    
    def initialize_all_tables(self) -> None:
        """Initialize all database tables, indexes, and triggers."""
        logger.info("Starting database initialization...")
        
        try:
            self.create_user_tables()
            self.create_learning_tables()
            self.create_skills_tables()
            self.create_indexes()
            self.create_triggers()
            
            logger.info("Database initialization completed successfully")
            
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise
    
    def get_database_schema_info(self) -> Dict[str, Any]:
        """Get information about the database schema."""
        try:
            # Get table information
            tables_query = """
            SELECT name, sql 
            FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
            """
            tables = self.db.execute_query(tables_query)
            
            # Get index information
            indexes_query = """
            SELECT name, sql 
            FROM sqlite_master 
            WHERE type='index' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
            """
            indexes = self.db.execute_query(indexes_query)
            
            # Get trigger information
            triggers_query = """
            SELECT name, sql 
            FROM sqlite_master 
            WHERE type='trigger'
            ORDER BY name
            """
            triggers = self.db.execute_query(triggers_query)
            
            schema_info = {
                'tables': [{'name': table['name'], 'sql': table['sql']} for table in tables],
                'indexes': [{'name': index['name'], 'sql': index['sql']} for index in indexes],
                'triggers': [{'name': trigger['name'], 'sql': trigger['sql']} for trigger in triggers],
                'table_count': len(tables),
                'index_count': len(indexes),
                'trigger_count': len(triggers)
            }
            
            return schema_info
            
        except Exception as e:
            logger.error(f"Error getting database schema info: {e}")
            return {'error': str(e)}
    
    def reset_database(self) -> None:
        """Reset the database by dropping all tables (use with caution!)."""
        logger.warning("Resetting database - all data will be lost!")
        
        try:
            # Get all table names
            tables_query = """
            SELECT name 
            FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            """
            tables = self.db.execute_query(tables_query)
            
            # Drop all tables
            for table in tables:
                drop_sql = f"DROP TABLE IF EXISTS {table['name']}"
                self.db.execute_update(drop_sql)
                logger.info(f"Dropped table: {table['name']}")
            
            logger.info("Database reset completed")
            
        except Exception as e:
            logger.error(f"Database reset failed: {e}")
            raise


def initialize_database_schema(db_path: Optional[str] = None) -> DatabaseInitializer:
    """
    Initialize the database schema.
    
    Args:
        db_path: Path to SQLite database file
        
    Returns:
        DatabaseInitializer: Initialized database initializer
    """
    initializer = DatabaseInitializer(db_path)
    initializer.initialize_all_tables()
    return initializer


def get_database_initializer(db_path: Optional[str] = None) -> DatabaseInitializer:
    """
    Get a database initializer instance.
    
    Args:
        db_path: Path to SQLite database file
        
    Returns:
        DatabaseInitializer: Database initializer instance
    """
    return DatabaseInitializer(db_path)


if __name__ == "__main__":
    # Initialize database when run directly
    initializer = initialize_database_schema()
    schema_info = initializer.get_database_schema_info()
    
    print(f"Database initialized with {schema_info['table_count']} tables")
    print(f"Tables: {[table['name'] for table in schema_info['tables']]}")
