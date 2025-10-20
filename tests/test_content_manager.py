"""
Tests for content management utilities.

This module contains comprehensive tests for the content manager functionality,
including content storage, retrieval, search, and learning path management.
"""

import pytest
import json
from datetime import datetime, timezone
from unittest.mock import Mock, patch, MagicMock

# Import the modules to test
from backend.utils.content_manager import (
    ContentManager,
    ContentMetadata,
    ContentSearchResult,
    LearningPath,
    get_content_manager,
    initialize_content_manager,
    reset_content_manager
)


class TestContentMetadata:
    """Test ContentMetadata dataclass."""
    
    def test_content_metadata_creation(self):
        """Test ContentMetadata creation with all fields."""
        metadata = ContentMetadata(
            content_id="test_123",
            title="Test Content",
            content_type="document",
            category="programming",
            subcategory="python",
            difficulty_level="intermediate",
            estimated_duration=30,
            tags=["python", "programming"],
            skills_covered=["coding", "debugging"],
            prerequisites=["basic-python"],
            learning_objectives=["learn-python-basics"],
            author="Test Author",
            source_url="https://example.com",
            file_path="/path/to/file",
            file_hash="abc123",
            text_content="This is test content",
            embedding_id="embed_123"
        )
        
        assert metadata.content_id == "test_123"
        assert metadata.title == "Test Content"
        assert metadata.content_type == "document"
        assert metadata.category == "programming"
        assert metadata.subcategory == "python"
        assert metadata.difficulty_level == "intermediate"
        assert metadata.estimated_duration == 30
        assert metadata.tags == ["python", "programming"]
        assert metadata.skills_covered == ["coding", "debugging"]
        assert metadata.prerequisites == ["basic-python"]
        assert metadata.learning_objectives == ["learn-python-basics"]
        assert metadata.author == "Test Author"
        assert metadata.source_url == "https://example.com"
        assert metadata.file_path == "/path/to/file"
        assert metadata.file_hash == "abc123"
        assert metadata.text_content == "This is test content"
        assert metadata.embedding_id == "embed_123"
        assert isinstance(metadata.created_at, datetime)
        assert isinstance(metadata.updated_at, datetime)
    
    def test_content_metadata_defaults(self):
        """Test ContentMetadata with default values."""
        metadata = ContentMetadata(
            content_id="test_123",
            title="Test Content",
            content_type="document",
            category="programming"
        )
        
        assert metadata.subcategory is None
        assert metadata.difficulty_level == "beginner"
        assert metadata.estimated_duration is None
        assert metadata.tags == []
        assert metadata.skills_covered == []
        assert metadata.prerequisites == []
        assert metadata.learning_objectives == []
        assert metadata.author is None
        assert metadata.source_url is None
        assert metadata.file_path is None
        assert metadata.file_hash is None
        assert metadata.text_content is None
        assert metadata.embedding_id is None


class TestContentSearchResult:
    """Test ContentSearchResult dataclass."""
    
    def test_content_search_result_creation(self):
        """Test ContentSearchResult creation."""
        result = ContentSearchResult(
            content_id="test_123",
            title="Test Content",
            content_type="document",
            category="programming",
            difficulty_level="intermediate",
            relevance_score=0.95,
            text_snippet="This is a snippet...",
            skills_covered=["python", "programming"],
            estimated_duration=30
        )
        
        assert result.content_id == "test_123"
        assert result.title == "Test Content"
        assert result.content_type == "document"
        assert result.category == "programming"
        assert result.difficulty_level == "intermediate"
        assert result.relevance_score == 0.95
        assert result.text_snippet == "This is a snippet..."
        assert result.skills_covered == ["python", "programming"]
        assert result.estimated_duration == 30


