"""
Content management utilities for learning content database.

This module provides comprehensive content management capabilities for the Personal Learning Agent,
including content storage, retrieval, categorization, and integration with the AI client.
"""

import os
import json
import hashlib
from typing import Dict, List, Optional, Union, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import logging
from datetime import datetime, timezone

# Database imports
from ..database.connection import get_database
from ..database.vector_store import get_vector_store
from ..core.ai_client import get_ai_client
from ..core.config import get_config

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class ContentMetadata:
    """Metadata for learning content."""
    content_id: str
    title: str
    content_type: str  # 'document', 'article', 'video', 'course', 'assessment'
    category: str
    subcategory: Optional[str] = None
    difficulty_level: str = 'beginner'  # 'beginner', 'intermediate', 'advanced'
    estimated_duration: Optional[int] = None  # in minutes
    tags: List[str] = None
    skills_covered: List[str] = None
    prerequisites: List[str] = None
    learning_objectives: List[str] = None
    created_at: datetime = None
    updated_at: datetime = None
    author: Optional[str] = None
    source_url: Optional[str] = None
    file_path: Optional[str] = None
    file_hash: Optional[str] = None
    text_content: Optional[str] = None
    embedding_id: Optional[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.skills_covered is None:
            self.skills_covered = []
        if self.prerequisites is None:
            self.prerequisites = []
        if self.learning_objectives is None:
            self.learning_objectives = []
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)
        if self.updated_at is None:
            self.updated_at = datetime.now(timezone.utc)


@dataclass
class ContentSearchResult:
    """Search result for content queries."""
    content_id: str
    title: str
    content_type: str
    category: str
    difficulty_level: str
    relevance_score: float
    text_snippet: str
    skills_covered: List[str]
    estimated_duration: Optional[int]


@dataclass
class LearningPath:
    """Learning path structure."""
    path_id: str
    title: str
    description: str
    target_skills: List[str]
    difficulty_level: str
    estimated_duration: int  # total minutes
    content_sequence: List[str]  # content_ids in order
    prerequisites: List[str]
    learning_objectives: List[str]
    created_at: datetime = None
    updated_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)
        if self.updated_at is None:
            self.updated_at = datetime.now(timezone.utc)


