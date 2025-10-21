"""
Learning Engine for Personalized Learning Path Generation.

This module provides AI-powered learning path generation, content recommendation,
and personalized learning experiences based on user skill gaps and context.
"""

import logging
import json
import uuid
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone
from dataclasses import dataclass

# Database and AI imports
from ..database.connection import get_database
from ..database.vector_store import get_vector_store
from ..core.ai_client import get_ai_client
from ..core.config import get_config

# Model imports
from ..models.learning import (
    LearningPath, LearningPathCreate, LearningPathUpdate,
    LearningContent, LearningContentCreate, LearningContentUpdate,
    LearningProgress, LearningProgressCreate, LearningProgressUpdate,
    ContentType, DifficultyLevel
)
from ..models.skills import SkillsAssessment, SkillGap
from ..models.user import UserProfile

# Service imports
from .skills_engine import SkillsEngine
from .user_service import UserService

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class LearningRecommendation:
    """Learning recommendation with priority and context."""
    content_id: str
    title: str
    content_type: str
    difficulty: str
    estimated_duration: int
    skills_covered: List[str]
    priority_score: float
    reasoning: str
    prerequisites: List[str]
    learning_objectives: List[str]


@dataclass
class PersonalizedLearningPath:
    """Personalized learning path with recommendations."""
    path_id: str
    title: str
    description: str
    target_skills: List[str]
    difficulty: str
    estimated_duration: int
    content_sequence: List[LearningRecommendation]
    prerequisites: List[str]
    learning_objectives: List[str]
    priority_order: List[str]
    success_metrics: Dict[str, Any]
    created_at: datetime