class TestLearningPath:
    """Test LearningPath dataclass."""
    
    def test_learning_path_creation(self):
        """Test LearningPath creation."""
        path = LearningPath(
            path_id="path_123",
            title="Python Learning Path",
            description="Learn Python from basics to advanced",
            target_skills=["python", "programming"],
            difficulty_level="intermediate",
            estimated_duration=120,
            content_sequence=["content_1", "content_2", "content_3"],
            prerequisites=["basic-programming"],
            learning_objectives=["master-python"]
        )
        
        assert path.path_id == "path_123"
        assert path.title == "Python Learning Path"
        assert path.description == "Learn Python from basics to advanced"
        assert path.target_skills == ["python", "programming"]
        assert path.difficulty_level == "intermediate"
        assert path.estimated_duration == 120
        assert path.content_sequence == ["content_1", "content_2", "content_3"]
        assert path.prerequisites == ["basic-programming"]
        assert path.learning_objectives == ["master-python"]
        assert isinstance(path.created_at, datetime)
        assert isinstance(path.updated_at, datetime)


class TestContentManager:
    """Test ContentManager class."""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing."""
        config = Mock()
        config.get_settings.return_value = Mock(
            data_dir="/tmp/test_data"
        )
        return config
    
    @pytest.fixture
    def mock_db(self):
        """Mock database for testing."""
        db = Mock()
        db.execute.return_value = None
        db.commit.return_value = None
        db.rollback.return_value = None
        return db
    
    @pytest.fixture
    def mock_vector_store(self):
        """Mock vector store for testing."""
        vector_store = Mock()
        vector_store.add_documents.return_value = ["embed_123"]
        vector_store.similarity_search_with_score.return_value = [
            (Mock(metadata={'content_id': 'test_123'}), 0.1)
        ]
        return vector_store
    
    @pytest.fixture
    def mock_ai_client(self):
        """Mock AI client for testing."""
        ai_client = Mock()
        ai_client.generate_embeddings.return_value = Mock(
            embeddings=[[0.1, 0.2, 0.3]],
            error=None
        )
        return ai_client
    
    @pytest.fixture
    def content_manager(self, mock_config, mock_db, mock_vector_store, mock_ai_client):
        """Create ContentManager instance for testing."""
        with patch('backend.utils.content_manager.get_database', return_value=mock_db):
            with patch('backend.utils.content_manager.get_vector_store', return_value=mock_vector_store):
                with patch('backend.utils.content_manager.get_ai_client', return_value=mock_ai_client):
                    with patch('backend.utils.content_manager.get_config', return_value=mock_config):
                        with patch('pathlib.Path.mkdir'):
                            return ContentManager(mock_config)
    
    def test_content_manager_initialization(self, mock_config, mock_db, mock_vector_store, mock_ai_client):
        """Test ContentManager initialization."""
        with patch('backend.utils.content_manager.get_database', return_value=mock_db):
            with patch('backend.utils.content_manager.get_vector_store', return_value=mock_vector_store):
                with patch('backend.utils.content_manager.get_ai_client', return_value=mock_ai_client):
                    with patch('backend.utils.content_manager.get_config', return_value=mock_config):
                        with patch('pathlib.Path.mkdir'):
                            manager = ContentManager(mock_config)
                            
                            assert manager.config == mock_config
                            assert manager.db == mock_db
                            assert manager.vector_store == mock_vector_store
                            assert manager.ai_client == mock_ai_client
    
    def test_content_categories(self, content_manager):
        """Test content categories structure."""
        categories = content_manager.CONTENT_CATEGORIES
        
        assert 'programming' in categories
        assert 'data-science' in categories
        assert 'business' in categories
        assert 'design' in categories
        assert 'soft-skills' in categories
        
        # Check programming category structure
        programming = categories['programming']
        assert 'subcategories' in programming
        assert 'skills' in programming
        assert 'python' in programming['subcategories']
        assert 'coding' in programming['skills']
    
    def test_difficulty_levels(self, content_manager):
        """Test difficulty levels."""
        levels = content_manager.DIFFICULTY_LEVELS
        
        assert 'beginner' in levels
        assert 'intermediate' in levels
        assert 'advanced' in levels
        assert 'expert' in levels
    
    def test_generate_content_id(self, content_manager):
        """Test content ID generation."""
        content_id1 = content_manager.generate_content_id("Test Title", "document")
        content_id2 = content_manager.generate_content_id("Test Title", "document")
        
        # Should be different due to timestamp
        assert content_id1 != content_id2
        assert content_id1.startswith("document_")
        assert len(content_id1) == len("document_") + 12  # 12 char hash
    
    def test_add_content(self, content_manager, mock_db, mock_vector_store, mock_ai_client):
        """Test adding content to database."""
        # Mock database cursor
        mock_cursor = Mock()
        mock_db.execute.return_value = mock_cursor
        
        content_id = content_manager.add_content(
            title="Test Content",
            content_type="document",
            category="programming",
            text_content="This is test content",
            subcategory="python",
            difficulty_level="intermediate",
            estimated_duration=30,
            tags=["python", "programming"],
            skills_covered=["coding"],
            author="Test Author"
        )
        
        # Verify database calls
        assert mock_db.execute.called
        assert mock_db.commit.called
        
        # Verify vector store call
        mock_vector_store.add_documents.assert_called_once()
        
        # Verify AI client call
        mock_ai_client.generate_embeddings.assert_called_once_with("This is test content")
        
        # Verify content ID format
        assert content_id.startswith("document_")
    
    def test_add_content_embedding_error(self, content_manager, mock_db, mock_vector_store, mock_ai_client):
        """Test adding content when embedding generation fails."""
        # Mock embedding error
        mock_ai_client.generate_embeddings.return_value = Mock(
            embeddings=None,
            error="Embedding generation failed"
        )
        
        # Mock database cursor
        mock_cursor = Mock()
        mock_db.execute.return_value = mock_cursor
        
        content_id = content_manager.add_content(
            title="Test Content",
            content_type="document",
            category="programming",
            text_content="This is test content"
        )
        
        # Should still succeed but with no embedding
        assert content_id.startswith("document_")
        assert mock_db.execute.called
        assert mock_db.commit.called
    
    def test_get_content(self, content_manager, mock_db):
        """Test getting content by ID."""
        # Mock database response
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = (
            "test_123",  # content_id
            "Test Content",  # title
            "document",  # content_type
            "programming",  # category
            "python",  # subcategory
            "intermediate",  # difficulty_level
            30,  # estimated_duration
            '["python", "programming"]',  # tags
            '["coding"]',  # skills_covered
            '["basic-python"]',  # prerequisites
            '["learn-python"]',  # learning_objectives
            "2024-01-01T00:00:00+00:00",  # created_at
            "2024-01-01T00:00:00+00:00",  # updated_at
            "Test Author",  # author
            "https://example.com",  # source_url
            "/path/to/file",  # file_path
            "abc123",  # file_hash
            "This is test content",  # text_content
            "embed_123"  # embedding_id
        )
        mock_db.execute.return_value = mock_cursor
        
        content = content_manager.get_content("test_123")
        
        assert content is not None
        assert content.content_id == "test_123"
        assert content.title == "Test Content"
        assert content.category == "programming"
        assert content.tags == ["python", "programming"]
        assert content.skills_covered == ["coding"]
    
    def test_get_content_not_found(self, content_manager, mock_db):
        """Test getting content that doesn't exist."""
        # Mock database response
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = None
        mock_db.execute.return_value = mock_cursor
        
        content = content_manager.get_content("nonexistent")
        
        assert content is None
    
    def test_search_content(self, content_manager, mock_vector_store, mock_ai_client, mock_db):
        """Test content search functionality."""
        # Mock AI client response
        mock_ai_client.generate_embeddings.return_value = Mock(
            embeddings=[[0.1, 0.2, 0.3]],
            error=None
        )
        
        # Mock vector store response
        mock_doc = Mock()
        mock_doc.metadata = {'content_id': 'test_123'}
        mock_vector_store.similarity_search_with_score.return_value = [
            (mock_doc, 0.1)
        ]
        
        # Mock database response for get_content
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = (
            "test_123", "Test Content", "document", "programming", "python",
            "intermediate", 30, '["python"]', '["coding"]', '[]', '[]',
            "2024-01-01T00:00:00+00:00", "2024-01-01T00:00:00+00:00",
            "Test Author", None, None, None, "This is test content", "embed_123"
        )
        mock_db.execute.return_value = mock_cursor
        
        results = content_manager.search_content("python programming")
        
        assert len(results) == 1
        assert results[0].content_id == "test_123"
        assert results[0].title == "Test Content"
        assert results[0].relevance_score == 0.9  # 1.0 - 0.1
    
    def test_search_content_with_filters(self, content_manager, mock_vector_store, mock_ai_client, mock_db):
        """Test content search with filters."""
        # Mock AI client response
        mock_ai_client.generate_embeddings.return_value = Mock(
            embeddings=[[0.1, 0.2, 0.3]],
            error=None
        )
        
        # Mock vector store response
        mock_doc = Mock()
        mock_doc.metadata = {'content_id': 'test_123'}
        mock_vector_store.similarity_search_with_score.return_value = [
            (mock_doc, 0.1)
        ]
        
        # Mock database response for get_content
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = (
            "test_123", "Test Content", "document", "programming", "python",
            "intermediate", 30, '["python"]', '["coding"]', '[]', '[]',
            "2024-01-01T00:00:00+00:00", "2024-01-01T00:00:00+00:00",
            "Test Author", None, None, None, "This is test content", "embed_123"
        )
        mock_db.execute.return_value = mock_cursor
        
        results = content_manager.search_content(
            "python programming",
            category="programming",
            difficulty_level="intermediate",
            content_type="document"
        )
        
        assert len(results) == 1
        assert results[0].category == "programming"
        assert results[0].difficulty_level == "intermediate"
        assert results[0].content_type == "document"
    
    def test_get_content_by_category(self, content_manager, mock_db):
        """Test getting content by category."""
        # Mock database response
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            ("test_123", "Test Content 1", "document", "programming", "python",
             "intermediate", 30, '["python"]', '["coding"]', '[]', '[]',
             "2024-01-01T00:00:00+00:00", "2024-01-01T00:00:00+00:00",
             "Test Author", None, None, None, "Content 1", "embed_123"),
            ("test_456", "Test Content 2", "document", "programming", "java",
             "advanced", 45, '["java"]', '["coding"]', '[]', '[]',
             "2024-01-01T00:00:00+00:00", "2024-01-01T00:00:00+00:00",
             "Test Author", None, None, None, "Content 2", "embed_456")
        ]
        mock_db.execute.return_value = mock_cursor
        
        results = content_manager.get_content_by_category("programming", limit=10)
        
        assert len(results) == 2
        assert results[0].content_id == "test_123"
        assert results[1].content_id == "test_456"
        assert all(content.category == "programming" for content in results)
    
    def test_update_content(self, content_manager, mock_db):
        """Test updating content."""
        # Mock database cursor
        mock_cursor = Mock()
        mock_db.execute.return_value = mock_cursor
        
        success = content_manager.update_content(
            "test_123",
            title="Updated Title",
            tags=["updated", "tags"]
        )
        
        assert success is True
        assert mock_db.execute.called
        assert mock_db.commit.called
    
    def test_update_content_no_fields(self, content_manager, mock_db):
        """Test updating content with no fields."""
        success = content_manager.update_content("test_123")
        
        assert success is False
        assert not mock_db.execute.called
    
    def test_delete_content(self, content_manager, mock_db, mock_vector_store):
        """Test deleting content."""
        # Mock get_content to return existing content
        mock_content = Mock()
        mock_content.embedding_id = "embed_123"
        content_manager.get_content = Mock(return_value=mock_content)
        
        # Mock database cursor
        mock_cursor = Mock()
        mock_db.execute.return_value = mock_cursor
        
        success = content_manager.delete_content("test_123")
        
        assert success is True
        assert mock_db.execute.called
        assert mock_db.commit.called
        mock_vector_store.delete_documents.assert_called_once_with(["embed_123"])
    
    def test_delete_content_not_found(self, content_manager, mock_db):
        """Test deleting content that doesn't exist."""
        # Mock get_content to return None
        content_manager.get_content = Mock(return_value=None)
        
        success = content_manager.delete_content("nonexistent")
        
        assert success is False
        assert not mock_db.execute.called
    
    def test_get_content_statistics(self, content_manager, mock_db):
        """Test getting content statistics."""
        # Mock database responses
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = (10,)  # total content
        mock_cursor.fetchall.side_effect = [
            [("programming", 5), ("data-science", 3), ("business", 2)],  # by category
            [("intermediate", 4), ("beginner", 3), ("advanced", 3)],  # by difficulty
            [("document", 7), ("video", 2), ("article", 1)]  # by type
        ]
        mock_db.execute.return_value = mock_cursor
        
        stats = content_manager.get_content_statistics()
        
        assert stats['total_content'] == 10
        assert stats['by_category']['programming'] == 5
        assert stats['by_difficulty']['intermediate'] == 4
        assert stats['by_type']['document'] == 7
    
    def test_create_learning_path(self, content_manager, mock_db):
        """Test creating a learning path."""
        # Mock database cursor
        mock_cursor = Mock()
        mock_db.execute.return_value = mock_cursor
        
        path_id = content_manager.create_learning_path(
            title="Python Learning Path",
            description="Learn Python programming",
            target_skills=["python", "programming"],
            difficulty_level="intermediate",
            content_sequence=["content_1", "content_2"],
            estimated_duration=120
        )
        
        assert path_id.startswith("path_")
        assert mock_db.execute.called
        assert mock_db.commit.called
    
    def test_get_learning_path(self, content_manager, mock_db):
        """Test getting a learning path."""
        # Mock database response
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = (
            "path_123",  # path_id
            "Python Learning Path",  # title
            "Learn Python programming",  # description
            '["python", "programming"]',  # target_skills
            "intermediate",  # difficulty_level
            120,  # estimated_duration
            '["content_1", "content_2"]',  # content_sequence
            '["basic-programming"]',  # prerequisites
            '["master-python"]',  # learning_objectives
            "2024-01-01T00:00:00+00:00",  # created_at
            "2024-01-01T00:00:00+00:00"  # updated_at
        )
        mock_db.execute.return_value = mock_cursor
        
        path = content_manager.get_learning_path("path_123")
        
        assert path is not None
        assert path.path_id == "path_123"
        assert path.title == "Python Learning Path"
        assert path.target_skills == ["python", "programming"]
        assert path.content_sequence == ["content_1", "content_2"]