class ContentManager:
    """
    Comprehensive content management system for learning materials.
    
    Provides content storage, retrieval, categorization, and AI-powered
    content analysis and recommendation capabilities.
    """
    
    # Content categories
    CONTENT_CATEGORIES = {
        'programming': {
            'subcategories': ['python', 'javascript', 'java', 'c++', 'web-development', 'mobile-development'],
            'skills': ['coding', 'debugging', 'algorithms', 'data-structures', 'software-architecture']
        },
        'data-science': {
            'subcategories': ['machine-learning', 'statistics', 'data-analysis', 'visualization', 'big-data'],
            'skills': ['python', 'r', 'sql', 'statistics', 'machine-learning', 'data-visualization']
        },
        'business': {
            'subcategories': ['management', 'marketing', 'finance', 'strategy', 'leadership'],
            'skills': ['project-management', 'communication', 'analytics', 'strategy', 'leadership']
        },
        'design': {
            'subcategories': ['ui-ux', 'graphic-design', 'web-design', 'product-design'],
            'skills': ['design-thinking', 'user-research', 'prototyping', 'visual-design']
        },
        'soft-skills': {
            'subcategories': ['communication', 'leadership', 'time-management', 'collaboration'],
            'skills': ['presentation', 'negotiation', 'teamwork', 'problem-solving']
        }
    }
    
    # Difficulty levels
    DIFFICULTY_LEVELS = ['beginner', 'intermediate', 'advanced', 'expert']
    
    def __init__(self, config_manager=None):
        """
        Initialize content manager.
        
        Args:
            config_manager: Configuration manager instance
        """
        self.config = config_manager or get_config()
        self.settings = self.config.get_settings()
        
        # Initialize database and vector store
        self.db = get_database()
        self.vector_store = get_vector_store()
        self.ai_client = get_ai_client()
        
        # Create content directory
        self.content_dir = Path(self.settings.data_dir) / "content"
        self.content_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize database tables
        self._initialize_database()
        
        logger.info("Content manager initialized successfully")
    
    def _initialize_database(self) -> None:
        """Initialize database tables for content management."""
        try:
            # Create content table
            self.db.execute_update("""
                CREATE TABLE IF NOT EXISTS content (
                    content_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    content_type TEXT NOT NULL,
                    category TEXT NOT NULL,
                    subcategory TEXT,
                    difficulty_level TEXT NOT NULL,
                    estimated_duration INTEGER,
                    tags TEXT,  -- JSON array
                    skills_covered TEXT,  -- JSON array
                    prerequisites TEXT,  -- JSON array
                    learning_objectives TEXT,  -- JSON array
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    author TEXT,
                    source_url TEXT,
                    file_path TEXT,
                    file_hash TEXT,
                    text_content TEXT,
                    embedding_id TEXT
                )
            """)
            
            # Create learning paths table
            self.db.execute_update("""
                CREATE TABLE IF NOT EXISTS learning_paths (
                    path_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT,
                    target_skills TEXT,  -- JSON array
                    difficulty_level TEXT NOT NULL,
                    estimated_duration INTEGER,
                    content_sequence TEXT,  -- JSON array
                    prerequisites TEXT,  -- JSON array
                    learning_objectives TEXT,  -- JSON array
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create content relationships table
            self.db.execute_update("""
                CREATE TABLE IF NOT EXISTS content_relationships (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content_id TEXT NOT NULL,
                    related_content_id TEXT NOT NULL,
                    relationship_type TEXT NOT NULL,  -- 'prerequisite', 'follows', 'related'
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (content_id) REFERENCES content (content_id),
                    FOREIGN KEY (related_content_id) REFERENCES content (content_id)
                )
            """)
            
            # Create indexes
            self.db.execute_update("CREATE INDEX IF NOT EXISTS idx_content_category ON content (category)")
            self.db.execute_update("CREATE INDEX IF NOT EXISTS idx_content_difficulty ON content (difficulty_level)")
            self.db.execute_update("CREATE INDEX IF NOT EXISTS idx_content_type ON content (content_type)")
            self.db.execute_update("CREATE INDEX IF NOT EXISTS idx_content_created ON content (created_at)")
            logger.info("Content database tables initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize content database: {e}")
            raise
    
    def generate_content_id(self, title: str, content_type: str) -> str:
        """
        Generate unique content ID.
        
        Args:
            title: Content title
            content_type: Type of content
            
        Returns:
            Unique content ID
        """
        # Create hash from title and timestamp
        timestamp = datetime.now(timezone.utc).isoformat()
        hash_input = f"{title}_{content_type}_{timestamp}"
        content_hash = hashlib.md5(hash_input.encode()).hexdigest()[:12]
        
        return f"{content_type}_{content_hash}"
    
    def add_content(
        self,
        title: str,
        content_type: str,
        category: str,
        text_content: str,
        subcategory: Optional[str] = None,
        difficulty_level: str = 'beginner',
        estimated_duration: Optional[int] = None,
        tags: Optional[List[str]] = None,
        skills_covered: Optional[List[str]] = None,
        prerequisites: Optional[List[str]] = None,
        learning_objectives: Optional[List[str]] = None,
        author: Optional[str] = None,
        source_url: Optional[str] = None,
        file_path: Optional[str] = None,
        file_hash: Optional[str] = None
    ) -> str:
        """
        Add new content to the database.
        
        Args:
            title: Content title
            content_type: Type of content
            category: Content category
            text_content: Text content to store
            subcategory: Optional subcategory
            difficulty_level: Difficulty level
            estimated_duration: Estimated duration in minutes
            tags: List of tags
            skills_covered: List of skills covered
            prerequisites: List of prerequisites
            learning_objectives: List of learning objectives
            author: Content author
            source_url: Source URL
            file_path: File path
            file_hash: File hash
            
        Returns:
            Content ID of the added content
        """
        try:
            # Generate content ID
            content_id = self.generate_content_id(title, content_type)
            
            # Generate embedding for the content
            embedding_response = self.ai_client.generate_embeddings(text_content)
            if embedding_response.error:
                logger.warning(f"Failed to generate embedding for content {content_id}: {embedding_response.error}")
                embedding_id = None
            else:
                # Store embedding in vector store
                embedding_id = self.vector_store.add_documents(
                    collection_name="content",
                    documents=[text_content],
                    metadatas=[{
                        'content_id': content_id,
                        'title': title,
                        'content_type': content_type,
                        'category': category,
                        'difficulty_level': difficulty_level
                    }],
                    ids=[content_id]  # Use content_id as the document ID
                )[0]
            
            # Prepare metadata
            metadata = ContentMetadata(
                content_id=content_id,
                title=title,
                content_type=content_type,
                category=category,
                subcategory=subcategory,
                difficulty_level=difficulty_level,
                estimated_duration=estimated_duration,
                tags=tags or [],
                skills_covered=skills_covered or [],
                prerequisites=prerequisites or [],
                learning_objectives=learning_objectives or [],
                author=author,
                source_url=source_url,
                file_path=file_path,
                file_hash=file_hash,
                text_content=text_content,
                embedding_id=embedding_id
            )
            
            # Insert into database
            self.db.execute_update("""
                INSERT INTO content (
                    content_id, title, content_type, category, subcategory,
                    difficulty_level, estimated_duration, tags, skills_covered,
                    prerequisites, learning_objectives, author, source_url,
                    file_path, file_hash, text_content, embedding_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                metadata.content_id,
                metadata.title,
                metadata.content_type,
                metadata.category,
                metadata.subcategory,
                metadata.difficulty_level,
                metadata.estimated_duration,
                json.dumps(metadata.tags),
                json.dumps(metadata.skills_covered),
                json.dumps(metadata.prerequisites),
                json.dumps(metadata.learning_objectives),
                metadata.author,
                metadata.source_url,
                metadata.file_path,
                metadata.file_hash,
                metadata.text_content,
                metadata.embedding_id
            ))
            
            logger.info(f"Successfully added content: {content_id} - {title}")
            return content_id
            
        except Exception as e:
            logger.error(f"Failed to add content: {e}")
            raise
    
    def get_content(self, content_id: str) -> Optional[ContentMetadata]:
        """
        Get content by ID.
        
        Args:
            content_id: Content ID
            
        Returns:
            ContentMetadata if found, None otherwise
        """
        try:
            results = self.db.execute_query("SELECT * FROM content WHERE content_id = ?", (content_id,))
            
            if not results:
                return None
            
            row = results[0]
            
            return ContentMetadata(
                content_id=row[0],
                title=row[1],
                content_type=row[2],
                category=row[3],
                subcategory=row[4],
                difficulty_level=row[5],
                estimated_duration=row[6],
                tags=json.loads(row[7]) if row[7] else [],
                skills_covered=json.loads(row[8]) if row[8] else [],
                prerequisites=json.loads(row[9]) if row[9] else [],
                learning_objectives=json.loads(row[10]) if row[10] else [],
                created_at=datetime.fromisoformat(row[11]) if row[11] else None,
                updated_at=datetime.fromisoformat(row[12]) if row[12] else None,
                author=row[13],
                source_url=row[14],
                file_path=row[15],
                file_hash=row[16],
                text_content=row[17],
                embedding_id=row[18]
            )
            
        except Exception as e:
            logger.error(f"Failed to get content {content_id}: {e}")
            return None
    
    def search_content(
        self,
        query: str,
        category: Optional[str] = None,
        difficulty_level: Optional[str] = None,
        content_type: Optional[str] = None,
        limit: int = 10
    ) -> List[ContentSearchResult]:
        """
        Search content using semantic search.
        
        Args:
            query: Search query
            category: Filter by category
            difficulty_level: Filter by difficulty level
            content_type: Filter by content type
            limit: Maximum number of results
            
        Returns:
            List of ContentSearchResult objects
        """
        try:
            # Generate embedding for the query
            embedding_response = self.ai_client.generate_embeddings(query)
            if embedding_response.error:
                logger.error(f"Failed to generate embedding for query: {embedding_response.error}")
                return []
            
            # Search in vector store
            search_results = self.vector_store.search_documents(
                collection_name="content",
                query_text=query,
                n_results=limit * 2  # Get more results for filtering
            )
            
            logger.debug(f"Search results: {search_results}")
            
            results = []
            if search_results.get('ids') and search_results['ids']:
                for i, doc_id in enumerate(search_results['ids']):
                    # Get content metadata from database using the document ID
                    # First try the doc_id directly, then try to find by content_id in metadata
                    content = self.get_content(doc_id)
                    if not content and search_results.get('metadatas') and i < len(search_results['metadatas']):
                        # Try to get content using content_id from metadata
                        metadata = search_results['metadatas'][i]
                        content_id = metadata.get('content_id')
                        if content_id:
                            content = self.get_content(content_id)
                    
                    if not content:
                        continue
                    
                    # Apply filters
                    if category and content.category != category:
                        continue
                    if difficulty_level and content.difficulty_level != difficulty_level:
                        continue
                    if content_type and content.content_type != content_type:
                        continue
                    
                    # Calculate relevance score from distance
                    distance = search_results.get('distances', [])[i] if search_results.get('distances') and i < len(search_results['distances']) else 1.0
                    relevance_score = max(0.0, 1.0 - distance)  # Convert distance to similarity score, ensure non-negative
                    
                    # Create search result
                    result = ContentSearchResult(
                        content_id=content.content_id,
                        title=content.title,
                        content_type=content.content_type,
                        category=content.category,
                        difficulty_level=content.difficulty_level,
                        relevance_score=relevance_score,
                        text_snippet=content.text_content[:200] + "..." if len(content.text_content) > 200 else content.text_content,
                        skills_covered=content.skills_covered,
                        estimated_duration=content.estimated_duration
                    )
                    
                    results.append(result)
                    
                    if len(results) >= limit:
                        break
            
            return results
            
        except Exception as e:
            logger.error(f"Content search failed: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return []
    
    def get_content_by_category(self, category: str, limit: int = 20) -> List[ContentMetadata]:
        """
        Get content by category.
        
        Args:
            category: Content category
            limit: Maximum number of results
            
        Returns:
            List of ContentMetadata objects
        """
        try:
            results = self.db.execute_query(
                "SELECT * FROM content WHERE category = ? ORDER BY created_at DESC LIMIT ?",
                (category, limit)
            )
            
            content_results = []
            for row in results:
                content = ContentMetadata(
                    content_id=row[0],
                    title=row[1],
                    content_type=row[2],
                    category=row[3],
                    subcategory=row[4],
                    difficulty_level=row[5],
                    estimated_duration=row[6],
                    tags=json.loads(row[7]) if row[7] else [],
                    skills_covered=json.loads(row[8]) if row[8] else [],
                    prerequisites=json.loads(row[9]) if row[9] else [],
                    learning_objectives=json.loads(row[10]) if row[10] else [],
                    created_at=datetime.fromisoformat(row[11]) if row[11] else None,
                    updated_at=datetime.fromisoformat(row[12]) if row[12] else None,
                    author=row[13],
                    source_url=row[14],
                    file_path=row[15],
                    file_hash=row[16],
                    text_content=row[17],
                    embedding_id=row[18]
                )
                content_results.append(content)
            
            return content_results
            
        except Exception as e:
            logger.error(f"Failed to get content by category {category}: {e}")
            return []
    
    def update_content(self, content_id: str, **kwargs) -> bool:
        """
        Update content metadata.
        
        Args:
            content_id: Content ID
            **kwargs: Fields to update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Build update query
            update_fields = []
            values = []
            
            for field, value in kwargs.items():
                if field in ['tags', 'skills_covered', 'prerequisites', 'learning_objectives']:
                    value = json.dumps(value) if value else None
                update_fields.append(f"{field} = ?")
                values.append(value)
            
            if not update_fields:
                return False
            
            # Add updated_at timestamp
            update_fields.append("updated_at = ?")
            values.append(datetime.now(timezone.utc).isoformat())
            values.append(content_id)
            
            query = f"UPDATE content SET {', '.join(update_fields)} WHERE content_id = ?"
            self.db.execute_update(query, values)
            
            logger.info(f"Successfully updated content: {content_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update content {content_id}: {e}")
            return False
    
    def delete_content(self, content_id: str) -> bool:
        """
        Delete content from database and vector store.
        
        Args:
            content_id: Content ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get content to find embedding ID
            content = self.get_content(content_id)
            if not content:
                return False
            
            # Delete from vector store if embedding exists
            if content.embedding_id:
                try:
                    self.vector_store.delete_documents("content", [content.embedding_id])
                except Exception as e:
                    logger.warning(f"Failed to delete embedding for content {content_id}: {e}")
            
            # Delete from database
            self.db.execute_update("DELETE FROM content WHERE content_id = ?", (content_id,))
            self.db.execute_update("DELETE FROM content_relationships WHERE content_id = ? OR related_content_id = ?", 
                          (content_id, content_id))
            
            logger.info(f"Successfully deleted content: {content_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete content {content_id}: {e}")
            return False
    
    def get_content_statistics(self) -> Dict[str, Any]:
        """
        Get content statistics.
        
        Returns:
            Dictionary with content statistics
        """
        try:
            stats = {}
            
            # Total content count
            results = self.db.execute_query("SELECT COUNT(*) FROM content")
            stats['total_content'] = results[0][0]
            
            # Content by category
            results = self.db.execute_query("""
                SELECT category, COUNT(*) FROM content 
                GROUP BY category ORDER BY COUNT(*) DESC
            """)
            stats['by_category'] = dict(results)
            
            # Content by difficulty level
            results = self.db.execute_query("""
                SELECT difficulty_level, COUNT(*) FROM content 
                GROUP BY difficulty_level ORDER BY COUNT(*) DESC
            """)
            stats['by_difficulty'] = dict(results)
            
            # Content by type
            results = self.db.execute_query("""
                SELECT content_type, COUNT(*) FROM content 
                GROUP BY content_type ORDER BY COUNT(*) DESC
            """)
            stats['by_type'] = dict(results)
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get content statistics: {e}")
            return {}
    
    def create_learning_path(
        self,
        title: str,
        description: str,
        target_skills: List[str],
        difficulty_level: str,
        content_sequence: List[str],
        estimated_duration: Optional[int] = None,
        prerequisites: Optional[List[str]] = None,
        learning_objectives: Optional[List[str]] = None
    ) -> str:
        """
        Create a learning path.
        
        Args:
            title: Learning path title
            description: Learning path description
            target_skills: List of target skills
            difficulty_level: Difficulty level
            content_sequence: List of content IDs in order
            estimated_duration: Total estimated duration in minutes
            prerequisites: List of prerequisites
            learning_objectives: List of learning objectives
            
        Returns:
            Learning path ID
        """
        try:
            # Generate path ID
            path_id = f"path_{hashlib.md5(f'{title}_{datetime.now().isoformat()}'.encode()).hexdigest()[:12]}"
            
            # Calculate total duration if not provided
            if not estimated_duration:
                total_duration = 0
                for content_id in content_sequence:
                    content = self.get_content(content_id)
                    if content and content.estimated_duration:
                        total_duration += content.estimated_duration
                estimated_duration = total_duration
            
            # Insert learning path
            self.db.execute_update("""
                INSERT INTO learning_paths (
                    path_id, title, description, target_skills, difficulty_level,
                    estimated_duration, content_sequence, prerequisites, learning_objectives
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                path_id,
                title,
                description,
                json.dumps(target_skills),
                difficulty_level,
                estimated_duration,
                json.dumps(content_sequence),
                json.dumps(prerequisites or []),
                json.dumps(learning_objectives or [])
            ))
            
            logger.info(f"Successfully created learning path: {path_id} - {title}")
            return path_id
            
        except Exception as e:
            logger.error(f"Failed to create learning path: {e}")
            raise
    
    def get_learning_path(self, path_id: str) -> Optional[LearningPath]:
        """
        Get learning path by ID.
        
        Args:
            path_id: Learning path ID
            
        Returns:
            LearningPath if found, None otherwise
        """
        try:
            results = self.db.execute_query("SELECT * FROM learning_paths WHERE path_id = ?", (path_id,))
            
            if not results:
                return None
            
            row = results[0]
            
            return LearningPath(
                path_id=row[0],
                title=row[1],
                description=row[2],
                target_skills=json.loads(row[3]) if row[3] else [],
                difficulty_level=row[4],
                estimated_duration=row[5],
                content_sequence=json.loads(row[6]) if row[6] else [],
                prerequisites=json.loads(row[7]) if row[7] else [],
                learning_objectives=json.loads(row[8]) if row[8] else [],
                created_at=datetime.fromisoformat(row[9]) if row[9] else None,
                updated_at=datetime.fromisoformat(row[10]) if row[10] else None
            )
            
        except Exception as e:
            logger.error(f"Failed to get learning path {path_id}: {e}")
            return None


# Global content manager instance
_content_manager: Optional[ContentManager] = None


def get_content_manager() -> ContentManager:
    """
    Get the global content manager instance.
    
    Returns:
        ContentManager: Global content manager instance
    """
    global _content_manager
    if _content_manager is None:
        _content_manager = ContentManager()
    return _content_manager


def initialize_content_manager(config_manager=None) -> ContentManager:
    """
    Initialize the global content manager.
    
    Args:
        config_manager: Configuration manager instance
        
    Returns:
        ContentManager: Initialized content manager instance
    """
    global _content_manager
    _content_manager = ContentManager(config_manager)
    return _content_manager


def reset_content_manager() -> None:
    """Reset the global content manager instance (useful for testing)."""
    global _content_manager
    _content_manager = None
