"""
User context aggregation system for AI personalization.

This module builds comprehensive user context by aggregating data from user profiles,
tasks, skills, learning progress, and assessments to provide rich context for AI agents.
"""

import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging

from ..database.connection import get_database
from ..database.vector_store import get_vector_store
from ..core.ai_client import get_ai_client
from ..models.user import UserContext, UserProfile, UserTask, UserSkill
from ..models.learning import LearningProgress
from ..models.skills import SkillsAssessment, SkillGap

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UserContextBuilder:
    """
    Builds comprehensive user context for AI personalization.
    
    This class aggregates user data from multiple sources to create rich context
    that can be used by AI agents for personalized recommendations and interactions.
    """
    
    def __init__(self):
        """Initialize the user context builder."""
        self.db = get_database()
        self.vector_store = get_vector_store()
        self.ai_client = get_ai_client()
        logger.info("User context builder initialized")
    
    def build_user_context(self, user_id: str) -> UserContext:
        """
        Build comprehensive user context for AI personalization.
        
        Args:
            user_id: User ID to build context for
            
        Returns:
            UserContext: Comprehensive user context
        """
        logger.info(f"Building user context for user: {user_id}")
        
        try:
            # Get user profile data
            user_profile = self._get_user_profile(user_id)
            if not user_profile:
                raise ValueError(f"User profile not found for user_id: {user_id}")
            
            # Aggregate various context components
            current_focus_areas = self._get_current_focus_areas(user_id)
            recent_work_summary = self._get_recent_work_summary(user_id)
            upcoming_priorities = self._get_upcoming_priorities(user_id)
            learning_goals = self._get_learning_goals(user_id)
            skill_gaps = self._get_skill_gaps(user_id)
            
            # Generate AI-powered context summary
            context_summary = self._generate_context_summary(
                user_profile, current_focus_areas, recent_work_summary, 
                upcoming_priorities, learning_goals, skill_gaps
            )
            
            # Create user context
            user_context = UserContext(
                user_id=user_id,
                current_focus_areas=current_focus_areas,
                recent_work_summary=recent_work_summary,
                upcoming_priorities=upcoming_priorities,
                learning_goals=learning_goals,
                skill_gaps=skill_gaps,
                context_summary=context_summary,
                last_updated=datetime.utcnow()
            )
            
            # Store context in vector store for semantic search
            self._store_context_in_vector_store(user_context)
            
            # Update context in database
            self._update_context_in_database(user_context)
            
            logger.info(f"User context built successfully for user: {user_id}")
            return user_context
            
        except Exception as e:
            logger.error(f"Error building user context for {user_id}: {e}")
            raise
    
    def _get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile data."""
        query = "SELECT * FROM user_profiles WHERE id = ? AND is_active = 1"
        results = self.db.execute_query(query, (user_id,))
        
        if results:
            profile = dict(results[0])
            # Parse JSON fields
            for field in ['personal_goals', 'team_info', 'project_info', 'connections', 'preferences', 'skill_gaps']:
                if profile.get(field):
                    try:
                        profile[field] = json.loads(profile[field])
                    except json.JSONDecodeError:
                        profile[field] = None
            return profile
        return None
    
    def _get_current_focus_areas(self, user_id: str) -> List[str]:
        """Get current focus areas from recent tasks and skills."""
        focus_areas = []
        
        # Get recent active tasks (last 30 days)
        query = """
        SELECT DISTINCT project_context, skills_used
        FROM user_tasks 
        WHERE user_id = ? 
        AND status IN ('pending', 'in_progress')
        AND created_at >= datetime('now', '-30 days')
        """
        results = self.db.execute_query(query, (user_id,))
        
        for result in results:
            if result['project_context']:
                focus_areas.append(result['project_context'])
            
            if result['skills_used']:
                try:
                    skills = json.loads(result['skills_used'])
                    focus_areas.extend(skills)
                except json.JSONDecodeError:
                    pass
        
        # Get high-priority skills being learned
        query = """
        SELECT skill_name 
        FROM user_skills 
        WHERE user_id = ? 
        AND learning_priority IN ('high', 'critical')
        AND level != target_level
        """
        results = self.db.execute_query(query, (user_id,))
        focus_areas.extend([result['skill_name'] for result in results])
        
        # Remove duplicates and return
        return list(set(focus_areas))
    
    def _get_recent_work_summary(self, user_id: str) -> Optional[str]:
        """Generate summary of recent work from completed tasks."""
        # Get completed tasks from last 30 days
        query = """
        SELECT title, description, skills_used, skills_learned, project_context
        FROM user_tasks 
        WHERE user_id = ? 
        AND status = 'completed'
        AND completed_date >= date('now', '-30 days')
        ORDER BY completed_date DESC
        LIMIT 10
        """
        results = self.db.execute_query(query, (user_id,))
        
        if not results:
            return None
        
        # Build summary
        tasks_summary = []
        for task in results:
            task_info = f"- {task['title']}"
            if task['project_context']:
                task_info += f" (Project: {task['project_context']})"
            tasks_summary.append(task_info)
        
        return "Recent completed work:\n" + "\n".join(tasks_summary)
    
    def _get_upcoming_priorities(self, user_id: str) -> List[str]:
        """Get upcoming priorities from pending and in-progress tasks."""
        priorities = []
        
        # Get high-priority upcoming tasks
        query = """
        SELECT title, due_date, priority, project_context
        FROM user_tasks 
        WHERE user_id = ? 
        AND status IN ('pending', 'in_progress')
        AND priority IN ('high', 'urgent')
        ORDER BY due_date ASC
        LIMIT 10
        """
        results = self.db.execute_query(query, (user_id,))
        
        for task in results:
            priority_text = f"{task['title']}"
            if task['due_date']:
                priority_text += f" (Due: {task['due_date']})"
            if task['project_context']:
                priority_text += f" - {task['project_context']}"
            priorities.append(priority_text)
        
        return priorities
    
    def _get_learning_goals(self, user_id: str) -> List[str]:
        """Get learning goals from user profile and skill gaps."""
        goals = []
        
        # Get personal goals from profile
        user_profile = self._get_user_profile(user_id)
        if user_profile and user_profile.get('personal_goals'):
            goals.extend(user_profile['personal_goals'])
        
        # Get learning goals from skill gaps
        query = """
        SELECT skill_name, target_level, recommended_actions
        FROM skill_gaps 
        WHERE user_id = ? 
        AND priority IN ('high', 'critical')
        ORDER BY priority DESC
        """
        results = self.db.execute_query(query, (user_id,))
        
        for gap in results:
            goal = f"Improve {gap['skill_name']} to {gap['target_level']} level"
            goals.append(goal)
            
            if gap['recommended_actions']:
                try:
                    actions = json.loads(gap['recommended_actions'])
                    goals.extend(actions[:2])  # Add top 2 recommended actions
                except json.JSONDecodeError:
                    pass
        
        return goals
    
    def _get_skill_gaps(self, user_id: str) -> List[str]:
        """Get identified skill gaps."""
        query = """
        SELECT skill_name, gap_size, priority
        FROM skill_gaps 
        WHERE user_id = ? 
        ORDER BY priority DESC, gap_size DESC
        """
        results = self.db.execute_query(query, (user_id,))
        
        gaps = []
        for gap in results:
            gap_text = f"{gap['skill_name']} ({gap['gap_size']} gap, {gap['priority']} priority)"
            gaps.append(gap_text)
        
        return gaps
    
    def _generate_context_summary(
        self, 
        user_profile: Dict[str, Any], 
        focus_areas: List[str], 
        recent_work: Optional[str], 
        upcoming_priorities: List[str], 
        learning_goals: List[str], 
        skill_gaps: List[str]
    ) -> str:
        """Generate AI-powered context summary."""
        try:
            # Prepare context data for AI
            context_data = {
                "user_profile": {
                    "name": user_profile.get('name'),
                    "job_role": user_profile.get('job_role'),
                    "experience_summary": user_profile.get('experience_summary'),
                    "team_info": user_profile.get('team_info'),
                    "project_info": user_profile.get('project_info')
                },
                "current_focus_areas": focus_areas,
                "recent_work_summary": recent_work,
                "upcoming_priorities": upcoming_priorities,
                "learning_goals": learning_goals,
                "skill_gaps": skill_gaps
            }
            
            # Create prompt for AI context generation
            prompt = f"""
            Based on the following user data, generate a concise but comprehensive context summary 
            that would help an AI agent understand this user's current situation, goals, and learning needs.
            
            User Data:
            {json.dumps(context_data, indent=2)}
            
            Please provide a 2-3 sentence summary that captures:
            1. The user's current role and focus areas
            2. Their recent work and upcoming priorities  
            3. Their key learning goals and skill gaps
            
            Keep it professional and actionable for an AI learning assistant.
            """
            
            # Generate summary using AI
            response = self.ai_client.generate_text(prompt, max_tokens=200)
            
            if response.error:
                logger.warning(f"AI generation failed: {response.error}")
                return self._generate_fallback_summary(user_profile, focus_areas, learning_goals)
            
            return response.content.strip()
            
        except Exception as e:
            logger.warning(f"Error generating AI context summary: {e}")
            # Fallback to manual summary
            return self._generate_fallback_summary(user_profile, focus_areas, learning_goals)
    
    def _generate_fallback_summary(
        self, 
        user_profile: Dict[str, Any], 
        focus_areas: List[str], 
        learning_goals: List[str]
    ) -> str:
        """Generate fallback context summary without AI."""
        name = user_profile.get('name', 'User')
        job_role = user_profile.get('job_role', 'Professional')
        
        summary_parts = [f"{name} is a {job_role}"]
        
        if focus_areas:
            summary_parts.append(f"currently focused on {', '.join(focus_areas[:3])}")
        
        if learning_goals:
            summary_parts.append(f"with learning goals including {learning_goals[0]}")
        
        return ". ".join(summary_parts) + "."
    
    def _store_context_in_vector_store(self, user_context: UserContext) -> None:
        """Store user context in vector store for semantic search."""
        try:
            # Create context document
            context_doc = f"""
            User Context for {user_context.user_id}:
            
            Current Focus Areas: {', '.join(user_context.current_focus_areas)}
            Recent Work: {user_context.recent_work_summary or 'No recent work data'}
            Upcoming Priorities: {', '.join(user_context.upcoming_priorities)}
            Learning Goals: {', '.join(user_context.learning_goals)}
            Skill Gaps: {', '.join(user_context.skill_gaps)}
            Context Summary: {user_context.context_summary or 'No summary available'}
            """
            
            # Store in vector store
            self.vector_store.add_documents(
                collection_name='user_context',
                documents=[context_doc],
                metadatas=[{
                    'user_id': user_context.user_id,
                    'last_updated': user_context.last_updated.isoformat(),
                    'context_type': 'user_profile'
                }],
                ids=[f"context_{user_context.user_id}"]
            )
            
            logger.info(f"User context stored in vector store for user: {user_context.user_id}")
            
        except Exception as e:
            logger.warning(f"Error storing context in vector store: {e}")
    
    def _update_context_in_database(self, user_context: UserContext) -> None:
        """Update user context in database."""
        try:
            # Check if context exists
            check_query = "SELECT id FROM user_context WHERE user_id = ?"
            existing = self.db.execute_query(check_query, (user_context.user_id,))
            
            if existing:
                # Update existing context
                update_query = """
                UPDATE user_context SET
                    current_focus_areas = ?,
                    recent_work_summary = ?,
                    upcoming_priorities = ?,
                    learning_goals = ?,
                    skill_gaps = ?,
                    context_summary = ?,
                    last_updated = ?
                WHERE user_id = ?
                """
                params = (
                    json.dumps(user_context.current_focus_areas),
                    user_context.recent_work_summary,
                    json.dumps(user_context.upcoming_priorities),
                    json.dumps(user_context.learning_goals),
                    json.dumps(user_context.skill_gaps),
                    user_context.context_summary,
                    user_context.last_updated,
                    user_context.user_id
                )
                self.db.execute_update(update_query, params)
            else:
                # Insert new context
                insert_query = """
                INSERT INTO user_context (
                    id, user_id, current_focus_areas, recent_work_summary,
                    upcoming_priorities, learning_goals, skill_gaps, context_summary, last_updated
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                params = (
                    f"context_{user_context.user_id}",
                    user_context.user_id,
                    json.dumps(user_context.current_focus_areas),
                    user_context.recent_work_summary,
                    json.dumps(user_context.upcoming_priorities),
                    json.dumps(user_context.learning_goals),
                    json.dumps(user_context.skill_gaps),
                    user_context.context_summary,
                    user_context.last_updated
                )
                self.db.execute_update(insert_query, params)
            
            logger.info(f"User context updated in database for user: {user_context.user_id}")
            
        except Exception as e:
            logger.error(f"Error updating context in database: {e}")
            raise
    
    def get_user_context_for_ai(self, user_id: str) -> Dict[str, Any]:
        """
        Get user context formatted for AI agent consumption.
        
        Args:
            user_id: User ID
            
        Returns:
            Dict containing formatted user context for AI
        """
        try:
            # Get or build user context
            context_query = "SELECT * FROM user_context WHERE user_id = ?"
            results = self.db.execute_query(context_query, (user_id,))
            
            if not results:
                # Build context if it doesn't exist
                user_context = self.build_user_context(user_id)
            else:
                # Parse existing context
                context_data = dict(results[0])
                user_context = UserContext(
                    user_id=context_data['user_id'],
                    current_focus_areas=json.loads(context_data['current_focus_areas'] or '[]'),
                    recent_work_summary=context_data['recent_work_summary'],
                    upcoming_priorities=json.loads(context_data['upcoming_priorities'] or '[]'),
                    learning_goals=json.loads(context_data['learning_goals'] or '[]'),
                    skill_gaps=json.loads(context_data['skill_gaps'] or '[]'),
                    context_summary=context_data['context_summary'],
                    last_updated=datetime.fromisoformat(context_data['last_updated'])
                )
            
            # Get additional user profile data
            user_profile = self._get_user_profile(user_id)
            
            # Format for AI consumption
            ai_context = {
                "user_id": user_id,
                "profile": {
                    "name": user_profile.get('name') if user_profile else None,
                    "job_role": user_profile.get('job_role') if user_profile else None,
                    "experience_summary": user_profile.get('experience_summary') if user_profile else None,
                    "team_info": user_profile.get('team_info') if user_profile else None,
                    "project_info": user_profile.get('project_info') if user_profile else None
                },
                "context": {
                    "current_focus_areas": user_context.current_focus_areas,
                    "recent_work_summary": user_context.recent_work_summary,
                    "upcoming_priorities": user_context.upcoming_priorities,
                    "learning_goals": user_context.learning_goals,
                    "skill_gaps": user_context.skill_gaps,
                    "context_summary": user_context.context_summary,
                    "last_updated": user_context.last_updated.isoformat()
                }
            }
            
            return ai_context
            
        except Exception as e:
            logger.error(f"Error getting user context for AI: {e}")
            raise
    
    def refresh_user_context(self, user_id: str) -> UserContext:
        """
        Refresh user context by rebuilding it from current data.
        
        Args:
            user_id: User ID
            
        Returns:
            UserContext: Refreshed user context
        """
        logger.info(f"Refreshing user context for user: {user_id}")
        return self.build_user_context(user_id)


# Global context builder instance
_context_builder_instance: Optional[UserContextBuilder] = None


def get_user_context_builder() -> UserContextBuilder:
    """
    Get the global user context builder instance.
    
    Returns:
        UserContextBuilder: Global context builder instance
    """
    global _context_builder_instance
    if _context_builder_instance is None:
        _context_builder_instance = UserContextBuilder()
    return _context_builder_instance


def initialize_user_context_builder() -> UserContextBuilder:
    """
    Initialize the global user context builder.
    
    Returns:
        UserContextBuilder: Initialized context builder instance
    """
    global _context_builder_instance
    _context_builder_instance = UserContextBuilder()
    return _context_builder_instance
