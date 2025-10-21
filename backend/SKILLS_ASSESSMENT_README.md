# Skills Assessment Engine

## Overview

The Skills Assessment Engine is a comprehensive AI-powered system that analyzes work artifacts to identify skill gaps and assess competency levels. It provides personalized learning recommendations and detailed progress tracking for the Personal Learning Agent.

## Features

### 🎯 Core Capabilities
- **AI-Powered Analysis**: Uses OpenAI GPT-4 for semantic analysis of work artifacts
- **Skills Taxonomy**: Comprehensive categorization of technical and soft skills
- **Gap Detection**: Identifies skill gaps with priority and urgency levels
- **Competency Assessment**: Evaluates current skill levels (beginner to expert)
- **Report Generation**: Creates detailed assessment reports and learning roadmaps
- **External Integration**: Supports GitHub and Google Drive for artifact retrieval

### 📊 Assessment Types
- **Artifact Analysis**: Analyzes uploaded documents, code, and text
- **Self Assessment**: User-reported skill levels
- **Peer Review**: Feedback from colleagues
- **Automated Testing**: Technical skill validation
- **Work Sample Analysis**: Real work product evaluation

## Architecture

### Core Components

```
backend/
├── services/
│   ├── skills_engine.py              # Main skills assessment engine
│   ├── skills_report_generator.py    # Report generation service
│   └── external_integration.py       # GitHub/Google Drive integration
├── api/
│   └── skills.py                     # RESTful API endpoints
├── models/
│   └── skills.py                     # Pydantic data models
└── scripts/
    ├── init_skills_taxonomy.py       # Initialize skills taxonomy
    └── test_skills_assessment.py     # Test the system
```

### Data Models

#### SkillsAssessment
- Assessment metadata and results
- AI analysis data and recommendations
- Status tracking and timestamps

#### SkillGap
- Identified skill gaps with priority levels
- Business impact and learning effort estimates
- Evidence sources and recommended actions

#### SkillsTaxonomy
- Comprehensive skills categorization
- Proficiency levels and prerequisites
- Learning resources and assessment methods

## Quick Start

### 1. Initialize Skills Taxonomy

```bash
cd backend
python scripts/init_skills_taxonomy.py
```

This loads the skills taxonomy from `data/skills_taxonomy.json` into the database.

### 2. Test the System

```bash
python scripts/test_skills_assessment.py
```

This runs comprehensive tests of all skills assessment functionality.

### 3. Start the API Server

```bash
python main.py
```

The skills assessment API will be available at `/api/skills/`.

## API Endpoints

### Skills Taxonomy
- `GET /api/skills/taxonomy` - Get all skills taxonomy entries
- `GET /api/skills/taxonomy/search?q=python` - Search skills taxonomy
- `POST /api/skills/taxonomy` - Create new taxonomy entry
- `POST /api/skills/taxonomy/load-from-file` - Load from JSON file

### Skills Assessments
- `POST /api/skills/assessments` - Create new assessment
- `GET /api/skills/assessments/{id}` - Get assessment details
- `GET /api/skills/assessments/user/{user_id}` - Get user's assessments
- `PUT /api/skills/assessments/{id}/status` - Update assessment status

### Artifact Analysis
- `POST /api/skills/assessments/{id}/analyze-text` - Analyze text content
- `POST /api/skills/assessments/{id}/analyze-files` - Analyze uploaded files
- `POST /api/skills/assessments/{id}/analyze-mixed` - Analyze mixed artifacts

### Skill Gaps
- `POST /api/skills/gaps` - Create skill gap
- `GET /api/skills/gaps/{id}` - Get gap details
- `GET /api/skills/gaps/user/{user_id}` - Get user's gaps

### Reports
- `GET /api/skills/assessments/{id}/report` - Get comprehensive report

## Usage Examples

### 1. Create and Run Assessment

```python
from backend.services.skills_engine import get_skills_engine
from backend.models.skills import SkillsAssessmentCreate, AssessmentType

# Create assessment
skills_engine = get_skills_engine()
assessment_data = SkillsAssessmentCreate(
    user_id="user_123",
    assessment_type=AssessmentType.ARTIFACT_ANALYSIS,
    title="Product Manager Skills Assessment",
    description="Assessment based on recent PRDs and user stories"
)
assessment = skills_engine.create_skills_assessment(assessment_data)

# Analyze artifacts
artifacts = ["PRD content...", "User stories...", "Technical specs..."]
updated_assessment = skills_engine.analyze_work_artifacts(assessment.id, artifacts)
```

### 2. Generate Report

```python
from backend.services.skills_report_generator import get_skills_report_generator

report_generator = get_skills_report_generator()
report = report_generator.generate_comprehensive_report(assessment.id)

# Generate learning roadmap
roadmap = report_generator.generate_learning_roadmap("user_123")
```

