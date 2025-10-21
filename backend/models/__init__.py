"""
Data models for the Personal Learning Agent.

This package contains all Pydantic models for user profiles, learning data,
skills assessment, and progress tracking.
"""

from .user import (
    UserProfile,
    UserProfileCreate,
    UserProfileUpdate,
    UserContext,
    UserPreferences,
    UserConnections,
    UserTask,
    UserTaskCreate,
    UserTaskUpdate,
    UserSkill,
    UserSkillCreate,
    UserSkillUpdate,
    SkillLevel,
    SkillSource,
    TeamInfo,
    ProjectInfo
)

from .learning import (
    LearningPath,
    LearningPathCreate,
    LearningPathUpdate,
    LearningContent,
    LearningContentCreate,
    LearningContentUpdate,
    LearningProgress,
    LearningProgressCreate,
    LearningProgressUpdate,
    ContentType,
    DifficultyLevel
)

from .skills import (
    SkillsAssessment,
    SkillsAssessmentCreate,
    SkillsAssessmentUpdate,
    SkillGap,
    SkillGapCreate,
    SkillGapUpdate,
    SkillsTaxonomy,
    SkillsTaxonomyCreate,
    SkillsTaxonomyUpdate
)

__all__ = [
    # User models
    "UserProfile",
    "UserProfileCreate", 
    "UserProfileUpdate",
    "UserContext",
    "UserPreferences",
    "UserConnections",
    "UserTask",
    "UserTaskCreate",
    "UserTaskUpdate",
    "UserSkill",
    "UserSkillCreate",
    "UserSkillUpdate",
    "SkillLevel",
    "SkillSource",
    "TeamInfo",
    "ProjectInfo",
    
    # Learning models
    "LearningPath",
    "LearningPathCreate",
    "LearningPathUpdate",
    "LearningContent",
    "LearningContentCreate",
    "LearningContentUpdate",
    "LearningProgress",
    "LearningProgressCreate",
    "LearningProgressUpdate",
    "ContentType",
    "DifficultyLevel",
    
    # Skills models
    "SkillsAssessment",
    "SkillsAssessmentCreate",
    "SkillsAssessmentUpdate",
    "SkillGap",
    "SkillGapCreate",
    "SkillGapUpdate",
    "SkillsTaxonomy",
    "SkillsTaxonomyCreate",
    "SkillsTaxonomyUpdate"
]
