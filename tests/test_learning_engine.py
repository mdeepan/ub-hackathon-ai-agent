"""
Comprehensive tests for the Learning Engine.

This module tests the learning path generation, content recommendation,
and personalized learning experiences functionality.
"""

import pytest
import json
import uuid
from datetime import datetime, timezone
from unittest.mock import Mock, patch, MagicMock

# Import the modules to test
from backend.services.learning_engine import (
    LearningEngine, LearningRecommendation, PersonalizedLearningPath,
    get_learning_engine
)
from backend.models.learning import LearningContent, LearningPath, ContentType, DifficultyLevel
from backend.models.skills import SkillGap
from backend.models.user import UserProfile, UserContext, UserPreferences, SkillLevel


class TestLearningEngine:
    """Test cases for the Learning Engine."""
    
    @pytest.fixture
    def mock_dependencies(self):
        """Mock all external dependencies."""
        with patch('backend.services.learning_engine.get_database') as mock_db, \
             patch('backend.services.learning_engine.get_vector_store') as mock_vector, \
             patch('backend.services.learning_engine.get_ai_client') as mock_ai, \
             patch('backend.services.learning_engine.get_config') as mock_config, \
             patch('backend.services.learning_engine.SkillsEngine') as mock_skills_engine, \
             patch('backend.services.learning_engine.UserService') as mock_user_service:
            
            # Setup mock database
            mock_db_instance = Mock()
            mock_db_instance.execute_query.return_value = []
            mock_db_instance.execute_update.return_value = None
            mock_db.return_value = mock_db_instance
            
            # Setup mock AI client
            mock_ai_instance = Mock()
            mock_ai_instance.generate_response.return_value = json.dumps({
                "title": "Test Learning Content",
                "learning_objectives": ["Learn test concepts", "Apply test knowledge"],
                "content_structure": ["Introduction", "Main concepts", "Practice"],
                "practical_exercises": ["Exercise 1", "Exercise 2"],
                "key_takeaways": ["Key point 1", "Key point 2"],
                "prerequisites": []
            })
            mock_ai.return_value = mock_ai_instance
            
            # Setup mock skills engine
            mock_skills_instance = Mock()
            mock_skills_instance.get_user_skill_gaps.return_value = []
            mock_skills_engine.return_value = mock_skills_instance
            
            # Setup mock user service
            mock_user_instance = Mock()
            mock_user_instance.get_user_profile.return_value = None
            mock_user_service.return_value = mock_user_instance
            
            yield {
                'db': mock_db_instance,
                'ai': mock_ai_instance,
                'skills_engine': mock_skills_instance,
                'user_service': mock_user_instance
            }
    
    @pytest.fixture
    def sample_user_profile(self):
        """Create a sample user profile for testing."""
        return UserProfile(
            id="test_user_123",
            username="testuser",
            email="test@example.com",
            current_role="Product Manager",
            years_of_experience=3,
            industry="Technology",
            team_size=5,
            current_projects=[
                Mock(name="Mobile App Project"),
                Mock(name="Data Analytics Initiative")
            ],
            skills=[],
            preferences=UserPreferences(),
            context=UserContext(user_id="test_user_123")
        )
    
    @pytest.fixture
    def sample_skill_gaps(self):
        """Create sample skill gaps for testing."""
        return [
            SkillGap(
                id="gap_1",
                user_id="test_user_123",
                skill_name="React Native",
                current_level=SkillLevel.BEGINNER,
                target_level=SkillLevel.INTERMEDIATE,
                gap_size=2.0,
                category="technical_skills",
                priority_score=8.5,
                created_at=datetime.now(timezone.utc)
            ),
            SkillGap(
                id="gap_2",
                user_id="test_user_123",
                skill_name="User Research",
                current_level=SkillLevel.INTERMEDIATE,
                target_level=SkillLevel.ADVANCED,
                gap_size=1.5,
                category="product_management",
                priority_score=7.0,
                created_at=datetime.now(timezone.utc)
            )
        ]
    
    def test_learning_engine_initialization(self, mock_dependencies):
        """Test learning engine initialization."""
        engine = LearningEngine()
        
        assert engine is not None
        assert engine.content_categories is not None
        assert "product_management" in engine.content_categories
        assert "technical_skills" in engine.content_categories
        assert "soft_skills" in engine.content_categories
        assert engine.micro_learning_duration is not None
        assert "quick_tip" in engine.micro_learning_duration
    
    def test_generate_personalized_learning_path_with_skill_gaps(
        self, mock_dependencies, sample_user_profile, sample_skill_gaps
    ):
        """Test learning path generation with skill gaps."""
        # Setup mocks
        mock_dependencies['user_service'].get_user_profile.return_value = sample_user_profile
        mock_dependencies['skills_engine'].get_user_skill_gaps.return_value = sample_skill_gaps
        
        # Mock database queries for content search
        mock_dependencies['db'].execute_query.return_value = []
        
        engine = LearningEngine()
        
        # Generate learning path
        learning_path = engine.generate_personalized_learning_path("test_user_123")
        
        assert learning_path is not None
        assert learning_path.path_id is not None
        assert learning_path.title is not None
        assert learning_path.target_skills is not None
        assert len(learning_path.target_skills) > 0
        assert learning_path.content_sequence is not None
        assert learning_path.estimated_duration > 0
        assert learning_path.created_at is not None
    
    def test_generate_personalized_learning_path_no_skill_gaps(
        self, mock_dependencies, sample_user_profile
    ):
        """Test learning path generation when no skill gaps exist."""
        # Setup mocks
        mock_dependencies['user_service'].get_user_profile.return_value = sample_user_profile
        mock_dependencies['skills_engine'].get_user_skill_gaps.return_value = []
        
        engine = LearningEngine()
        
        # Generate learning path
        learning_path = engine.generate_personalized_learning_path("test_user_123")
        
        assert learning_path is not None
        assert learning_path.path_id is not None
        assert "Introduction" in learning_path.title or "Fundamentals" in learning_path.title
        assert learning_path.content_sequence is not None
        assert len(learning_path.content_sequence) > 0
    
    def test_generate_personalized_learning_path_user_not_found(self, mock_dependencies):
        """Test learning path generation when user is not found."""
        # Setup mocks
        mock_dependencies['user_service'].get_user_profile.return_value = None
        
        engine = LearningEngine()
        
        # Should raise ValueError
        with pytest.raises(ValueError, match="User profile not found"):
            engine.generate_personalized_learning_path("nonexistent_user")
    
    def test_prioritize_skill_gaps(self, mock_dependencies, sample_user_profile, sample_skill_gaps):
        """Test skill gap prioritization."""
        # Setup mocks
        mock_dependencies['ai'].generate_response.return_value = json.dumps([
            "User Research", "React Native"
        ])
        
        engine = LearningEngine()
        
        # Test prioritization
        prioritized_gaps = engine._prioritize_skill_gaps(sample_skill_gaps, sample_user_profile)
        
        assert prioritized_gaps is not None
        assert len(prioritized_gaps) == len(sample_skill_gaps)
        assert prioritized_gaps[0].skill_name == "User Research"
        assert prioritized_gaps[1].skill_name == "React Native"
    
    def test_prioritize_skill_gaps_ai_failure(self, mock_dependencies, sample_user_profile, sample_skill_gaps):
        """Test skill gap prioritization when AI fails."""
        # Setup mocks to simulate AI failure
        mock_dependencies['ai'].generate_response.side_effect = Exception("AI service unavailable")
        
        engine = LearningEngine()
        
        # Should fallback to gap size priority
        prioritized_gaps = engine._prioritize_skill_gaps(sample_skill_gaps, sample_user_profile)
        
        assert prioritized_gaps is not None
        assert len(prioritized_gaps) == len(sample_skill_gaps)
        # Should be sorted by gap size (descending)
        assert prioritized_gaps[0].gap_size >= prioritized_gaps[1].gap_size
    
    def test_get_content_for_skill_gap(self, mock_dependencies, sample_user_profile, sample_skill_gaps):
        """Test content retrieval for a specific skill gap."""
        # Setup mocks
        mock_dependencies['db'].execute_query.return_value = []
        mock_dependencies['ai'].generate_response.return_value = json.dumps({
            "title": "React Native Fundamentals",
            "learning_objectives": ["Learn React Native basics", "Build a simple app"],
            "content_structure": ["Introduction", "Components", "Navigation"],
            "practical_exercises": ["Create a component", "Add navigation"],
            "key_takeaways": ["React Native is powerful", "Cross-platform development"],
            "prerequisites": ["JavaScript", "React"]
        })
        
        engine = LearningEngine()
        
        # Test content generation
        recommendations = engine._get_content_for_skill_gap(
            sample_skill_gaps[0], sample_user_profile, "intermediate"
        )
        
        assert recommendations is not None
        assert len(recommendations) > 0
        assert recommendations[0].content_id is not None
        assert recommendations[0].title is not None
        assert recommendations[0].skills_covered is not None
        assert "React Native" in recommendations[0].skills_covered
    
    def test_search_existing_content(self, mock_dependencies):
        """Test searching for existing content."""
        # Setup mock database response
        mock_dependencies['db'].execute_query.return_value = [
            (
                "content_1", "React Native Basics", "Learn React Native", "tutorial",
                "beginner", 15, '["React Native", "Mobile Development"]',
                '["JavaScript"]', '["Learn basics", "Build app"]',
                None, "https://example.com", None, "content_text_here", None
            )
        ]
        
        engine = LearningEngine()
        
        # Test content search
        content_list = engine._search_existing_content("React Native", "beginner")
        
        assert content_list is not None
        assert len(content_list) == 1
        assert content_list[0]['id'] == "content_1"
        assert content_list[0]['title'] == "React Native Basics"
        assert content_list[0]['skills_covered'] == ["React Native", "Mobile Development"]
    
    def test_generate_micro_learning_content(self, mock_dependencies, sample_user_profile, sample_skill_gaps):
        """Test micro-learning content generation."""
        # Setup mocks
        mock_dependencies['ai'].generate_response.return_value = json.dumps({
            "title": "React Native Components",
            "learning_objectives": ["Understand components", "Create custom components"],
            "content_structure": ["What are components", "Component lifecycle", "Best practices"],
            "practical_exercises": ["Create a button component", "Style the component"],
            "key_takeaways": ["Components are reusable", "Props make components flexible"],
            "prerequisites": ["JavaScript basics"]
        })
        
        engine = LearningEngine()
        
        # Test content generation
        content_list = engine._generate_micro_learning_content(
            sample_skill_gaps[0], sample_user_profile, "intermediate"
        )
        
        assert content_list is not None
        assert len(content_list) == 1
        content = content_list[0]
        assert content['id'] is not None
        assert content['title'] == "React Native Components"
        assert content['content_type'] in engine.micro_learning_duration
        assert content['estimated_duration'] > 0
        assert content['skills_covered'] == ["React Native"]
    
    def test_select_content_type(self, mock_dependencies):
        """Test content type selection."""
        engine = LearningEngine()
        
        # Test various skill mappings
        assert engine._select_content_type("programming", "beginner") == "tutorial"
        assert engine._select_content_type("data_analysis", "intermediate") == "practical_exercise"
        assert engine._select_content_type("user_research", "advanced") == "case_study"
        assert engine._select_content_type("unknown_skill", "beginner") == "concept_explanation"
    
    def test_determine_difficulty_level(self, mock_dependencies):
        """Test difficulty level determination."""
        engine = LearningEngine()
        
        # Test various level combinations
        assert engine._determine_difficulty_level("beginner", "intermediate") == "intermediate"
        assert engine._determine_difficulty_level("beginner", "advanced") == "advanced"
        assert engine._determine_difficulty_level("intermediate", "advanced") == "intermediate"
        assert engine._determine_difficulty_level("advanced", "expert") == "beginner"
    
    def test_calculate_priority_score(self, mock_dependencies, sample_user_profile, sample_skill_gaps):
        """Test priority score calculation."""
        engine = LearningEngine()
        
        content = {
            'estimated_duration': 10,
            'difficulty': 'intermediate',
            'content_type': 'tutorial'
        }
        
        score = engine._calculate_priority_score(content, sample_skill_gaps[0], sample_user_profile)
        
        assert score > 0
        assert isinstance(score, float)
    
    def test_create_personalized_path(self, mock_dependencies, sample_user_profile, sample_skill_gaps):
        """Test personalized path creation."""
        engine = LearningEngine()
        
        # Create sample recommendations
        recommendations = [
            LearningRecommendation(
                content_id="rec_1",
                title="Test Content 1",
                content_type="tutorial",
                difficulty="beginner",
                estimated_duration=15,
                skills_covered=["React Native"],
                priority_score=8.0,
                reasoning="Test reasoning",
                prerequisites=[],
                learning_objectives=["Learn basics"]
            )
        ]
        
        # Test path creation
        learning_path = engine._create_personalized_path(
            "test_user_123", sample_user_profile, sample_skill_gaps, recommendations
        )
        
        assert learning_path is not None
        assert learning_path.path_id is not None
        assert learning_path.title is not None
        assert learning_path.target_skills is not None
        assert learning_path.content_sequence == recommendations
        assert learning_path.estimated_duration == 15
        assert learning_path.success_metrics is not None
    
    def test_calculate_difficulty_distribution(self, mock_dependencies):
        """Test difficulty distribution calculation."""
        engine = LearningEngine()
        
        recommendations = [
            LearningRecommendation(
                content_id="rec_1", title="Test 1", content_type="tutorial",
                difficulty="beginner", estimated_duration=10, skills_covered=[],
                priority_score=8.0, reasoning="", prerequisites=[], learning_objectives=[]
            ),
            LearningRecommendation(
                content_id="rec_2", title="Test 2", content_type="tutorial",
                difficulty="intermediate", estimated_duration=15, skills_covered=[],
                priority_score=7.0, reasoning="", prerequisites=[], learning_objectives=[]
            ),
            LearningRecommendation(
                content_id="rec_3", title="Test 3", content_type="tutorial",
                difficulty="beginner", estimated_duration=12, skills_covered=[],
                priority_score=6.0, reasoning="", prerequisites=[], learning_objectives=[]
            )
        ]
        
        distribution = engine._calculate_difficulty_distribution(recommendations)
        
        assert distribution["beginner"] == 2
        assert distribution["intermediate"] == 1
        assert distribution["advanced"] == 0
        assert distribution["expert"] == 0
    
    def test_determine_overall_difficulty(self, mock_dependencies):
        """Test overall difficulty determination."""
        engine = LearningEngine()
        
        # Test with beginner content
        beginner_recs = [
            LearningRecommendation(
                content_id="rec_1", title="Test 1", content_type="tutorial",
                difficulty="beginner", estimated_duration=10, skills_covered=[],
                priority_score=8.0, reasoning="", prerequisites=[], learning_objectives=[]
            )
        ]
        assert engine._determine_overall_difficulty(beginner_recs) == "beginner"
        
        # Test with mixed content
        mixed_recs = [
            LearningRecommendation(
                content_id="rec_1", title="Test 1", content_type="tutorial",
                difficulty="beginner", estimated_duration=10, skills_covered=[],
                priority_score=8.0, reasoning="", prerequisites=[], learning_objectives=[]
            ),
            LearningRecommendation(
                content_id="rec_2", title="Test 2", content_type="tutorial",
                difficulty="intermediate", estimated_duration=15, skills_covered=[],
                priority_score=7.0, reasoning="", prerequisites=[], learning_objectives=[]
            )
        ]
        assert engine._determine_overall_difficulty(mixed_recs) == "intermediate"
    
    def test_get_learning_path(self, mock_dependencies):
        """Test getting a learning path by ID."""
        # Setup mock database response
        mock_dependencies['db'].execute_query.side_effect = [
            [("path_1", "Test Path", "Test Description", '["React Native"]', "intermediate", 30, '["content_1"]', '[]', '["Learn React Native"]', '["React Native"]', "true", "2024-01-01T00:00:00", "2024-01-01T00:00:00")],
            [("content_1", "Test Content", "Test Description", "tutorial", "beginner", 15, '["React Native"]', '[]', '["Learn basics"]', None, "https://example.com", None, "content_text", None)]
        ]
        
        engine = LearningEngine()
        
        # Test getting learning path
        learning_path = engine.get_learning_path("path_1")
        
        assert learning_path is not None
        assert learning_path.path_id == "path_1"
        assert learning_path.title == "Test Path"
        assert learning_path.target_skills == ["React Native"]
        assert len(learning_path.content_sequence) == 1
    
    def test_get_learning_path_not_found(self, mock_dependencies):
        """Test getting a learning path that doesn't exist."""
        # Setup mock database response
        mock_dependencies['db'].execute_query.return_value = []
        
        engine = LearningEngine()
        
        # Test getting non-existent learning path
        learning_path = engine.get_learning_path("nonexistent_path")
        
        assert learning_path is None
    
    def test_get_user_learning_paths(self, mock_dependencies):
        """Test getting all learning paths for a user."""
        # Setup mock database response
        mock_dependencies['db'].execute_query.side_effect = [
            [("path_1",), ("path_2",)],  # First query for path IDs
            [("path_1", "Test Path 1", "Description 1", '["React Native"]', "intermediate", 30, '["content_1"]', '[]', '["Learn React Native"]', '["React Native"]', "true", "2024-01-01T00:00:00", "2024-01-01T00:00:00")],  # Second query for path 1
            [("content_1", "Test Content", "Description", "tutorial", "beginner", 15, '["React Native"]', '[]', '["Learn basics"]', None, "https://example.com", None, "content_text", None)],  # Third query for content
            [("path_2", "Test Path 2", "Description 2", '["User Research"]', "beginner", 20, '["content_2"]', '[]', '["Learn User Research"]', '["User Research"]', "true", "2024-01-01T00:00:00", "2024-01-01T00:00:00")],  # Fourth query for path 2
            [("content_2", "Test Content 2", "Description 2", "article", "beginner", 10, '["User Research"]', '[]', '["Learn basics"]', None, "https://example.com", None, "content_text", None)]  # Fifth query for content 2
        ]
        
        engine = LearningEngine()
        
        # Test getting user learning paths
        learning_paths = engine.get_user_learning_paths("test_user_123")
        
        assert learning_paths is not None
        assert len(learning_paths) == 2
        assert learning_paths[0].path_id == "path_1"
        assert learning_paths[1].path_id == "path_2"
    
    def test_format_content_text(self, mock_dependencies):
        """Test content text formatting."""
        engine = LearningEngine()
        
        content_data = {
            "title": "Test Learning Module",
            "learning_objectives": ["Objective 1", "Objective 2"],
            "content_structure": ["Step 1", "Step 2", "Step 3"],
            "practical_exercises": ["Exercise 1", "Exercise 2"],
            "key_takeaways": ["Takeaway 1", "Takeaway 2"],
            "prerequisites": ["Prerequisite 1"]
        }
        
        formatted_text = engine._format_content_text(content_data)
        
        assert "# Test Learning Module" in formatted_text
        assert "## Learning Objectives" in formatted_text
        assert "- Objective 1" in formatted_text
        assert "## Content Structure" in formatted_text
        assert "1. Step 1" in formatted_text
        assert "## Practical Exercises" in formatted_text
        assert "## Key Takeaways" in formatted_text
    
    def test_global_learning_engine_instance(self, mock_dependencies):
        """Test global learning engine instance."""
        # Clear any existing instance
        import backend.services.learning_engine
        backend.services.learning_engine._learning_engine = None
        
        # Get instance
        engine1 = get_learning_engine()
        engine2 = get_learning_engine()
        
        # Should be the same instance
        assert engine1 is engine2
        assert engine1 is not None