### 3. External Integration

```python
from backend.services.external_integration import get_external_integration_service

integration_service = get_external_integration_service()

# Get GitHub artifacts
github_artifacts = integration_service.get_github_artifacts(
    repositories=["my-repo"],
    file_extensions=[".py", ".md", ".txt"]
)

# Get Google Drive documents
drive_artifacts = integration_service.get_google_drive_artifacts(
    file_types=["application/vnd.google-apps.document"]
)
```

## Configuration

### Environment Variables

```bash
# OpenAI API
OPENAI_API_KEY=your_openai_api_key

# GitHub Integration (optional)
GITHUB_TOKEN=your_github_token
GITHUB_USERNAME=your_github_username

# Google Drive Integration (optional)
GOOGLE_DRIVE_ACCESS_TOKEN=your_google_drive_token
GOOGLE_DRIVE_FOLDER_ID=your_folder_id
```

### Skills Taxonomy

The skills taxonomy is defined in `data/skills_taxonomy.json` with the following structure:

```json
{
  "category_name": {
    "description": "Category description",
    "core_skills": ["skill1", "skill2"],
    "subcategories": {
      "subcategory_name": {
        "description": "Subcategory description",
        "skills": ["skill3", "skill4"]
      }
    }
  }
}
```

## AI Analysis Process

### 1. Artifact Processing
- Text extraction from various file formats
- Content cleaning and normalization
- Metadata extraction

### 2. Semantic Analysis
- AI-powered skills identification
- Competency level assessment
- Gap detection and prioritization

### 3. Report Generation
- Executive summary with key insights
- Detailed skills analysis
- Learning recommendations
- Action plans and timelines

## Supported File Formats

- **Documents**: PDF, DOCX, PPTX, TXT, HTML, MD
- **Data**: JSON, CSV, XLSX
- **Code**: All text-based programming languages
- **External**: GitHub repositories, Google Drive documents

## Performance Considerations

- **File Size Limit**: 10MB per file
- **Batch Processing**: Supports multiple file uploads
- **AI Rate Limits**: Implements retry logic and exponential backoff
- **Caching**: Skills taxonomy cached for performance
- **Background Processing**: Long-running analyses run asynchronously

## Error Handling

- **Graceful Degradation**: System continues working even if some components fail
- **Comprehensive Logging**: Detailed logs for debugging and monitoring
- **User-Friendly Messages**: Clear error messages for API consumers
- **Fallback Analysis**: Basic analysis when AI analysis fails

## Testing

### Unit Tests
```bash
pytest tests/test_skills_engine.py
pytest tests/test_skills_report_generator.py
```

### Integration Tests
```bash
python scripts/test_skills_assessment.py
```

### API Tests
```bash
# Test with curl
curl -X POST "http://localhost:8000/api/skills/assessments" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test_user", "title": "Test Assessment"}'
```

## Monitoring and Analytics

### Key Metrics
- Assessment completion rates
- AI analysis accuracy
- User engagement with recommendations
- Skill gap resolution rates

### Logging
- All operations logged with appropriate levels
- Performance metrics tracked
- Error rates monitored
- User activity patterns analyzed

## Future Enhancements

### Planned Features
- **Multi-language Support**: Analysis in multiple languages
- **Advanced Analytics**: Predictive skill development modeling
- **Integration Expansion**: More external tools (Slack, Jira, etc.)
- **Real-time Updates**: Live skill assessment updates
- **Collaborative Features**: Team skill assessments

### Technical Improvements
- **Performance Optimization**: Faster AI analysis
- **Scalability**: Support for larger user bases
- **Security**: Enhanced data privacy and security
- **Mobile Support**: Mobile-optimized interfaces

## Troubleshooting

### Common Issues

1. **AI Analysis Fails**
   - Check OpenAI API key and quota
   - Verify network connectivity
   - Review error logs for specific issues

2. **File Upload Issues**
   - Check file size limits (10MB)
   - Verify supported file formats
   - Ensure proper file permissions

3. **Database Errors**
   - Verify database connection
   - Check schema initialization
   - Review database logs

4. **External Integration Issues**
   - Verify API credentials
   - Check rate limits
   - Review integration logs

### Getting Help

- Check the logs in the application
- Review the test scripts for examples
- Consult the API documentation
- Check the GitHub issues for known problems

## Contributing

1. Follow the existing code structure
2. Add comprehensive tests for new features
3. Update documentation for API changes
4. Follow the logging and error handling patterns
5. Ensure backward compatibility

## License

This project is part of the Personal Learning Agent system. See the main project license for details.
