"""
API package for the Personal Learning Agent.

This package contains FastAPI routers and endpoints for the REST API.
"""

from .user import router as user_router

__all__ = [
    "user_router"
]
