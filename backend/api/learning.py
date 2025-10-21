"""
Learning API endpoints for the Personal Learning Agent.

This module provides REST API endpoints for learning path generation,
content management, and progress tracking.
"""

import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel

# Service imports
from ..services.learning_engine import get_learning_engine, PersonalizedLearningPath, LearningRecommendation
from ..services.skills_engine import get_skills_engine
from ..services.user_service import get_user_service

# Model imports
from ..models.learning import (
    LearningPath, LearningPathCreate, LearningPathUpdate,
    LearningContent, LearningContentCreate, LearningContentUpdate,
    LearningProgress, LearningProgressCreate, LearningProgressUpdate
)
from ..models.skills import SkillGap

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/learning", tags=["learning"])


class LearningPathGenerationRequest(BaseModel):
    """Request model for learning path generation."""
    user_id: str
    max_duration_hours: Optional[int] = None
    preferred_difficulty: Optional[str] = None
    skill_gap_ids: Optional[List[str]] = None


class LearningPathGenerationResponse(BaseModel):
    """Response model for learning path generation."""
    success: bool
    learning_path: Optional[Dict[str, Any]] = None
    message: str


class ContentRecommendationResponse(BaseModel):
    """Response model for content recommendations."""
    success: bool
    recommendations: List[Dict[str, Any]]
    total_count: int
    message: str


@router.get("/health")
async def health_check():
    """Health check endpoint for learning service."""
    try:
        learning_engine = get_learning_engine()
        return {
            "status": "healthy",
            "service": "learning_engine",
            "message": "Learning engine is operational"
        }
    except Exception as e:
        logger.error(f"Learning service health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Learning service unavailable: {str(e)}")


@router.post("/generate-path", response_model=LearningPathGenerationResponse)
async def generate_learning_path(request: LearningPathGenerationRequest):
    """
    Generate a personalized learning path for a user.
    
    Args:
        request: Learning path generation request
        
    Returns:
        LearningPathGenerationResponse: Generated learning path
    """
    logger.info(f"Generating learning path for user: {request.user_id}")
    
    try:
        learning_engine = get_learning_engine()
        skills_engine = get_skills_engine()
        
        # Get skill gaps if specific IDs provided
        skill_gaps = None
        if request.skill_gap_ids:
            skill_gaps = []
            for gap_id in request.skill_gap_ids:
                gap = skills_engine.get_skill_gap(gap_id)
                if gap:
                    skill_gaps.append(gap)
        
        # Generate learning path
        learning_path = learning_engine.generate_personalized_learning_path(
            user_id=request.user_id,
            skill_gaps=skill_gaps,
            max_duration_hours=request.max_duration_hours,
            preferred_difficulty=request.preferred_difficulty
        )
        
        # Convert to response format
        path_data = {
            "path_id": learning_path.path_id,
            "title": learning_path.title,
            "description": learning_path.description,
            "target_skills": learning_path.target_skills,
            "difficulty": learning_path.difficulty,
            "estimated_duration": learning_path.estimated_duration,
            "content_sequence": [
                {
                    "content_id": rec.content_id,
                    "title": rec.title,
                    "content_type": rec.content_type,
                    "difficulty": rec.difficulty,
                    "estimated_duration": rec.estimated_duration,
                    "skills_covered": rec.skills_covered,
                    "priority_score": rec.priority_score,
                    "reasoning": rec.reasoning,
                    "prerequisites": rec.prerequisites,
                    "learning_objectives": rec.learning_objectives
                }
                for rec in learning_path.content_sequence
            ],
            "prerequisites": learning_path.prerequisites,
            "learning_objectives": learning_path.learning_objectives,
            "priority_order": learning_path.priority_order,
            "success_metrics": learning_path.success_metrics,
            "created_at": learning_path.created_at.isoformat()
        }
        
        logger.info(f"Successfully generated learning path for user: {request.user_id}")
        return LearningPathGenerationResponse(
            success=True,
            learning_path=path_data,
            message=f"Learning path generated with {len(learning_path.content_sequence)} modules"
        )
        
    except Exception as e:
        logger.error(f"Error generating learning path for user {request.user_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate learning path: {str(e)}"
        )


