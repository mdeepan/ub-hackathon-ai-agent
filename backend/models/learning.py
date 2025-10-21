"""
Learning data models for the Personal Learning Agent.

This module contains Pydantic models for learning paths, content, and progress tracking.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum
import uuid


class ContentType(str, Enum):
    """Types of learning content."""
    ARTICLE = "article"
    VIDEO = "video"
    EXERCISE = "exercise"
    QUIZ = "quiz"
    INTERACTIVE = "interactive"
    COURSE = "course"
    TUTORIAL = "tutorial"
    WORKSHOP = "workshop"


class DifficultyLevel(str, Enum):
    """Difficulty levels for learning content."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class LearningContent(BaseModel):
    """Learning content model."""
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique content ID")
    title: str = Field(..., description="Content title", min_length=1, max_length=200)
    description: Optional[str] = Field(None, description="Content description", max_length=2000)
    content_type: ContentType = Field(ContentType.ARTICLE, description="Type of learning content")
    difficulty: DifficultyLevel = Field(DifficultyLevel.BEGINNER, description="Content difficulty level")
    estimated_duration: Optional[int] = Field(None, description="Estimated duration in minutes", ge=1)
    skills_covered: List[str] = Field(default_factory=list, description="Skills covered by this content")
    prerequisites: List[str] = Field(default_factory=list, description="Prerequisite skills or content")
    learning_objectives: List[str] = Field(default_factory=list, description="Learning objectives")
    content_url: Optional[str] = Field(None, description="URL to the learning content")
    content_text: Optional[str] = Field(None, description="Text content (for articles, tutorials)")
    tags: List[str] = Field(default_factory=list, description="Content tags for categorization")
    is_active: bool = Field(True, description="Whether content is active and available")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Content creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Content last update timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Introduction to React Native",
                "description": "Learn the basics of React Native for mobile app development",
                "content_type": "video",
                "difficulty": "beginner",
                "estimated_duration": 45,
                "skills_covered": ["React Native", "Mobile Development", "JavaScript"],
                "prerequisites": ["JavaScript", "React"],
                "learning_objectives": [
                    "Understand React Native fundamentals",
                    "Build a simple mobile app",
                    "Deploy to mobile devices"
                ],
                "content_url": "https://example.com/react-native-intro",
                "tags": ["mobile", "react", "javascript", "development"]
            }
        }


class LearningPath(BaseModel):
    """Learning path model for structured learning journeys."""
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique learning path ID")
    title: str = Field(..., description="Learning path title", min_length=1, max_length=200)
    description: Optional[str] = Field(None, description="Learning path description", max_length=2000)
    target_skills: List[str] = Field(default_factory=list, description="Skills this path aims to develop")
    difficulty: DifficultyLevel = Field(DifficultyLevel.BEGINNER, description="Overall path difficulty")
    estimated_duration: Optional[int] = Field(None, description="Total estimated duration in hours", ge=1)
    content_sequence: List[str] = Field(default_factory=list, description="Ordered list of content IDs")
    prerequisites: List[str] = Field(default_factory=list, description="Prerequisite skills")
    learning_objectives: List[str] = Field(default_factory=list, description="Overall learning objectives")
    tags: List[str] = Field(default_factory=list, description="Path tags for categorization")
    is_active: bool = Field(True, description="Whether path is active and available")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Path creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Path last update timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Full-Stack Mobile Development",
                "description": "Complete learning path for building mobile applications with React Native",
                "target_skills": ["React Native", "Node.js", "Database Design", "API Development"],
                "difficulty": "intermediate",
                "estimated_duration": 40,
                "content_sequence": ["content_1", "content_2", "content_3"],
                "prerequisites": ["JavaScript", "HTML", "CSS"],
                "learning_objectives": [
                    "Build a complete mobile application",
                    "Implement backend APIs",
                    "Deploy to app stores"
                ],
                "tags": ["mobile", "fullstack", "react", "nodejs"]
            }
        }


class LearningProgress(BaseModel):
    """Learning progress tracking model."""
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique progress ID")
    user_id: str = Field(..., description="User ID")
    content_id: Optional[str] = Field(None, description="Content ID (for content-specific progress)")
    learning_path_id: Optional[str] = Field(None, description="Learning path ID (for path-specific progress)")
    status: str = Field("not_started", description="Progress status")
    completion_percentage: float = Field(0.0, description="Completion percentage (0-100)", ge=0, le=100)
    time_spent: Optional[int] = Field(None, description="Time spent in minutes", ge=0)
    quiz_score: Optional[float] = Field(None, description="Quiz score (0-100)", ge=0, le=100)
    started_at: Optional[datetime] = Field(None, description="When learning started")
    completed_at: Optional[datetime] = Field(None, description="When learning was completed")
    last_accessed_at: Optional[datetime] = Field(None, description="Last access timestamp")
    notes: Optional[str] = Field(None, description="User notes about the learning experience", max_length=1000)
    skills_gained: List[str] = Field(default_factory=list, description="Skills gained from this learning")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Progress creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Progress last update timestamp")
    
    @validator('status')
    def validate_status(cls, v):
        allowed_statuses = ['not_started', 'in_progress', 'completed', 'paused', 'abandoned']
        if v not in allowed_statuses:
            raise ValueError(f'Status must be one of: {allowed_statuses}')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user_123",
                "content_id": "content_456",
                "status": "in_progress",
                "completion_percentage": 65.0,
                "time_spent": 120,
                "quiz_score": 85.0,
                "started_at": "2024-01-15T10:00:00Z",
                "last_accessed_at": "2024-01-20T14:30:00Z",
                "notes": "Great content, very practical examples",
                "skills_gained": ["React Native Basics", "Component Lifecycle"]
            }
        }