class TestLearningRecommendation:
    """Test cases for LearningRecommendation dataclass."""
    
    def test_learning_recommendation_creation(self):
        """Test LearningRecommendation creation."""
        rec = LearningRecommendation(
            content_id="test_content_123",
            title="Test Learning Content",
            content_type="tutorial",
            difficulty="intermediate",
            estimated_duration=15,
            skills_covered=["React Native", "Mobile Development"],
            priority_score=8.5,
            reasoning="High priority for current project",
            prerequisites=["JavaScript", "React"],
            learning_objectives=["Learn React Native basics", "Build a mobile app"]
        )
        
        assert rec.content_id == "test_content_123"
        assert rec.title == "Test Learning Content"
        assert rec.content_type == "tutorial"
        assert rec.difficulty == "intermediate"
        assert rec.estimated_duration == 15
        assert rec.skills_covered == ["React Native", "Mobile Development"]
        assert rec.priority_score == 8.5
        assert rec.reasoning == "High priority for current project"
        assert rec.prerequisites == ["JavaScript", "React"]
        assert rec.learning_objectives == ["Learn React Native basics", "Build a mobile app"]


class TestPersonalizedLearningPath:
    """Test cases for PersonalizedLearningPath dataclass."""
    
    def test_personalized_learning_path_creation(self):
        """Test PersonalizedLearningPath creation."""
        recommendations = [
            LearningRecommendation(
                content_id="rec_1", title="Test 1", content_type="tutorial",
                difficulty="beginner", estimated_duration=10, skills_covered=[],
                priority_score=8.0, reasoning="", prerequisites=[], learning_objectives=[]
            )
        ]
        
        path = PersonalizedLearningPath(
            path_id="test_path_123",
            title="Test Learning Path",
            description="A test learning path for demonstration",
            target_skills=["React Native", "User Research"],
            difficulty="intermediate",
            estimated_duration=30,
            content_sequence=recommendations,
            prerequisites=["JavaScript"],
            learning_objectives=["Learn React Native", "Improve user research skills"],
            priority_order=["React Native", "User Research"],
            success_metrics={"completion_rate": 0.8, "satisfaction": 4.5},
            created_at=datetime.now(timezone.utc)
        )
        
        assert path.path_id == "test_path_123"
        assert path.title == "Test Learning Path"
        assert path.description == "A test learning path for demonstration"
        assert path.target_skills == ["React Native", "User Research"]
        assert path.difficulty == "intermediate"
        assert path.estimated_duration == 30
        assert path.content_sequence == recommendations
        assert path.prerequisites == ["JavaScript"]
        assert path.learning_objectives == ["Learn React Native", "Improve user research skills"]
        assert path.priority_order == ["React Native", "User Research"]
        assert path.success_metrics == {"completion_rate": 0.8, "satisfaction": 4.5}
        assert path.created_at is not None


if __name__ == "__main__":
    pytest.main([__file__])