class TestGlobalFunctions:
    """Test global utility functions."""
    
    def test_get_content_manager(self):
        """Test getting global content manager instance."""
        # Reset global instance
        reset_content_manager()
        
        manager1 = get_content_manager()
        manager2 = get_content_manager()
        
        # Should return the same instance
        assert manager1 is manager2
        assert isinstance(manager1, ContentManager)
    
    def test_initialize_content_manager(self):
        """Test initializing content manager with config."""
        mock_config = Mock()
        
        with patch('backend.utils.content_manager.get_database'):
            with patch('backend.utils.content_manager.get_vector_store'):
                with patch('backend.utils.content_manager.get_ai_client'):
                    with patch('backend.utils.content_manager.get_config', return_value=mock_config):
                        with patch('pathlib.Path.mkdir'):
                            manager = initialize_content_manager(mock_config)
                            
                            assert isinstance(manager, ContentManager)
                            assert manager.config == mock_config
    
    def test_reset_content_manager(self):
        """Test resetting content manager."""
        # Get initial instance
        manager1 = get_content_manager()
        
        # Reset
        reset_content_manager()
        
        # Get new instance
        manager2 = get_content_manager()
        
        # Should be different instances
        assert manager1 is not manager2


if __name__ == "__main__":
    pytest.main([__file__])
