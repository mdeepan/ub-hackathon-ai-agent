"""
User data models for the Personal Learning Agent.

This module contains Pydantic models for user profiles, preferences, tasks,
skills, and context information that will be used for AI personalization.
"""

from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, date
from enum import Enum
import uuid


class SkillLevel(str, Enum):
    """Skill proficiency levels."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class SkillSource(str, Enum):
    """Source of skill assessment."""
    INFERRED = "inferred"  # AI-inferred from work artifacts
    SELF_DECLARED = "self_declared"  # User self-assessment
    VALIDATED = "validated"  # Validated through work completion
    TESTED = "tested"  # Tested through assessments


class UserConnections(BaseModel):
    """External application connections for the user."""
    slack_handle: Optional[str] = Field(None, description="Slack username/handle")
    github_username: Optional[str] = Field(None, description="GitHub username")
    linkedin_url: Optional[str] = Field(None, description="LinkedIn profile URL")
    email: Optional[EmailStr] = Field(None, description="Primary email address")
    google_drive_connected: bool = Field(False, description="Google Drive integration status")
    github_connected: bool = Field(False, description="GitHub integration status")
    slack_connected: bool = Field(False, description="Slack integration status")
    
    class Config:
        json_schema_extra = {
            "example": {
                "slack_handle": "@john.doe",
                "github_username": "johndoe",
                "linkedin_url": "https://linkedin.com/in/johndoe",
                "email": "john.doe@company.com",
                "google_drive_connected": True,
                "github_connected": True,
                "slack_connected": False
            }
        }


class TeamInfo(BaseModel):
    """Team and organizational information."""
    team_name: Optional[str] = Field(None, description="Name of the user's team")
    team_size: Optional[int] = Field(None, description="Number of team members", ge=1)
    team_role: Optional[str] = Field(None, description="User's role within the team")
    manager_name: Optional[str] = Field(None, description="Manager's name")
    department: Optional[str] = Field(None, description="Department or division")
    company: Optional[str] = Field(None, description="Company name")
    location: Optional[str] = Field(None, description="Work location (city, country)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "team_name": "Product Engineering",
                "team_size": 8,
                "team_role": "Senior Product Manager",
                "manager_name": "Sarah Johnson",
                "department": "Product",
                "company": "TechCorp Inc.",
                "location": "San Francisco, CA"
            }
        }


class ProjectInfo(BaseModel):
    """Current project information."""
    project_name: Optional[str] = Field(None, description="Name of current project")
    project_description: Optional[str] = Field(None, description="Project description")
    project_phase: Optional[str] = Field(None, description="Current project phase")
    project_technologies: List[str] = Field(default_factory=list, description="Technologies used in project")
    project_domain: Optional[str] = Field(None, description="Project domain (e.g., fintech, healthcare)")
    project_start_date: Optional[date] = Field(None, description="Project start date")
    project_end_date: Optional[date] = Field(None, description="Expected project end date")
    
    class Config:
        json_schema_extra = {
            "example": {
                "project_name": "Mobile Banking App",
                "project_description": "Next-generation mobile banking application with AI features",
                "project_phase": "Development",
                "project_technologies": ["React Native", "Node.js", "PostgreSQL", "AWS"],
                "project_domain": "Fintech",
                "project_start_date": "2024-01-15",
                "project_end_date": "2024-06-30"
            }
        }


class UserPreferences(BaseModel):
    """User learning preferences and settings."""
    preferred_learning_style: Optional[str] = Field(None, description="Preferred learning style")
    preferred_content_types: List[str] = Field(
        default_factory=lambda: ["articles", "videos", "exercises"],
        description="Preferred content types"
    )
    preferred_session_duration: Optional[int] = Field(15, description="Preferred session duration in minutes", ge=5, le=120)
    preferred_difficulty: Optional[str] = Field("intermediate", description="Preferred difficulty level")
    timezone: Optional[str] = Field("UTC", description="User's timezone")
    notification_preferences: Dict[str, bool] = Field(
        default_factory=lambda: {
            "daily_reminders": True,
            "weekly_progress": True,
            "skill_recommendations": True,
            "learning_reminders": True
        },
        description="Notification preferences"
    )
    privacy_settings: Dict[str, bool] = Field(
        default_factory=lambda: {
            "share_progress": False,
            "share_skills": False,
            "allow_analytics": True
        },
        description="Privacy and sharing settings"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "preferred_learning_style": "visual",
                "preferred_content_types": ["videos", "interactive_exercises"],
                "preferred_session_duration": 20,
                "preferred_difficulty": "intermediate",
                "timezone": "America/New_York",
                "notification_preferences": {
                    "daily_reminders": True,
                    "weekly_progress": True,
                    "skill_recommendations": True,
                    "learning_reminders": False
                },
                "privacy_settings": {
                    "share_progress": False,
                    "share_skills": True,
                    "allow_analytics": True
                }
            }
        }


class UserTask(BaseModel):
    """User work task model."""
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique task ID")
    title: str = Field(..., description="Task title", min_length=1, max_length=200)
    description: Optional[str] = Field(None, description="Task description", max_length=1000)
    status: str = Field("pending", description="Task status")
    priority: str = Field("medium", description="Task priority")
    due_date: Optional[date] = Field(None, description="Task due date")
    completed_date: Optional[date] = Field(None, description="Task completion date")
    estimated_hours: Optional[float] = Field(None, description="Estimated hours to complete", ge=0)
    actual_hours: Optional[float] = Field(None, description="Actual hours spent", ge=0)
    skills_used: List[str] = Field(default_factory=list, description="Skills used in this task")
    skills_learned: List[str] = Field(default_factory=list, description="Skills learned from this task")
    project_context: Optional[str] = Field(None, description="Project context for this task")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Task creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Task last update timestamp")
    
    @validator('status')
    def validate_status(cls, v):
        allowed_statuses = ['pending', 'in_progress', 'completed', 'cancelled', 'on_hold']
        if v not in allowed_statuses:
            raise ValueError(f'Status must be one of: {allowed_statuses}')
        return v
    
    @validator('priority')
    def validate_priority(cls, v):
        allowed_priorities = ['low', 'medium', 'high', 'urgent']
        if v not in allowed_priorities:
            raise ValueError(f'Priority must be one of: {allowed_priorities}')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Design user authentication flow",
                "description": "Create wireframes and user stories for the new authentication system",
                "status": "in_progress",
                "priority": "high",
                "due_date": "2024-02-15",
                "estimated_hours": 8.0,
                "actual_hours": 5.5,
                "skills_used": ["UX Design", "User Research", "Figma"],
                "skills_learned": ["Authentication Patterns", "Security Best Practices"],
                "project_context": "Mobile Banking App"
            }
        }


class UserSkill(BaseModel):
    """User skill model with proficiency and source tracking."""
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique skill ID")
    skill_name: str = Field(..., description="Skill name", min_length=1, max_length=100)
    category: Optional[str] = Field(None, description="Skill category")
    level: SkillLevel = Field(SkillLevel.BEGINNER, description="Current skill level")
    source: SkillSource = Field(SkillSource.SELF_DECLARED, description="Source of skill assessment")
    confidence_score: Optional[float] = Field(None, description="Confidence score (0-1)", ge=0, le=1)
    last_used_date: Optional[date] = Field(None, description="Last date this skill was used")
    last_assessed_date: Optional[date] = Field(None, description="Last assessment date")
    evidence_count: int = Field(0, description="Number of evidence pieces supporting this skill", ge=0)
    learning_priority: Optional[str] = Field(None, description="Learning priority for this skill")
    target_level: Optional[SkillLevel] = Field(None, description="Target skill level")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Skill creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Skill last update timestamp")
    
    @validator('learning_priority')
    def validate_learning_priority(cls, v):
        if v is not None:
            allowed_priorities = ['low', 'medium', 'high', 'critical']
            if v not in allowed_priorities:
                raise ValueError(f'Learning priority must be one of: {allowed_priorities}')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "skill_name": "Product Strategy",
                "category": "Product Management",
                "level": "intermediate",
                "source": "validated",
                "confidence_score": 0.75,
                "last_used_date": "2024-01-20",
                "last_assessed_date": "2024-01-15",
                "evidence_count": 5,
                "learning_priority": "high",
                "target_level": "advanced"
            }
        }


class UserContext(BaseModel):
    """Aggregated user context for AI personalization."""
    user_id: str = Field(..., description="User ID")
    current_focus_areas: List[str] = Field(default_factory=list, description="Current focus areas")
    recent_work_summary: Optional[str] = Field(None, description="Summary of recent work")
    upcoming_priorities: List[str] = Field(default_factory=list, description="Upcoming priorities")
    learning_goals: List[str] = Field(default_factory=list, description="Current learning goals")
    skill_gaps: List[str] = Field(default_factory=list, description="Identified skill gaps")
    context_summary: Optional[str] = Field(None, description="AI-generated context summary")
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Context last update timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user_123",
                "current_focus_areas": ["Mobile Development", "User Experience"],
                "recent_work_summary": "Working on mobile banking app authentication flow and user onboarding",
                "upcoming_priorities": ["Launch MVP", "User testing", "Performance optimization"],
                "learning_goals": ["Advanced React Native", "Security best practices"],
                "skill_gaps": ["Advanced JavaScript", "API Design"],
                "context_summary": "Product manager focused on fintech mobile app with strong UX skills but needs technical depth"
            }
        }


class UserProfile(BaseModel):
    """Comprehensive user profile model."""
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique user ID")
    username: str = Field(..., description="Username", min_length=3, max_length=50)
    name: str = Field(..., description="Full name", min_length=1, max_length=100)
    job_role: str = Field(..., description="Current job role", min_length=1, max_length=100)
    experience_summary: Optional[str] = Field(None, description="Experience summary", max_length=2000)
    personal_goals: List[str] = Field(default_factory=list, description="Personal goals and OKRs")
    team_info: Optional[TeamInfo] = Field(None, description="Team and organizational information")
    project_info: Optional[ProjectInfo] = Field(None, description="Current project information")
    connections: Optional[UserConnections] = Field(None, description="External application connections")
    preferences: Optional[UserPreferences] = Field(None, description="User preferences and settings")
    
    # Work and learning data
    recent_tasks: List[UserTask] = Field(default_factory=list, description="Recent work tasks")
    upcoming_tasks: List[UserTask] = Field(default_factory=list, description="Upcoming work tasks")
    skills: List[UserSkill] = Field(default_factory=list, description="User skills")
    skill_gaps: List[str] = Field(default_factory=list, description="Identified skill gaps")
    
    # Context and metadata
    context: Optional[UserContext] = Field(None, description="Aggregated user context")
    is_active: bool = Field(True, description="Whether user profile is active")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Profile creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Profile last update timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "john_doe",
                "name": "John Doe",
                "job_role": "Senior Product Manager",
                "experience_summary": "5+ years in product management with focus on mobile applications and fintech",
                "personal_goals": [
                    "Launch successful mobile banking app",
                    "Improve technical skills in React Native",
                    "Build stronger data analysis capabilities"
                ],
                "team_info": {
                    "team_name": "Product Engineering",
                    "team_size": 8,
                    "team_role": "Senior Product Manager",
                    "company": "TechCorp Inc."
                },
                "project_info": {
                    "project_name": "Mobile Banking App",
                    "project_phase": "Development",
                    "project_technologies": ["React Native", "Node.js", "PostgreSQL"]
                },
                "connections": {
                    "slack_handle": "@john.doe",
                    "github_username": "johndoe",
                    "email": "john.doe@company.com"
                },
                "skill_gaps": ["Advanced JavaScript", "API Design", "Security Best Practices"]
            }
        }


# Create and Update models for API operations
class UserProfileCreate(BaseModel):
    """Model for creating a new user profile."""
    username: str = Field(..., description="Username", min_length=3, max_length=50)
    name: str = Field(..., description="Full name", min_length=1, max_length=100)
    job_role: str = Field(..., description="Current job role", min_length=1, max_length=100)
    experience_summary: Optional[str] = Field(None, description="Experience summary", max_length=2000)
    personal_goals: List[str] = Field(default_factory=list, description="Personal goals and OKRs")
    team_info: Optional[TeamInfo] = Field(None, description="Team and organizational information")
    project_info: Optional[ProjectInfo] = Field(None, description="Current project information")
    connections: Optional[UserConnections] = Field(None, description="External application connections")
    preferences: Optional[UserPreferences] = Field(None, description="User preferences and settings")


class UserProfileUpdate(BaseModel):
    """Model for updating an existing user profile."""
    name: Optional[str] = Field(None, description="Full name", min_length=1, max_length=100)
    job_role: Optional[str] = Field(None, description="Current job role", min_length=1, max_length=100)
    experience_summary: Optional[str] = Field(None, description="Experience summary", max_length=2000)
    personal_goals: Optional[List[str]] = Field(None, description="Personal goals and OKRs")
    team_info: Optional[TeamInfo] = Field(None, description="Team and organizational information")
    project_info: Optional[ProjectInfo] = Field(None, description="Current project information")
    connections: Optional[UserConnections] = Field(None, description="External application connections")
    preferences: Optional[UserPreferences] = Field(None, description="User preferences and settings")
    is_active: Optional[bool] = Field(None, description="Whether user profile is active")


class UserTaskCreate(BaseModel):
    """Model for creating a new user task."""
    title: str = Field(..., description="Task title", min_length=1, max_length=200)
    description: Optional[str] = Field(None, description="Task description", max_length=1000)
    status: str = Field("pending", description="Task status")
    priority: str = Field("medium", description="Task priority")
    due_date: Optional[date] = Field(None, description="Task due date")
    estimated_hours: Optional[float] = Field(None, description="Estimated hours to complete", ge=0)
    skills_used: List[str] = Field(default_factory=list, description="Skills used in this task")
    skills_learned: List[str] = Field(default_factory=list, description="Skills learned from this task")
    project_context: Optional[str] = Field(None, description="Project context for this task")


class UserTaskUpdate(BaseModel):
    """Model for updating an existing user task."""
    title: Optional[str] = Field(None, description="Task title", min_length=1, max_length=200)
    description: Optional[str] = Field(None, description="Task description", max_length=1000)
    status: Optional[str] = Field(None, description="Task status")
    priority: Optional[str] = Field(None, description="Task priority")
    due_date: Optional[date] = Field(None, description="Task due date")
    completed_date: Optional[date] = Field(None, description="Task completion date")
    estimated_hours: Optional[float] = Field(None, description="Estimated hours to complete", ge=0)
    actual_hours: Optional[float] = Field(None, description="Actual hours spent", ge=0)
    skills_used: Optional[List[str]] = Field(None, description="Skills used in this task")
    skills_learned: Optional[List[str]] = Field(None, description="Skills learned from this task")
    project_context: Optional[str] = Field(None, description="Project context for this task")


class UserSkillCreate(BaseModel):
    """Model for creating a new user skill."""
    skill_name: str = Field(..., description="Skill name", min_length=1, max_length=100)
    category: Optional[str] = Field(None, description="Skill category")
    level: SkillLevel = Field(SkillLevel.BEGINNER, description="Current skill level")
    source: SkillSource = Field(SkillSource.SELF_DECLARED, description="Source of skill assessment")
    confidence_score: Optional[float] = Field(None, description="Confidence score (0-1)", ge=0, le=1)
    learning_priority: Optional[str] = Field(None, description="Learning priority for this skill")
    target_level: Optional[SkillLevel] = Field(None, description="Target skill level")


class UserSkillUpdate(BaseModel):
    """Model for updating an existing user skill."""
    skill_name: Optional[str] = Field(None, description="Skill name", min_length=1, max_length=100)
    category: Optional[str] = Field(None, description="Skill category")
    level: Optional[SkillLevel] = Field(None, description="Current skill level")
    source: Optional[SkillSource] = Field(None, description="Source of skill assessment")
    confidence_score: Optional[float] = Field(None, description="Confidence score (0-1)", ge=0, le=1)
    last_used_date: Optional[date] = Field(None, description="Last date this skill was used")
    last_assessed_date: Optional[date] = Field(None, description="Last assessment date")
    evidence_count: Optional[int] = Field(None, description="Number of evidence pieces supporting this skill", ge=0)
    learning_priority: Optional[str] = Field(None, description="Learning priority for this skill")
    target_level: Optional[SkillLevel] = Field(None, description="Target skill level")