@router.get("/path/{path_id}")
async def get_learning_path(path_id: str):
    """
    Get a specific learning path by ID.
    
    Args:
        path_id: Learning path ID
        
    Returns:
        Dict: Learning path details
    """
    logger.info(f"Getting learning path: {path_id}")
    
    try:
        learning_engine = get_learning_engine()
        learning_path = learning_engine.get_learning_path(path_id)
        
        if not learning_path:
            raise HTTPException(status_code=404, detail="Learning path not found")
        
        # Convert to response format
        path_data = {
            "path_id": learning_path.path_id,
            "title": learning_path.title,
            "description": learning_path.description,
            "target_skills": learning_path.target_skills,
            "difficulty": learning_path.difficulty,
            "estimated_duration": learning_path.estimated_duration,
            "content_sequence": [
                {
                    "content_id": rec.content_id,
                    "title": rec.title,
                    "content_type": rec.content_type,
                    "difficulty": rec.difficulty,
                    "estimated_duration": rec.estimated_duration,
                    "skills_covered": rec.skills_covered,
                    "priority_score": rec.priority_score,
                    "reasoning": rec.reasoning,
                    "prerequisites": rec.prerequisites,
                    "learning_objectives": rec.learning_objectives
                }
                for rec in learning_path.content_sequence
            ],
            "prerequisites": learning_path.prerequisites,
            "learning_objectives": learning_path.learning_objectives,
            "priority_order": learning_path.priority_order,
            "success_metrics": learning_path.success_metrics,
            "created_at": learning_path.created_at.isoformat()
        }
        
        return path_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting learning path {path_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get learning path: {str(e)}"
        )


@router.get("/user/{user_id}/paths")
async def get_user_learning_paths(user_id: str):
    """
    Get all learning paths for a user.
    
    Args:
        user_id: User ID
        
    Returns:
        List[Dict]: User's learning paths
    """
    logger.info(f"Getting learning paths for user: {user_id}")
    
    try:
        learning_engine = get_learning_engine()
        learning_paths = learning_engine.get_user_learning_paths(user_id)
        
        # Convert to response format
        paths_data = []
        for path in learning_paths:
            path_data = {
                "path_id": path.path_id,
                "title": path.title,
                "description": path.description,
                "target_skills": path.target_skills,
                "difficulty": path.difficulty,
                "estimated_duration": path.estimated_duration,
                "content_count": len(path.content_sequence),
                "created_at": path.created_at.isoformat()
            }
            paths_data.append(path_data)
        
        return {
            "success": True,
            "learning_paths": paths_data,
            "total_count": len(paths_data),
            "message": f"Found {len(paths_data)} learning paths for user"
        }
        
    except Exception as e:
        logger.error(f"Error getting learning paths for user {user_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get learning paths: {str(e)}"
        )


@router.get("/content/recommendations")
async def get_content_recommendations(
    skill_name: str = Query(..., description="Skill name to get recommendations for"),
    difficulty: Optional[str] = Query(None, description="Difficulty level filter"),
    limit: int = Query(10, description="Maximum number of recommendations", ge=1, le=50)
):
    """
    Get content recommendations for a specific skill.
    
    Args:
        skill_name: Skill name
        difficulty: Optional difficulty filter
        limit: Maximum number of recommendations
        
    Returns:
        ContentRecommendationResponse: Content recommendations
    """
    logger.info(f"Getting content recommendations for skill: {skill_name}")
    
    try:
        learning_engine = get_learning_engine()
        
        # Search for content
        content_list = learning_engine._search_existing_content(skill_name, difficulty or "beginner")
        
        # Convert to response format
        recommendations = []
        for content in content_list[:limit]:
            rec_data = {
                "content_id": content['id'],
                "title": content['title'],
                "content_type": content['content_type'],
                "difficulty": content['difficulty'],
                "estimated_duration": content['estimated_duration'],
                "skills_covered": content['skills_covered'],
                "prerequisites": content.get('prerequisites', []),
                "learning_objectives": content.get('learning_objectives', []),
                "reasoning": content.get('reasoning', '')
            }
            recommendations.append(rec_data)
        
        return ContentRecommendationResponse(
            success=True,
            recommendations=recommendations,
            total_count=len(recommendations),
            message=f"Found {len(recommendations)} content recommendations for {skill_name}"
        )
        
    except Exception as e:
        logger.error(f"Error getting content recommendations for {skill_name}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get content recommendations: {str(e)}"
        )


