"""
User profile API endpoints for the Personal Learning Agent.

This module provides REST API endpoints for user profile management,
task tracking, skill management, and context retrieval.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional, Dict, Any
import logging

from ..models.user import (
    UserProfile, UserProfileCreate, UserProfileUpdate,
    UserTask, UserTaskCreate, UserTaskUpdate,
    UserSkill, UserSkillCreate, UserSkillUpdate,
    UserContext
)
from ..services.user_service import get_user_service, UserService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/users", tags=["users"])


# Dependency injection
def get_user_service_dependency() -> UserService:
    """Get user service dependency."""
    return get_user_service()


# User Profile Endpoints

@router.post("/", response_model=UserProfile, status_code=status.HTTP_201_CREATED)
async def create_user_profile(
    profile_data: UserProfileCreate,
    user_service: UserService = Depends(get_user_service_dependency)
):
    """
    Create a new user profile.
    
    Args:
        profile_data: User profile creation data
        user_service: User service dependency
        
    Returns:
        UserProfile: Created user profile
        
    Raises:
        HTTPException: If username already exists or creation fails
    """
    try:
        logger.info(f"Creating user profile for username: {profile_data.username}")
        user_profile = user_service.create_user_profile(profile_data)
        return user_profile
    except ValueError as e:
        logger.warning(f"Validation error creating user profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating user profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user profile"
        )


@router.get("/{user_id}", response_model=UserProfile)
async def get_user_profile(
    user_id: str,
    user_service: UserService = Depends(get_user_service_dependency)
):
    """
    Get user profile by ID.
    
    Args:
        user_id: User ID
        user_service: User service dependency
        
    Returns:
        UserProfile: User profile
        
    Raises:
        HTTPException: If user not found
    """
    try:
        user_profile = user_service.get_user_profile(user_id)
        if not user_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User profile not found for ID: {user_id}"
            )
        return user_profile
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user profile"
        )


@router.get("/username/{username}", response_model=UserProfile)
async def get_user_by_username(
    username: str,
    user_service: UserService = Depends(get_user_service_dependency)
):
    """
    Get user profile by username.
    
    Args:
        username: Username
        user_service: User service dependency
        
    Returns:
        UserProfile: User profile
        
    Raises:
        HTTPException: If user not found
    """
    try:
        user_profile = user_service.get_user_by_username(username)
        if not user_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User profile not found for username: {username}"
            )
        return user_profile
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user by username: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user profile"
        )


@router.put("/{user_id}", response_model=UserProfile)
async def update_user_profile(
    user_id: str,
    update_data: UserProfileUpdate,
    user_service: UserService = Depends(get_user_service_dependency)
):
    """
    Update user profile.
    
    Args:
        user_id: User ID
        update_data: Profile update data
        user_service: User service dependency
        
    Returns:
        UserProfile: Updated user profile
        
    Raises:
        HTTPException: If user not found or update fails
    """
    try:
        user_profile = user_service.update_user_profile(user_id, update_data)
        if not user_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User profile not found for ID: {user_id}"
            )
        return user_profile
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user profile"
        )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_profile(
    user_id: str,
    user_service: UserService = Depends(get_user_service_dependency)
):
    """
    Delete user profile (soft delete).
    
    Args:
        user_id: User ID
        user_service: User service dependency
        
    Raises:
        HTTPException: If deletion fails
    """
    try:
        success = user_service.delete_user_profile(user_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User profile not found for ID: {user_id}"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user profile"
        )


# User Task Endpoints

@router.post("/{user_id}/tasks", response_model=UserTask, status_code=status.HTTP_201_CREATED)
async def create_user_task(
    user_id: str,
    task_data: UserTaskCreate,
    user_service: UserService = Depends(get_user_service_dependency)
):
    """
    Create a new user task.
    
    Args:
        user_id: User ID
        task_data: Task creation data
        user_service: User service dependency
        
    Returns:
        UserTask: Created task
        
    Raises:
        HTTPException: If user not found or creation fails
    """
    try:
        # Verify user exists
        if not user_service.get_user_profile(user_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User profile not found for ID: {user_id}"
            )
        
        task = user_service.create_user_task(user_id, task_data)
        return task
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating user task: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user task"
        )


@router.get("/{user_id}/tasks", response_model=List[UserTask])
async def get_user_tasks(
    user_id: str,
    status: Optional[str] = None,
    limit: int = 50,
    user_service: UserService = Depends(get_user_service_dependency)
):
    """
    Get user tasks with optional filtering.
    
    Args:
        user_id: User ID
        status: Optional status filter
        limit: Maximum number of tasks to return
        user_service: User service dependency
        
    Returns:
        List[UserTask]: List of user tasks
        
    Raises:
        HTTPException: If user not found
    """
    try:
        # Verify user exists
        if not user_service.get_user_profile(user_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User profile not found for ID: {user_id}"
            )
        
        tasks = user_service.get_user_tasks(user_id, status, limit)
        return tasks
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user tasks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user tasks"
        )


@router.get("/tasks/{task_id}", response_model=UserTask)
async def get_user_task(
    task_id: str,
    user_service: UserService = Depends(get_user_service_dependency)
):
    """
    Get user task by ID.
    
    Args:
        task_id: Task ID
        user_service: User service dependency
        
    Returns:
        UserTask: User task
        
    Raises:
        HTTPException: If task not found
    """
    try:
        task = user_service.get_user_task(task_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task not found for ID: {task_id}"
            )
        return task
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user task: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user task"
        )


@router.put("/tasks/{task_id}", response_model=UserTask)
async def update_user_task(
    task_id: str,
    update_data: UserTaskUpdate,
    user_service: UserService = Depends(get_user_service_dependency)
):
    """
    Update user task.
    
    Args:
        task_id: Task ID
        update_data: Task update data
        user_service: User service dependency
        
    Returns:
        UserTask: Updated task
        
    Raises:
        HTTPException: If task not found or update fails
    """
    try:
        task = user_service.update_user_task(task_id, update_data)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task not found for ID: {task_id}"
            )
        return task
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user task: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user task"
        )


# User Skill Endpoints

@router.post("/{user_id}/skills", response_model=UserSkill, status_code=status.HTTP_201_CREATED)
async def create_user_skill(
    user_id: str,
    skill_data: UserSkillCreate,
    user_service: UserService = Depends(get_user_service_dependency)
):
    """
    Create a new user skill.
    
    Args:
        user_id: User ID
        skill_data: Skill creation data
        user_service: User service dependency
        
    Returns:
        UserSkill: Created skill
        
    Raises:
        HTTPException: If user not found or creation fails
    """
    try:
        # Verify user exists
        if not user_service.get_user_profile(user_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User profile not found for ID: {user_id}"
            )
        
        skill = user_service.create_user_skill(user_id, skill_data)
        return skill
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating user skill: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user skill"
        )


@router.get("/{user_id}/skills", response_model=List[UserSkill])
async def get_user_skills(
    user_id: str,
    category: Optional[str] = None,
    user_service: UserService = Depends(get_user_service_dependency)
):
    """
    Get user skills with optional category filtering.
    
    Args:
        user_id: User ID
        category: Optional category filter
        user_service: User service dependency
        
    Returns:
        List[UserSkill]: List of user skills
        
    Raises:
        HTTPException: If user not found
    """
    try:
        # Verify user exists
        if not user_service.get_user_profile(user_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User profile not found for ID: {user_id}"
            )
        
        skills = user_service.get_user_skills(user_id, category)
        return skills
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user skills: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user skills"
        )


@router.get("/skills/{skill_id}", response_model=UserSkill)
async def get_user_skill(
    skill_id: str,
    user_service: UserService = Depends(get_user_service_dependency)
):
    """
    Get user skill by ID.
    
    Args:
        skill_id: Skill ID
        user_service: User service dependency
        
    Returns:
        UserSkill: User skill
        
    Raises:
        HTTPException: If skill not found
    """
    try:
        skill = user_service.get_user_skill(skill_id)
        if not skill:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Skill not found for ID: {skill_id}"
            )
        return skill
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user skill: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user skill"
        )


@router.put("/skills/{skill_id}", response_model=UserSkill)
async def update_user_skill(
    skill_id: str,
    update_data: UserSkillUpdate,
    user_service: UserService = Depends(get_user_service_dependency)
):
    """
    Update user skill.
    
    Args:
        skill_id: Skill ID
        update_data: Skill update data
        user_service: User service dependency
        
    Returns:
        UserSkill: Updated skill
        
    Raises:
        HTTPException: If skill not found or update fails
    """
    try:
        skill = user_service.update_user_skill(skill_id, update_data)
        if not skill:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Skill not found for ID: {skill_id}"
            )
        return skill
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user skill: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user skill"
        )


# User Context and Analytics Endpoints

@router.get("/{user_id}/context", response_model=Dict[str, Any])
async def get_user_context(
    user_id: str,
    user_service: UserService = Depends(get_user_service_dependency)
):
    """
    Get user context for AI personalization.
    
    Args:
        user_id: User ID
        user_service: User service dependency
        
    Returns:
        Dict: User context for AI consumption
        
    Raises:
        HTTPException: If user not found or context retrieval fails
    """
    try:
        # Verify user exists
        if not user_service.get_user_profile(user_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User profile not found for ID: {user_id}"
            )
        
        context = user_service.get_user_context(user_id)
        if not context:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve user context"
            )
        return context
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user context: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user context"
        )


@router.post("/{user_id}/context/refresh", response_model=Dict[str, Any])
async def refresh_user_context(
    user_id: str,
    user_service: UserService = Depends(get_user_service_dependency)
):
    """
    Refresh user context by rebuilding it from current data.
    
    Args:
        user_id: User ID
        user_service: User service dependency
        
    Returns:
        Dict: Refreshed user context
        
    Raises:
        HTTPException: If user not found or refresh fails
    """
    try:
        # Verify user exists
        if not user_service.get_user_profile(user_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User profile not found for ID: {user_id}"
            )
        
        context = user_service.refresh_user_context(user_id)
        return context.dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error refreshing user context: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to refresh user context"
        )


@router.get("/{user_id}/analytics", response_model=Dict[str, Any])
async def get_user_analytics(
    user_id: str,
    user_service: UserService = Depends(get_user_service_dependency)
):
    """
    Get user analytics and statistics.
    
    Args:
        user_id: User ID
        user_service: User service dependency
        
    Returns:
        Dict: User analytics data
        
    Raises:
        HTTPException: If user not found or analytics retrieval fails
    """
    try:
        # Verify user exists
        if not user_service.get_user_profile(user_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User profile not found for ID: {user_id}"
            )
        
        analytics = user_service.get_user_analytics(user_id)
        return analytics
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user analytics"
        )


# Health Check Endpoint

@router.get("/health", response_model=Dict[str, str])
async def health_check():
    """
    Health check endpoint for user service.
    
    Returns:
        Dict: Health status
    """
    return {"status": "healthy", "service": "user_service"}
