"""
Authentication API endpoints for the Personal Learning Agent.

This module provides REST API endpoints for user authentication,
session management, and password handling.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any
import hashlib
import secrets
import logging
from datetime import datetime, timedelta

from ..models.user import UserProfile, UserProfileCreate
from ..services.user_service import get_user_service, UserService
from pydantic import BaseModel


class RegisterRequest(BaseModel):
    """Request model for user registration."""
    username: str
    password: str
    name: str
    job_role: str


class LoginRequest(BaseModel):
    """Request model for user login."""
    username: str
    password: str

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/auth", tags=["authentication"])

# Security scheme
security = HTTPBearer()

# In-memory session storage (for MVP - in production, use Redis or database)
active_sessions: Dict[str, Dict[str, Any]] = {}

# Session configuration
SESSION_DURATION_HOURS = 24
SECRET_KEY = "pla-secret-key-change-in-production"  # In production, use environment variable


def hash_password(password: str) -> str:
    """Hash password using SHA-256 with salt."""
    salt = secrets.token_hex(16)
    password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    return f"{salt}:{password_hash}"


def verify_password(password: str, hashed_password: str) -> bool:
    """Verify password against hash."""
    try:
        salt, password_hash = hashed_password.split(":")
        return hashlib.sha256((password + salt).encode()).hexdigest() == password_hash
    except ValueError:
        return False


def create_session_token() -> str:
    """Create a new session token."""
    return secrets.token_urlsafe(32)


def create_session(user_id: str, username: str) -> str:
    """Create a new user session."""
    token = create_session_token()
    expires_at = datetime.utcnow() + timedelta(hours=SESSION_DURATION_HOURS)
    
    active_sessions[token] = {
        "user_id": user_id,
        "username": username,
        "created_at": datetime.utcnow(),
        "expires_at": expires_at,
        "is_active": True
    }
    
    return token


def get_session(token: str) -> Optional[Dict[str, Any]]:
    """Get session information by token."""
    if token not in active_sessions:
        return None
    
    session = active_sessions[token]
    
    # Check if session is expired
    if datetime.utcnow() > session["expires_at"]:
        del active_sessions[token]
        return None
    
    return session


def invalidate_session(token: str) -> bool:
    """Invalidate a session."""
    if token in active_sessions:
        del active_sessions[token]
        return True
    return False


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Get current authenticated user from session token."""
    token = credentials.credentials
    session = get_session(token)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return session


# Dependency injection
def get_user_service_dependency() -> UserService:
    """Get user service dependency."""
    return get_user_service()


# Authentication Endpoints

@router.post("/register", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def register_user(
    request: RegisterRequest,
    user_service: UserService = Depends(get_user_service_dependency)
):
    """
    Register a new user with username and password.
    
    Args:
        request: Request body containing username, password, name, job_role
        user_service: User service dependency
        
    Returns:
        Dict: Registration result with session token
        
    Raises:
        HTTPException: If username already exists or registration fails
    """
    try:
        username = request.username
        password = request.password
        name = request.name
        job_role = request.job_role
        
        # Check if username already exists
        existing_user = user_service.get_user_by_username(username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists"
            )
        
        # Hash password
        hashed_password = hash_password(password)
        
        # Create user profile
        profile_data = UserProfileCreate(
            username=username,
            name=name,
            job_role=job_role,
            experience_summary="",
            personal_goals=[]
        )
        
        user_profile = user_service.create_user_profile(profile_data)
        
        # Store hashed password (in production, store in separate auth table)
        # For MVP, we'll store it in the user profile's experience_summary field
        # This is not secure for production - use proper auth table
        from ..models.user import UserProfileUpdate
        password_update = UserProfileUpdate(experience_summary=f"AUTH_PASSWORD:{hashed_password}")
        user_service.update_user_profile(user_profile.id, password_update)
        
        # Create session
        session_token = create_session(user_profile.id, username)
        
        logger.info(f"User registered successfully: {username}")
        
        return {
            "message": "User registered successfully",
            "user_id": user_profile.id,
            "username": username,
            "session_token": session_token,
            "expires_in_hours": SESSION_DURATION_HOURS
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registering user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register user"
        )


@router.post("/login", response_model=Dict[str, Any])
async def login_user(
    request: LoginRequest,
    user_service: UserService = Depends(get_user_service_dependency)
):
    """
    Login user with username and password.
    
    Args:
        request: Request body containing username and password
        user_service: User service dependency
        
    Returns:
        Dict: Login result with session token
        
    Raises:
        HTTPException: If credentials are invalid
    """
    try:
        username = request.username
        password = request.password
        
        # Get user by username
        user_profile = user_service.get_user_by_username(username)
        if not user_profile:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )
        
        # Get stored password hash
        stored_auth = user_profile.experience_summary or ""
        if not stored_auth.startswith("AUTH_PASSWORD:"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )
        
        hashed_password = stored_auth.replace("AUTH_PASSWORD:", "")
        
        # Verify password
        if not verify_password(password, hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )
        
        # Create session
        session_token = create_session(user_profile.id, username)
        
        logger.info(f"User logged in successfully: {username}")
        
        return {
            "message": "Login successful",
            "user_id": user_profile.id,
            "username": username,
            "session_token": session_token,
            "expires_in_hours": SESSION_DURATION_HOURS
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error logging in user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to login user"
        )