# Create and Update models for API operations
class LearningContentCreate(BaseModel):
    """Model for creating new learning content."""
    title: str = Field(..., description="Content title", min_length=1, max_length=200)
    description: Optional[str] = Field(None, description="Content description", max_length=2000)
    content_type: ContentType = Field(ContentType.ARTICLE, description="Type of learning content")
    difficulty: DifficultyLevel = Field(DifficultyLevel.BEGINNER, description="Content difficulty level")
    estimated_duration: Optional[int] = Field(None, description="Estimated duration in minutes", ge=1)
    skills_covered: List[str] = Field(default_factory=list, description="Skills covered by this content")
    prerequisites: List[str] = Field(default_factory=list, description="Prerequisite skills or content")
    learning_objectives: List[str] = Field(default_factory=list, description="Learning objectives")
    content_url: Optional[str] = Field(None, description="URL to the learning content")
    content_text: Optional[str] = Field(None, description="Text content (for articles, tutorials)")
    tags: List[str] = Field(default_factory=list, description="Content tags for categorization")


class LearningContentUpdate(BaseModel):
    """Model for updating existing learning content."""
    title: Optional[str] = Field(None, description="Content title", min_length=1, max_length=200)
    description: Optional[str] = Field(None, description="Content description", max_length=2000)
    content_type: Optional[ContentType] = Field(None, description="Type of learning content")
    difficulty: Optional[DifficultyLevel] = Field(None, description="Content difficulty level")
    estimated_duration: Optional[int] = Field(None, description="Estimated duration in minutes", ge=1)
    skills_covered: Optional[List[str]] = Field(None, description="Skills covered by this content")
    prerequisites: Optional[List[str]] = Field(None, description="Prerequisite skills or content")
    learning_objectives: Optional[List[str]] = Field(None, description="Learning objectives")
    content_url: Optional[str] = Field(None, description="URL to the learning content")
    content_text: Optional[str] = Field(None, description="Text content (for articles, tutorials)")
    tags: Optional[List[str]] = Field(None, description="Content tags for categorization")
    is_active: Optional[bool] = Field(None, description="Whether content is active and available")


class LearningPathCreate(BaseModel):
    """Model for creating new learning paths."""
    title: str = Field(..., description="Learning path title", min_length=1, max_length=200)
    description: Optional[str] = Field(None, description="Learning path description", max_length=2000)
    target_skills: List[str] = Field(default_factory=list, description="Skills this path aims to develop")
    difficulty: DifficultyLevel = Field(DifficultyLevel.BEGINNER, description="Overall path difficulty")
    estimated_duration: Optional[int] = Field(None, description="Total estimated duration in hours", ge=1)
    content_sequence: List[str] = Field(default_factory=list, description="Ordered list of content IDs")
    prerequisites: List[str] = Field(default_factory=list, description="Prerequisite skills")
    learning_objectives: List[str] = Field(default_factory=list, description="Overall learning objectives")
    tags: List[str] = Field(default_factory=list, description="Path tags for categorization")


class LearningPathUpdate(BaseModel):
    """Model for updating existing learning paths."""
    title: Optional[str] = Field(None, description="Learning path title", min_length=1, max_length=200)
    description: Optional[str] = Field(None, description="Learning path description", max_length=2000)
    target_skills: Optional[List[str]] = Field(None, description="Skills this path aims to develop")
    difficulty: Optional[DifficultyLevel] = Field(None, description="Overall path difficulty")
    estimated_duration: Optional[int] = Field(None, description="Total estimated duration in hours", ge=1)
    content_sequence: Optional[List[str]] = Field(None, description="Ordered list of content IDs")
    prerequisites: Optional[List[str]] = Field(None, description="Prerequisite skills")
    learning_objectives: Optional[List[str]] = Field(None, description="Overall learning objectives")
    tags: Optional[List[str]] = Field(None, description="Path tags for categorization")
    is_active: Optional[bool] = Field(None, description="Whether path is active and available")


class LearningProgressCreate(BaseModel):
    """Model for creating new learning progress."""
    user_id: str = Field(..., description="User ID")
    content_id: Optional[str] = Field(None, description="Content ID (for content-specific progress)")
    learning_path_id: Optional[str] = Field(None, description="Learning path ID (for path-specific progress)")
    status: str = Field("not_started", description="Progress status")
    notes: Optional[str] = Field(None, description="User notes about the learning experience", max_length=1000)


class LearningProgressUpdate(BaseModel):
    """Model for updating existing learning progress."""
    status: Optional[str] = Field(None, description="Progress status")
    completion_percentage: Optional[float] = Field(None, description="Completion percentage (0-100)", ge=0, le=100)
    time_spent: Optional[int] = Field(None, description="Time spent in minutes", ge=0)
    quiz_score: Optional[float] = Field(None, description="Quiz score (0-100)", ge=0, le=100)
    started_at: Optional[datetime] = Field(None, description="When learning started")
    completed_at: Optional[datetime] = Field(None, description="When learning was completed")
    last_accessed_at: Optional[datetime] = Field(None, description="Last access timestamp")
    notes: Optional[str] = Field(None, description="User notes about the learning experience", max_length=1000)
    skills_gained: Optional[List[str]] = Field(None, description="Skills gained from this learning")
