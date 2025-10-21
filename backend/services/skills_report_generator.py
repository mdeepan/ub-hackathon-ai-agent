"""
Skills assessment report generator for the Personal Learning Agent.

This module provides comprehensive report generation capabilities for skills assessments,
including detailed analysis reports, learning recommendations, and progress tracking.
"""

import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging

from ..services.skills_engine import get_skills_engine
from ..services.user_service import get_user_service
from ..models.skills import SkillsAssessment, SkillGap, SkillsTaxonomy
from ..models.user import UserProfile

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SkillsReportGenerator:
    """
    Comprehensive skills assessment report generator.
    
    This class generates detailed reports including skills analysis, gap identification,
    learning recommendations, and progress tracking insights.
    """
    
    def __init__(self):
        """Initialize the report generator."""
        self.skills_engine = get_skills_engine()
        self.user_service = get_user_service()
        logger.info("Skills report generator initialized")
    
    def generate_comprehensive_report(self, assessment_id: str) -> Dict[str, Any]:
        """
        Generate a comprehensive skills assessment report.
        
        Args:
            assessment_id: Skills assessment ID
            
        Returns:
            Dict[str, Any]: Comprehensive assessment report
        """
        logger.info(f"Generating comprehensive report for assessment: {assessment_id}")
        
        try:
            # Get assessment data
            assessment = self.skills_engine.get_skills_assessment(assessment_id)
            if not assessment:
                raise ValueError(f"Assessment not found: {assessment_id}")
            
            # Get user profile
            user_profile = self.user_service.get_user_profile(assessment.user_id)
            
            # Get skill gaps
            skill_gaps = self.skills_engine.get_user_skill_gaps(assessment.user_id)
            
            # Get skills taxonomy for context
            skills_taxonomy = self.skills_engine.get_all_skills_taxonomy()
            
            # Generate report sections
            report = {
                "report_metadata": self._generate_report_metadata(assessment, user_profile),
                "executive_summary": self._generate_executive_summary(assessment, skill_gaps),
                "skills_analysis": self._generate_skills_analysis(assessment, skills_taxonomy),
                "gap_analysis": self._generate_gap_analysis(skill_gaps),
                "learning_recommendations": self._generate_learning_recommendations(assessment, skill_gaps),
                "progress_insights": self._generate_progress_insights(assessment.user_id),
                "action_plan": self._generate_action_plan(skill_gaps, user_profile),
                "appendix": self._generate_appendix(assessment, skill_gaps, skills_taxonomy)
            }
            
            logger.info(f"Comprehensive report generated for assessment: {assessment_id}")
            return report
            
        except Exception as e:
            logger.error(f"Error generating comprehensive report: {e}")
            raise
    
    def generate_executive_summary(self, assessment_id: str) -> Dict[str, Any]:
        """
        Generate executive summary for skills assessment.
        
        Args:
            assessment_id: Skills assessment ID
            
        Returns:
            Dict[str, Any]: Executive summary
        """
        try:
            assessment = self.skills_engine.get_skills_assessment(assessment_id)
            if not assessment:
                raise ValueError(f"Assessment not found: {assessment_id}")
            
            skill_gaps = self.skills_engine.get_user_skill_gaps(assessment.user_id)
            user_profile = self.user_service.get_user_profile(assessment.user_id)
            
            return self._generate_executive_summary(assessment, skill_gaps)
            
        except Exception as e:
            logger.error(f"Error generating executive summary: {e}")
            raise
    
    def generate_learning_roadmap(self, user_id: str) -> Dict[str, Any]:
        """
        Generate personalized learning roadmap based on skill gaps.
        
        Args:
            user_id: User ID
            
        Returns:
            Dict[str, Any]: Learning roadmap
        """
        logger.info(f"Generating learning roadmap for user: {user_id}")
        
        try:
            # Get user data
            user_profile = self.user_service.get_user_profile(user_id)
            skill_gaps = self.skills_engine.get_user_skill_gaps(user_id)
            skills_taxonomy = self.skills_engine.get_all_skills_taxonomy()
            
            # Generate roadmap
            roadmap = {
                "user_context": self._get_user_context_summary(user_profile),
                "priority_gaps": self._prioritize_skill_gaps(skill_gaps),
                "learning_phases": self._generate_learning_phases(skill_gaps, skills_taxonomy),
                "timeline": self._generate_learning_timeline(skill_gaps),
                "success_metrics": self._define_success_metrics(skill_gaps),
                "resources": self._recommend_learning_resources(skill_gaps, skills_taxonomy)
            }
            
            logger.info(f"Learning roadmap generated for user: {user_id}")
            return roadmap
            
        except Exception as e:
            logger.error(f"Error generating learning roadmap: {e}")
            raise
    
    def generate_progress_report(self, user_id: str, time_period: str = "30d") -> Dict[str, Any]:
        """
        Generate progress report for user's skill development.
        
        Args:
            user_id: User ID
            time_period: Time period for progress analysis (7d, 30d, 90d, 1y)
            
        Returns:
            Dict[str, Any]: Progress report
        """
        logger.info(f"Generating progress report for user: {user_id}, period: {time_period}")
        
        try:
            # Get user assessments within time period
            assessments = self.skills_engine.get_user_assessments(user_id, limit=50)
            cutoff_date = self._get_cutoff_date(time_period)
            
            recent_assessments = [
                a for a in assessments 
                if a.created_at >= cutoff_date
            ]
            
            # Get current skill gaps
            current_gaps = self.skills_engine.get_user_skill_gaps(user_id)
            
            # Generate progress analysis
            progress_report = {
                "time_period": time_period,
                "assessment_count": len(recent_assessments),
                "skill_improvements": self._analyze_skill_improvements(recent_assessments),
                "gap_reductions": self._analyze_gap_reductions(current_gaps, recent_assessments),
                "learning_velocity": self._calculate_learning_velocity(recent_assessments),
                "recommendations": self._generate_progress_recommendations(current_gaps, recent_assessments)
            }
            
            logger.info(f"Progress report generated for user: {user_id}")
            return progress_report
            
        except Exception as e:
            logger.error(f"Error generating progress report: {e}")
            raise
    
    # Private helper methods
    
    def _generate_report_metadata(self, assessment: SkillsAssessment, user_profile: Optional[UserProfile]) -> Dict[str, Any]:
        """Generate report metadata."""
        return {
            "report_id": f"skills_report_{assessment.id}",
            "generated_at": datetime.utcnow().isoformat(),
            "assessment_id": assessment.id,
            "user_id": assessment.user_id,
            "user_name": user_profile.name if user_profile else "Unknown",
            "user_role": user_profile.job_role if user_profile else "Unknown",
            "assessment_title": assessment.title,
            "assessment_type": assessment.assessment_type,
            "assessment_date": assessment.created_at.isoformat(),
            "report_version": "1.0"
        }
    
    def _generate_executive_summary(self, assessment: SkillsAssessment, skill_gaps: List[SkillGap]) -> Dict[str, Any]:
        """Generate executive summary."""
        # Calculate key metrics
        total_gaps = len(skill_gaps)
        high_priority_gaps = len([gap for gap in skill_gaps if gap.priority == "high"])
        critical_gaps = len([gap for gap in skill_gaps if gap.priority == "critical"])
        
        # Categorize gaps
        gap_categories = {}
        for gap in skill_gaps:
            category = gap.category or "Other"
            if category not in gap_categories:
                gap_categories[category] = 0
            gap_categories[category] += 1
        
        return {
            "overall_score": assessment.overall_score,
            "confidence_level": assessment.confidence_level,
            "total_skill_gaps": total_gaps,
            "high_priority_gaps": high_priority_gaps,
            "critical_gaps": critical_gaps,
            "gap_categories": gap_categories,
            "key_insights": self._extract_key_insights(assessment, skill_gaps),
            "top_recommendations": self._get_top_recommendations(assessment, skill_gaps)
        }
    
    def _generate_skills_analysis(self, assessment: SkillsAssessment, skills_taxonomy: List[SkillsTaxonomy]) -> Dict[str, Any]:
        """Generate skills analysis section."""
        if not assessment.assessment_data:
            return {"error": "No assessment data available"}
        
        assessment_data = assessment.assessment_data
        skills_demonstrated = assessment_data.get("skills_demonstrated", [])
        
        # Analyze skills by category
        skills_by_category = {}
        for skill in skills_demonstrated:
            category = skill.get("category", "Other")
            if category not in skills_by_category:
                skills_by_category[category] = []
            skills_by_category[category].append(skill)
        
        # Calculate competency distribution
        competency_distribution = {"beginner": 0, "intermediate": 0, "advanced": 0, "expert": 0}
        for skill in skills_demonstrated:
            level = skill.get("competency_level", "beginner")
            if level in competency_distribution:
                competency_distribution[level] += 1
        
        return {
            "total_skills_evaluated": len(skills_demonstrated),
            "skills_by_category": skills_by_category,
            "competency_distribution": competency_distribution,
            "top_skills": self._get_top_skills(skills_demonstrated),
            "skills_breakdown": skills_demonstrated
        }
    
    def _generate_gap_analysis(self, skill_gaps: List[SkillGap]) -> Dict[str, Any]:
        """Generate gap analysis section."""
        if not skill_gaps:
            return {"message": "No skill gaps identified"}
        
        # Analyze gaps by priority
        gaps_by_priority = {"critical": [], "high": [], "medium": [], "low": []}
        for gap in skill_gaps:
            gaps_by_priority[gap.priority].append(gap)
        
        # Analyze gaps by category
        gaps_by_category = {}
        for gap in skill_gaps:
            category = gap.category or "Other"
            if category not in gaps_by_category:
                gaps_by_category[category] = []
            gaps_by_category[category].append(gap)
        
        # Calculate gap sizes
        gap_sizes = {"small": 0, "medium": 0, "large": 0}
        for gap in skill_gaps:
            if gap.gap_size in gap_sizes:
                gap_sizes[gap.gap_size] += 1
        
        return {
            "total_gaps": len(skill_gaps),
            "gaps_by_priority": {k: len(v) for k, v in gaps_by_priority.items()},
            "gaps_by_category": {k: len(v) for k, v in gaps_by_category.items()},
            "gap_sizes": gap_sizes,
            "top_gaps": self._get_top_gaps(skill_gaps),
            "detailed_gaps": [gap.dict() for gap in skill_gaps]
        }
    
    def _generate_learning_recommendations(self, assessment: SkillsAssessment, skill_gaps: List[SkillGap]) -> Dict[str, Any]:
        """Generate learning recommendations section."""
        recommendations = []
        
        # Get recommendations from assessment
        if assessment.recommendations:
            recommendations.extend(assessment.recommendations)
        
        # Get recommendations from skill gaps
        for gap in skill_gaps:
            if gap.recommended_actions:
                recommendations.extend(gap.recommended_actions)
        
        # Categorize recommendations
        categorized_recommendations = {
            "immediate_actions": [],
            "short_term_goals": [],
            "long_term_goals": [],
            "skill_specific": {}
        }
        
        for gap in skill_gaps:
            if gap.priority in ["critical", "high"]:
                categorized_recommendations["immediate_actions"].extend(gap.recommended_actions)
            elif gap.priority == "medium":
                categorized_recommendations["short_term_goals"].extend(gap.recommended_actions)
            else:
                categorized_recommendations["long_term_goals"].extend(gap.recommended_actions)
            
            # Skill-specific recommendations
            if gap.skill_name not in categorized_recommendations["skill_specific"]:
                categorized_recommendations["skill_specific"][gap.skill_name] = []
            categorized_recommendations["skill_specific"][gap.skill_name].extend(gap.recommended_actions)
        
        return {
            "total_recommendations": len(recommendations),
            "categorized_recommendations": categorized_recommendations,
            "priority_actions": self._prioritize_recommendations(recommendations),
            "learning_paths": self._suggest_learning_paths(skill_gaps)
        }
    
    def _generate_progress_insights(self, user_id: str) -> Dict[str, Any]:
        """Generate progress insights section."""
        try:
            # Get user analytics
            analytics = self.user_service.get_user_analytics(user_id)
            
            # Get recent assessments
            recent_assessments = self.skills_engine.get_user_assessments(user_id, limit=5)
            
            return {
                "user_analytics": analytics,
                "recent_assessments": [a.dict() for a in recent_assessments],
                "progress_trends": self._analyze_progress_trends(recent_assessments),
                "learning_velocity": self._calculate_learning_velocity(recent_assessments)
            }
            
        except Exception as e:
            logger.error(f"Error generating progress insights: {e}")
            return {"error": "Unable to generate progress insights"}
    
    def _generate_action_plan(self, skill_gaps: List[SkillGap], user_profile: Optional[UserProfile]) -> Dict[str, Any]:
        """Generate actionable plan section."""
        # Prioritize gaps
        prioritized_gaps = sorted(skill_gaps, key=lambda x: self._get_priority_score(x))
        
        # Create action plan phases
        action_plan = {
            "phase_1_immediate": {
                "timeframe": "1-2 weeks",
                "focus": "Critical and high-priority gaps",
                "gaps": [gap for gap in prioritized_gaps if gap.priority in ["critical", "high"]][:3],
                "actions": []
            },
            "phase_2_short_term": {
                "timeframe": "1-2 months",
                "focus": "Medium-priority gaps and skill building",
                "gaps": [gap for gap in prioritized_gaps if gap.priority == "medium"][:5],
                "actions": []
            },
            "phase_3_long_term": {
                "timeframe": "3-6 months",
                "focus": "Skill mastery and advanced development",
                "gaps": [gap for gap in prioritized_gaps if gap.priority == "low"][:5],
                "actions": []
            }
        }
        
        # Generate specific actions for each phase
        for phase in action_plan.values():
            for gap in phase["gaps"]:
                if gap.recommended_actions:
                    phase["actions"].extend(gap.recommended_actions[:2])  # Top 2 actions per gap
        
        return {
            "overview": f"Personalized action plan for {user_profile.name if user_profile else 'user'}",
            "phases": action_plan,
            "success_metrics": self._define_success_metrics(skill_gaps),
            "timeline": self._generate_action_timeline(action_plan)
        }
    
    def _generate_appendix(self, assessment: SkillsAssessment, skill_gaps: List[SkillGap], skills_taxonomy: List[SkillsTaxonomy]) -> Dict[str, Any]:
        """Generate appendix section."""
        return {
            "assessment_details": assessment.dict(),
            "skill_gaps_details": [gap.dict() for gap in skill_gaps],
            "skills_taxonomy_reference": [skill.dict() for skill in skills_taxonomy[:20]],  # First 20 for brevity
            "methodology": {
                "assessment_type": assessment.assessment_type,
                "analysis_method": "AI-powered semantic analysis",
                "confidence_level": assessment.confidence_level,
                "artifacts_analyzed": len(assessment.artifacts_analyzed)
            }
        }
    
    # Additional helper methods for specific report sections
    
    def _extract_key_insights(self, assessment: SkillsAssessment, skill_gaps: List[SkillGap]) -> List[str]:
        """Extract key insights from assessment and gaps."""
        insights = []
        
        if assessment.overall_score:
            if assessment.overall_score >= 80:
                insights.append("Strong overall skill competency demonstrated")
            elif assessment.overall_score >= 60:
                insights.append("Moderate skill competency with room for improvement")
            else:
                insights.append("Significant skill development opportunities identified")
        
        if skill_gaps:
            critical_gaps = [gap for gap in skill_gaps if gap.priority == "critical"]
            if critical_gaps:
                insights.append(f"{len(critical_gaps)} critical skill gaps require immediate attention")
            
            high_priority_gaps = [gap for gap in skill_gaps if gap.priority == "high"]
            if high_priority_gaps:
                insights.append(f"{len(high_priority_gaps)} high-priority skill gaps identified")
        
        return insights
    
    def _get_top_recommendations(self, assessment: SkillsAssessment, skill_gaps: List[SkillGap]) -> List[str]:
        """Get top recommendations from assessment and gaps."""
        recommendations = []
        
        # Get assessment recommendations
        if assessment.recommendations:
            recommendations.extend(assessment.recommendations[:3])
        
        # Get top gap recommendations
        high_priority_gaps = [gap for gap in skill_gaps if gap.priority in ["critical", "high"]]
        for gap in high_priority_gaps[:3]:
            if gap.recommended_actions:
                recommendations.extend(gap.recommended_actions[:1])
        
        return recommendations[:5]  # Top 5 recommendations
    
    def _get_top_skills(self, skills_demonstrated: List[Dict]) -> List[Dict]:
        """Get top skills by competency level."""
        return sorted(skills_demonstrated, key=lambda x: self._get_competency_score(x.get("competency_level", "beginner")), reverse=True)[:5]
    
    def _get_top_gaps(self, skill_gaps: List[SkillGap]) -> List[SkillGap]:
        """Get top skill gaps by priority."""
        return sorted(skill_gaps, key=lambda x: self._get_priority_score(x), reverse=True)[:5]
    
    def _get_priority_score(self, gap: SkillGap) -> int:
        """Get priority score for gap prioritization."""
        priority_scores = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        return priority_scores.get(gap.priority, 0)
    
    def _get_competency_score(self, level: str) -> int:
        """Get competency score for level comparison."""
        competency_scores = {"expert": 4, "advanced": 3, "intermediate": 2, "beginner": 1}
        return competency_scores.get(level, 0)
    
    def _prioritize_recommendations(self, recommendations: List[str]) -> List[str]:
        """Prioritize recommendations based on keywords and context."""
        # Simple prioritization based on keywords
        priority_keywords = ["critical", "urgent", "immediate", "essential", "must"]
        high_priority = []
        normal_priority = []
        
        for rec in recommendations:
            if any(keyword in rec.lower() for keyword in priority_keywords):
                high_priority.append(rec)
            else:
                normal_priority.append(rec)
        
        return high_priority + normal_priority
    
    def _suggest_learning_paths(self, skill_gaps: List[SkillGap]) -> List[Dict[str, Any]]:
        """Suggest learning paths based on skill gaps."""
        learning_paths = []
        
        # Group gaps by category
        gaps_by_category = {}
        for gap in skill_gaps:
            category = gap.category or "Other"
            if category not in gaps_by_category:
                gaps_by_category[category] = []
            gaps_by_category[category].append(gap)
        
        # Create learning paths for each category
        for category, gaps in gaps_by_category.items():
            if gaps:
                learning_paths.append({
                    "category": category,
                    "gaps_count": len(gaps),
                    "estimated_duration": f"{len(gaps) * 2}-{len(gaps) * 4} weeks",
                    "focus_skills": [gap.skill_name for gap in gaps[:3]],
                    "learning_approach": "Structured learning with hands-on practice"
                })
        
        return learning_paths
    
    def _analyze_progress_trends(self, assessments: List[SkillsAssessment]) -> Dict[str, Any]:
        """Analyze progress trends from assessments."""
        if len(assessments) < 2:
            return {"message": "Insufficient data for trend analysis"}
        
        # Sort by date
        sorted_assessments = sorted(assessments, key=lambda x: x.created_at)
        
        # Calculate trend
        scores = [a.overall_score for a in sorted_assessments if a.overall_score is not None]
        if len(scores) >= 2:
            trend = "improving" if scores[-1] > scores[0] else "declining" if scores[-1] < scores[0] else "stable"
            improvement = scores[-1] - scores[0] if len(scores) >= 2 else 0
        else:
            trend = "insufficient_data"
            improvement = 0
        
        return {
            "trend": trend,
            "improvement": improvement,
            "assessment_count": len(assessments),
            "latest_score": scores[-1] if scores else None,
            "first_score": scores[0] if scores else None
        }
    
    def _calculate_learning_velocity(self, assessments: List[SkillsAssessment]) -> Dict[str, Any]:
        """Calculate learning velocity from assessments."""
        if len(assessments) < 2:
            return {"message": "Insufficient data for velocity calculation"}
        
        # Calculate time span
        sorted_assessments = sorted(assessments, key=lambda x: x.created_at)
        time_span = (sorted_assessments[-1].created_at - sorted_assessments[0].created_at).days
        
        if time_span == 0:
            return {"message": "All assessments on same day"}
        
        # Calculate velocity metrics
        total_assessments = len(assessments)
        assessments_per_week = (total_assessments / time_span) * 7 if time_span > 0 else 0
        
        return {
            "assessments_per_week": round(assessments_per_week, 2),
            "total_assessments": total_assessments,
            "time_span_days": time_span,
            "velocity_category": "high" if assessments_per_week > 1 else "moderate" if assessments_per_week > 0.5 else "low"
        }
    
    def _get_cutoff_date(self, time_period: str) -> datetime:
        """Get cutoff date for time period."""
        now = datetime.utcnow()
        if time_period == "7d":
            return now - timedelta(days=7)
        elif time_period == "30d":
            return now - timedelta(days=30)
        elif time_period == "90d":
            return now - timedelta(days=90)
        elif time_period == "1y":
            return now - timedelta(days=365)
        else:
            return now - timedelta(days=30)  # Default to 30 days
    
    def _get_user_context_summary(self, user_profile: Optional[UserProfile]) -> Dict[str, Any]:
        """Get user context summary."""
        if not user_profile:
            return {"error": "User profile not found"}
        
        return {
            "name": user_profile.name,
            "job_role": user_profile.job_role,
            "experience_summary": user_profile.experience_summary,
            "personal_goals": user_profile.personal_goals,
            "team_info": user_profile.team_info.dict() if user_profile.team_info else None,
            "project_info": user_profile.project_info.dict() if user_profile.project_info else None
        }
    
    def _prioritize_skill_gaps(self, skill_gaps: List[SkillGap]) -> List[SkillGap]:
        """Prioritize skill gaps for learning roadmap."""
        return sorted(skill_gaps, key=lambda x: self._get_priority_score(x), reverse=True)
    
    def _generate_learning_phases(self, skill_gaps: List[SkillGap], skills_taxonomy: List[SkillsTaxonomy]) -> List[Dict[str, Any]]:
        """Generate learning phases for roadmap."""
        phases = []
        
        # Phase 1: Critical and High Priority
        critical_high_gaps = [gap for gap in skill_gaps if gap.priority in ["critical", "high"]]
        if critical_high_gaps:
            phases.append({
                "phase": 1,
                "name": "Foundation Building",
                "duration": "2-4 weeks",
                "focus": "Critical and high-priority skill gaps",
                "gaps": critical_high_gaps[:5],
                "learning_approach": "Intensive focused learning"
            })
        
        # Phase 2: Medium Priority
        medium_gaps = [gap for gap in skill_gaps if gap.priority == "medium"]
        if medium_gaps:
            phases.append({
                "phase": 2,
                "name": "Skill Development",
                "duration": "4-8 weeks",
                "focus": "Medium-priority skill gaps",
                "gaps": medium_gaps[:8],
                "learning_approach": "Structured learning with practice"
            })
        
        # Phase 3: Low Priority and Mastery
        low_gaps = [gap for gap in skill_gaps if gap.priority == "low"]
        if low_gaps:
            phases.append({
                "phase": 3,
                "name": "Skill Mastery",
                "duration": "8-12 weeks",
                "focus": "Low-priority gaps and skill mastery",
                "gaps": low_gaps[:10],
                "learning_approach": "Advanced learning and specialization"
            })
        
        return phases
    
    def _generate_learning_timeline(self, skill_gaps: List[SkillGap]) -> Dict[str, Any]:
        """Generate learning timeline."""
        total_gaps = len(skill_gaps)
        critical_gaps = len([gap for gap in skill_gaps if gap.priority == "critical"])
        high_gaps = len([gap for gap in skill_gaps if gap.priority == "high"])
        
        # Estimate timeline based on gap count and priority
        foundation_weeks = max(2, (critical_gaps + high_gaps) * 1)
        development_weeks = max(4, (total_gaps - critical_gaps - high_gaps) * 2)
        mastery_weeks = max(8, total_gaps * 1)
        
        return {
            "total_estimated_duration": f"{foundation_weeks + development_weeks + mastery_weeks} weeks",
            "foundation_phase": f"{foundation_weeks} weeks",
            "development_phase": f"{development_weeks} weeks",
            "mastery_phase": f"{mastery_weeks} weeks",
            "milestones": [
                f"Week {foundation_weeks}: Complete foundation building",
                f"Week {foundation_weeks + development_weeks}: Complete skill development",
                f"Week {foundation_weeks + development_weeks + mastery_weeks}: Achieve skill mastery"
            ]
        }
    
    def _define_success_metrics(self, skill_gaps: List[SkillGap]) -> List[Dict[str, Any]]:
        """Define success metrics for learning plan."""
        return [
            {
                "metric": "Skill Gap Reduction",
                "target": f"Reduce {len(skill_gaps)} identified gaps by 80%",
                "measurement": "Quarterly assessments"
            },
            {
                "metric": "Competency Improvement",
                "target": "Improve overall competency score by 20 points",
                "measurement": "Skills assessment scores"
            },
            {
                "metric": "Learning Completion",
                "target": "Complete 90% of recommended learning activities",
                "measurement": "Learning progress tracking"
            },
            {
                "metric": "Application Success",
                "target": "Apply learned skills in 3+ work projects",
                "measurement": "Work task completion and feedback"
            }
        ]
    
    def _recommend_learning_resources(self, skill_gaps: List[SkillGap], skills_taxonomy: List[SkillsTaxonomy]) -> Dict[str, List[str]]:
        """Recommend learning resources based on skill gaps."""
        resources = {
            "online_courses": [],
            "books": [],
            "practice_projects": [],
            "communities": [],
            "tools": []
        }
        
        # Get unique categories from gaps
        categories = list(set([gap.category for gap in skill_gaps if gap.category]))
        
        # Add category-specific resources
        for category in categories:
            if category.lower() in ["programming", "technical-skills"]:
                resources["online_courses"].extend([
                    "Coursera - Programming Specializations",
                    "Udemy - Technical Skills Courses",
                    "edX - Computer Science Programs"
                ])
                resources["practice_projects"].extend([
                    "GitHub - Open source contributions",
                    "LeetCode - Coding challenges",
                    "Kaggle - Data science projects"
                ])
            elif category.lower() in ["business", "soft-skills"]:
                resources["online_courses"].extend([
                    "LinkedIn Learning - Business Skills",
                    "Coursera - Business Specializations",
                    "MasterClass - Leadership Courses"
                ])
                resources["books"].extend([
                    "Business Strategy Books",
                    "Leadership and Management Guides",
                    "Communication Skills Resources"
                ])
        
        return resources
    
    def _generate_action_timeline(self, action_plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate timeline for action plan."""
        timeline = []
        current_date = datetime.utcnow()
        
        for phase_name, phase_data in action_plan.items():
            if phase_name.startswith("phase_"):
                # Parse timeframe
                timeframe = phase_data.get("timeframe", "1-2 weeks")
                weeks = 2  # Default
                if "week" in timeframe:
                    weeks = int(timeframe.split()[0].split("-")[0])
                
                timeline.append({
                    "phase": phase_name,
                    "start_date": current_date.isoformat(),
                    "end_date": (current_date + timedelta(weeks=weeks)).isoformat(),
                    "focus": phase_data.get("focus", ""),
                    "gaps_count": len(phase_data.get("gaps", [])),
                    "actions_count": len(phase_data.get("actions", []))
                })
                
                current_date += timedelta(weeks=weeks)
        
        return timeline
    
    def _analyze_skill_improvements(self, assessments: List[SkillsAssessment]) -> Dict[str, Any]:
        """Analyze skill improvements from assessments."""
        if len(assessments) < 2:
            return {"message": "Insufficient data for improvement analysis"}
        
        # Sort by date
        sorted_assessments = sorted(assessments, key=lambda x: x.created_at)
        
        improvements = []
        for i in range(1, len(sorted_assessments)):
            prev_assessment = sorted_assessments[i-1]
            curr_assessment = sorted_assessments[i]
            
            if prev_assessment.overall_score and curr_assessment.overall_score:
                improvement = curr_assessment.overall_score - prev_assessment.overall_score
                improvements.append({
                    "assessment_id": curr_assessment.id,
                    "date": curr_assessment.created_at.isoformat(),
                    "score_improvement": improvement,
                    "previous_score": prev_assessment.overall_score,
                    "current_score": curr_assessment.overall_score
                })
        
        return {
            "total_improvements": len(improvements),
            "average_improvement": sum(imp["score_improvement"] for imp in improvements) / len(improvements) if improvements else 0,
            "improvement_details": improvements
        }
    
    def _analyze_gap_reductions(self, current_gaps: List[SkillGap], assessments: List[SkillsAssessment]) -> Dict[str, Any]:
        """Analyze gap reductions from assessments."""
        # This would require historical gap data, which we don't have in current implementation
        # For now, return a placeholder
        return {
            "message": "Gap reduction analysis requires historical gap data",
            "current_gaps": len(current_gaps),
            "suggestion": "Track gap status changes over time for better analysis"
        }
    
    def _generate_progress_recommendations(self, current_gaps: List[SkillGap], assessments: List[SkillsAssessment]) -> List[str]:
        """Generate progress recommendations."""
        recommendations = []
        
        if not assessments:
            recommendations.append("Start with initial skills assessment to establish baseline")
            return recommendations
        
        # Analyze recent performance
        recent_scores = [a.overall_score for a in assessments[-3:] if a.overall_score]
        if recent_scores:
            avg_recent_score = sum(recent_scores) / len(recent_scores)
            if avg_recent_score < 60:
                recommendations.append("Focus on foundational skills before advanced topics")
            elif avg_recent_score > 80:
                recommendations.append("Consider advanced specialization and mentoring others")
        
        # Gap-based recommendations
        critical_gaps = [gap for gap in current_gaps if gap.priority == "critical"]
        if critical_gaps:
            recommendations.append(f"Address {len(critical_gaps)} critical skill gaps immediately")
        
        high_gaps = [gap for gap in current_gaps if gap.priority == "high"]
        if high_gaps:
            recommendations.append(f"Plan focused learning for {len(high_gaps)} high-priority gaps")
        
        return recommendations


# Global report generator instance
_report_generator_instance: Optional[SkillsReportGenerator] = None


def get_skills_report_generator() -> SkillsReportGenerator:
    """
    Get the global skills report generator instance.
    
    Returns:
        SkillsReportGenerator: Global report generator instance
    """
    global _report_generator_instance
    if _report_generator_instance is None:
        _report_generator_instance = SkillsReportGenerator()
    return _report_generator_instance


def initialize_skills_report_generator() -> SkillsReportGenerator:
    """
    Initialize the global skills report generator.
    
    Returns:
        SkillsReportGenerator: Initialized report generator instance
    """
    global _report_generator_instance
    _report_generator_instance = SkillsReportGenerator()
    return _report_generator_instance
