"""
Comprehensive integration tests for the Learning System.

This module tests the complete learning system integration including
learning engine, API endpoints, and database operations.
"""

import pytest
import json
import uuid
from datetime import datetime, timezone
from unittest.mock import Mock, patch, MagicMock

# Import the modules to test
from backend.services.learning_engine import get_learning_engine, LearningEngine
from backend.models.learning import LearningContentCreate, ContentType, DifficultyLevel
from backend.models.skills import SkillGap
from backend.models.user import UserProfile, UserContext, UserPreferences, SkillLevel


class TestLearningSystemIntegration:
    """Integration tests for the complete learning system."""
    
    def test_learning_engine_initialization(self):
        """Test that the learning engine initializes correctly."""
        engine = get_learning_engine()
        
        assert engine is not None
        assert hasattr(engine, 'content_categories')
        assert hasattr(engine, 'micro_learning_duration')
        assert 'product_management' in engine.content_categories
        assert 'technical_skills' in engine.content_categories
        assert 'soft_skills' in engine.content_categories
        
        # Verify micro-learning duration targets
        assert engine.micro_learning_duration['quick_tip'] == 5
        assert engine.micro_learning_duration['tutorial'] == 15
        assert engine.micro_learning_duration['practical_exercise'] == 15
    
    def test_content_type_selection(self):
        """Test content type selection logic."""
        engine = get_learning_engine()
        
        # Test various skill mappings
        assert engine._select_content_type("programming", "beginner") == "tutorial"
        assert engine._select_content_type("data_analysis", "intermediate") == "practical_exercise"
        assert engine._select_content_type("user_research", "advanced") == "case_study"
        assert engine._select_content_type("unknown_skill", "beginner") == "concept_explanation"
    
    def test_difficulty_level_determination(self):
        """Test difficulty level determination logic."""
        engine = get_learning_engine()
        
        # Test various level combinations
        assert engine._determine_difficulty_level("beginner", "intermediate") == "intermediate"
        assert engine._determine_difficulty_level("beginner", "advanced") == "advanced"
        assert engine._determine_difficulty_level("intermediate", "advanced") == "intermediate"
        assert engine._determine_difficulty_level("advanced", "expert") == "beginner"
    
    def test_priority_score_calculation(self):
        """Test priority score calculation logic."""
        engine = get_learning_engine()
        
        # Create mock objects
        mock_user_profile = Mock()
        mock_skill_gap = Mock()
        mock_skill_gap.gap_size = 2.0
        
        content = {
            'estimated_duration': 10,
            'difficulty': 'intermediate',
            'content_type': 'tutorial'
        }
        
        score = engine._calculate_priority_score(content, mock_skill_gap, mock_user_profile)
        
        assert score > 0
        assert isinstance(score, float)
        # Should include gap size (20) + duration bonus (5) + difficulty bonus (3) + content type bonus (2)
        assert score >= 20  # At least the gap size contribution
    
    def test_difficulty_distribution_calculation(self):
        """Test difficulty distribution calculation."""
        engine = get_learning_engine()
        
        # Create mock recommendations
        recommendations = [
            Mock(difficulty="beginner"),
            Mock(difficulty="intermediate"),
            Mock(difficulty="beginner"),
            Mock(difficulty="advanced")
        ]
        
        distribution = engine._calculate_difficulty_distribution(recommendations)
        
        assert distribution["beginner"] == 2
        assert distribution["intermediate"] == 1
        assert distribution["advanced"] == 1
        assert distribution["expert"] == 0
    
    def test_overall_difficulty_determination(self):
        """Test overall difficulty determination."""
        engine = get_learning_engine()
        
        # Test with beginner content
        beginner_recs = [Mock(difficulty="beginner")]
        assert engine._determine_overall_difficulty(beginner_recs) == "beginner"
        
        # Test with mixed content
        mixed_recs = [
            Mock(difficulty="beginner"),
            Mock(difficulty="intermediate")
        ]
        assert engine._determine_overall_difficulty(mixed_recs) == "intermediate"
        
        # Test with advanced content
        advanced_recs = [
            Mock(difficulty="advanced"),
            Mock(difficulty="expert")
        ]
        assert engine._determine_overall_difficulty(advanced_recs) == "advanced"
    
    def test_content_text_formatting(self):
        """Test content text formatting."""
        engine = get_learning_engine()
        
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
    
    @patch('backend.services.learning_engine.get_ai_client')
    def test_micro_learning_content_generation(self, mock_ai_client):
        """Test micro-learning content generation with AI."""
        # Setup mock AI client
        mock_ai_instance = Mock()
        mock_ai_instance.generate_response.return_value = json.dumps({
            "title": "React Native Components",
            "learning_objectives": ["Understand components", "Create custom components"],
            "content_structure": ["What are components", "Component lifecycle", "Best practices"],
            "practical_exercises": ["Create a button component", "Style the component"],
            "key_takeaways": ["Components are reusable", "Props make components flexible"],
            "prerequisites": ["JavaScript basics"]
        })
        mock_ai_client.return_value = mock_ai_instance
        
        engine = get_learning_engine()
        
        # Create mock objects
        mock_user_profile = Mock()
        mock_skill_gap = Mock()
        mock_skill_gap.skill_name = "React Native"
        
        # Test content generation
        content_list = engine._generate_micro_learning_content(
            mock_skill_gap, mock_user_profile, "intermediate"
        )
        
        assert content_list is not None
        assert len(content_list) == 1
        content = content_list[0]
        assert content['id'] is not None
        assert content['title'] == "React Native Components"
        assert content['content_type'] in engine.micro_learning_duration
        assert content['estimated_duration'] > 0
        assert content['skills_covered'] == ["React Native"]
        assert content['learning_objectives'] == ["Understand components", "Create custom components"]
    
    def test_learning_recommendation_creation(self):
        """Test learning recommendation creation."""
        from backend.services.learning_engine import LearningRecommendation
        
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
    
    def test_personalized_learning_path_creation(self):
        """Test personalized learning path creation."""
        from backend.services.learning_engine import PersonalizedLearningPath, LearningRecommendation
        
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
    
    def test_learning_content_model_validation(self):
        """Test learning content model validation."""
        content = LearningContentCreate(
            title="Test Learning Content",
            description="A test piece of learning content",
            content_type=ContentType.TUTORIAL,
            difficulty=DifficultyLevel.INTERMEDIATE,
            estimated_duration=15,
            skills_covered=["React Native", "Mobile Development"],
            prerequisites=["JavaScript", "React"],
            learning_objectives=["Learn React Native basics", "Build a mobile app"],
            content_text="This is the content text...",
            tags=["mobile", "react", "development"]
        )
        
        assert content.title == "Test Learning Content"
        assert content.content_type == ContentType.TUTORIAL
        assert content.difficulty == DifficultyLevel.INTERMEDIATE
        assert content.estimated_duration == 15
        assert content.skills_covered == ["React Native", "Mobile Development"]
        assert content.prerequisites == ["JavaScript", "React"]
        assert content.learning_objectives == ["Learn React Native basics", "Build a mobile app"]
        assert content.tags == ["mobile", "react", "development"]
    
    def test_skill_gap_model_validation(self):
        """Test skill gap model validation."""
        skill_gap = SkillGap(
            id="gap_1",
            user_id="test_user_123",
            skill_name="React Native",
            current_level=SkillLevel.BEGINNER,
            target_level=SkillLevel.INTERMEDIATE,
            gap_size=2.0,
            category="technical_skills",
            priority_score=8.5,
            created_at=datetime.now(timezone.utc)
        )
        
        assert skill_gap.id == "gap_1"
        assert skill_gap.user_id == "test_user_123"
        assert skill_gap.skill_name == "React Native"
        assert skill_gap.current_level == SkillLevel.BEGINNER
        assert skill_gap.target_level == SkillLevel.INTERMEDIATE
        assert skill_gap.gap_size == 2.0
        assert skill_gap.category == "technical_skills"
        assert skill_gap.priority_score == 8.5
        assert skill_gap.created_at is not None
    
    def test_user_profile_model_validation(self):
        """Test user profile model validation."""
        user_profile = UserProfile(
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
        
        assert user_profile.id == "test_user_123"
        assert user_profile.username == "testuser"
        assert user_profile.email == "test@example.com"
        assert user_profile.current_role == "Product Manager"
        assert user_profile.years_of_experience == 3
        assert user_profile.industry == "Technology"
        assert user_profile.team_size == 5
        assert len(user_profile.current_projects) == 2
        assert user_profile.context.user_id == "test_user_123"


if __name__ == "__main__":
    pytest.main([__file__])
