#!/usr/bin/env python3
"""
Test script for skills assessment system.

This script tests the skills assessment engine, including taxonomy loading,
assessment creation, artifact analysis, and report generation.
"""

import sys
import os
from pathlib import Path
from typing import List, Dict, Any

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.services.skills_engine import get_skills_engine
from backend.services.skills_report_generator import get_skills_report_generator
from backend.services.external_integration import get_external_integration_service
from backend.models.skills import SkillsAssessmentCreate, AssessmentType
from backend.database.init_db import initialize_database_schema
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_skills_taxonomy():
    """Test skills taxonomy functionality."""
    logger.info("Testing skills taxonomy...")
    
    try:
        skills_engine = get_skills_engine()
        
        # Get all taxonomy entries
        all_taxonomy = skills_engine.get_all_skills_taxonomy()
        logger.info(f"Total skills taxonomy entries: {len(all_taxonomy)}")
        
        if not all_taxonomy:
            logger.warning("No skills taxonomy entries found. Run init_skills_taxonomy.py first.")
            return False
        
        # Test category filtering
        programming_skills = skills_engine.get_skills_taxonomy_by_category("programming")
        logger.info(f"Programming skills: {len(programming_skills)}")
        
        # Test search functionality
        search_results = skills_engine.search_skills_taxonomy("python")
        logger.info(f"Search results for 'python': {len(search_results)}")
        
        logger.info("✅ Skills taxonomy test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Skills taxonomy test failed: {e}")
        return False


def test_skills_assessment_creation():
    """Test skills assessment creation."""
    logger.info("Testing skills assessment creation...")
    
    try:
        skills_engine = get_skills_engine()
        
        # Create a test assessment
        assessment_data = SkillsAssessmentCreate(
            user_id="test_user_123",
            assessment_type=AssessmentType.ARTIFACT_ANALYSIS,
            title="Test Skills Assessment",
            description="A test assessment for the skills engine",
            artifacts_analyzed=[],
            skills_evaluated=[]
        )
        
        assessment = skills_engine.create_skills_assessment(assessment_data)
        logger.info(f"Created assessment: {assessment.id}")
        
        # Retrieve the assessment
        retrieved_assessment = skills_engine.get_skills_assessment(assessment.id)
        if not retrieved_assessment:
            raise Exception("Failed to retrieve created assessment")
        
        logger.info("✅ Skills assessment creation test passed")
        return assessment.id
        
    except Exception as e:
        logger.error(f"❌ Skills assessment creation test failed: {e}")
        return None


def test_artifact_analysis(assessment_id: str):
    """Test artifact analysis functionality."""
    logger.info("Testing artifact analysis...")
    
    try:
        skills_engine = get_skills_engine()
        
        # Create sample artifacts for analysis
        sample_artifacts = [
            """
            Product Requirements Document: Mobile App Feature
            
            Overview:
            We need to implement a new feature for our mobile application that allows users
            to track their learning progress and receive personalized recommendations.
            
            Technical Requirements:
            - Backend API development using Python and FastAPI
            - Database design with SQLite and ChromaDB for vector storage
            - AI integration with OpenAI API for personalized recommendations
            - Frontend development using React Native for cross-platform compatibility
            
            User Stories:
            1. As a user, I want to see my learning progress so that I can track my improvement
            2. As a user, I want to receive personalized learning recommendations based on my skills
            3. As a user, I want to upload my work documents for skills assessment
            
            Acceptance Criteria:
            - The system should analyze uploaded documents using AI
            - Users should receive actionable learning recommendations
            - The interface should be intuitive and responsive
            - Performance should be optimized for mobile devices
            """,
            
            """
            Code Review Comments:
            
            File: backend/services/skills_engine.py
            
            Issues Found:
            1. The AI analysis function could benefit from better error handling
            2. Consider adding input validation for artifact content
            3. The skills taxonomy loading could be optimized for large datasets
            4. Add unit tests for the assessment creation workflow
            
            Suggestions:
            - Implement retry logic for AI API calls
            - Add comprehensive logging for debugging
            - Consider caching frequently accessed taxonomy data
            - Add integration tests for the complete assessment flow
            """,
            
            """
            Project Status Update:
            
            Current Sprint Progress:
            - Completed: Database schema design and implementation
            - Completed: Basic API endpoints for user management
            - In Progress: Skills assessment engine development
            - Pending: Frontend interface development
            - Pending: Integration testing and deployment
            
            Technical Challenges:
            - Optimizing AI response times for large document analysis
            - Managing vector storage for semantic search
            - Ensuring data privacy and security compliance
            
            Next Steps:
            - Complete skills assessment engine testing
            - Begin frontend development with React Native
            - Set up CI/CD pipeline for automated testing
            - Plan user acceptance testing phase
            """
        ]
        
        # Analyze artifacts
        logger.info("Starting artifact analysis...")
        updated_assessment = skills_engine.analyze_work_artifacts(assessment_id, sample_artifacts)
        
        logger.info(f"Analysis completed. Status: {updated_assessment.status}")
        logger.info(f"Overall score: {updated_assessment.overall_score}")
        logger.info(f"Confidence level: {updated_assessment.confidence_level}")
        logger.info(f"Skills evaluated: {len(updated_assessment.skills_evaluated)}")
        
        if updated_assessment.assessment_data:
            assessment_data = updated_assessment.assessment_data
            skills_demonstrated = assessment_data.get("skills_demonstrated", [])
            skill_gaps = assessment_data.get("skill_gaps", [])
            
            logger.info(f"Skills demonstrated: {len(skills_demonstrated)}")
            logger.info(f"Skill gaps identified: {len(skill_gaps)}")
            
            # Show some examples
            if skills_demonstrated:
                logger.info("Sample skills demonstrated:")
                for skill in skills_demonstrated[:3]:
                    logger.info(f"  - {skill.get('skill_name', 'Unknown')}: {skill.get('competency_level', 'Unknown')}")
            
            if skill_gaps:
                logger.info("Sample skill gaps:")
                for gap in skill_gaps[:3]:
                    logger.info(f"  - {gap.get('skill_name', 'Unknown')}: {gap.get('priority', 'Unknown')} priority")
        
        logger.info("✅ Artifact analysis test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Artifact analysis test failed: {e}")
        return False


