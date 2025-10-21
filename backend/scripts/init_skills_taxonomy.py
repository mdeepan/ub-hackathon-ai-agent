#!/usr/bin/env python3
"""
Script to initialize skills taxonomy from JSON file.

This script loads the skills taxonomy from the JSON file and populates the database
with skills taxonomy entries for the Personal Learning Agent.
"""

import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.services.skills_engine import get_skills_engine
from backend.database.init_db import initialize_database_schema
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Initialize skills taxonomy from JSON file."""
    try:
        logger.info("Starting skills taxonomy initialization...")
        
        # Initialize database schema first
        logger.info("Initializing database schema...")
        initialize_database_schema()
        logger.info("Database schema initialized successfully")
        
        # Get skills engine
        skills_engine = get_skills_engine()
        
        # Load skills taxonomy from JSON file
        taxonomy_file_path = Path(__file__).parent.parent.parent / "data" / "skills_taxonomy.json"
        
        if not taxonomy_file_path.exists():
            logger.error(f"Skills taxonomy file not found: {taxonomy_file_path}")
            return False
        
        logger.info(f"Loading skills taxonomy from: {taxonomy_file_path}")
        taxonomy_entries = skills_engine.load_skills_taxonomy_from_file(str(taxonomy_file_path))
        
        logger.info(f"Successfully loaded {len(taxonomy_entries)} skills taxonomy entries")
        
        # Verify the entries were created
        all_taxonomy = skills_engine.get_all_skills_taxonomy()
        logger.info(f"Total skills taxonomy entries in database: {len(all_taxonomy)}")
        
        # Show some statistics
        categories = {}
        for entry in all_taxonomy:
            category = entry.category
            if category not in categories:
                categories[category] = 0
            categories[category] += 1
        
        logger.info("Skills taxonomy by category:")
        for category, count in sorted(categories.items()):
            logger.info(f"  {category}: {count} skills")
        
        logger.info("Skills taxonomy initialization completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Skills taxonomy initialization failed: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
