from fastapi import FastAPI
import uvicorn
import os
from dotenv import load_dotenv

# 1. Load environment variables from the .env file
load_dotenv()

# 2. Create the FastAPI application instance
# We can set a title for documentation purposes
app = FastAPI(
    title="AI Hackathon Agent Backend",
    description="API for the LangChain agent logic and services."
)

# 3. Define the first API endpoint (route)
# This is an asynchronous function (async def) which is standard for FastAPI
@app.get("/")
def read_root():
    """
    Returns a simple welcome message for the root path.
    """
    return {"message": "Hello World! FastAPI Backend is running."}

# 4. Define a simple check to ensure the OpenAI API key is loaded
@app.get("/status")
def get_status():
    """
    Checks if the OpenAI API key is present in the environment variables.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        status_message = "OpenAI API Key is loaded."
    else:
        status_message = "ERROR: OpenAI API Key NOT loaded. Check your .env file."
        
    return {"status": "ok", "message": status_message}

# 5. Optional: Run the server directly using uvicorn if executed as a script
# This is generally used for development
if __name__ == "__main__":
    # The 'host'='0.0.0.0' makes it accessible externally (good for local testing and Streamlit integration)
    # The 'port' can be any available port, 8000 is the FastAPI default
    uvicorn.run(app, host="0.0.0.0", port=8000)