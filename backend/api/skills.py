"""
Skills assessment API endpoints for the Personal Learning Agent.

This module provides RESTful API endpoints for skills assessment, gap analysis,
and skills taxonomy management.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
import logging

from ..services.skills_engine import get_skills_engine
from ..models.skills import (
    SkillsAssessment, SkillsAssessmentCreate, SkillsAssessmentUpdate,
    SkillGap, SkillGapCreate, SkillGapUpdate,
    SkillsTaxonomy, SkillsTaxonomyCreate, SkillsTaxonomyUpdate,
    AssessmentStatus, AssessmentType
)
from ..utils.file_processor import get_file_processor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/skills", tags=["skills"])


# Skills Taxonomy Endpoints

@router.get("/taxonomy", response_model=List[SkillsTaxonomy])
async def get_skills_taxonomy(category: Optional[str] = None):
    """
    Get skills taxonomy entries.
    
    Args:
        category: Optional category filter
        
    Returns:
        List[SkillsTaxonomy]: Skills taxonomy entries
    """
    try:
        skills_engine = get_skills_engine()
        
        if category:
            taxonomy = skills_engine.get_skills_taxonomy_by_category(category)
        else:
            taxonomy = skills_engine.get_all_skills_taxonomy()
        
        return taxonomy
        
    except Exception as e:
        logger.error(f"Error getting skills taxonomy: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/taxonomy/search", response_model=List[SkillsTaxonomy])
async def search_skills_taxonomy(q: str):
    """
    Search skills taxonomy by skill name or description.
    
    Args:
        q: Search query
        
    Returns:
        List[SkillsTaxonomy]: Matching skills taxonomy entries
    """
    try:
        skills_engine = get_skills_engine()
        results = skills_engine.search_skills_taxonomy(q)
        
        return results
        
    except Exception as e:
        logger.error(f"Error searching skills taxonomy: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/taxonomy", response_model=SkillsTaxonomy)
async def create_skills_taxonomy_entry(taxonomy_data: SkillsTaxonomyCreate):
    """
    Create a new skills taxonomy entry.
    
    Args:
        taxonomy_data: Skills taxonomy creation data
        
    Returns:
        SkillsTaxonomy: Created taxonomy entry
    """
    try:
        skills_engine = get_skills_engine()
        taxonomy_entry = skills_engine.create_skills_taxonomy_entry(taxonomy_data)
        
        return taxonomy_entry
        
    except Exception as e:
        logger.error(f"Error creating skills taxonomy entry: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/taxonomy/load-from-file")
async def load_skills_taxonomy_from_file(file_path: str):
    """
    Load skills taxonomy from JSON file.
    
    Args:
        file_path: Path to skills taxonomy JSON file
        
    Returns:
        Dict: Loading results
    """
    try:
        skills_engine = get_skills_engine()
        taxonomy_entries = skills_engine.load_skills_taxonomy_from_file(file_path)
        
        return {
            "message": f"Loaded {len(taxonomy_entries)} skills taxonomy entries",
            "entries_loaded": len(taxonomy_entries),
            "file_path": file_path
        }
        
    except Exception as e:
        logger.error(f"Error loading skills taxonomy from file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Skills Assessment Endpoints

@router.post("/assessments", response_model=SkillsAssessment)
async def create_skills_assessment(assessment_data: SkillsAssessmentCreate):
    """
    Create a new skills assessment.
    
    Args:
        assessment_data: Skills assessment creation data
        
    Returns:
        SkillsAssessment: Created assessment
    """
    try:
        skills_engine = get_skills_engine()
        assessment = skills_engine.create_skills_assessment(assessment_data)
        
        return assessment
        
    except Exception as e:
        logger.error(f"Error creating skills assessment: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/assessments/{assessment_id}", response_model=SkillsAssessment)
async def get_skills_assessment(assessment_id: str):
    """
    Get skills assessment by ID.
    
    Args:
        assessment_id: Assessment ID
        
    Returns:
        SkillsAssessment: Skills assessment
    """
    try:
        skills_engine = get_skills_engine()
        assessment = skills_engine.get_skills_assessment(assessment_id)
        
        if not assessment:
            raise HTTPException(status_code=404, detail="Assessment not found")
        
        return assessment
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting skills assessment: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/assessments/user/{user_id}", response_model=List[SkillsAssessment])
async def get_user_assessments(user_id: str, limit: int = 20):
    """
    Get user's skills assessments.
    
    Args:
        user_id: User ID
        limit: Maximum number of assessments to return
        
    Returns:
        List[SkillsAssessment]: User's assessments
    """
    try:
        skills_engine = get_skills_engine()
        assessments = skills_engine.get_user_assessments(user_id, limit)
        
        return assessments
        
    except Exception as e:
        logger.error(f"Error getting user assessments: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/assessments/{assessment_id}/status")
async def update_assessment_status(assessment_id: str, status: AssessmentStatus):
    """
    Update assessment status.
    
    Args:
        assessment_id: Assessment ID
        status: New status
        
    Returns:
        Dict: Update result
    """
    try:
        skills_engine = get_skills_engine()
        success = skills_engine.update_assessment_status(assessment_id, status)
        
        if not success:
            raise HTTPException(status_code=404, detail="Assessment not found")
        
        return {"message": "Assessment status updated successfully", "status": status}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating assessment status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Artifact Analysis Endpoints

@router.post("/assessments/{assessment_id}/analyze-text")
async def analyze_text_artifacts(
    assessment_id: str, 
    text_content: str = Form(...),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Analyze text artifacts for skills assessment.
    
    Args:
        assessment_id: Assessment ID
        text_content: Text content to analyze
        background_tasks: Background tasks for async processing
        
    Returns:
        Dict: Analysis initiation result
    """
    try:
        skills_engine = get_skills_engine()
        
        # Check if assessment exists
        assessment = skills_engine.get_skills_assessment(assessment_id)
        if not assessment:
            raise HTTPException(status_code=404, detail="Assessment not found")
        
        # Start analysis in background
        background_tasks.add_task(
            skills_engine.analyze_work_artifacts,
            assessment_id,
            [text_content]
        )
        
        return {
            "message": "Text analysis started",
            "assessment_id": assessment_id,
            "status": "in_progress"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting text analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/assessments/{assessment_id}/analyze-files")
async def analyze_file_artifacts(
    assessment_id: str,
    files: List[UploadFile] = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Analyze file artifacts for skills assessment.
    
    Args:
        assessment_id: Assessment ID
        files: Uploaded files to analyze
        background_tasks: Background tasks for async processing
        
    Returns:
        Dict: Analysis initiation result
    """
    try:
        skills_engine = get_skills_engine()
        file_processor = get_file_processor()
        
        # Check if assessment exists
        assessment = skills_engine.get_skills_assessment(assessment_id)
        if not assessment:
            raise HTTPException(status_code=404, detail="Assessment not found")
        
        # Process files
        processed_contents = file_processor.process_multiple_files(files)
        
        # Start analysis in background
        background_tasks.add_task(
            skills_engine.analyze_work_artifacts,
            assessment_id,
            processed_contents
        )
        
        return {
            "message": "File analysis started",
            "assessment_id": assessment_id,
            "files_processed": len(processed_contents),
            "status": "in_progress"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting file analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/assessments/{assessment_id}/analyze-mixed")
async def analyze_mixed_artifacts(
    assessment_id: str,
    text_content: Optional[str] = Form(None),
    files: Optional[List[UploadFile]] = File(None),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Analyze mixed artifacts (text and files) for skills assessment.
    
    Args:
        assessment_id: Assessment ID
        text_content: Optional text content
        files: Optional uploaded files
        background_tasks: Background tasks for async processing
        
    Returns:
        Dict: Analysis initiation result
    """
    try:
        skills_engine = get_skills_engine()
        file_processor = get_file_processor()
        
        # Check if assessment exists
        assessment = skills_engine.get_skills_assessment(assessment_id)
        if not assessment:
            raise HTTPException(status_code=404, detail="Assessment not found")
        
        # Prepare artifacts
        artifacts = []
        
        # Add text content if provided
        if text_content:
            artifacts.append(text_content)
        
        # Process files if provided
        if files:
            processed_contents = file_processor.process_multiple_files(files)
            artifacts.extend(processed_contents)
        
        if not artifacts:
            raise HTTPException(status_code=400, detail="No artifacts provided for analysis")
        
        # Start analysis in background
        background_tasks.add_task(
            skills_engine.analyze_work_artifacts,
            assessment_id,
            artifacts
        )
        
        return {
            "message": "Mixed artifact analysis started",
            "assessment_id": assessment_id,
            "artifacts_count": len(artifacts),
            "status": "in_progress"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting mixed artifact analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Skill Gap Endpoints

@router.post("/gaps", response_model=SkillGap)
async def create_skill_gap(gap_data: SkillGapCreate):
    """
    Create a new skill gap.
    
    Args:
        gap_data: Skill gap creation data
        
    Returns:
        SkillGap: Created skill gap
    """
    try:
        skills_engine = get_skills_engine()
        skill_gap = skills_engine.create_skill_gap(gap_data)
        
        return skill_gap
        
    except Exception as e:
        logger.error(f"Error creating skill gap: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/gaps/{gap_id}", response_model=SkillGap)
async def get_skill_gap(gap_id: str):
    """
    Get skill gap by ID.
    
    Args:
        gap_id: Skill gap ID
        
    Returns:
        SkillGap: Skill gap
    """
    try:
        skills_engine = get_skills_engine()
        skill_gap = skills_engine.get_skill_gap(gap_id)
        
        if not skill_gap:
            raise HTTPException(status_code=404, detail="Skill gap not found")
        
        return skill_gap
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting skill gap: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/gaps/user/{user_id}", response_model=List[SkillGap])
async def get_user_skill_gaps(user_id: str, priority: Optional[str] = None):
    """
    Get user's skill gaps.
    
    Args:
        user_id: User ID
        priority: Optional priority filter (low, medium, high, critical)
        
    Returns:
        List[SkillGap]: User's skill gaps
    """
    try:
        skills_engine = get_skills_engine()
        skill_gaps = skills_engine.get_user_skill_gaps(user_id, priority)
        
        return skill_gaps
        
    except Exception as e:
        logger.error(f"Error getting user skill gaps: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Assessment Report Endpoints

@router.get("/assessments/{assessment_id}/report")
async def get_assessment_report(assessment_id: str):
    """
    Get comprehensive skills assessment report.
    
    Args:
        assessment_id: Assessment ID
        
    Returns:
        Dict: Comprehensive assessment report
    """
    try:
        skills_engine = get_skills_engine()
        
        # Get assessment
        assessment = skills_engine.get_skills_assessment(assessment_id)
        if not assessment:
            raise HTTPException(status_code=404, detail="Assessment not found")
        
        # Get skill gaps for the user
        skill_gaps = skills_engine.get_user_skill_gaps(assessment.user_id)
        
        # Build comprehensive report
        report = {
            "assessment": assessment.dict(),
            "skill_gaps": [gap.dict() for gap in skill_gaps],
            "summary": {
                "total_skills_evaluated": len(assessment.skills_evaluated),
                "total_skill_gaps": len(skill_gaps),
                "high_priority_gaps": len([gap for gap in skill_gaps if gap.priority == "high"]),
                "critical_gaps": len([gap for gap in skill_gaps if gap.priority == "critical"]),
                "overall_score": assessment.overall_score,
                "confidence_level": assessment.confidence_level
            }
        }
        
        return report
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating assessment report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Utility Endpoints

@router.get("/categories")
async def get_skill_categories():
    """
    Get all available skill categories.
    
    Returns:
        List[str]: Available skill categories
    """
    try:
        skills_engine = get_skills_engine()
        taxonomy = skills_engine.get_all_skills_taxonomy()
        
        categories = list(set([skill.category for skill in taxonomy]))
        categories.sort()
        
        return categories
        
    except Exception as e:
        logger.error(f"Error getting skill categories: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """
    Health check endpoint for skills assessment service.
    
    Returns:
        Dict: Health status
    """
    try:
        skills_engine = get_skills_engine()
        
        # Test basic functionality
        taxonomy_count = len(skills_engine.get_all_skills_taxonomy())
        
        return {
            "status": "healthy",
            "service": "skills_assessment",
            "taxonomy_entries": taxonomy_count,
            "ai_client_available": skills_engine.ai_client is not None
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "service": "skills_assessment",
                "error": str(e)
            }
        )
