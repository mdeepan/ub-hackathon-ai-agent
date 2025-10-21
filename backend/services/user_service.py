"""
User service for profile management and CRUD operations.

This module provides comprehensive user profile management including creation,
updates, retrieval, and context building for the Personal Learning Agent.
"""

import json
import uuid
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, date
import logging

from ..database.connection import get_database
from ..models.user import (
    UserProfile, UserProfileCreate, UserProfileUpdate,
    UserTask, UserTaskCreate, UserTaskUpdate,
    UserSkill, UserSkillCreate, UserSkillUpdate,
    UserContext, UserConnections, TeamInfo, ProjectInfo, UserPreferences
)
from .user_context_builder import get_user_context_builder

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UserService:
    """
    User service for comprehensive profile management.
    
    This service handles all user-related operations including profile management,
    task tracking, skill management, and context building.
    """
    
    def __init__(self):
        """Initialize the user service."""
        self.db = get_database()
        self.context_builder = get_user_context_builder()
        logger.info("User service initialized")
    
    # User Profile Management
    
    def create_user_profile(self, profile_data: UserProfileCreate) -> UserProfile:
        """
        Create a new user profile.
        
        Args:
            profile_data: User profile creation data
            
        Returns:
            UserProfile: Created user profile
            
        Raises:
            ValueError: If username already exists
        """
        logger.info(f"Creating user profile for username: {profile_data.username}")
        
        try:
            # Check if username already exists
            if self.get_user_by_username(profile_data.username):
                raise ValueError(f"Username '{profile_data.username}' already exists")
            
            # Generate user ID
            user_id = str(uuid.uuid4())
            
            # Prepare profile data for database
            profile_dict = profile_data.dict()
            
            # Convert complex objects to JSON strings
            json_fields = ['personal_goals', 'team_info', 'project_info', 'connections', 'preferences']
            for field in json_fields:
                if profile_dict.get(field):
                    profile_dict[field] = json.dumps(profile_dict[field])
                else:
                    profile_dict[field] = None
            
            # Insert user profile
            insert_query = """
            INSERT INTO user_profiles (
                id, username, name, job_role, experience_summary,
                personal_goals, team_info, project_info, connections, preferences, skill_gaps
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            params = (
                user_id,
                profile_dict['username'],
                profile_dict['name'],
                profile_dict['job_role'],
                profile_dict['experience_summary'],
                profile_dict['personal_goals'],
                profile_dict['team_info'],
                profile_dict['project_info'],
                profile_dict['connections'],
                profile_dict['preferences'],
                json.dumps([])  # Empty skill gaps initially
            )
            
            self.db.execute_update(insert_query, params)
            
            # Get created profile
            created_profile = self.get_user_profile(user_id)
            
            # Build initial user context
            self.context_builder.build_user_context(user_id)
            
            logger.info(f"User profile created successfully: {user_id}")
            return created_profile
            
        except Exception as e:
            logger.error(f"Error creating user profile: {e}")
            raise
    
    def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """
        Get user profile by ID.
        
        Args:
            user_id: User ID
            
        Returns:
            UserProfile: User profile or None if not found
        """
        query = "SELECT * FROM user_profiles WHERE id = ? AND is_active = 1"
        results = self.db.execute_query(query, (user_id,))
        
        if not results:
            return None
        
        return self._parse_user_profile(results[0])
    
    def get_user_by_username(self, username: str) -> Optional[UserProfile]:
        """
        Get user profile by username.
        
        Args:
            username: Username
            
        Returns:
            UserProfile: User profile or None if not found
        """
        query = "SELECT * FROM user_profiles WHERE username = ? AND is_active = 1"
        results = self.db.execute_query(query, (username,))
        
        if not results:
            return None
        
        return self._parse_user_profile(results[0])
    
    def update_user_profile(self, user_id: str, update_data: UserProfileUpdate) -> Optional[UserProfile]:
        """
        Update user profile.
        
        Args:
            user_id: User ID
            update_data: Profile update data
            
        Returns:
            UserProfile: Updated user profile or None if not found
        """
        logger.info(f"Updating user profile: {user_id}")
        
        try:
            # Check if user exists
            if not self.get_user_profile(user_id):
                return None
            
            # Prepare update data
            update_dict = update_data.dict(exclude_unset=True)
            
            # Convert complex objects to JSON strings
            json_fields = ['personal_goals', 'team_info', 'project_info', 'connections', 'preferences']
            for field in json_fields:
                if field in update_dict and update_dict[field] is not None:
                    update_dict[field] = json.dumps(update_dict[field])
            
            # Build update query
            set_clauses = []
            params = []
            
            for field, value in update_dict.items():
                set_clauses.append(f"{field} = ?")
                params.append(value)
            
            if not set_clauses:
                return self.get_user_profile(user_id)
            
            set_clauses.append("updated_at = CURRENT_TIMESTAMP")
            params.append(user_id)
            
            update_query = f"""
            UPDATE user_profiles 
            SET {', '.join(set_clauses)}
            WHERE id = ?
            """
            
            self.db.execute_update(update_query, tuple(params))
            
            # Refresh user context
            self.context_builder.refresh_user_context(user_id)
            
            logger.info(f"User profile updated successfully: {user_id}")
            return self.get_user_profile(user_id)
            
        except Exception as e:
            logger.error(f"Error updating user profile: {e}")
            raise
    
    def delete_user_profile(self, user_id: str) -> bool:
        """
        Soft delete user profile.
        
        Args:
            user_id: User ID
            
        Returns:
            bool: True if deleted successfully
        """
        logger.info(f"Deleting user profile: {user_id}")
        
        try:
            update_query = """
            UPDATE user_profiles 
            SET is_active = 0, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """
            
            affected_rows = self.db.execute_update(update_query, (user_id,))
            
            if affected_rows > 0:
                logger.info(f"User profile deleted successfully: {user_id}")
                return True
            else:
                logger.warning(f"User profile not found for deletion: {user_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting user profile: {e}")
            raise
    
    # User Task Management
    
    def create_user_task(self, user_id: str, task_data: UserTaskCreate) -> UserTask:
        """
        Create a new user task.
        
        Args:
            user_id: User ID
            task_data: Task creation data
            
        Returns:
            UserTask: Created task
        """
        logger.info(f"Creating task for user: {user_id}")
        
        try:
            task_id = str(uuid.uuid4())
            task_dict = task_data.dict()
            
            # Convert lists to JSON strings
            json_fields = ['skills_used', 'skills_learned']
            for field in json_fields:
                if task_dict.get(field):
                    task_dict[field] = json.dumps(task_dict[field])
                else:
                    task_dict[field] = json.dumps([])
            
            insert_query = """
            INSERT INTO user_tasks (
                id, user_id, title, description, status, priority,
                due_date, estimated_hours, skills_used, skills_learned, project_context
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            params = (
                task_id,
                user_id,
                task_dict['title'],
                task_dict['description'],
                task_dict['status'],
                task_dict['priority'],
                task_dict['due_date'],
                task_dict['estimated_hours'],
                task_dict['skills_used'],
                task_dict['skills_learned'],
                task_dict['project_context']
            )
            
            self.db.execute_update(insert_query, params)
            
            # Refresh user context
            self.context_builder.refresh_user_context(user_id)
            
            logger.info(f"Task created successfully: {task_id}")
            return self.get_user_task(task_id)
            
        except Exception as e:
            logger.error(f"Error creating user task: {e}")
            raise
    
    def get_user_task(self, task_id: str) -> Optional[UserTask]:
        """Get user task by ID."""
        query = "SELECT * FROM user_tasks WHERE id = ?"
        results = self.db.execute_query(query, (task_id,))
        
        if not results:
            return None
        
        return self._parse_user_task(results[0])
    
    def get_user_tasks(self, user_id: str, status: Optional[str] = None, limit: int = 50) -> List[UserTask]:
        """
        Get user tasks with optional filtering.
        
        Args:
            user_id: User ID
            status: Optional status filter
            limit: Maximum number of tasks to return
            
        Returns:
            List[UserTask]: List of user tasks
        """
        query = "SELECT * FROM user_tasks WHERE user_id = ?"
        params = [user_id]
        
        if status:
            query += " AND status = ?"
            params.append(status)
        
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        
        results = self.db.execute_query(query, tuple(params))
        return [self._parse_user_task(result) for result in results]
    
    def update_user_task(self, task_id: str, update_data: UserTaskUpdate) -> Optional[UserTask]:
        """Update user task."""
        logger.info(f"Updating task: {task_id}")
        
        try:
            # Check if task exists
            if not self.get_user_task(task_id):
                return None
            
            # Get user_id for context refresh
            user_query = "SELECT user_id FROM user_tasks WHERE id = ?"
            user_results = self.db.execute_query(user_query, (task_id,))
            if not user_results:
                return None
            user_id = user_results[0]['user_id']
            
            # Prepare update data
            update_dict = update_data.dict(exclude_unset=True)
            
            # Convert lists to JSON strings
            json_fields = ['skills_used', 'skills_learned']
            for field in json_fields:
                if field in update_dict and update_dict[field] is not None:
                    update_dict[field] = json.dumps(update_dict[field])
            
            # Build update query
            set_clauses = []
            params = []
            
            for field, value in update_dict.items():
                set_clauses.append(f"{field} = ?")
                params.append(value)
            
            if not set_clauses:
                return self.get_user_task(task_id)
            
            set_clauses.append("updated_at = CURRENT_TIMESTAMP")
            params.append(task_id)
            
            update_query = f"""
            UPDATE user_tasks 
            SET {', '.join(set_clauses)}
            WHERE id = ?
            """
            
            self.db.execute_update(update_query, tuple(params))
            
            # Refresh user context
            self.context_builder.refresh_user_context(user_id)
            
            logger.info(f"Task updated successfully: {task_id}")
            return self.get_user_task(task_id)
            
        except Exception as e:
            logger.error(f"Error updating user task: {e}")
            raise
    
    # User Skill Management
    
    def create_user_skill(self, user_id: str, skill_data: UserSkillCreate) -> UserSkill:
        """Create a new user skill."""
        logger.info(f"Creating skill for user: {user_id}")
        
        try:
            skill_id = str(uuid.uuid4())
            skill_dict = skill_data.dict()
            
            insert_query = """
            INSERT INTO user_skills (
                id, user_id, skill_name, category, level, source,
                confidence_score, learning_priority, target_level
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            params = (
                skill_id,
                user_id,
                skill_dict['skill_name'],
                skill_dict['category'],
                skill_dict['level'],
                skill_dict['source'],
                skill_dict['confidence_score'],
                skill_dict['learning_priority'],
                skill_dict['target_level']
            )
            
            self.db.execute_update(insert_query, params)
            
            # Refresh user context
            self.context_builder.refresh_user_context(user_id)
            
            logger.info(f"Skill created successfully: {skill_id}")
            return self.get_user_skill(skill_id)
            
        except Exception as e:
            logger.error(f"Error creating user skill: {e}")
            raise
    
    def get_user_skill(self, skill_id: str) -> Optional[UserSkill]:
        """Get user skill by ID."""
        query = "SELECT * FROM user_skills WHERE id = ?"
        results = self.db.execute_query(query, (skill_id,))
        
        if not results:
            return None
        
        return self._parse_user_skill(results[0])
    
    def get_user_skills(self, user_id: str, category: Optional[str] = None) -> List[UserSkill]:
        """Get user skills with optional category filtering."""
        query = "SELECT * FROM user_skills WHERE user_id = ?"
        params = [user_id]
        
        if category:
            query += " AND category = ?"
            params.append(category)
        
        query += " ORDER BY created_at DESC"
        
        results = self.db.execute_query(query, tuple(params))
        return [self._parse_user_skill(result) for result in results]
    
    def update_user_skill(self, skill_id: str, update_data: UserSkillUpdate) -> Optional[UserSkill]:
        """Update user skill."""
        logger.info(f"Updating skill: {skill_id}")
        
        try:
            # Check if skill exists
            if not self.get_user_skill(skill_id):
                return None
            
            # Get user_id for context refresh
            user_query = "SELECT user_id FROM user_skills WHERE id = ?"
            user_results = self.db.execute_query(user_query, (skill_id,))
            if not user_results:
                return None
            user_id = user_results[0]['user_id']
            
            # Prepare update data
            update_dict = update_data.dict(exclude_unset=True)
            
            # Build update query
            set_clauses = []
            params = []
            
            for field, value in update_dict.items():
                set_clauses.append(f"{field} = ?")
                params.append(value)
            
            if not set_clauses:
                return self.get_user_skill(skill_id)
            
            set_clauses.append("updated_at = CURRENT_TIMESTAMP")
            params.append(skill_id)
            
            update_query = f"""
            UPDATE user_skills 
            SET {', '.join(set_clauses)}
            WHERE id = ?
            """
            
            self.db.execute_update(update_query, tuple(params))
            
            # Refresh user context
            self.context_builder.refresh_user_context(user_id)
            
            logger.info(f"Skill updated successfully: {skill_id}")
            return self.get_user_skill(skill_id)
            
        except Exception as e:
            logger.error(f"Error updating user skill: {e}")
            raise
    
    # Context and Analytics
    
    def get_user_context(self, user_id: str) -> Optional[UserContext]:
        """Get user context for AI personalization."""
        try:
            return self.context_builder.get_user_context_for_ai(user_id)
        except Exception as e:
            logger.error(f"Error getting user context: {e}")
            return None
    
    def refresh_user_context(self, user_id: str) -> UserContext:
        """Refresh user context by rebuilding it."""
        return self.context_builder.refresh_user_context(user_id)
    
    def get_user_analytics(self, user_id: str) -> Dict[str, Any]:
        """Get user analytics and statistics."""
        try:
            analytics = {}
            
            # Task statistics
            task_stats_query = """
            SELECT 
                COUNT(*) as total_tasks,
                COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_tasks,
                COUNT(CASE WHEN status = 'in_progress' THEN 1 END) as in_progress_tasks,
                COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_tasks,
                AVG(actual_hours) as avg_hours_per_task
            FROM user_tasks 
            WHERE user_id = ?
            """
            task_results = self.db.execute_query(task_stats_query, (user_id,))
            if task_results:
                analytics['tasks'] = dict(task_results[0])
            
            # Skill statistics
            skill_stats_query = """
            SELECT 
                COUNT(*) as total_skills,
                COUNT(CASE WHEN level = 'expert' THEN 1 END) as expert_skills,
                COUNT(CASE WHEN level = 'advanced' THEN 1 END) as advanced_skills,
                COUNT(CASE WHEN level = 'intermediate' THEN 1 END) as intermediate_skills,
                COUNT(CASE WHEN level = 'beginner' THEN 1 END) as beginner_skills,
                AVG(confidence_score) as avg_confidence
            FROM user_skills 
            WHERE user_id = ?
            """
            skill_results = self.db.execute_query(skill_stats_query, (user_id,))
            if skill_results:
                analytics['skills'] = dict(skill_results[0])
            
            # Recent activity
            recent_tasks = self.get_user_tasks(user_id, limit=5)
            analytics['recent_tasks'] = [task.dict() for task in recent_tasks]
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error getting user analytics: {e}")
            return {}
    
    # Helper Methods
    
    def _parse_user_profile(self, row) -> UserProfile:
        """Parse database row to UserProfile object."""
        # Convert Row to dict
        row_dict = dict(row)
        
        # Parse JSON fields
        json_fields = ['personal_goals', 'team_info', 'project_info', 'connections', 'preferences', 'skill_gaps']
        for field in json_fields:
            if row_dict.get(field):
                try:
                    row_dict[field] = json.loads(row_dict[field])
                except json.JSONDecodeError:
                    row_dict[field] = None
            else:
                row_dict[field] = None
        
        # Create UserProfile object
        return UserProfile(
            id=row_dict['id'],
            username=row_dict['username'],
            name=row_dict['name'],
            job_role=row_dict['job_role'],
            experience_summary=row_dict['experience_summary'],
            personal_goals=row_dict['personal_goals'] or [],
            team_info=TeamInfo(**row_dict['team_info']) if row_dict['team_info'] else None,
            project_info=ProjectInfo(**row_dict['project_info']) if row_dict['project_info'] else None,
            connections=UserConnections(**row_dict['connections']) if row_dict['connections'] else None,
            preferences=UserPreferences(**row_dict['preferences']) if row_dict['preferences'] else None,
            skill_gaps=row_dict['skill_gaps'] or [],
            is_active=bool(row_dict['is_active']),
            created_at=datetime.fromisoformat(row_dict['created_at']),
            updated_at=datetime.fromisoformat(row_dict['updated_at'])
        )
    
    def _parse_user_task(self, row) -> UserTask:
        """Parse database row to UserTask object."""
        # Convert Row to dict
        row_dict = dict(row)
        
        # Parse JSON fields
        json_fields = ['skills_used', 'skills_learned']
        for field in json_fields:
            if row_dict.get(field):
                try:
                    row_dict[field] = json.loads(row_dict[field])
                except json.JSONDecodeError:
                    row_dict[field] = []
            else:
                row_dict[field] = []
        
        # Parse dates
        if row_dict.get('due_date'):
            row_dict['due_date'] = datetime.strptime(row_dict['due_date'], '%Y-%m-%d').date()
        if row_dict.get('completed_date'):
            row_dict['completed_date'] = datetime.strptime(row_dict['completed_date'], '%Y-%m-%d').date()
        
        return UserTask(**row_dict)
    
    def _parse_user_skill(self, row) -> UserSkill:
        """Parse database row to UserSkill object."""
        # Convert Row to dict
        row_dict = dict(row)
        
        # Parse dates
        if row_dict.get('last_used_date'):
            row_dict['last_used_date'] = datetime.strptime(row_dict['last_used_date'], '%Y-%m-%d').date()
        if row_dict.get('last_assessed_date'):
            row_dict['last_assessed_date'] = datetime.strptime(row_dict['last_assessed_date'], '%Y-%m-%d').date()
        
        return UserSkill(**row_dict)


# Global user service instance
_user_service_instance: Optional[UserService] = None


def get_user_service() -> UserService:
    """
    Get the global user service instance.
    
    Returns:
        UserService: Global user service instance
    """
    global _user_service_instance
    if _user_service_instance is None:
        _user_service_instance = UserService()
    return _user_service_instance


def initialize_user_service() -> UserService:
    """
    Initialize the global user service.
    
    Returns:
        UserService: Initialized user service instance
    """
    global _user_service_instance
    _user_service_instance = UserService()
    return _user_service_instance
