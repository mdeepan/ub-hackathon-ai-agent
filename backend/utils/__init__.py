"""
Utilities package for the Personal Learning Agent.

This package contains utility modules for file processing, content management,
and other helper functions used throughout the application.
"""

from .file_processor import (
    FileProcessor,
    FileMetadata,
    ProcessedContent,
    get_file_processor,
    initialize_file_processor,
    reset_file_processor
)

from .content_manager import (
    ContentManager,
    ContentMetadata,
    ContentSearchResult,
    LearningPath,
    get_content_manager,
    initialize_content_manager,
    reset_content_manager
)

__all__ = [
    # File processor
    'FileProcessor',
    'FileMetadata', 
    'ProcessedContent',
    'get_file_processor',
    'initialize_file_processor',
    'reset_file_processor',
    
    # Content manager
    'ContentManager',
    'ContentMetadata',
    'ContentSearchResult',
    'LearningPath',
    'get_content_manager',
    'initialize_content_manager',
    'reset_content_manager'
]
