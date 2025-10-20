from fastapi import FastAPI, HTTPException
import uvicorn
import os
from dotenv import load_dotenv
from typing import Dict, Any

# Import our custom modules
from backend.core.config import get_config, validate_environment, setup_logging
from backend.core.ai_client import get_ai_client, validate_ai_setup
from backend.database.connection import get_database
from backend.database.vector_store import get_vector_store

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

# 4. Define API endpoints
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

# 5. Optional: Run the server directly using uvicorn if executed as a script
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