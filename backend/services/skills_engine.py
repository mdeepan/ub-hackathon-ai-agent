"""
Skills assessment engine for the Personal Learning Agent.

This module provides AI-powered skills assessment capabilities including semantic analysis
of work artifacts, skills gap detection, and competency level assessment.
"""

import json
import uuid
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime
import logging

from ..database.connection import get_database
from ..core.ai_client import get_ai_client
from ..models.skills import (
    SkillsAssessment, SkillsAssessmentCreate, SkillsAssessmentUpdate,
    SkillGap, SkillGapCreate, SkillGapUpdate,
    SkillsTaxonomy, SkillsTaxonomyCreate, SkillsTaxonomyUpdate,
    AssessmentStatus, AssessmentType
)
from ..utils.file_processor import get_file_processor, ProcessedContent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SkillsEngine:
    """
    AI-powered skills assessment engine.
    
    This engine analyzes work artifacts to identify skill gaps and assess competency levels
    using semantic analysis and the skills taxonomy.
    """
    
    def __init__(self):
        """Initialize the skills engine."""
        self.db = get_database()
        self.ai_client = get_ai_client()
        self.file_processor = get_file_processor()
        logger.info("Skills engine initialized")
    
    # Skills Taxonomy Management
    
    def load_skills_taxonomy_from_file(self, file_path: str) -> List[SkillsTaxonomy]:
        """
        Load skills taxonomy from JSON file.
        
        Args:
            file_path: Path to skills taxonomy JSON file
            
        Returns:
            List[SkillsTaxonomy]: Loaded skills taxonomy entries
        """
        logger.info(f"Loading skills taxonomy from: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                taxonomy_data = json.load(f)
            
            taxonomy_entries = []
            
            for category, category_data in taxonomy_data.items():
                # Process core skills
                if 'core_skills' in category_data:
                    for skill_name in category_data['core_skills']:
                        entry = SkillsTaxonomyCreate(
                            skill_name=skill_name,
                            category=category,
                            description=category_data.get('description', ''),
                            proficiency_levels=['beginner', 'intermediate', 'advanced', 'expert'],
                            related_skills=[],
                            prerequisites=[],
                            typical_use_cases=[],
                            industry_relevance=[category],
                            learning_resources=[],
                            assessment_methods=['artifact_analysis', 'self_assessment']
                        )
                        taxonomy_entries.append(self.create_skills_taxonomy_entry(entry))
                
                # Process subcategory skills
                if 'subcategories' in category_data:
                    for subcategory, subcategory_data in category_data['subcategories'].items():
                        for skill_name in subcategory_data.get('skills', []):
                            entry = SkillsTaxonomyCreate(
                                skill_name=skill_name,
                                category=category,
                                subcategory=subcategory,
                                description=subcategory_data.get('description', ''),
                                proficiency_levels=['beginner', 'intermediate', 'advanced', 'expert'],
                                related_skills=[],
                                prerequisites=[],
                                typical_use_cases=[],
                                industry_relevance=[category],
                                learning_resources=[],
                                assessment_methods=['artifact_analysis', 'self_assessment']
                            )
                            taxonomy_entries.append(self.create_skills_taxonomy_entry(entry))
            
            logger.info(f"Loaded {len(taxonomy_entries)} skills taxonomy entries")
            return taxonomy_entries
            
        except Exception as e:
            logger.error(f"Error loading skills taxonomy: {e}")
            raise
    
    def create_skills_taxonomy_entry(self, taxonomy_data: SkillsTaxonomyCreate) -> SkillsTaxonomy:
        """
        Create a new skills taxonomy entry.
        
        Args:
            taxonomy_data: Skills taxonomy creation data
            
        Returns:
            SkillsTaxonomy: Created taxonomy entry
        """
        logger.info(f"Creating skills taxonomy entry: {taxonomy_data.skill_name}")
        
        try:
            # Check if skill already exists
            existing_query = "SELECT * FROM skills_taxonomy WHERE skill_name = ?"
            existing_results = self.db.execute_query(existing_query, (taxonomy_data.skill_name,))
            
            if existing_results:
                logger.info(f"Skill '{taxonomy_data.skill_name}' already exists, skipping creation")
                return self._parse_skills_taxonomy(existing_results[0])
            
            taxonomy_id = str(uuid.uuid4())
            taxonomy_dict = taxonomy_data.dict()
            
            # Convert lists to JSON strings
            json_fields = [
                'proficiency_levels', 'related_skills', 'prerequisites',
                'typical_use_cases', 'industry_relevance', 'learning_resources', 'assessment_methods'
            ]
            for field in json_fields:
                if taxonomy_dict.get(field):
                    taxonomy_dict[field] = json.dumps(taxonomy_dict[field])
                else:
                    taxonomy_dict[field] = json.dumps([])
            
            insert_query = """
            INSERT INTO skills_taxonomy (
                id, skill_name, category, subcategory, description,
                proficiency_levels, related_skills, prerequisites,
                typical_use_cases, industry_relevance, learning_resources, assessment_methods
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            params = (
                taxonomy_id,
                taxonomy_dict['skill_name'],
                taxonomy_dict['category'],
                taxonomy_dict['subcategory'],
                taxonomy_dict['description'],
                taxonomy_dict['proficiency_levels'],
                taxonomy_dict['related_skills'],
                taxonomy_dict['prerequisites'],
                taxonomy_dict['typical_use_cases'],
                taxonomy_dict['industry_relevance'],
                taxonomy_dict['learning_resources'],
                taxonomy_dict['assessment_methods']
            )
            
            self.db.execute_update(insert_query, params)
            
            logger.info(f"Skills taxonomy entry created: {taxonomy_id}")
            return self.get_skills_taxonomy_entry(taxonomy_id)
            
        except Exception as e:
            logger.error(f"Error creating skills taxonomy entry: {e}")
            raise
    
    def get_skills_taxonomy_entry(self, taxonomy_id: str) -> Optional[SkillsTaxonomy]:
        """Get skills taxonomy entry by ID."""
        query = "SELECT * FROM skills_taxonomy WHERE id = ? AND is_active = 1"
        results = self.db.execute_query(query, (taxonomy_id,))
        
        if not results:
            return None
        
        return self._parse_skills_taxonomy(results[0])
    
    def get_skills_taxonomy_by_category(self, category: str) -> List[SkillsTaxonomy]:
        """Get all skills taxonomy entries for a category."""
        query = "SELECT * FROM skills_taxonomy WHERE category = ? AND is_active = 1 ORDER BY skill_name"
        results = self.db.execute_query(query, (category,))
        
        return [self._parse_skills_taxonomy(result) for result in results]
    
    def get_all_skills_taxonomy(self) -> List[SkillsTaxonomy]:
        """Get all active skills taxonomy entries."""
        query = "SELECT * FROM skills_taxonomy WHERE is_active = 1 ORDER BY category, skill_name"
        results = self.db.execute_query(query)
        
        return [self._parse_skills_taxonomy(result) for result in results]
    
    def search_skills_taxonomy(self, query_text: str) -> List[SkillsTaxonomy]:
        """
        Search skills taxonomy by skill name or description.
        
        Args:
            query_text: Search query text
            
        Returns:
            List[SkillsTaxonomy]: Matching skills taxonomy entries
        """
        search_query = """
        SELECT * FROM skills_taxonomy 
        WHERE is_active = 1 
        AND (skill_name LIKE ? OR description LIKE ? OR category LIKE ?)
        ORDER BY skill_name
        """
        
        search_term = f"%{query_text}%"
        results = self.db.execute_query(search_query, (search_term, search_term, search_term))
        
        return [self._parse_skills_taxonomy(result) for result in results]
    
    # Skills Assessment Management
    
    def create_skills_assessment(self, assessment_data: SkillsAssessmentCreate) -> SkillsAssessment:
        """
        Create a new skills assessment.
        
        Args:
            assessment_data: Skills assessment creation data
            
        Returns:
            SkillsAssessment: Created assessment
        """
        logger.info(f"Creating skills assessment: {assessment_data.title}")
        
        try:
            assessment_id = str(uuid.uuid4())
            assessment_dict = assessment_data.dict()
            
            # Convert lists to JSON strings
            json_fields = ['artifacts_analyzed', 'skills_evaluated']
            for field in json_fields:
                if assessment_dict.get(field):
                    assessment_dict[field] = json.dumps(assessment_dict[field])
                else:
                    assessment_dict[field] = json.dumps([])
            
            insert_query = """
            INSERT INTO skills_assessments (
                id, user_id, assessment_type, status, title, description,
                artifacts_analyzed, skills_evaluated
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            params = (
                assessment_id,
                assessment_dict['user_id'],
                assessment_dict['assessment_type'],
                AssessmentStatus.PENDING,
                assessment_dict['title'],
                assessment_dict['description'],
                assessment_dict['artifacts_analyzed'],
                assessment_dict['skills_evaluated']
            )
            
            self.db.execute_update(insert_query, params)
            
            logger.info(f"Skills assessment created: {assessment_id}")
            return self.get_skills_assessment(assessment_id)
            
        except Exception as e:
            logger.error(f"Error creating skills assessment: {e}")
            raise
    
    def get_skills_assessment(self, assessment_id: str) -> Optional[SkillsAssessment]:
        """Get skills assessment by ID."""
        query = "SELECT * FROM skills_assessments WHERE id = ?"
        results = self.db.execute_query(query, (assessment_id,))
        
        if not results:
            return None
        
        return self._parse_skills_assessment(results[0])
    
    def get_user_assessments(self, user_id: str, limit: int = 20) -> List[SkillsAssessment]:
        """Get user's skills assessments."""
        query = """
        SELECT * FROM skills_assessments 
        WHERE user_id = ? 
        ORDER BY created_at DESC 
        LIMIT ?
        """
        results = self.db.execute_query(query, (user_id, limit))
        
        return [self._parse_skills_assessment(result) for result in results]
    
    def update_assessment_status(self, assessment_id: str, status: AssessmentStatus) -> bool:
        """Update assessment status."""
        logger.info(f"Updating assessment status: {assessment_id} -> {status}")
        
        try:
            update_query = """
            UPDATE skills_assessments 
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """
            
            affected_rows = self.db.execute_update(update_query, (status, assessment_id))
            
            if affected_rows > 0:
                logger.info(f"Assessment status updated: {assessment_id}")
                return True
            else:
                logger.warning(f"Assessment not found: {assessment_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating assessment status: {e}")
            raise
    
    # AI-Powered Skills Analysis
    
    def analyze_work_artifacts(
        self, 
        assessment_id: str, 
        artifacts: List[Union[str, ProcessedContent]]
    ) -> SkillsAssessment:
        """
        Analyze work artifacts using AI to identify skills and competency levels.
        
        Args:
            assessment_id: Skills assessment ID
            artifacts: List of text content or processed content from artifacts
            
        Returns:
            SkillsAssessment: Updated assessment with analysis results
        """
        logger.info(f"Analyzing work artifacts for assessment: {assessment_id}")
        
        try:
            # Update assessment status to in progress
            self.update_assessment_status(assessment_id, AssessmentStatus.IN_PROGRESS)
            
            # Combine all artifact text
            combined_text = self._combine_artifact_text(artifacts)
            
            # Get skills taxonomy for context
            skills_taxonomy = self.get_all_skills_taxonomy()
            taxonomy_context = self._build_taxonomy_context(skills_taxonomy)
            
            # Perform AI analysis
            analysis_result = self._perform_ai_skills_analysis(combined_text, taxonomy_context)
            
            # Update assessment with results
            updated_assessment = self._update_assessment_with_analysis(
                assessment_id, analysis_result, artifacts
            )
            
            logger.info(f"Artifact analysis completed for assessment: {assessment_id}")
            return updated_assessment
            
        except Exception as e:
            logger.error(f"Error analyzing work artifacts: {e}")
            # Update status to failed
            self.update_assessment_status(assessment_id, AssessmentStatus.FAILED)
            raise
    
    def _combine_artifact_text(self, artifacts: List[Union[str, ProcessedContent]]) -> str:
        """Combine text from multiple artifacts."""
        combined_text = ""
        
        for artifact in artifacts:
            if isinstance(artifact, str):
                combined_text += artifact + "\n\n"
            elif isinstance(artifact, ProcessedContent):
                combined_text += artifact.text + "\n\n"
        
        return combined_text.strip()
    
    def _build_taxonomy_context(self, skills_taxonomy: List[SkillsTaxonomy]) -> str:
        """Build context string from skills taxonomy."""
        context_parts = []
        
        for skill in skills_taxonomy:
            skill_info = f"Skill: {skill.skill_name}\n"
            skill_info += f"Category: {skill.category}\n"
            if skill.subcategory:
                skill_info += f"Subcategory: {skill.subcategory}\n"
            if skill.description:
                skill_info += f"Description: {skill.description}\n"
            skill_info += f"Proficiency Levels: {', '.join(skill.proficiency_levels)}\n"
            if skill.typical_use_cases:
                skill_info += f"Use Cases: {', '.join(skill.typical_use_cases)}\n"
            context_parts.append(skill_info)
        
        return "\n\n".join(context_parts)
    
    def _perform_ai_skills_analysis(self, text: str, taxonomy_context: str) -> Dict[str, Any]:
        """Perform AI-powered skills analysis."""
        system_prompt = """
        You are an expert skills assessment analyst. Your task is to analyze work artifacts 
        and identify the skills demonstrated, competency levels, and potential skill gaps.
        
        Skills Taxonomy Context:
        {taxonomy_context}
        
        Please analyze the provided work artifacts and return a JSON response with the following structure:
        {{
            "skills_demonstrated": [
                {{
                    "skill_name": "string",
                    "category": "string",
                    "competency_level": "beginner|intermediate|advanced|expert",
                    "confidence_score": 0.0-1.0,
                    "evidence": "specific examples from the text",
                    "strengths": ["list of strengths"],
                    "areas_for_improvement": ["list of areas to improve"]
                }}
            ],
            "skill_gaps": [
                {{
                    "skill_name": "string",
                    "category": "string",
                    "gap_size": "small|medium|large",
                    "priority": "low|medium|high|critical",
                    "business_impact": "description of impact",
                    "recommended_actions": ["list of recommended learning actions"]
                }}
            ],
            "overall_assessment": {{
                "overall_score": 0-100,
                "confidence_level": 0.0-1.0,
                "summary": "overall assessment summary",
                "key_strengths": ["list of key strengths"],
                "primary_gaps": ["list of primary skill gaps"],
                "recommendations": ["list of top recommendations"]
            }}
        }}
        
        Focus on both product management skills and technical skills relevant to the work context.
        Be specific and provide actionable insights.
        """
        
        user_prompt = f"""
        Please analyze the following work artifacts for skills assessment:
        
        {text}
        
        Provide a comprehensive analysis of demonstrated skills, competency levels, 
        and identified skill gaps. Focus on actionable insights for learning and development.
        """
        
        try:
            response = self.ai_client.generate_text(
                user_prompt,
                system_message=system_prompt.format(taxonomy_context=taxonomy_context)
            )
            
            if response.error:
                raise Exception(f"AI analysis failed: {response.error}")
            
            # Parse JSON response
            analysis_result = json.loads(response.content)
            
            return analysis_result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI analysis response: {e}")
            # Return fallback analysis
            return self._create_fallback_analysis(text)
        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            raise
    
    def _create_fallback_analysis(self, text: str) -> Dict[str, Any]:
        """Create a fallback analysis when AI analysis fails."""
        return {
            "skills_demonstrated": [],
            "skill_gaps": [],
            "overall_assessment": {
                "overall_score": 50,
                "confidence_level": 0.3,
                "summary": "Analysis incomplete due to technical issues",
                "key_strengths": [],
                "primary_gaps": [],
                "recommendations": ["Please try the analysis again or contact support"]
            }
        }
    
    def _update_assessment_with_analysis(
        self, 
        assessment_id: str, 
        analysis_result: Dict[str, Any], 
        artifacts: List[Union[str, ProcessedContent]]
    ) -> SkillsAssessment:
        """Update assessment with analysis results."""
        logger.info(f"Updating assessment with analysis results: {assessment_id}")
        
        try:
            # Extract skills evaluated
            skills_evaluated = []
            for skill in analysis_result.get("skills_demonstrated", []):
                skills_evaluated.append(skill["skill_name"])
            
            # Extract artifact IDs (for now, use simple identifiers)
            artifact_ids = []
            for i, artifact in enumerate(artifacts):
                if isinstance(artifact, ProcessedContent):
                    artifact_ids.append(f"artifact_{i}_{artifact.metadata.file_hash[:8]}")
                else:
                    artifact_ids.append(f"text_artifact_{i}")
            
            # Update assessment
            update_query = """
            UPDATE skills_assessments 
            SET 
                status = ?,
                artifacts_analyzed = ?,
                skills_evaluated = ?,
                overall_score = ?,
                confidence_level = ?,
                assessment_data = ?,
                recommendations = ?,
                started_at = CURRENT_TIMESTAMP,
                completed_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """
            
            overall_assessment = analysis_result.get("overall_assessment", {})
            
            params = (
                AssessmentStatus.COMPLETED,
                json.dumps(artifact_ids),
                json.dumps(skills_evaluated),
                overall_assessment.get("overall_score"),
                overall_assessment.get("confidence_level"),
                json.dumps(analysis_result),
                json.dumps(overall_assessment.get("recommendations", [])),
                assessment_id
            )
            
            self.db.execute_update(update_query, params)
            
            # Create skill gaps
            self._create_skill_gaps_from_analysis(assessment_id, analysis_result)
            
            logger.info(f"Assessment updated with analysis results: {assessment_id}")
            return self.get_skills_assessment(assessment_id)
            
        except Exception as e:
            logger.error(f"Error updating assessment with analysis: {e}")
            raise
    
    def _create_skill_gaps_from_analysis(
        self, 
        assessment_id: str, 
        analysis_result: Dict[str, Any]
    ) -> None:
        """Create skill gaps from analysis results."""
        try:
            # Get user_id from assessment
            assessment = self.get_skills_assessment(assessment_id)
            if not assessment:
                return
            
            user_id = assessment.user_id
            
            # Create skill gaps
            for gap_data in analysis_result.get("skill_gaps", []):
                skill_gap = SkillGapCreate(
                    user_id=user_id,
                    skill_name=gap_data["skill_name"],
                    category=gap_data.get("category"),
                    gap_size=gap_data.get("gap_size", "medium"),
                    priority=gap_data.get("priority", "medium"),
                    business_impact=gap_data.get("business_impact"),
                    recommended_actions=gap_data.get("recommended_actions", []),
                    evidence_sources=[f"assessment_{assessment_id}"]
                )
                
                self.create_skill_gap(skill_gap)
                
        except Exception as e:
            logger.error(f"Error creating skill gaps from analysis: {e}")
    
    # Skill Gap Management
    
    def create_skill_gap(self, gap_data: SkillGapCreate) -> SkillGap:
        """Create a new skill gap."""
        logger.info(f"Creating skill gap: {gap_data.skill_name}")
        
        try:
            gap_id = str(uuid.uuid4())
            gap_dict = gap_data.dict()
            
            # Convert lists to JSON strings
            json_fields = ['evidence_sources', 'recommended_actions', 'related_skills']
            for field in json_fields:
                if gap_dict.get(field):
                    gap_dict[field] = json.dumps(gap_dict[field])
                else:
                    gap_dict[field] = json.dumps([])
            
            insert_query = """
            INSERT INTO skill_gaps (
                id, user_id, skill_name, category, current_level, target_level,
                gap_size, priority, urgency, business_impact, learning_effort,
                evidence_sources, recommended_actions, related_skills
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            params = (
                gap_id,
                gap_dict['user_id'],
                gap_dict['skill_name'],
                gap_dict['category'],
                gap_dict['current_level'],
                gap_dict['target_level'],
                gap_dict['gap_size'],
                gap_dict['priority'],
                gap_dict['urgency'],
                gap_dict['business_impact'],
                gap_dict['learning_effort'],
                gap_dict['evidence_sources'],
                gap_dict['recommended_actions'],
                gap_dict['related_skills']
            )
            
            self.db.execute_update(insert_query, params)
            
            logger.info(f"Skill gap created: {gap_id}")
            return self.get_skill_gap(gap_id)
            
        except Exception as e:
            logger.error(f"Error creating skill gap: {e}")
            raise
    
    def get_skill_gap(self, gap_id: str) -> Optional[SkillGap]:
        """Get skill gap by ID."""
        query = "SELECT * FROM skill_gaps WHERE id = ?"
        results = self.db.execute_query(query, (gap_id,))
        
        if not results:
            return None
        
        return self._parse_skill_gap(results[0])
    
    def get_user_skill_gaps(self, user_id: str, priority: Optional[str] = None) -> List[SkillGap]:
        """Get user's skill gaps with optional priority filtering."""
        query = "SELECT * FROM skill_gaps WHERE user_id = ?"
        params = [user_id]
        
        if priority:
            query += " AND priority = ?"
            params.append(priority)
        
        query += " ORDER BY created_at DESC"
        
        results = self.db.execute_query(query, tuple(params))
        return [self._parse_skill_gap(result) for result in results]
    
    # Helper Methods
    
    def _parse_skills_taxonomy(self, row) -> SkillsTaxonomy:
        """Parse database row to SkillsTaxonomy object."""
        row_dict = dict(row)
        
        # Parse JSON fields
        json_fields = [
            'proficiency_levels', 'related_skills', 'prerequisites',
            'typical_use_cases', 'industry_relevance', 'learning_resources', 'assessment_methods'
        ]
        for field in json_fields:
            if row_dict.get(field):
                try:
                    row_dict[field] = json.loads(row_dict[field])
                except json.JSONDecodeError:
                    row_dict[field] = []
            else:
                row_dict[field] = []
        
        return SkillsTaxonomy(**row_dict)
    
    def _parse_skills_assessment(self, row) -> SkillsAssessment:
        """Parse database row to SkillsAssessment object."""
        row_dict = dict(row)
        
        # Parse JSON fields
        json_fields = ['artifacts_analyzed', 'skills_evaluated', 'assessment_data', 'recommendations']
        for field in json_fields:
            if row_dict.get(field):
                try:
                    row_dict[field] = json.loads(row_dict[field])
                except json.JSONDecodeError:
                    row_dict[field] = [] if field in ['artifacts_analyzed', 'skills_evaluated', 'recommendations'] else {}
            else:
                row_dict[field] = [] if field in ['artifacts_analyzed', 'skills_evaluated', 'recommendations'] else {}
        
        # Parse timestamps
        if row_dict.get('started_at'):
            row_dict['started_at'] = datetime.fromisoformat(row_dict['started_at'])
        if row_dict.get('completed_at'):
            row_dict['completed_at'] = datetime.fromisoformat(row_dict['completed_at'])
        
        return SkillsAssessment(**row_dict)
    
    def _parse_skill_gap(self, row) -> SkillGap:
        """Parse database row to SkillGap object."""
        row_dict = dict(row)
        
        # Parse JSON fields
        json_fields = ['evidence_sources', 'recommended_actions', 'related_skills']
        for field in json_fields:
            if row_dict.get(field):
                try:
                    row_dict[field] = json.loads(row_dict[field])
                except json.JSONDecodeError:
                    row_dict[field] = []
            else:
                row_dict[field] = []
        
        return SkillGap(**row_dict)


# Global skills engine instance
_skills_engine_instance: Optional[SkillsEngine] = None


def get_skills_engine() -> SkillsEngine:
    """
    Get the global skills engine instance.
    
    Returns:
        SkillsEngine: Global skills engine instance
    """
    global _skills_engine_instance
    if _skills_engine_instance is None:
        _skills_engine_instance = SkillsEngine()
    return _skills_engine_instance


def initialize_skills_engine() -> SkillsEngine:
    """
    Initialize the global skills engine.
    
    Returns:
        SkillsEngine: Initialized skills engine instance
    """
    global _skills_engine_instance
    _skills_engine_instance = SkillsEngine()
    return _skills_engine_instance
