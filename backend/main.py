from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
import uvicorn
import os
from dotenv import load_dotenv
from typing import Dict, Any, List, Optional

# Import our custom modules
from backend.core.config import get_config, validate_environment, setup_logging
from backend.core.ai_client import get_ai_client, validate_ai_setup
from backend.database.connection import get_database
from backend.database.vector_store import get_vector_store
from backend.database.init_db import initialize_database_schema
from backend.utils.file_processor import get_file_processor
from backend.utils.content_manager import get_content_manager
from backend.api.user import router as user_router
from backend.api.skills import router as skills_router
from backend.api.learning import router as learning_router

# 1. Load environment variables from the .env file
load_dotenv()

# 2. Setup logging
setup_logging()

# 3. Create the FastAPI application instance
# We can set a title for documentation purposes
app = FastAPI(
    title="Personal Learning Agent Backend",
    description="API for the Personal Learning Agent with AI-powered skills assessment and learning path generation.",
    version="1.0.0"
)

# 4. Initialize database schema
try:
    initialize_database_schema()
    print("✅ Database schema initialized successfully")
except Exception as e:
    print(f"❌ Database schema initialization failed: {e}")

# 5. Include API routers
app.include_router(user_router)
app.include_router(skills_router)
app.include_router(learning_router)

# 6. Define API endpoints
@app.get("/")
def read_root():
    """
    Returns a welcome message for the root path.
    """
    config = get_config()
    settings = config.get_settings()
    
    return {
        "message": f"Welcome to {settings.app_name} v{settings.app_version}",
        "description": "AI-powered Personal Learning Agent with skills assessment and learning path generation",
        "status": "running"
    }

@app.get("/status")
def get_status():
    """
    Comprehensive system status check including all components.
    """
    status = {
        "application": "running",
        "version": get_config().get_settings().app_version,
        "components": {}
    }
    
    # Check environment configuration
    try:
        env_valid = validate_environment()
        status["components"]["environment"] = {
            "status": "ok" if env_valid else "error",
            "message": "Environment variables validated" if env_valid else "Missing required environment variables"
        }
    except Exception as e:
        status["components"]["environment"] = {
            "status": "error",
            "message": f"Environment validation failed: {str(e)}"
        }
    
    # Check database connection
    try:
        db = get_database()
        db_info = db.get_database_info()
        db_test = db.test_connection()
        status["components"]["database"] = {
            "status": "ok" if db_test else "error",
            "message": "Database connection successful" if db_test else "Database connection failed",
            "info": db_info
        }
    except Exception as e:
        status["components"]["database"] = {
            "status": "error",
            "message": f"Database error: {str(e)}"
        }
    
    # Check vector store
    try:
        vector_store = get_vector_store()
        vector_test = vector_store.test_connection()
        status["components"]["vector_store"] = {
            "status": "ok" if vector_test else "error",
            "message": "Vector store connection successful" if vector_test else "Vector store connection failed"
        }
    except Exception as e:
        status["components"]["vector_store"] = {
            "status": "error",
            "message": f"Vector store error: {str(e)}"
        }
    
    # Check AI client
    try:
        ai_valid = validate_ai_setup()
        status["components"]["ai_client"] = {
            "status": "ok" if ai_valid else "error",
            "message": "AI client setup successful" if ai_valid else "AI client setup failed"
        }
    except Exception as e:
        status["components"]["ai_client"] = {
            "status": "error",
            "message": f"AI client error: {str(e)}"
        }
    
    # Overall status
    all_ok = all(
        component.get("status") == "ok" 
        for component in status["components"].values()
    )
    status["overall_status"] = "healthy" if all_ok else "degraded"
    
    return status

@app.get("/health")
def health_check():
    """
    Simple health check endpoint for load balancers.
    """
    return {"status": "healthy", "timestamp": "2024-01-01T00:00:00Z"}