class LearningEngine:
    """
    AI-powered learning engine for personalized learning path generation.
    
    Provides intelligent content recommendation, learning path creation,
    and adaptive learning experiences based on user skill gaps and context.
    """
    
    def __init__(self):
        """Initialize the learning engine."""
        self.db = get_database()
        self.vector_store = get_vector_store()
        self.ai_client = get_ai_client()
        self.config = get_config()
        
        # Initialize services
        self.skills_engine = SkillsEngine()
        self.user_service = UserService()
        
        # Learning content categories and micro-learning structure
        self.content_categories = {
            "product_management": [
                "user_research", "product_strategy", "roadmapping", "stakeholder_management",
                "data_analysis", "user_experience", "agile_methodology", "market_research"
            ],
            "technical_skills": [
                "programming", "database_design", "api_development", "system_architecture",
                "cloud_computing", "devops", "security", "testing"
            ],
            "soft_skills": [
                "leadership", "communication", "collaboration", "problem_solving",
                "critical_thinking", "time_management", "presentation", "negotiation"
            ]
        }
        
        # Micro-learning duration targets (7-15 minutes)
        self.micro_learning_duration = {
            "quick_tip": 5,
            "concept_explanation": 10,
            "practical_exercise": 15,
            "case_study": 12,
            "tutorial": 15,
            "quiz": 8
        }
        
        logger.info("Learning Engine initialized successfully")
    
    def generate_personalized_learning_path(
        self,
        user_id: str,
        skill_gaps: Optional[List[SkillGap]] = None,
        max_duration_hours: Optional[int] = None,
        preferred_difficulty: Optional[str] = None
    ) -> PersonalizedLearningPath:
        """
        Generate a personalized learning path based on user skill gaps and context.
        
        Args:
            user_id: User ID
            skill_gaps: List of skill gaps (if None, will be retrieved)
            max_duration_hours: Maximum learning path duration
            preferred_difficulty: Preferred difficulty level
            
        Returns:
            PersonalizedLearningPath: Generated learning path
        """
        logger.info(f"Generating personalized learning path for user: {user_id}")
        
        try:
            # Get user context
            user_profile = self.user_service.get_user_profile(user_id)
            if not user_profile:
                raise ValueError(f"User profile not found for user: {user_id}")
            
            # Get skill gaps if not provided
            if not skill_gaps:
                skill_gaps = self.skills_engine.get_user_skill_gaps(user_id)
            
            if not skill_gaps:
                logger.warning(f"No skill gaps found for user: {user_id}")
                return self._create_default_learning_path(user_id, user_profile)
            
            # Generate learning recommendations
            recommendations = self._generate_learning_recommendations(
                user_profile, skill_gaps, max_duration_hours, preferred_difficulty
            )
            
            # Create personalized learning path
            learning_path = self._create_personalized_path(
                user_id, user_profile, skill_gaps, recommendations
            )
            
            # Store the learning path
            self._store_learning_path(learning_path)
            
            logger.info(f"Successfully generated learning path for user: {user_id}")
            return learning_path
            
        except Exception as e:
            logger.error(f"Error generating learning path for user {user_id}: {e}")
            raise
    
    def _generate_learning_recommendations(
        self,
        user_profile: UserProfile,
        skill_gaps: List[SkillGap],
        max_duration_hours: Optional[int],
        preferred_difficulty: Optional[str]
    ) -> List[LearningRecommendation]:
        """Generate AI-powered learning recommendations."""
        logger.info("Generating learning recommendations")
        
        try:
            # Prioritize skill gaps
            prioritized_gaps = self._prioritize_skill_gaps(skill_gaps, user_profile)
            
            # Generate content recommendations for each gap
            recommendations = []
            total_duration = 0
            max_duration_minutes = (max_duration_hours * 60) if max_duration_hours else 480  # 8 hours default
            
            for gap in prioritized_gaps:
                if total_duration >= max_duration_minutes:
                    break
                
                # Get content recommendations for this skill gap
                gap_recommendations = self._get_content_for_skill_gap(
                    gap, user_profile, preferred_difficulty
                )
                
                # Add recommendations that fit within time constraints
                for rec in gap_recommendations:
                    if total_duration + rec.estimated_duration <= max_duration_minutes:
                        recommendations.append(rec)
                        total_duration += rec.estimated_duration
                    else:
                        break
            
            # Sort by priority score
            recommendations.sort(key=lambda x: x.priority_score, reverse=True)
            
            logger.info(f"Generated {len(recommendations)} learning recommendations")
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating learning recommendations: {e}")
            raise
    
    def _prioritize_skill_gaps(
        self,
        skill_gaps: List[SkillGap],
        user_profile: UserProfile
    ) -> List[SkillGap]:
        """Prioritize skill gaps based on user context and impact."""
        logger.info("Prioritizing skill gaps")
        
        try:
            # Create priority scoring prompt
            priority_prompt = f"""
            Analyze and prioritize these skill gaps for a Product Manager:
            
            User Context:
            - Role: {user_profile.current_role}
            - Experience: {user_profile.years_of_experience} years
            - Industry: {user_profile.industry}
            - Team Size: {user_profile.team_size}
            - Current Projects: {', '.join([p.name for p in user_profile.current_projects])}
            
            Skill Gaps:
            {json.dumps([{
                'skill_name': gap.skill_name,
                'current_level': gap.current_level,
                'target_level': gap.target_level,
                'gap_size': gap.gap_size,
                'category': gap.category
            } for gap in skill_gaps], indent=2)}
            
            Please prioritize these gaps considering:
            1. Impact on current work and projects
            2. Career advancement potential
            3. Learning difficulty and time investment
            4. Prerequisites and dependencies
            
            Return a JSON list with skill names in priority order.
            """
            
            # Get AI prioritization
            response = self.ai_client.generate_response(priority_prompt)
            priority_order = json.loads(response)
            
            # Sort skill gaps by priority
            gap_dict = {gap.skill_name: gap for gap in skill_gaps}
            prioritized_gaps = []
            
            for skill_name in priority_order:
                if skill_name in gap_dict:
                    prioritized_gaps.append(gap_dict[skill_name])
            
            # Add any remaining gaps not in the priority list
            for gap in skill_gaps:
                if gap not in prioritized_gaps:
                    prioritized_gaps.append(gap)
            
            logger.info(f"Prioritized {len(prioritized_gaps)} skill gaps")
            return prioritized_gaps
            
        except Exception as e:
            logger.error(f"Error prioritizing skill gaps: {e}")
            # Fallback to gap size priority
            return sorted(skill_gaps, key=lambda x: x.gap_size, reverse=True)
    
    def _get_content_for_skill_gap(
        self,
        skill_gap: SkillGap,
        user_profile: UserProfile,
        preferred_difficulty: Optional[str]
    ) -> List[LearningRecommendation]:
        """Get content recommendations for a specific skill gap."""
        logger.info(f"Getting content for skill gap: {skill_gap.skill_name}")
        
        try:
            # Determine appropriate difficulty level
            difficulty = preferred_difficulty or self._determine_difficulty_level(
                skill_gap.current_level, skill_gap.target_level
            )
            
            # Search for existing content
            existing_content = self._search_existing_content(skill_gap.skill_name, difficulty)
            
            # Generate new content if needed
            if not existing_content:
                existing_content = self._generate_micro_learning_content(
                    skill_gap, user_profile, difficulty
                )
            
            # Create recommendations
            recommendations = []
            for content in existing_content:
                rec = LearningRecommendation(
                    content_id=content.get('id', str(uuid.uuid4())),
                    title=content['title'],
                    content_type=content['content_type'],
                    difficulty=content['difficulty'],
                    estimated_duration=content['estimated_duration'],
                    skills_covered=content['skills_covered'],
                    priority_score=self._calculate_priority_score(content, skill_gap, user_profile),
                    reasoning=content.get('reasoning', ''),
                    prerequisites=content.get('prerequisites', []),
                    learning_objectives=content.get('learning_objectives', [])
                )
                recommendations.append(rec)
            
            # Sort by priority score
            recommendations.sort(key=lambda x: x.priority_score, reverse=True)
            
            logger.info(f"Found {len(recommendations)} content recommendations for {skill_gap.skill_name}")
            return recommendations
            
        except Exception as e:
            logger.error(f"Error getting content for skill gap {skill_gap.skill_name}: {e}")
            return []
    
    def _search_existing_content(
        self,
        skill_name: str,
        difficulty: str
    ) -> List[Dict[str, Any]]:
        """Search for existing learning content."""
        try:
            # Search in database
            results = self.db.execute_query("""
                SELECT * FROM learning_content 
                WHERE skills_covered LIKE ? 
                AND difficulty = ? 
                AND is_active = 1
                ORDER BY created_at DESC
                LIMIT 10
            """, (f'%{skill_name}%', difficulty))
            
            content_list = []
            for row in results:
                content = {
                    'id': row[0],
                    'title': row[1],
                    'content_type': row[3],
                    'difficulty': row[4],
                    'estimated_duration': row[5] or 10,
                    'skills_covered': json.loads(row[6]) if row[6] else [],
                    'prerequisites': json.loads(row[7]) if row[7] else [],
                    'learning_objectives': json.loads(row[8]) if row[8] else [],
                    'content_text': row[11],
                    'reasoning': f"Existing content covering {skill_name}"
                }
                content_list.append(content)
            
            return content_list
            
        except Exception as e:
            logger.error(f"Error searching existing content: {e}")
            return []
    
    def _generate_micro_learning_content(
        self,
        skill_gap: SkillGap,
        user_profile: UserProfile,
        difficulty: str
    ) -> List[Dict[str, Any]]:
        """Generate micro-learning content using AI."""
        logger.info(f"Generating micro-learning content for: {skill_gap.skill_name}")
        
        try:
            # Determine content type and duration
            content_type = self._select_content_type(skill_gap.skill_name, difficulty)
            duration = self.micro_learning_duration.get(content_type, 10)
            
            # Create content generation prompt
            content_prompt = f"""
            Create a micro-learning module for a Product Manager to learn {skill_gap.skill_name}.
            
            Context:
            - Current skill level: {skill_gap.current_level}
            - Target skill level: {skill_gap.target_level}
            - User role: {user_profile.current_role}
            - Experience: {user_profile.years_of_experience} years
            - Industry: {user_profile.industry}
            
            Requirements:
            - Content type: {content_type}
            - Duration: {duration} minutes
            - Difficulty: {difficulty}
            - Focus on practical, actionable learning
            
            Please provide:
            1. Title (concise and engaging)
            2. Learning objectives (3-5 specific goals)
            3. Content structure (step-by-step breakdown)
            4. Practical exercises or examples
            5. Key takeaways
            6. Prerequisites (if any)
            
            Format as JSON with the following structure:
            {{
                "title": "string",
                "learning_objectives": ["string"],
                "content_structure": ["string"],
                "practical_exercises": ["string"],
                "key_takeaways": ["string"],
                "prerequisites": ["string"]
            }}
            """
            
            # Generate content using AI
            response = self.ai_client.generate_response(content_prompt)
            content_data = json.loads(response)
            
            # Create content object
            content = {
                'id': str(uuid.uuid4()),
                'title': content_data['title'],
                'content_type': content_type,
                'difficulty': difficulty,
                'estimated_duration': duration,
                'skills_covered': [skill_gap.skill_name],
                'prerequisites': content_data.get('prerequisites', []),
                'learning_objectives': content_data.get('learning_objectives', []),
                'content_text': self._format_content_text(content_data),
                'reasoning': f"AI-generated content for {skill_gap.skill_name} skill gap"
            }
            
            # Store the generated content
            self._store_generated_content(content)
            
            return [content]
            
        except Exception as e:
            logger.error(f"Error generating micro-learning content: {e}")
            return []
    
    def _select_content_type(self, skill_name: str, difficulty: str) -> str:
        """Select appropriate content type based on skill and difficulty."""
        # Map skills to content types
        content_type_mapping = {
            "programming": "tutorial",
            "data_analysis": "practical_exercise",
            "user_research": "case_study",
            "product_strategy": "concept_explanation",
            "stakeholder_management": "case_study",
            "api_development": "tutorial",
            "database_design": "practical_exercise"
        }
        
        return content_type_mapping.get(skill_name.lower(), "concept_explanation")
    
    def _format_content_text(self, content_data: Dict[str, Any]) -> str:
        """Format content data into readable text."""
        text_parts = []
        
        # Title
        text_parts.append(f"# {content_data['title']}\n")
        
        # Learning objectives
        if content_data.get('learning_objectives'):
            text_parts.append("## Learning Objectives")
            for obj in content_data['learning_objectives']:
                text_parts.append(f"- {obj}")
            text_parts.append("")
        
        # Content structure
        if content_data.get('content_structure'):
            text_parts.append("## Content Structure")
            for i, step in enumerate(content_data['content_structure'], 1):
                text_parts.append(f"{i}. {step}")
            text_parts.append("")
        
        # Practical exercises
        if content_data.get('practical_exercises'):
            text_parts.append("## Practical Exercises")
            for exercise in content_data['practical_exercises']:
                text_parts.append(f"- {exercise}")
            text_parts.append("")
        
        # Key takeaways
        if content_data.get('key_takeaways'):
            text_parts.append("## Key Takeaways")
            for takeaway in content_data['key_takeaways']:
                text_parts.append(f"- {takeaway}")
        
        return "\n".join(text_parts)
    
    def _determine_difficulty_level(self, current_level: str, target_level: str) -> str:
        """Determine appropriate difficulty level based on skill levels."""
        level_mapping = {
            "beginner": 1,
            "intermediate": 2,
            "advanced": 3,
            "expert": 4
        }
        
        current_num = level_mapping.get(current_level.lower(), 1)
        target_num = level_mapping.get(target_level.lower(), 2)
        
        if target_num - current_num >= 2:
            return "advanced"
        elif target_num - current_num == 1:
            return "intermediate"
        else:
            return "beginner"
    
    def _calculate_priority_score(
        self,
        content: Dict[str, Any],
        skill_gap: SkillGap,
        user_profile: UserProfile
    ) -> float:
        """Calculate priority score for content recommendation."""
        score = 0.0
        
        # Base score from gap size
        score += skill_gap.gap_size * 10
        
        # Duration bonus (shorter is better for micro-learning)
        duration = content.get('estimated_duration', 15)
        if duration <= 10:
            score += 5
        elif duration <= 15:
            score += 3
        
        # Difficulty alignment
        if content.get('difficulty') == 'intermediate':
            score += 3
        elif content.get('difficulty') == 'beginner':
            score += 2
        
        # Content type bonus
        content_type = content.get('content_type', '')
        if content_type in ['tutorial', 'practical_exercise']:
            score += 2
        
        return score
    
    def _create_personalized_path(
        self,
        user_id: str,
        user_profile: UserProfile,
        skill_gaps: List[SkillGap],
        recommendations: List[LearningRecommendation]
    ) -> PersonalizedLearningPath:
        """Create a personalized learning path from recommendations."""
        path_id = str(uuid.uuid4())
        
        # Calculate total duration
        total_duration = sum(rec.estimated_duration for rec in recommendations)
        
        # Create learning objectives
        learning_objectives = []
        for gap in skill_gaps[:5]:  # Top 5 gaps
            learning_objectives.append(f"Improve {gap.skill_name} from {gap.current_level} to {gap.target_level}")
        
        # Create success metrics
        success_metrics = {
            "target_skills_improved": len(skill_gaps),
            "estimated_completion_time": f"{total_duration} minutes",
            "learning_modules": len(recommendations),
            "difficulty_distribution": self._calculate_difficulty_distribution(recommendations)
        }
        
        return PersonalizedLearningPath(
            path_id=path_id,
            title=f"Personalized Learning Path for {user_profile.current_role}",
            description=f"Customized learning journey to address {len(skill_gaps)} skill gaps",
            target_skills=[gap.skill_name for gap in skill_gaps],
            difficulty=self._determine_overall_difficulty(recommendations),
            estimated_duration=total_duration,
            content_sequence=recommendations,
            prerequisites=[],
            learning_objectives=learning_objectives,
            priority_order=[gap.skill_name for gap in skill_gaps],
            success_metrics=success_metrics,
            created_at=datetime.now(timezone.utc)
        )
    
    def _calculate_difficulty_distribution(self, recommendations: List[LearningRecommendation]) -> Dict[str, int]:
        """Calculate difficulty level distribution."""
        distribution = {"beginner": 0, "intermediate": 0, "advanced": 0, "expert": 0}
        for rec in recommendations:
            distribution[rec.difficulty] = distribution.get(rec.difficulty, 0) + 1
        return distribution
    
    def _determine_overall_difficulty(self, recommendations: List[LearningRecommendation]) -> str:
        """Determine overall difficulty of the learning path."""
        if not recommendations:
            return "beginner"
        
        difficulty_scores = {"beginner": 1, "intermediate": 2, "advanced": 3, "expert": 4}
        avg_score = sum(difficulty_scores.get(rec.difficulty, 1) for rec in recommendations) / len(recommendations)
        
        if avg_score >= 3:
            return "advanced"
        elif avg_score >= 2:
            return "intermediate"
        else:
            return "beginner"
    
    def _create_default_learning_path(self, user_id: str, user_profile: UserProfile) -> PersonalizedLearningPath:
        """Create a default learning path when no skill gaps are found."""
        logger.info(f"Creating default learning path for user: {user_id}")
        
        # Create basic recommendations for common PM skills
        default_recommendations = [
            LearningRecommendation(
                content_id=str(uuid.uuid4()),
                title="Product Management Fundamentals",
                content_type="concept_explanation",
                difficulty="beginner",
                estimated_duration=15,
                skills_covered=["product_management", "strategy"],
                priority_score=8.0,
                reasoning="Essential foundation for product managers",
                prerequisites=[],
                learning_objectives=["Understand core PM principles", "Learn strategic thinking"]
            )
        ]
        
        return PersonalizedLearningPath(
            path_id=str(uuid.uuid4()),
            title="Introduction to Product Management",
            description="Essential learning path for new product managers",
            target_skills=["product_management", "strategy", "user_research"],
            difficulty="beginner",
            estimated_duration=15,
            content_sequence=default_recommendations,
            prerequisites=[],
            learning_objectives=["Build foundational PM knowledge"],
            priority_order=["product_management"],
            success_metrics={"target_skills_improved": 1, "learning_modules": 1},
            created_at=datetime.now(timezone.utc)
        )
    
    def _store_learning_path(self, learning_path: PersonalizedLearningPath) -> None:
        """Store the learning path in the database."""
        try:
            # Store learning path
            self.db.execute_update("""
                INSERT OR REPLACE INTO learning_paths (
                    id, title, description, target_skills, difficulty,
                    estimated_duration, content_sequence, prerequisites,
                    learning_objectives, tags, is_active, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                learning_path.path_id,
                learning_path.title,
                learning_path.description,
                json.dumps(learning_path.target_skills),
                learning_path.difficulty,
                learning_path.estimated_duration,
                json.dumps([rec.content_id for rec in learning_path.content_sequence]),
                json.dumps(learning_path.prerequisites),
                json.dumps(learning_path.learning_objectives),
                json.dumps(learning_path.priority_order),
                True,
                learning_path.created_at.isoformat(),
                learning_path.created_at.isoformat()
            ))
            
            # Store content recommendations
            for rec in learning_path.content_sequence:
                self._store_content_recommendation(rec)
            
            logger.info(f"Stored learning path: {learning_path.path_id}")
            
        except Exception as e:
            logger.error(f"Error storing learning path: {e}")
            raise
    
    def _store_content_recommendation(self, recommendation: LearningRecommendation) -> None:
        """Store a content recommendation."""
        try:
            self.db.execute_update("""
                INSERT OR REPLACE INTO learning_content (
                    id, title, description, content_type, difficulty,
                    estimated_duration, skills_covered, prerequisites,
                    learning_objectives, content_text, tags, is_active,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                recommendation.content_id,
                recommendation.title,
                recommendation.reasoning,
                recommendation.content_type,
                recommendation.difficulty,
                recommendation.estimated_duration,
                json.dumps(recommendation.skills_covered),
                json.dumps(recommendation.prerequisites),
                json.dumps(recommendation.learning_objectives),
                "",  # content_text would be populated if available
                json.dumps([]),
                True,
                datetime.now(timezone.utc).isoformat(),
                datetime.now(timezone.utc).isoformat()
            ))
            
        except Exception as e:
            logger.error(f"Error storing content recommendation: {e}")
    
    def _store_generated_content(self, content: Dict[str, Any]) -> None:
        """Store AI-generated content."""
        try:
            self.db.execute_update("""
                INSERT OR REPLACE INTO learning_content (
                    id, title, description, content_type, difficulty,
                    estimated_duration, skills_covered, prerequisites,
                    learning_objectives, content_text, tags, is_active,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                content['id'],
                content['title'],
                content.get('reasoning', ''),
                content['content_type'],
                content['difficulty'],
                content['estimated_duration'],
                json.dumps(content['skills_covered']),
                json.dumps(content['prerequisites']),
                json.dumps(content['learning_objectives']),
                content.get('content_text', ''),
                json.dumps([]),
                True,
                datetime.now(timezone.utc).isoformat(),
                datetime.now(timezone.utc).isoformat()
            ))
            
            logger.info(f"Stored generated content: {content['id']}")
            
        except Exception as e:
            logger.error(f"Error storing generated content: {e}")
    
    def get_learning_path(self, path_id: str) -> Optional[PersonalizedLearningPath]:
        """Get a learning path by ID."""
        try:
            result = self.db.execute_query("""
                SELECT * FROM learning_paths WHERE id = ?
            """, (path_id,))
            
            if not result:
                return None
            
            row = result[0]
            
            # Get content sequence
            content_sequence = []
            content_ids = json.loads(row[6]) if row[6] else []
            
            for content_id in content_ids:
                content = self._get_content_recommendation(content_id)
                if content:
                    content_sequence.append(content)
            
            return PersonalizedLearningPath(
                path_id=row[0],
                title=row[1],
                description=row[2],
                target_skills=json.loads(row[3]) if row[3] else [],
                difficulty=row[4],
                estimated_duration=row[5],
                content_sequence=content_sequence,
                prerequisites=json.loads(row[7]) if row[7] else [],
                learning_objectives=json.loads(row[8]) if row[8] else [],
                priority_order=json.loads(row[9]) if row[9] else [],
                success_metrics={},
                created_at=datetime.fromisoformat(row[11])
            )
            
        except Exception as e:
            logger.error(f"Error getting learning path {path_id}: {e}")
            return None
    
    def _get_content_recommendation(self, content_id: str) -> Optional[LearningRecommendation]:
        """Get a content recommendation by ID."""
        try:
            result = self.db.execute_query("""
                SELECT * FROM learning_content WHERE id = ?
            """, (content_id,))
            
            if not result:
                return None
            
            row = result[0]
            
            return LearningRecommendation(
                content_id=row[0],
                title=row[1],
                content_type=row[3],
                difficulty=row[4],
                estimated_duration=row[5] or 10,
                skills_covered=json.loads(row[6]) if row[6] else [],
                priority_score=0.0,  # Would need to be calculated
                reasoning=row[2] or "",
                prerequisites=json.loads(row[7]) if row[7] else [],
                learning_objectives=json.loads(row[8]) if row[8] else []
            )
            
        except Exception as e:
            logger.error(f"Error getting content recommendation {content_id}: {e}")
            return None
    
    def get_user_learning_paths(self, user_id: str) -> List[PersonalizedLearningPath]:
        """Get all learning paths for a user."""
        try:
            # For now, return all learning paths (in a real system, you'd filter by user)
            results = self.db.execute_query("""
                SELECT id FROM learning_paths 
                WHERE is_active = 1 
                ORDER BY created_at DESC
                LIMIT 10
            """)
            
            learning_paths = []
            for row in results:
                path = self.get_learning_path(row[0])
                if path:
                    learning_paths.append(path)
            
            return learning_paths
            
        except Exception as e:
            logger.error(f"Error getting learning paths for user {user_id}: {e}")
            return []


# Global instance
_learning_engine = None


def get_learning_engine() -> LearningEngine:
    """Get the global learning engine instance."""
    global _learning_engine
    if _learning_engine is None:
        _learning_engine = LearningEngine()
    return _learning_engine
