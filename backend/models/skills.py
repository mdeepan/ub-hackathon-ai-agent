"""
Skills assessment data models for the Personal Learning Agent.

This module contains Pydantic models for skills assessment, gap analysis, and taxonomy.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum
import uuid


class AssessmentStatus(str, Enum):
    """Status of skills assessment."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class AssessmentType(str, Enum):
    """Type of skills assessment."""
    ARTIFACT_ANALYSIS = "artifact_analysis"
    SELF_ASSESSMENT = "self_assessment"
    PEER_REVIEW = "peer_review"
    AUTOMATED_TEST = "automated_test"
    WORK_SAMPLE = "work_sample"


class SkillsAssessment(BaseModel):
    """Skills assessment model."""
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique assessment ID")
    user_id: str = Field(..., description="User ID")
    assessment_type: AssessmentType = Field(AssessmentType.ARTIFACT_ANALYSIS, description="Type of assessment")
    status: AssessmentStatus = Field(AssessmentStatus.PENDING, description="Assessment status")
    title: str = Field(..., description="Assessment title", min_length=1, max_length=200)
    description: Optional[str] = Field(None, description="Assessment description", max_length=2000)
    artifacts_analyzed: List[str] = Field(default_factory=list, description="List of artifact IDs analyzed")
    skills_evaluated: List[str] = Field(default_factory=list, description="Skills evaluated in this assessment")
    overall_score: Optional[float] = Field(None, description="Overall assessment score (0-100)", ge=0, le=100)
    confidence_level: Optional[float] = Field(None, description="Confidence level of assessment (0-1)", ge=0, le=1)
    assessment_data: Optional[Dict[str, Any]] = Field(None, description="Raw assessment data and results")
    recommendations: List[str] = Field(default_factory=list, description="Learning recommendations based on assessment")
    started_at: Optional[datetime] = Field(None, description="When assessment started")
    completed_at: Optional[datetime] = Field(None, description="When assessment was completed")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Assessment creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Assessment last update timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user_123",
                "assessment_type": "artifact_analysis",
                "status": "completed",
                "title": "Product Management Skills Assessment",
                "description": "Assessment based on recent PRDs and user stories",
                "artifacts_analyzed": ["artifact_1", "artifact_2"],
                "skills_evaluated": ["Product Strategy", "User Research", "Technical Writing"],
                "overall_score": 75.5,
                "confidence_level": 0.85,
                "recommendations": [
                    "Focus on advanced user research techniques",
                    "Improve technical documentation skills"
                ]
            }
        }


class SkillGap(BaseModel):
    """Skill gap model for identifying learning needs."""
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique gap ID")
    user_id: str = Field(..., description="User ID")
    skill_name: str = Field(..., description="Skill name", min_length=1, max_length=100)
    category: Optional[str] = Field(None, description="Skill category")
    current_level: Optional[str] = Field(None, description="Current skill level")
    target_level: Optional[str] = Field(None, description="Target skill level")
    gap_size: Optional[str] = Field(None, description="Size of the gap (small, medium, large)")
    priority: str = Field("medium", description="Learning priority")
    urgency: str = Field("medium", description="Urgency of addressing this gap")
    business_impact: Optional[str] = Field(None, description="Expected business impact")
    learning_effort: Optional[str] = Field(None, description="Estimated learning effort")
    evidence_sources: List[str] = Field(default_factory=list, description="Sources of evidence for this gap")
    recommended_actions: List[str] = Field(default_factory=list, description="Recommended learning actions")
    related_skills: List[str] = Field(default_factory=list, description="Related skills to consider")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Gap creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Gap last update timestamp")
    
    @validator('priority')
    def validate_priority(cls, v):
        allowed_priorities = ['low', 'medium', 'high', 'critical']
        if v not in allowed_priorities:
            raise ValueError(f'Priority must be one of: {allowed_priorities}')
        return v
    
    @validator('urgency')
    def validate_urgency(cls, v):
        allowed_urgencies = ['low', 'medium', 'high', 'critical']
        if v not in allowed_urgencies:
            raise ValueError(f'Urgency must be one of: {allowed_urgencies}')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user_123",
                "skill_name": "Advanced JavaScript",
                "category": "Programming",
                "current_level": "intermediate",
                "target_level": "advanced",
                "gap_size": "medium",
                "priority": "high",
                "urgency": "medium",
                "business_impact": "Critical for upcoming mobile app project",
                "learning_effort": "20-30 hours",
                "evidence_sources": ["code_review", "project_requirements"],
                "recommended_actions": [
                    "Complete advanced JavaScript course",
                    "Practice with React Native projects",
                    "Review modern ES6+ features"
                ],
                "related_skills": ["React Native", "TypeScript", "API Design"]
            }
        }