@router.get("/content/{content_id}")
async def get_learning_content(content_id: str):
    """
    Get specific learning content by ID.
    
    Args:
        content_id: Content ID
        
    Returns:
        Dict: Learning content details
    """
    logger.info(f"Getting learning content: {content_id}")
    
    try:
        learning_engine = get_learning_engine()
        content = learning_engine._get_content_recommendation(content_id)
        
        if not content:
            raise HTTPException(status_code=404, detail="Learning content not found")
        
        # Convert to response format
        content_data = {
            "content_id": content.content_id,
            "title": content.title,
            "content_type": content.content_type,
            "difficulty": content.difficulty,
            "estimated_duration": content.estimated_duration,
            "skills_covered": content.skills_covered,
            "prerequisites": content.prerequisites,
            "learning_objectives": content.learning_objectives,
            "reasoning": content.reasoning
        }
        
        return content_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting learning content {content_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get learning content: {str(e)}"
        )


@router.post("/content")
async def create_learning_content(content: LearningContentCreate):
    """
    Create new learning content.
    
    Args:
        content: Learning content creation data
        
    Returns:
        Dict: Created content details
    """
    logger.info(f"Creating learning content: {content.title}")
    
    try:
        learning_engine = get_learning_engine()
        
        # Convert to content dict
        content_dict = {
            'id': content.id or str(uuid.uuid4()),
            'title': content.title,
            'content_type': content.content_type.value,
            'difficulty': content.difficulty.value,
            'estimated_duration': content.estimated_duration or 10,
            'skills_covered': content.skills_covered,
            'prerequisites': content.prerequisites,
            'learning_objectives': content.learning_objectives,
            'content_text': content.content_text or '',
            'reasoning': f"User-created content: {content.title}"
        }
        
        # Store the content
        learning_engine._store_generated_content(content_dict)
        
        return {
            "success": True,
            "content_id": content_dict['id'],
            "message": f"Learning content '{content.title}' created successfully"
        }
        
    except Exception as e:
        logger.error(f"Error creating learning content: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create learning content: {str(e)}"
        )


@router.get("/categories")
async def get_content_categories():
    """
    Get available content categories and types.
    
    Returns:
        Dict: Content categories and micro-learning structure
    """
    try:
        learning_engine = get_learning_engine()
        
        return {
            "success": True,
            "content_categories": learning_engine.content_categories,
            "micro_learning_duration": learning_engine.micro_learning_duration,
            "message": "Content categories retrieved successfully"
        }
        
    except Exception as e:
        logger.error(f"Error getting content categories: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get content categories: {str(e)}"
        )


@router.get("/stats")
async def get_learning_stats():
    """
    Get learning system statistics.
    
    Returns:
        Dict: Learning system statistics
    """
    try:
        learning_engine = get_learning_engine()
        
        # Get basic stats from database
        db = learning_engine.db
        
        # Count learning paths
        path_count = db.execute_query("SELECT COUNT(*) FROM learning_paths WHERE is_active = 1")[0][0]
        
        # Count learning content
        content_count = db.execute_query("SELECT COUNT(*) FROM learning_content WHERE is_active = 1")[0][0]
        
        # Count by difficulty
        difficulty_stats = {}
        for difficulty in ['beginner', 'intermediate', 'advanced', 'expert']:
            count = db.execute_query(
                "SELECT COUNT(*) FROM learning_content WHERE difficulty = ? AND is_active = 1",
                (difficulty,)
            )[0][0]
            difficulty_stats[difficulty] = count
        
        # Count by content type
        content_type_stats = {}
        for content_type in ['article', 'video', 'exercise', 'quiz', 'tutorial', 'course']:
            count = db.execute_query(
                "SELECT COUNT(*) FROM learning_content WHERE content_type = ? AND is_active = 1",
                (content_type,)
            )[0][0]
            content_type_stats[content_type] = count
        
        return {
            "success": True,
            "statistics": {
                "total_learning_paths": path_count,
                "total_learning_content": content_count,
                "difficulty_distribution": difficulty_stats,
                "content_type_distribution": content_type_stats,
                "micro_learning_targets": learning_engine.micro_learning_duration
            },
            "message": "Learning statistics retrieved successfully"
        }
        
    except Exception as e:
        logger.error(f"Error getting learning stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get learning statistics: {str(e)}"
        )