@router.post("/logout", response_model=Dict[str, str])
async def logout_user(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Logout user and invalidate session.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Dict: Logout confirmation
    """
    try:
        # Get token from request (we need to modify this to get the actual token)
        # For now, we'll invalidate all sessions for this user
        user_id = current_user["user_id"]
        
        # Find and invalidate user's sessions
        tokens_to_remove = []
        for token, session in active_sessions.items():
            if session["user_id"] == user_id:
                tokens_to_remove.append(token)
        
        for token in tokens_to_remove:
            del active_sessions[token]
        
        logger.info(f"User logged out successfully: {current_user['username']}")
        
        return {
            "message": "Logout successful"
        }
        
    except Exception as e:
        logger.error(f"Error logging out user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to logout user"
        )


@router.get("/me", response_model=Dict[str, Any])
async def get_current_user_info(
    current_user: Dict[str, Any] = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service_dependency)
):
    """
    Get current authenticated user information.
    
    Args:
        current_user: Current authenticated user
        user_service: User service dependency
        
    Returns:
        Dict: Current user information
    """
    try:
        user_profile = user_service.get_user_profile(current_user["user_id"])
        if not user_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )
        
        # Remove password hash from response
        safe_profile = user_profile.dict()
        if safe_profile.get("experience_summary", "").startswith("AUTH_PASSWORD:"):
            safe_profile["experience_summary"] = ""
        
        return {
            "user_id": user_profile.id,
            "username": user_profile.username,
            "name": user_profile.name,
            "job_role": user_profile.job_role,
            "profile": safe_profile,
            "session": {
                "created_at": current_user["created_at"],
                "expires_at": current_user["expires_at"]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting current user info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user information"
        )


@router.post("/change-password", response_model=Dict[str, str])
async def change_password(
    current_password: str,
    new_password: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service_dependency)
):
    """
    Change user password.
    
    Args:
        current_password: Current password
        new_password: New password
        current_user: Current authenticated user
        user_service: User service dependency
        
    Returns:
        Dict: Password change confirmation
        
    Raises:
        HTTPException: If current password is incorrect
    """
    try:
        # Get user profile
        user_profile = user_service.get_user_profile(current_user["user_id"])
        if not user_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )
        
        # Verify current password
        stored_auth = user_profile.experience_summary or ""
        if not stored_auth.startswith("AUTH_PASSWORD:"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user authentication data"
            )
        
        hashed_password = stored_auth.replace("AUTH_PASSWORD:", "")
        
        if not verify_password(current_password, hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Current password is incorrect"
            )
        
        # Hash new password
        new_hashed_password = hash_password(new_password)
        
        # Update password
        from ..models.user import UserProfileUpdate
        password_update = UserProfileUpdate(experience_summary=f"AUTH_PASSWORD:{new_hashed_password}")
        user_service.update_user_profile(user_profile.id, password_update)
        
        logger.info(f"Password changed successfully for user: {current_user['username']}")
        
        return {
            "message": "Password changed successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error changing password: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password"
        )


@router.get("/sessions", response_model=Dict[str, Any])
async def get_active_sessions(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get active sessions for current user.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Dict: Active sessions information
    """
    try:
        user_id = current_user["user_id"]
        user_sessions = []
        
        for token, session in active_sessions.items():
            if session["user_id"] == user_id:
                user_sessions.append({
                    "token": token[:8] + "...",  # Mask token for security
                    "created_at": session["created_at"],
                    "expires_at": session["expires_at"],
                    "is_current": token == current_user.get("token", "")
                })
        
        return {
            "user_id": user_id,
            "active_sessions": user_sessions,
            "total_sessions": len(user_sessions)
        }
        
    except Exception as e:
        logger.error(f"Error getting active sessions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get active sessions"
        )


# Health Check Endpoint

@router.get("/health", response_model=Dict[str, str])
async def auth_health_check():
    """
    Health check endpoint for authentication service.
    
    Returns:
        Dict: Health status
    """
    return {"status": "healthy", "service": "authentication"}