class SkillsTaxonomy(BaseModel):
    """Skills taxonomy model for organizing and categorizing skills."""
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique taxonomy ID")
    skill_name: str = Field(..., description="Skill name", min_length=1, max_length=100)
    category: str = Field(..., description="Skill category", min_length=1, max_length=50)
    subcategory: Optional[str] = Field(None, description="Skill subcategory", max_length=50)
    description: Optional[str] = Field(None, description="Skill description", max_length=1000)
    proficiency_levels: List[str] = Field(default_factory=list, description="Available proficiency levels")
    related_skills: List[str] = Field(default_factory=list, description="Related skills")
    prerequisites: List[str] = Field(default_factory=list, description="Prerequisite skills")
    typical_use_cases: List[str] = Field(default_factory=list, description="Typical use cases for this skill")
    industry_relevance: List[str] = Field(default_factory=list, description="Industries where this skill is relevant")
    learning_resources: List[str] = Field(default_factory=list, description="Suggested learning resources")
    assessment_methods: List[str] = Field(default_factory=list, description="Methods for assessing this skill")
    is_active: bool = Field(True, description="Whether this skill is active in the taxonomy")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Taxonomy creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Taxonomy last update timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "skill_name": "Product Strategy",
                "category": "Product Management",
                "subcategory": "Strategic Planning",
                "description": "Ability to develop and execute product strategies aligned with business goals",
                "proficiency_levels": ["beginner", "intermediate", "advanced", "expert"],
                "related_skills": ["Market Research", "Business Analysis", "Competitive Analysis"],
                "prerequisites": ["Product Management Basics", "Business Fundamentals"],
                "typical_use_cases": [
                    "Product roadmap planning",
                    "Market positioning",
                    "Feature prioritization"
                ],
                "industry_relevance": ["Technology", "E-commerce", "SaaS", "Fintech"],
                "learning_resources": [
                    "Product Strategy courses",
                    "Case studies",
                    "Industry reports"
                ],
                "assessment_methods": [
                    "Strategy document review",
                    "Market analysis presentation",
                    "Stakeholder feedback"
                ]
            }
        }


# Create and Update models for API operations
class SkillsAssessmentCreate(BaseModel):
    """Model for creating new skills assessments."""
    user_id: str = Field(..., description="User ID")
    assessment_type: AssessmentType = Field(AssessmentType.ARTIFACT_ANALYSIS, description="Type of assessment")
    title: str = Field(..., description="Assessment title", min_length=1, max_length=200)
    description: Optional[str] = Field(None, description="Assessment description", max_length=2000)
    artifacts_analyzed: List[str] = Field(default_factory=list, description="List of artifact IDs analyzed")
    skills_evaluated: List[str] = Field(default_factory=list, description="Skills evaluated in this assessment")


class SkillsAssessmentUpdate(BaseModel):
    """Model for updating existing skills assessments."""
    assessment_type: Optional[AssessmentType] = Field(None, description="Type of assessment")
    status: Optional[AssessmentStatus] = Field(None, description="Assessment status")
    title: Optional[str] = Field(None, description="Assessment title", min_length=1, max_length=200)
    description: Optional[str] = Field(None, description="Assessment description", max_length=2000)
    artifacts_analyzed: Optional[List[str]] = Field(None, description="List of artifact IDs analyzed")
    skills_evaluated: Optional[List[str]] = Field(None, description="Skills evaluated in this assessment")
    overall_score: Optional[float] = Field(None, description="Overall assessment score (0-100)", ge=0, le=100)
    confidence_level: Optional[float] = Field(None, description="Confidence level of assessment (0-1)", ge=0, le=1)
    assessment_data: Optional[Dict[str, Any]] = Field(None, description="Raw assessment data and results")
    recommendations: Optional[List[str]] = Field(None, description="Learning recommendations based on assessment")
    started_at: Optional[datetime] = Field(None, description="When assessment started")
    completed_at: Optional[datetime] = Field(None, description="When assessment was completed")