@app.post("/test-ai")
def test_ai_generation(prompt: str = "Hello, this is a test message."):
    """
    Test AI text generation functionality.
    """
    try:
        ai_client = get_ai_client()
        response = ai_client.generate_text(prompt)
        
        if response.error:
            raise HTTPException(status_code=500, detail=f"AI generation failed: {response.error}")
        
        return {
            "prompt": prompt,
            "response": response.content,
            "model": response.model,
            "response_time": response.response_time,
            "usage": response.usage
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI test failed: {str(e)}")

@app.post("/test-embeddings")
def test_embeddings(text: str = "This is a test text for embedding generation."):
    """
    Test AI embedding generation functionality.
    """
    try:
        ai_client = get_ai_client()
        response = ai_client.generate_embeddings(text)
        
        if response.error:
            raise HTTPException(status_code=500, detail=f"Embedding generation failed: {response.error}")
        
        return {
            "text": text,
            "embeddings_count": len(response.embeddings),
            "embedding_dimension": len(response.embeddings[0]) if response.embeddings else 0,
            "model": response.model,
            "response_time": response.response_time
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Embedding test failed: {str(e)}")

@app.post("/upload-file")
async def upload_file(file: UploadFile = File(...)):
    """
    Upload and process a file for skills assessment.
    """
    try:
        file_processor = get_file_processor()
        processed_content = file_processor.process_file(file)
        
        return {
            "filename": processed_content.metadata.filename,
            "file_type": processed_content.metadata.file_type,
            "file_size": processed_content.metadata.file_size,
            "text_length": processed_content.metadata.text_length,
            "page_count": processed_content.metadata.page_count,
            "processing_time": processed_content.metadata.processing_time,
            "file_hash": processed_content.metadata.file_hash,
            "text_preview": processed_content.text[:500] + "..." if len(processed_content.text) > 500 else processed_content.text
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")

@app.post("/upload-multiple-files")
async def upload_multiple_files(files: List[UploadFile] = File(...)):
    """
    Upload and process multiple files for skills assessment.
    """
    try:
        file_processor = get_file_processor()
        processed_contents = file_processor.process_multiple_files(files)
        
        results = []
        for content in processed_contents:
            results.append({
                "filename": content.metadata.filename,
                "file_type": content.metadata.file_type,
                "file_size": content.metadata.file_size,
                "text_length": content.metadata.text_length,
                "page_count": content.metadata.page_count,
                "processing_time": content.metadata.processing_time,
                "file_hash": content.metadata.file_hash,
                "error": content.metadata.error,
                "text_preview": content.text[:200] + "..." if len(content.text) > 200 else content.text
            })
        
        return {
            "total_files": len(files),
            "processed_files": len([r for r in results if not r.get("error")]),
            "failed_files": len([r for r in results if r.get("error")]),
            "results": results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Multiple file upload failed: {str(e)}")

@app.get("/supported-formats")
def get_supported_formats():
    """
    Get list of supported file formats for upload.
    """
    try:
        file_processor = get_file_processor()
        return {
            "supported_formats": file_processor.get_supported_formats(),
            "max_file_size_mb": file_processor.MAX_FILE_SIZE / (1024 * 1024),
            "processing_stats": file_processor.get_processing_stats()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get supported formats: {str(e)}")

@app.post("/add-content")
async def add_content(
    title: str = Form(...),
    content_type: str = Form(...),
    category: str = Form(...),
    text_content: str = Form(...),
    subcategory: Optional[str] = Form(None),
    difficulty_level: str = Form("beginner"),
    estimated_duration: Optional[int] = Form(None),
    tags: Optional[str] = Form(None),  # JSON string
    skills_covered: Optional[str] = Form(None),  # JSON string
    author: Optional[str] = Form(None),
    source_url: Optional[str] = Form(None)
):
    """
    Add new learning content to the database.
    """
    try:
        import json
        
        content_manager = get_content_manager()
        
        # Parse JSON strings
        tags_list = json.loads(tags) if tags else None
        skills_list = json.loads(skills_covered) if skills_covered else None
        
        content_id = content_manager.add_content(
            title=title,
            content_type=content_type,
            category=category,
            text_content=text_content,
            subcategory=subcategory,
            difficulty_level=difficulty_level,
            estimated_duration=estimated_duration,
            tags=tags_list,
            skills_covered=skills_list,
            author=author,
            source_url=source_url
        )
        
        return {
            "content_id": content_id,
            "message": "Content added successfully",
            "title": title,
            "category": category
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add content: {str(e)}")

@app.get("/search-content")
def search_content(
    query: str,
    category: Optional[str] = None,
    difficulty_level: Optional[str] = None,
    content_type: Optional[str] = None,
    limit: int = 10
):
    """
    Search learning content using semantic search.
    """
    try:
        content_manager = get_content_manager()
        results = content_manager.search_content(
            query=query,
            category=category,
            difficulty_level=difficulty_level,
            content_type=content_type,
            limit=limit
        )
        
        return {
            "query": query,
            "total_results": len(results),
            "results": [
                {
                    "content_id": result.content_id,
                    "title": result.title,
                    "content_type": result.content_type,
                    "category": result.category,
                    "difficulty_level": result.difficulty_level,
                    "relevance_score": result.relevance_score,
                    "text_snippet": result.text_snippet,
                    "skills_covered": result.skills_covered,
                    "estimated_duration": result.estimated_duration
                }
                for result in results
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Content search failed: {str(e)}")

@app.get("/content-statistics")
def get_content_statistics():
    """
    Get content database statistics.
    """
    try:
        content_manager = get_content_manager()
        stats = content_manager.get_content_statistics()
        
        return {
            "statistics": stats,
            "categories": content_manager.CONTENT_CATEGORIES,
            "difficulty_levels": content_manager.DIFFICULTY_LEVELS
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get content statistics: {str(e)}")

# 7. Optional: Run the server directly using uvicorn if executed as a script
# This is generally used for development
if __name__ == "__main__":
    # Get configuration
    config = get_config()
    settings = config.get_settings()
    
    # The 'host'='0.0.0.0' makes it accessible externally (good for local testing and Streamlit integration)
    # The 'port' can be any available port, 8000 is the FastAPI default
    uvicorn.run(
        app, 
        host=settings.api_host, 
        port=settings.api_port,
        log_level=settings.log_level.lower()
    )