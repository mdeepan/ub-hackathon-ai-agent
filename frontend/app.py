"""
Personal Learning Agent - Streamlit Frontend Application

This is the main Streamlit application that provides the user interface
for the Personal Learning Agent system.
"""

import streamlit as st
import requests
import json
from typing import Optional, Dict, Any
import os
from datetime import datetime

# Configure Streamlit page
st.set_page_config(
    page_title="Personal Learning Agent",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
API_ENDPOINTS = {
    "auth": {
        "register": f"{API_BASE_URL}/api/auth/register",
        "login": f"{API_BASE_URL}/api/auth/login",
        "logout": f"{API_BASE_URL}/api/auth/logout",
        "me": f"{API_BASE_URL}/api/auth/me",
        "change_password": f"{API_BASE_URL}/api/auth/change-password"
    },
    "users": {
        "profile": f"{API_BASE_URL}/api/users",
        "tasks": f"{API_BASE_URL}/api/users",
        "skills": f"{API_BASE_URL}/api/users",
        "context": f"{API_BASE_URL}/api/users"
    },
    "skills": {
        "assess": f"{API_BASE_URL}/api/skills/assess",
        "report": f"{API_BASE_URL}/api/skills/report"
    },
    "learning": {
        "generate_path": f"{API_BASE_URL}/api/learning/generate-path",
        "paths": f"{API_BASE_URL}/api/learning/user",
        "content": f"{API_BASE_URL}/api/learning/content"
    }
}


class APIClient:
    """API client for communicating with the backend."""
    
    def __init__(self):
        self.base_url = API_BASE_URL
        self.session_token = None
    
    def set_session_token(self, token: str):
        """Set the session token for authenticated requests."""
        self.session_token = token
    
    def get_headers(self) -> Dict[str, str]:
        """Get headers for API requests."""
        headers = {"Content-Type": "application/json"}
        if self.session_token:
            headers["Authorization"] = f"Bearer {self.session_token}"
        return headers
    
    def make_request(self, method: str, url: str, data: Optional[Dict] = None, files: Optional[Dict] = None) -> Dict[str, Any]:
        """Make an API request."""
        try:
            headers = self.get_headers()
            
            if method.upper() == "GET":
                response = requests.get(url, headers=headers)
            elif method.upper() == "POST":
                if files:
                    # Remove Content-Type header for file uploads
                    headers.pop("Content-Type", None)
                    response = requests.post(url, data=data, files=files, headers=headers)
                else:
                    response = requests.post(url, json=data, headers=headers)
            elif method.upper() == "PUT":
                response = requests.put(url, json=data, headers=headers)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            # Don't show error in Streamlit during testing
            if 'streamlit' not in str(type(st)).lower():
                st.error(f"API request failed: {str(e)}")
            return {"error": str(e)}
        except json.JSONDecodeError as e:
            # Don't show error in Streamlit during testing
            if 'streamlit' not in str(type(st)).lower():
                st.error(f"Failed to parse API response: {str(e)}")
            return {"error": "Invalid JSON response"}
        except Exception as e:
            # Catch any other exceptions
            if 'streamlit' not in str(type(st)).lower():
                st.error(f"Unexpected error: {str(e)}")
            return {"error": str(e)}


def initialize_session_state():
    """Initialize Streamlit session state variables."""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "user_info" not in st.session_state:
        st.session_state.user_info = None
    if "session_token" not in st.session_state:
        st.session_state.session_token = None
    if "api_client" not in st.session_state:
        st.session_state.api_client = APIClient()
    if "current_page" not in st.session_state:
        st.session_state.current_page = "login"


def check_authentication():
    """Check if user is authenticated."""
    if st.session_state.authenticated and st.session_state.session_token:
        # Verify session is still valid
        api_client = st.session_state.api_client
        api_client.set_session_token(st.session_state.session_token)
        
        response = api_client.make_request("GET", API_ENDPOINTS["auth"]["me"])
        if "error" in response:
            # Session expired or invalid
            st.session_state.authenticated = False
            st.session_state.user_info = None
            st.session_state.session_token = None
            st.session_state.current_page = "login"
            st.error("Session expired. Please login again.")
            return False
        
        st.session_state.user_info = response
        return True
    
    return False


def show_login_page():
    """Display the login page."""
    st.title("🎓 Personal Learning Agent")
    st.markdown("### Welcome to your AI-powered learning companion")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("---")
        
        # Login form
        with st.form("login_form"):
            st.subheader("Login")
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            
            col_login, col_register = st.columns(2)
            
            with col_login:
                login_submitted = st.form_submit_button("Login", type="primary")
            
            with col_register:
                register_submitted = st.form_submit_button("Register")
        
        if login_submitted:
            if username and password:
                api_client = st.session_state.api_client
                response = api_client.make_request("POST", API_ENDPOINTS["auth"]["login"], {
                    "username": username,
                    "password": password
                })
                
                if "error" not in response:
                    st.session_state.authenticated = True
                    st.session_state.session_token = response["session_token"]
                    st.session_state.user_info = response
                    st.session_state.current_page = "dashboard"
                    api_client.set_session_token(response["session_token"])
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Login failed. Please check your credentials.")
            else:
                st.error("Please enter both username and password.")
        
        if register_submitted:
            st.session_state.current_page = "register"
            st.rerun()
        
        st.markdown("---")
        st.markdown("""
        **About Personal Learning Agent:**
        
        The Personal Learning Agent is an AI-powered system that:
        - Analyzes your work artifacts to identify skill gaps
        - Generates personalized learning paths
        - Provides interactive learning support
        - Tracks your progress and correlates it with work completion
        
        Get started by registering a new account or logging in with existing credentials.
        """)


def show_register_page():
    """Display the registration page."""
    st.title("🎓 Personal Learning Agent")
    st.markdown("### Create your account")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("---")
        
        # Registration form
        with st.form("register_form"):
            st.subheader("Register")
            username = st.text_input("Username", placeholder="Choose a username (3-50 characters)")
            password = st.text_input("Password", type="password", placeholder="Choose a password")
            confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm your password")
            name = st.text_input("Full Name", placeholder="Enter your full name")
            job_role = st.text_input("Job Role", placeholder="e.g., Product Manager, Software Engineer")
            
            col_register, col_back = st.columns(2)
            
            with col_register:
                register_submitted = st.form_submit_button("Register", type="primary")
            
            with col_back:
                back_submitted = st.form_submit_button("Back to Login")
        
        if register_submitted:
            if username and password and name and job_role:
                if password == confirm_password:
                    if len(password) >= 6:
                        api_client = st.session_state.api_client
                        response = api_client.make_request("POST", API_ENDPOINTS["auth"]["register"], {
                            "username": username,
                            "password": password,
                            "name": name,
                            "job_role": job_role
                        })
                        
                        if "error" not in response:
                            st.session_state.authenticated = True
                            st.session_state.session_token = response["session_token"]
                            st.session_state.user_info = response
                            st.session_state.current_page = "dashboard"
                            api_client.set_session_token(response["session_token"])
                            st.success("Registration successful! Welcome to Personal Learning Agent!")
                            st.rerun()
                        else:
                            st.error(f"Registration failed: {response.get('error', 'Unknown error')}")
                    else:
                        st.error("Password must be at least 6 characters long.")
                else:
                    st.error("Passwords do not match.")
            else:
                st.error("Please fill in all required fields.")
        
        if back_submitted:
            st.session_state.current_page = "login"
            st.rerun()
        
        st.markdown("---")
        st.markdown("""
        **Registration Requirements:**
        - Username: 3-50 characters, must be unique
        - Password: At least 6 characters
        - Full Name: Your complete name
        - Job Role: Your current position or role
        
        After registration, you'll be able to:
        - Upload work artifacts for skills assessment
        - Generate personalized learning paths
        - Track your learning progress
        - Get AI-powered learning recommendations
        """)


def show_sidebar():
    """Display the sidebar navigation."""
    if st.session_state.authenticated and st.session_state.user_info:
        user_info = st.session_state.user_info
        
        st.sidebar.title("🎓 PLA")
        st.sidebar.markdown(f"**Welcome, {user_info.get('name', 'User')}!**")
        st.sidebar.markdown(f"*{user_info.get('job_role', '')}*")
        
        st.sidebar.markdown("---")
        
        # Navigation
        pages = {
            "🏠 Dashboard": "dashboard",
            "📊 Skills Assessment": "skills_assessment",
            "📚 Learning Path": "learning_path",
            "📈 Progress": "progress",
            "👤 Profile": "profile",
            "💬 Chat": "chat"
        }
        
        for page_name, page_key in pages.items():
            if st.sidebar.button(page_name, key=f"nav_{page_key}"):
                st.session_state.current_page = page_key
                st.rerun()
        
        st.sidebar.markdown("---")
        
        # User actions
        if st.sidebar.button("🔒 Logout"):
            # Logout logic
            api_client = st.session_state.api_client
            api_client.make_request("POST", API_ENDPOINTS["auth"]["logout"])
            
            st.session_state.authenticated = False
            st.session_state.user_info = None
            st.session_state.session_token = None
            st.session_state.current_page = "login"
            st.success("Logged out successfully!")
            st.rerun()
        
        # System status
        st.sidebar.markdown("---")
        st.sidebar.markdown("**System Status**")
        
        # Check API connection
        try:
            response = requests.get(f"{API_BASE_URL}/health", timeout=5)
            if response.status_code == 200:
                st.sidebar.success("🟢 API Connected")
            else:
                st.sidebar.error("🔴 API Error")
        except:
            st.sidebar.error("🔴 API Offline")


def show_dashboard():
    """Display the main dashboard."""
    st.title("🏠 Dashboard")
    
    if not st.session_state.authenticated:
        st.error("Please login to access the dashboard.")
        return
    
    user_info = st.session_state.user_info
    api_client = st.session_state.api_client
    
    # Welcome section
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown(f"### Welcome back, {user_info.get('name', 'User')}!")
        st.markdown(f"**Role:** {user_info.get('job_role', 'Not specified')}")
        st.markdown(f"**Username:** {user_info.get('username', '')}")
    
    with col2:
        st.markdown("### Quick Actions")
        if st.button("📊 Start Skills Assessment", type="primary"):
            st.session_state.current_page = "skills_assessment"
            st.rerun()
        
        if st.button("📚 View Learning Path"):
            st.session_state.current_page = "learning_path"
            st.rerun()
    
    st.markdown("---")
    
    # Dashboard content
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 📊 Skills Overview")
        st.info("Complete a skills assessment to see your current skill levels and identified gaps.")
        
        if st.button("Take Skills Assessment", key="dashboard_skills"):
            st.session_state.current_page = "skills_assessment"
            st.rerun()
    
    with col2:
        st.markdown("### 📚 Learning Progress")
        st.info("View your personalized learning paths and track your progress.")
        
        if st.button("View Learning Paths", key="dashboard_learning"):
            st.session_state.current_page = "learning_path"
            st.rerun()
    
    with col3:
        st.markdown("### 📈 Work Correlation")
        st.info("See how your learning progress correlates with your work completion.")
        
        if st.button("View Progress", key="dashboard_progress"):
            st.session_state.current_page = "progress"
            st.rerun()
    
    st.markdown("---")
    
    # Recent activity placeholder
    st.markdown("### 📋 Recent Activity")
    st.info("Complete a skills assessment and start learning to see your activity here.")


def show_skills_assessment():
    """Display the skills assessment page."""
    st.title("📊 Skills Assessment")
    
    if not st.session_state.authenticated:
        st.error("Please login to access skills assessment.")
        return
    
    st.markdown("### Analyze Your Work Artifacts")
    st.markdown("Upload your work documents or paste text to get AI-powered skills assessment.")
    
    # Assessment options
    assessment_type = st.radio(
        "Choose assessment method:",
        ["Upload Files", "Paste Text", "External Integration"],
        horizontal=True
    )
    
    if assessment_type == "Upload Files":
        st.markdown("#### Upload Work Documents")
        st.markdown("Supported formats: PDF, DOC, DOCX, TXT")
        
        uploaded_files = st.file_uploader(
            "Choose files",
            type=['pdf', 'doc', 'docx', 'txt'],
            accept_multiple_files=True,
            help="Upload your PRDs, user stories, technical specs, or other work documents"
        )
        
        if uploaded_files:
            st.success(f"Uploaded {len(uploaded_files)} file(s)")
            
            if st.button("🔍 Analyze Skills", type="primary"):
                with st.spinner("Analyzing your work artifacts..."):
                    # TODO: Implement file upload and analysis
                    st.info("Skills assessment feature will be implemented in the next step.")
    
    elif assessment_type == "Paste Text":
        st.markdown("#### Paste Your Work Content")
        
        text_content = st.text_area(
            "Paste your work content here",
            height=200,
            placeholder="Paste your PRD, user stories, technical documentation, or any work-related text..."
        )
        
        if text_content:
            if st.button("🔍 Analyze Skills", type="primary"):
                with st.spinner("Analyzing your work content..."):
                    # TODO: Implement text analysis
                    st.info("Skills assessment feature will be implemented in the next step.")
    
    else:  # External Integration
        st.markdown("#### External Tool Integration")
        st.info("External integration features (GitHub, Google Drive) will be implemented in future versions.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**GitHub Integration**")
            st.button("Connect GitHub", disabled=True)
            st.caption("Connect your GitHub to analyze code repositories")
        
        with col2:
            st.markdown("**Google Drive Integration**")
            st.button("Connect Google Drive", disabled=True)
            st.caption("Connect Google Drive to analyze shared documents")


def show_learning_path():
    """Display the learning path page."""
    st.title("📚 Learning Path")
    
    if not st.session_state.authenticated:
        st.error("Please login to access learning paths.")
        return
    
    st.markdown("### Your Personalized Learning Journey")
    st.info("Complete a skills assessment first to generate your personalized learning path.")
    
    # Placeholder for learning path content
    st.markdown("#### Learning Path Generation")
    st.markdown("Once you complete a skills assessment, your personalized learning path will appear here.")
    
    if st.button("Generate Learning Path", type="primary", disabled=True):
        st.info("Please complete a skills assessment first.")


def show_progress():
    """Display the progress tracking page."""
    st.title("📈 Progress Tracking")
    
    if not st.session_state.authenticated:
        st.error("Please login to access progress tracking.")
        return
    
    st.markdown("### Your Learning and Work Progress")
    st.info("Progress tracking features will be implemented in the next phase.")
    
    # Placeholder for progress content
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Learning Progress")
        st.info("Track your learning completion, time spent, and skill development.")
    
    with col2:
        st.markdown("#### Work Correlation")
        st.info("See how your learning progress correlates with work task completion.")


def show_profile():
    """Display the user profile page."""
    st.title("👤 Profile")
    
    if not st.session_state.authenticated:
        st.error("Please login to access your profile.")
        return
    
    user_info = st.session_state.user_info
    
    st.markdown("### Your Profile Information")
    
    # Display current profile
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Basic Information")
        st.text_input("Username", value=user_info.get('username', ''), disabled=True)
        st.text_input("Full Name", value=user_info.get('name', ''))
        st.text_input("Job Role", value=user_info.get('job_role', ''))
    
    with col2:
        st.markdown("#### Account Settings")
        st.text_input("Current Password", type="password", placeholder="Enter current password")
        st.text_input("New Password", type="password", placeholder="Enter new password")
        st.text_input("Confirm New Password", type="password", placeholder="Confirm new password")
    
    if st.button("Update Profile", type="primary"):
        st.info("Profile update feature will be implemented in the next step.")


def show_chat():
    """Display the chat interface page."""
    st.title("💬 Learning Support Chat")
    
    if not st.session_state.authenticated:
        st.error("Please login to access the chat interface.")
        return
    
    st.markdown("### AI-Powered Learning Assistant")
    st.info("Chat with your AI learning assistant for guidance and support.")
    
    # Chat interface placeholder
    st.markdown("#### Chat Interface")
    st.info("Chat interface will be implemented in the next step.")
    
    # Placeholder chat input
    user_input = st.text_input("Ask your learning assistant...", placeholder="Type your question here...")
    
    if st.button("Send", disabled=True):
        st.info("Chat functionality will be implemented in the next step.")


def main():
    """Main application function."""
    # Initialize session state
    initialize_session_state()
    
    # Check authentication
    if st.session_state.authenticated:
        check_authentication()
    
    # Show sidebar if authenticated
    if st.session_state.authenticated:
        show_sidebar()
    
    # Route to appropriate page
    current_page = st.session_state.current_page
    
    if current_page == "login":
        show_login_page()
    elif current_page == "register":
        show_register_page()
    elif current_page == "dashboard":
        show_dashboard()
    elif current_page == "skills_assessment":
        show_skills_assessment()
    elif current_page == "learning_path":
        show_learning_path()
    elif current_page == "progress":
        show_progress()
    elif current_page == "profile":
        show_profile()
    elif current_page == "chat":
        show_chat()
    else:
        st.session_state.current_page = "login"
        st.rerun()


if __name__ == "__main__":
    main()
