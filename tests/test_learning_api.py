"""
Comprehensive tests for the Learning API endpoints.

This module tests all learning-related API endpoints including
learning path generation, content management, and progress tracking.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from datetime import datetime, timezone

# Import the modules to test
from backend.main import app
from backend.api.learning import router
from backend.services.learning_engine import (
    LearningEngine, PersonalizedLearningPath, LearningRecommendation
)
from backend.models.learning import LearningContentCreate, ContentType, DifficultyLevel
from backend.models.skills import SkillGap
from backend.models.user import SkillLevel


class TestLearningAPI:
    """Test cases for Learning API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def mock_learning_engine(self):
        """Mock learning engine."""
        with patch('backend.api.learning.get_learning_engine') as mock:
            mock_engine = Mock(spec=LearningEngine)
            mock.return_value = mock_engine
            yield mock_engine
    
    @pytest.fixture
    def mock_skills_engine(self):
        """Mock skills engine."""
        with patch('backend.api.learning.get_skills_engine') as mock:
            mock_engine = Mock()
            mock.return_value = mock_engine
            yield mock_engine
    
    @pytest.fixture
    def mock_user_service(self):
        """Mock user service."""
        with patch('backend.api.learning.get_user_service') as mock:
            mock_service = Mock()
            mock.return_value = mock_service
            yield mock_service
    
    @pytest.fixture
    def sample_learning_path(self):
        """Create sample learning path for testing."""
        recommendations = [
            LearningRecommendation(
                content_id="content_1",
                title="React Native Fundamentals",
                content_type="tutorial",
                difficulty="beginner",
                estimated_duration=15,
                skills_covered=["React Native", "Mobile Development"],
                priority_score=8.5,
                reasoning="Essential for mobile app development",
                prerequisites=["JavaScript", "React"],
                learning_objectives=["Learn React Native basics", "Build a simple app"]
            ),
            LearningRecommendation(
                content_id="content_2",
                title="User Research Methods",
                content_type="article",
                difficulty="intermediate",
                estimated_duration=12,
                skills_covered=["User Research", "Product Management"],
                priority_score=7.0,
                reasoning="Important for product decisions",
                prerequisites=["Basic PM knowledge"],
                learning_objectives=["Learn research methods", "Apply to product decisions"]
            )
        ]
        
        return PersonalizedLearningPath(
            path_id="test_path_123",
            title="Personalized Learning Path for Product Manager",
            description="Customized learning journey to address 2 skill gaps",
            target_skills=["React Native", "User Research"],
            difficulty="intermediate",
            estimated_duration=27,
            content_sequence=recommendations,
            prerequisites=[],
            learning_objectives=[
                "Improve React Native from beginner to intermediate",
                "Improve User Research from intermediate to advanced"
            ],
            priority_order=["React Native", "User Research"],
            success_metrics={
                "target_skills_improved": 2,
                "estimated_completion_time": "27 minutes",
                "learning_modules": 2,
                "difficulty_distribution": {"beginner": 1, "intermediate": 1, "advanced": 0, "expert": 0}
            },
            created_at=datetime.now(timezone.utc)
        )
    
    def test_health_check(self, client):
        """Test learning service health check."""
        with patch('backend.api.learning.get_learning_engine') as mock:
            mock_engine = Mock()
            mock.return_value = mock_engine
            
            response = client.get("/api/learning/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["service"] == "learning_engine"
            assert "operational" in data["message"]
    
    def test_health_check_failure(self, client):
        """Test learning service health check failure."""
        with patch('backend.api.learning.get_learning_engine') as mock:
            mock.side_effect = Exception("Service unavailable")
            
            response = client.get("/api/learning/health")
            
            assert response.status_code == 500
            data = response.json()
            assert "unavailable" in data["detail"]
    
    def test_generate_learning_path_success(self, client, mock_learning_engine, sample_learning_path):
        """Test successful learning path generation."""
        # Setup mocks
        mock_learning_engine.generate_personalized_learning_path.return_value = sample_learning_path
        
        # Test request
        request_data = {
            "user_id": "test_user_123",
            "max_duration_hours": 2,
            "preferred_difficulty": "intermediate"
        }
        
        response = client.post("/api/learning/generate-path", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["learning_path"] is not None
        assert data["learning_path"]["path_id"] == "test_path_123"
        assert data["learning_path"]["title"] == "Personalized Learning Path for Product Manager"
        assert data["learning_path"]["estimated_duration"] == 27
        assert len(data["learning_path"]["content_sequence"]) == 2
        assert "2 modules" in data["message"]
        
        # Verify mock was called correctly
        mock_learning_engine.generate_personalized_learning_path.assert_called_once_with(
            user_id="test_user_123",
            skill_gaps=None,
            max_duration_hours=2,
            preferred_difficulty="intermediate"
        )
    
    def test_generate_learning_path_with_skill_gaps(self, client, mock_learning_engine, mock_skills_engine, sample_learning_path):
        """Test learning path generation with specific skill gaps."""
        # Setup mocks
        mock_learning_engine.generate_personalized_learning_path.return_value = sample_learning_path
        
        # Create mock skill gap
        mock_skill_gap = Mock()
        mock_skill_gap.id = "gap_1"
        mock_skill_gap.skill_name = "React Native"
        mock_skills_engine.get_skill_gap.return_value = mock_skill_gap
        
        # Test request with skill gap IDs
        request_data = {
            "user_id": "test_user_123",
            "skill_gap_ids": ["gap_1", "gap_2"]
        }
        
        response = client.post("/api/learning/generate-path", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        # Verify skill gap retrieval was called
        mock_skills_engine.get_skill_gap.assert_called()
    
    def test_generate_learning_path_failure(self, client, mock_learning_engine):
        """Test learning path generation failure."""
        # Setup mock to raise exception
        mock_learning_engine.generate_personalized_learning_path.side_effect = Exception("Generation failed")
        
        request_data = {
            "user_id": "test_user_123"
        }
        
        response = client.post("/api/learning/generate-path", json=request_data)
        
        assert response.status_code == 500
        data = response.json()
        assert "Failed to generate learning path" in data["detail"]
    
    def test_get_learning_path_success(self, client, mock_learning_engine, sample_learning_path):
        """Test getting a specific learning path."""
        # Setup mocks
        mock_learning_engine.get_learning_path.return_value = sample_learning_path
        
        response = client.get("/api/learning/path/test_path_123")
        
        assert response.status_code == 200
        data = response.json()
        assert data["path_id"] == "test_path_123"
        assert data["title"] == "Personalized Learning Path for Product Manager"
        assert data["estimated_duration"] == 27
        assert len(data["content_sequence"]) == 2
        
        # Verify mock was called correctly
        mock_learning_engine.get_learning_path.assert_called_once_with("test_path_123")
    
    def test_get_learning_path_not_found(self, client, mock_learning_engine):
        """Test getting a non-existent learning path."""
        # Setup mocks
        mock_learning_engine.get_learning_path.return_value = None
        
        response = client.get("/api/learning/path/nonexistent_path")
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]
    
    def test_get_learning_path_failure(self, client, mock_learning_engine):
        """Test getting learning path with error."""
        # Setup mock to raise exception
        mock_learning_engine.get_learning_path.side_effect = Exception("Database error")
        
        response = client.get("/api/learning/path/test_path_123")
        
        assert response.status_code == 500
        data = response.json()
        assert "Failed to get learning path" in data["detail"]
    
    def test_get_user_learning_paths_success(self, client, mock_learning_engine, sample_learning_path):
        """Test getting all learning paths for a user."""
        # Setup mocks
        mock_learning_engine.get_user_learning_paths.return_value = [sample_learning_path]
        
        response = client.get("/api/learning/user/test_user_123/paths")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["learning_paths"]) == 1
        assert data["learning_paths"][0]["path_id"] == "test_path_123"
        assert data["total_count"] == 1
        assert "Found 1 learning paths" in data["message"]
        
        # Verify mock was called correctly
        mock_learning_engine.get_user_learning_paths.assert_called_once_with("test_user_123")
    
    def test_get_user_learning_paths_failure(self, client, mock_learning_engine):
        """Test getting user learning paths with error."""
        # Setup mock to raise exception
        mock_learning_engine.get_user_learning_paths.side_effect = Exception("Database error")
        
        response = client.get("/api/learning/user/test_user_123/paths")
        
        assert response.status_code == 500
        data = response.json()
        assert "Failed to get learning paths" in data["detail"]
    
    def test_get_content_recommendations_success(self, client, mock_learning_engine):
        """Test getting content recommendations."""
        # Setup mocks
        mock_content = [
            {
                'id': 'content_1',
                'title': 'React Native Basics',
                'content_type': 'tutorial',
                'difficulty': 'beginner',
                'estimated_duration': 15,
                'skills_covered': ['React Native', 'Mobile Development'],
                'prerequisites': ['JavaScript'],
                'learning_objectives': ['Learn React Native basics'],
                'reasoning': 'Essential for mobile development'
            }
        ]
        mock_learning_engine._search_existing_content.return_value = mock_content
        
        response = client.get("/api/learning/content/recommendations?skill_name=React Native&difficulty=beginner&limit=5")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["recommendations"]) == 1
        assert data["recommendations"][0]["content_id"] == "content_1"
        assert data["recommendations"][0]["title"] == "React Native Basics"
        assert data["total_count"] == 1
        assert "Found 1 content recommendations" in data["message"]
        
        # Verify mock was called correctly
        mock_learning_engine._search_existing_content.assert_called_once_with("React Native", "beginner")
    
    def test_get_content_recommendations_failure(self, client, mock_learning_engine):
        """Test getting content recommendations with error."""
        # Setup mock to raise exception
        mock_learning_engine._search_existing_content.side_effect = Exception("Search error")
        
        response = client.get("/api/learning/content/recommendations?skill_name=React Native")
        
        assert response.status_code == 500
        data = response.json()
        assert "Failed to get content recommendations" in data["detail"]
    
    def test_get_learning_content_success(self, client, mock_learning_engine):
        """Test getting specific learning content."""
        # Setup mocks
        mock_recommendation = LearningRecommendation(
            content_id="content_1",
            title="React Native Fundamentals",
            content_type="tutorial",
            difficulty="beginner",
            estimated_duration=15,
            skills_covered=["React Native"],
            priority_score=8.0,
            reasoning="Essential learning content",
            prerequisites=["JavaScript"],
            learning_objectives=["Learn React Native basics"]
        )
        mock_learning_engine._get_content_recommendation.return_value = mock_recommendation
        
        response = client.get("/api/learning/content/content_1")
        
        assert response.status_code == 200
        data = response.json()
        assert data["content_id"] == "content_1"
        assert data["title"] == "React Native Fundamentals"
        assert data["content_type"] == "tutorial"
        assert data["difficulty"] == "beginner"
        assert data["estimated_duration"] == 15
        assert data["skills_covered"] == ["React Native"]
        
        # Verify mock was called correctly
        mock_learning_engine._get_content_recommendation.assert_called_once_with("content_1")
    
    def test_get_learning_content_not_found(self, client, mock_learning_engine):
        """Test getting non-existent learning content."""
        # Setup mocks
        mock_learning_engine._get_content_recommendation.return_value = None
        
        response = client.get("/api/learning/content/nonexistent_content")
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]
    
    def test_get_learning_content_failure(self, client, mock_learning_engine):
        """Test getting learning content with error."""
        # Setup mock to raise exception
        mock_learning_engine._get_content_recommendation.side_effect = Exception("Database error")
        
        response = client.get("/api/learning/content/content_1")
        
        assert response.status_code == 500
        data = response.json()
        assert "Failed to get learning content" in data["detail"]
    
    def test_create_learning_content_success(self, client, mock_learning_engine):
        """Test creating new learning content."""
        # Setup mocks
        mock_learning_engine._store_generated_content.return_value = None
        
        content_data = {
            "title": "New Learning Content",
            "description": "A new piece of learning content",
            "content_type": "tutorial",
            "difficulty": "intermediate",
            "estimated_duration": 20,
            "skills_covered": ["React Native", "Mobile Development"],
            "prerequisites": ["JavaScript"],
            "learning_objectives": ["Learn advanced React Native", "Build complex apps"],
            "content_text": "This is the content text...",
            "tags": ["mobile", "react", "development"]
        }
        
        response = client.post("/api/learning/content", json=content_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["content_id"] is not None
        assert "created successfully" in data["message"]
        
        # Verify mock was called correctly
        mock_learning_engine._store_generated_content.assert_called_once()
        call_args = mock_learning_engine._store_generated_content.call_args[0][0]
        assert call_args["title"] == "New Learning Content"
        assert call_args["content_type"] == "tutorial"
        assert call_args["difficulty"] == "intermediate"
    
    def test_create_learning_content_failure(self, client, mock_learning_engine):
        """Test creating learning content with error."""
        # Setup mock to raise exception
        mock_learning_engine._store_generated_content.side_effect = Exception("Storage error")
        
        content_data = {
            "title": "New Learning Content",
            "content_type": "tutorial",
            "difficulty": "intermediate"
        }
        
        response = client.post("/api/learning/content", json=content_data)
        
        assert response.status_code == 500
        data = response.json()
        assert "Failed to create learning content" in data["detail"]
    
    def test_get_content_categories_success(self, client, mock_learning_engine):
        """Test getting content categories."""
        # Setup mocks
        mock_learning_engine.content_categories = {
            "product_management": ["user_research", "product_strategy"],
            "technical_skills": ["programming", "database_design"]
        }
        mock_learning_engine.micro_learning_duration = {
            "quick_tip": 5,
            "tutorial": 15
        }
        
        response = client.get("/api/learning/categories")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "product_management" in data["content_categories"]
        assert "technical_skills" in data["content_categories"]
        assert "quick_tip" in data["micro_learning_duration"]
        assert "retrieved successfully" in data["message"]
    
    def test_get_content_categories_failure(self, client, mock_learning_engine):
        """Test getting content categories with error."""
        # Setup mock to raise exception
        mock_learning_engine.content_categories = None  # This will cause an error
        
        response = client.get("/api/learning/categories")
        
        assert response.status_code == 500
        data = response.json()
        assert "Failed to get content categories" in data["detail"]
    
    def test_get_learning_stats_success(self, client, mock_learning_engine):
        """Test getting learning system statistics."""
        # Setup mocks
        mock_db = Mock()
        mock_db.execute_query.side_effect = [
            [(5,)],  # learning paths count
            [(12,)],  # learning content count
            [(3,)],  # beginner count
            [(4,)],  # intermediate count
            [(3,)],  # advanced count
            [(2,)],  # expert count
            [(2,)],  # article count
            [(3,)],  # video count
            [(2,)],  # exercise count
            [(1,)],  # quiz count
            [(2,)],  # tutorial count
            [(2,)]   # course count
        ]
        mock_learning_engine.db = mock_db
        mock_learning_engine.micro_learning_duration = {"tutorial": 15}
        
        response = client.get("/api/learning/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["statistics"]["total_learning_paths"] == 5
        assert data["statistics"]["total_learning_content"] == 12
        assert data["statistics"]["difficulty_distribution"]["beginner"] == 3
        assert data["statistics"]["content_type_distribution"]["article"] == 2
        assert "retrieved successfully" in data["message"]
    
    def test_get_learning_stats_failure(self, client, mock_learning_engine):
        """Test getting learning statistics with error."""
        # Setup mock to raise exception
        mock_learning_engine.db = None  # This will cause an error
        
        response = client.get("/api/learning/stats")
        
        assert response.status_code == 500
        data = response.json()
        assert "Failed to get learning statistics" in data["detail"]
    
    def test_generate_learning_path_validation(self, client):
        """Test learning path generation request validation."""
        # Test missing user_id
        request_data = {
            "max_duration_hours": 2
        }
        
        response = client.post("/api/learning/generate-path", json=request_data)
        
        assert response.status_code == 422  # Validation error
    
    def test_content_recommendations_query_parameters(self, client, mock_learning_engine):
        """Test content recommendations with various query parameters."""
        # Setup mocks
        mock_learning_engine._search_existing_content.return_value = []
        
        # Test with all parameters
        response = client.get("/api/learning/content/recommendations?skill_name=React Native&difficulty=intermediate&limit=20")
        
        assert response.status_code == 200
        mock_learning_engine._search_existing_content.assert_called_with("React Native", "intermediate")
        
        # Test with minimal parameters
        response = client.get("/api/learning/content/recommendations?skill_name=JavaScript")
        
        assert response.status_code == 200
        mock_learning_engine._search_existing_content.assert_called_with("JavaScript", "beginner")
    
    def test_content_recommendations_limit_validation(self, client):
        """Test content recommendations limit validation."""
        # Test limit too high
        response = client.get("/api/learning/content/recommendations?skill_name=React Native&limit=100")
        
        assert response.status_code == 422  # Validation error
        
        # Test limit too low
        response = client.get("/api/learning/content/recommendations?skill_name=React Native&limit=0")
        
        assert response.status_code == 422  # Validation error


if __name__ == "__main__":
    pytest.main([__file__])