class SkillGapCreate(BaseModel):
    """Model for creating new skill gaps."""
    user_id: str = Field(..., description="User ID")
    skill_name: str = Field(..., description="Skill name", min_length=1, max_length=100)
    category: Optional[str] = Field(None, description="Skill category")
    current_level: Optional[str] = Field(None, description="Current skill level")
    target_level: Optional[str] = Field(None, description="Target skill level")
    gap_size: Optional[str] = Field(None, description="Size of the gap (small, medium, large)")
    priority: str = Field("medium", description="Learning priority")
    urgency: str = Field("medium", description="Urgency of addressing this gap")
    business_impact: Optional[str] = Field(None, description="Expected business impact")
    learning_effort: Optional[str] = Field(None, description="Estimated learning effort")
    evidence_sources: List[str] = Field(default_factory=list, description="Sources of evidence for this gap")
    recommended_actions: List[str] = Field(default_factory=list, description="Recommended learning actions")
    related_skills: List[str] = Field(default_factory=list, description="Related skills to consider")


class SkillGapUpdate(BaseModel):
    """Model for updating existing skill gaps."""
    skill_name: Optional[str] = Field(None, description="Skill name", min_length=1, max_length=100)
    category: Optional[str] = Field(None, description="Skill category")
    current_level: Optional[str] = Field(None, description="Current skill level")
    target_level: Optional[str] = Field(None, description="Target skill level")
    gap_size: Optional[str] = Field(None, description="Size of the gap (small, medium, large)")
    priority: Optional[str] = Field(None, description="Learning priority")
    urgency: Optional[str] = Field(None, description="Urgency of addressing this gap")
    business_impact: Optional[str] = Field(None, description="Expected business impact")
    learning_effort: Optional[str] = Field(None, description="Estimated learning effort")
    evidence_sources: Optional[List[str]] = Field(None, description="Sources of evidence for this gap")
    recommended_actions: Optional[List[str]] = Field(None, description="Recommended learning actions")
    related_skills: Optional[List[str]] = Field(None, description="Related skills to consider")


class SkillsTaxonomyCreate(BaseModel):
    """Model for creating new skills taxonomy entries."""
    skill_name: str = Field(..., description="Skill name", min_length=1, max_length=100)
    category: str = Field(..., description="Skill category", min_length=1, max_length=50)
    subcategory: Optional[str] = Field(None, description="Skill subcategory", max_length=50)
    description: Optional[str] = Field(None, description="Skill description", max_length=1000)
    proficiency_levels: List[str] = Field(default_factory=list, description="Available proficiency levels")
    related_skills: List[str] = Field(default_factory=list, description="Related skills")
    prerequisites: List[str] = Field(default_factory=list, description="Prerequisite skills")
    typical_use_cases: List[str] = Field(default_factory=list, description="Typical use cases for this skill")
    industry_relevance: List[str] = Field(default_factory=list, description="Industries where this skill is relevant")
    learning_resources: List[str] = Field(default_factory=list, description="Suggested learning resources")
    assessment_methods: List[str] = Field(default_factory=list, description="Methods for assessing this skill")


class SkillsTaxonomyUpdate(BaseModel):
    """Model for updating existing skills taxonomy entries."""
    skill_name: Optional[str] = Field(None, description="Skill name", min_length=1, max_length=100)
    category: Optional[str] = Field(None, description="Skill category", min_length=1, max_length=50)
    subcategory: Optional[str] = Field(None, description="Skill subcategory", max_length=50)
    description: Optional[str] = Field(None, description="Skill description", max_length=1000)
    proficiency_levels: Optional[List[str]] = Field(None, description="Available proficiency levels")
    related_skills: Optional[List[str]] = Field(None, description="Related skills")
    prerequisites: Optional[List[str]] = Field(None, description="Prerequisite skills")
    typical_use_cases: Optional[List[str]] = Field(None, description="Typical use cases for this skill")
    industry_relevance: Optional[List[str]] = Field(None, description="Industries where this skill is relevant")
    learning_resources: Optional[List[str]] = Field(None, description="Suggested learning resources")
    assessment_methods: Optional[List[str]] = Field(None, description="Methods for assessing this skill")
    is_active: Optional[bool] = Field(None, description="Whether this skill is active in the taxonomy")
