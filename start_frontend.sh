#!/bin/bash

# Start the Personal Learning Agent Frontend
echo "Starting Personal Learning Agent Frontend..."

# Set Streamlit configuration to skip email prompt
export STREAMLIT_SERVER_HEADLESS=true

# Start Streamlit
streamlit run frontend/app.py --server.port 8501 --server.headless true