def test_report_generation(assessment_id: str):
    """Test report generation functionality."""
    logger.info("Testing report generation...")
    
    try:
        report_generator = get_skills_report_generator()
        
        # Generate comprehensive report
        report = report_generator.generate_comprehensive_report(assessment_id)
        
        logger.info("Report generated successfully")
        logger.info(f"Report sections: {list(report.keys())}")
        
        # Check executive summary
        if "executive_summary" in report:
            summary = report["executive_summary"]
            logger.info(f"Overall score: {summary.get('overall_score', 'N/A')}")
            logger.info(f"Total skill gaps: {summary.get('total_skill_gaps', 'N/A')}")
            logger.info(f"High priority gaps: {summary.get('high_priority_gaps', 'N/A')}")
        
        # Check skills analysis
        if "skills_analysis" in report:
            skills_analysis = report["skills_analysis"]
            logger.info(f"Skills evaluated: {skills_analysis.get('total_skills_evaluated', 'N/A')}")
        
        # Check gap analysis
        if "gap_analysis" in report:
            gap_analysis = report["gap_analysis"]
            logger.info(f"Total gaps: {gap_analysis.get('total_gaps', 'N/A')}")
        
        # Generate learning roadmap
        roadmap = report_generator.generate_learning_roadmap("test_user_123")
        logger.info(f"Learning roadmap generated with {len(roadmap.get('learning_phases', []))} phases")
        
        logger.info("✅ Report generation test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Report generation test failed: {e}")
        return False


def test_external_integration():
    """Test external integration functionality."""
    logger.info("Testing external integration...")
    
    try:
        integration_service = get_external_integration_service()
        
        # Check integration status
        status = integration_service.get_integration_status()
        logger.info(f"Integration status: {status}")
        
        # Test GitHub integration (if configured)
        if status["github"]["configured"]:
            logger.info("GitHub integration is configured")
            # Note: We won't actually make API calls in the test to avoid rate limits
        else:
            logger.info("GitHub integration not configured (this is expected for testing)")
        
        # Test Google Drive integration (if configured)
        if status["google_drive"]["configured"]:
            logger.info("Google Drive integration is configured")
        else:
            logger.info("Google Drive integration not configured (this is expected for testing)")
        
        logger.info("✅ External integration test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ External integration test failed: {e}")
        return False


def main():
    """Run all skills assessment tests."""
    logger.info("Starting skills assessment system tests...")
    
    try:
        # Initialize database schema
        logger.info("Initializing database schema...")
        initialize_database_schema()
        logger.info("Database schema initialized")
        
        # Run tests
        tests_passed = 0
        total_tests = 5
        
        # Test 1: Skills taxonomy
        if test_skills_taxonomy():
            tests_passed += 1
        
        # Test 2: Skills assessment creation
        assessment_id = test_skills_assessment_creation()
        if assessment_id:
            tests_passed += 1
            
            # Test 3: Artifact analysis
            if test_artifact_analysis(assessment_id):
                tests_passed += 1
            
            # Test 4: Report generation
            if test_report_generation(assessment_id):
                tests_passed += 1
        
        # Test 5: External integration
        if test_external_integration():
            tests_passed += 1
        
        # Summary
        logger.info(f"\n{'='*50}")
        logger.info(f"Test Results: {tests_passed}/{total_tests} tests passed")
        
        if tests_passed == total_tests:
            logger.info("🎉 All tests passed! Skills assessment system is working correctly.")
            return True
        else:
            logger.warning(f"⚠️  {total_tests - tests_passed} tests failed. Please check the logs above.")
            return False
            
    except Exception as e:
        logger.error(f"❌ Test suite failed: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
