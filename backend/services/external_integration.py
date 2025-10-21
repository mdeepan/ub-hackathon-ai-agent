"""
External tool integration service for the Personal Learning Agent.

This module provides integration with external tools like GitHub and Google Drive
for retrieving work artifacts for skills assessment.
"""

import os
import json
import base64
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import logging
import requests
from dataclasses import dataclass

from ..core.config import get_config
from ..utils.file_processor import ProcessedContent, FileMetadata

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ExternalArtifact:
    """External artifact from integrated services."""
    id: str
    name: str
    content: str
    source: str  # 'github', 'google_drive', etc.
    url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class IntegrationConfig:
    """Configuration for external integrations."""
    github_token: Optional[str] = None
    github_username: Optional[str] = None
    google_drive_credentials: Optional[Dict[str, Any]] = None
    google_drive_folder_id: Optional[str] = None


class GitHubIntegration:
    """GitHub integration for retrieving code repositories and files."""
    
    def __init__(self, token: str, username: str):
        """
        Initialize GitHub integration.
        
        Args:
            token: GitHub personal access token
            username: GitHub username
        """
        self.token = token
        self.username = username
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Personal-Learning-Agent"
        }
        logger.info(f"GitHub integration initialized for user: {username}")
    
    def get_user_repositories(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get user's repositories.
        
        Args:
            limit: Maximum number of repositories to return
            
        Returns:
            List[Dict]: Repository information
        """
        try:
            url = f"{self.base_url}/user/repos"
            params = {
                "sort": "updated",
                "direction": "desc",
                "per_page": min(limit, 100)
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            repos = response.json()
            logger.info(f"Retrieved {len(repos)} repositories for user: {self.username}")
            
            return repos
            
        except requests.RequestException as e:
            logger.error(f"Error retrieving GitHub repositories: {e}")
            raise
    
    def get_repository_files(
        self, 
        repo_name: str, 
        file_extensions: Optional[List[str]] = None,
        max_files: int = 50
    ) -> List[ExternalArtifact]:
        """
        Get files from a repository.
        
        Args:
            repo_name: Repository name (owner/repo or just repo for user's repos)
            file_extensions: Optional list of file extensions to filter
            max_files: Maximum number of files to retrieve
            
        Returns:
            List[ExternalArtifact]: Repository files
        """
        try:
            # Ensure repo_name includes owner if not already present
            if "/" not in repo_name:
                repo_name = f"{self.username}/{repo_name}"
            
            # Get repository tree
            tree_url = f"{self.base_url}/repos/{repo_name}/git/trees/HEAD?recursive=1"
            response = requests.get(tree_url, headers=self.headers)
            response.raise_for_status()
            
            tree_data = response.json()
            files = []
            
            # Filter files by extension and type
            for item in tree_data.get("tree", []):
                if item["type"] == "blob":  # File (not directory)
                    file_path = item["path"]
                    file_name = file_path.split("/")[-1]
                    
                    # Filter by extension if specified
                    if file_extensions:
                        file_ext = "." + file_name.split(".")[-1] if "." in file_name else ""
                        if file_ext not in file_extensions:
                            continue
                    
                    # Skip large files and binary files
                    if item.get("size", 0) > 1000000:  # 1MB limit
                        continue
                    
                    # Get file content
                    try:
                        content = self._get_file_content(repo_name, file_path)
                        if content:
                            artifact = ExternalArtifact(
                                id=f"github_{repo_name}_{file_path}",
                                name=file_name,
                                content=content,
                                source="github",
                                url=f"https://github.com/{repo_name}/blob/HEAD/{file_path}",
                                metadata={
                                    "repository": repo_name,
                                    "path": file_path,
                                    "size": item.get("size", 0),
                                    "sha": item.get("sha")
                                }
                            )
                            files.append(artifact)
                            
                            if len(files) >= max_files:
                                break
                                
                    except Exception as e:
                        logger.warning(f"Error retrieving file content for {file_path}: {e}")
                        continue
            
            logger.info(f"Retrieved {len(files)} files from repository: {repo_name}")
            return files
            
        except requests.RequestException as e:
            logger.error(f"Error retrieving repository files: {e}")
            raise
    
    def get_recent_commits(self, repo_name: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get recent commits from a repository.
        
        Args:
            repo_name: Repository name
            limit: Maximum number of commits to return
            
        Returns:
            List[Dict]: Commit information
        """
        try:
            if "/" not in repo_name:
                repo_name = f"{self.username}/{repo_name}"
            
            url = f"{self.base_url}/repos/{repo_name}/commits"
            params = {"per_page": min(limit, 100)}
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            commits = response.json()
            logger.info(f"Retrieved {len(commits)} commits from repository: {repo_name}")
            
            return commits
            
        except requests.RequestException as e:
            logger.error(f"Error retrieving commits: {e}")
            raise
    
    def get_pull_requests(self, repo_name: str, state: str = "all", limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get pull requests from a repository.
        
        Args:
            repo_name: Repository name
            state: PR state (open, closed, all)
            limit: Maximum number of PRs to return
            
        Returns:
            List[Dict]: Pull request information
        """
        try:
            if "/" not in repo_name:
                repo_name = f"{self.username}/{repo_name}"
            
            url = f"{self.base_url}/repos/{repo_name}/pulls"
            params = {
                "state": state,
                "per_page": min(limit, 100)
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            prs = response.json()
            logger.info(f"Retrieved {len(prs)} pull requests from repository: {repo_name}")
            
            return prs
            
        except requests.RequestException as e:
            logger.error(f"Error retrieving pull requests: {e}")
            raise
    
    def _get_file_content(self, repo_name: str, file_path: str) -> Optional[str]:
        """Get content of a specific file."""
        try:
            url = f"{self.base_url}/repos/{repo_name}/contents/{file_path}"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            file_data = response.json()
            
            # Decode base64 content
            if file_data.get("encoding") == "base64":
                content = base64.b64decode(file_data["content"]).decode("utf-8")
                return content
            
            return None
            
        except Exception as e:
            logger.warning(f"Error getting file content for {file_path}: {e}")
            return None


class GoogleDriveIntegration:
    """Google Drive integration for retrieving documents and files."""
    
    def __init__(self, credentials: Dict[str, Any], folder_id: Optional[str] = None):
        """
        Initialize Google Drive integration.
        
        Args:
            credentials: Google Drive API credentials
            folder_id: Optional specific folder ID to search
        """
        self.credentials = credentials
        self.folder_id = folder_id
        self.base_url = "https://www.googleapis.com/drive/v3"
        self.access_token = self._get_access_token()
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json"
        }
        logger.info("Google Drive integration initialized")
    
    def _get_access_token(self) -> str:
        """Get access token from credentials."""
        # This is a simplified implementation
        # In a real implementation, you would use the Google Auth library
        # and handle token refresh properly
        return self.credentials.get("access_token", "")
    
    def get_documents(self, file_types: Optional[List[str]] = None, limit: int = 20) -> List[ExternalArtifact]:
        """
        Get documents from Google Drive.
        
        Args:
            file_types: Optional list of MIME types to filter
            limit: Maximum number of documents to return
            
        Returns:
            List[ExternalArtifact]: Drive documents
        """
        try:
            # Build query
            query_parts = []
            if self.folder_id:
                query_parts.append(f"'{self.folder_id}' in parents")
            
            if file_types:
                mime_conditions = [f"mimeType='{mime}'" for mime in file_types]
                query_parts.append(f"({' or '.join(mime_conditions)})")
            
            query = " and ".join(query_parts) if query_parts else ""
            
            # Get files
            url = f"{self.base_url}/files"
            params = {
                "q": query,
                "pageSize": min(limit, 100),
                "fields": "files(id,name,mimeType,createdTime,modifiedTime,webViewLink)"
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            files_data = response.json()
            artifacts = []
            
            for file_info in files_data.get("files", []):
                # Get file content
                content = self._get_file_content(file_info["id"], file_info["mimeType"])
                if content:
                    artifact = ExternalArtifact(
                        id=f"gdrive_{file_info['id']}",
                        name=file_info["name"],
                        content=content,
                        source="google_drive",
                        url=file_info.get("webViewLink"),
                        metadata={
                            "file_id": file_info["id"],
                            "mime_type": file_info["mimeType"],
                            "created_time": file_info.get("createdTime"),
                            "modified_time": file_info.get("modifiedTime")
                        }
                    )
                    artifacts.append(artifact)
            
            logger.info(f"Retrieved {len(artifacts)} documents from Google Drive")
            return artifacts
            
        except requests.RequestException as e:
            logger.error(f"Error retrieving Google Drive documents: {e}")
            raise
    
    def _get_file_content(self, file_id: str, mime_type: str) -> Optional[str]:
        """Get content of a Google Drive file."""
        try:
            # For text-based files, we can get the content directly
            if mime_type.startswith("text/") or mime_type in [
                "application/json",
                "application/xml",
                "text/csv"
            ]:
                url = f"{self.base_url}/files/{file_id}"
                params = {"alt": "media"}
                
                response = requests.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                
                return response.text
            
            # For Google Docs, Sheets, Slides, we would need to export
            elif mime_type in [
                "application/vnd.google-apps.document",
                "application/vnd.google-apps.spreadsheet",
                "application/vnd.google-apps.presentation"
            ]:
                export_mime = {
                    "application/vnd.google-apps.document": "text/plain",
                    "application/vnd.google-apps.spreadsheet": "text/csv",
                    "application/vnd.google-apps.presentation": "text/plain"
                }.get(mime_type, "text/plain")
                
                url = f"{self.base_url}/files/{file_id}/export"
                params = {"mimeType": export_mime}
                
                response = requests.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                
                return response.text
            
            return None
            
        except Exception as e:
            logger.warning(f"Error getting file content for {file_id}: {e}")
            return None


class ExternalIntegrationService:
    """
    Service for integrating with external tools to retrieve work artifacts.
    
    This service provides a unified interface for retrieving artifacts from
    various external sources like GitHub and Google Drive.
    """
    
    def __init__(self, config: Optional[IntegrationConfig] = None):
        """
        Initialize external integration service.
        
        Args:
            config: Integration configuration
        """
        self.config = config or self._load_config_from_environment()
        self.github_integration = None
        self.google_drive_integration = None
        
        # Initialize integrations if credentials are available
        if self.config.github_token and self.config.github_username:
            self.github_integration = GitHubIntegration(
                self.config.github_token,
                self.config.github_username
            )
        
        if self.config.google_drive_credentials:
            self.google_drive_integration = GoogleDriveIntegration(
                self.config.google_drive_credentials,
                self.config.google_drive_folder_id
            )
        
        logger.info("External integration service initialized")
    
    def _load_config_from_environment(self) -> IntegrationConfig:
        """Load integration configuration from environment variables."""
        return IntegrationConfig(
            github_token=os.getenv("GITHUB_TOKEN"),
            github_username=os.getenv("GITHUB_USERNAME"),
            google_drive_credentials=self._load_google_credentials(),
            google_drive_folder_id=os.getenv("GOOGLE_DRIVE_FOLDER_ID")
        )
    
    def _load_google_credentials(self) -> Optional[Dict[str, Any]]:
        """Load Google Drive credentials from environment or file."""
        # This is a simplified implementation
        # In a real implementation, you would load from a proper credentials file
        access_token = os.getenv("GOOGLE_DRIVE_ACCESS_TOKEN")
        if access_token:
            return {"access_token": access_token}
        return None
    
    def get_github_artifacts(
        self, 
        repositories: Optional[List[str]] = None,
        file_extensions: Optional[List[str]] = None,
        max_files_per_repo: int = 20
    ) -> List[ExternalArtifact]:
        """
        Get artifacts from GitHub repositories.
        
        Args:
            repositories: List of repository names (None for all user repos)
            file_extensions: List of file extensions to include
            max_files_per_repo: Maximum files per repository
            
        Returns:
            List[ExternalArtifact]: GitHub artifacts
        """
        if not self.github_integration:
            logger.warning("GitHub integration not configured")
            return []
        
        try:
            artifacts = []
            
            if repositories:
                repo_list = repositories
            else:
                # Get user's repositories
                user_repos = self.github_integration.get_user_repositories(limit=10)
                repo_list = [repo["name"] for repo in user_repos]
            
            for repo_name in repo_list:
                try:
                    repo_artifacts = self.github_integration.get_repository_files(
                        repo_name, file_extensions, max_files_per_repo
                    )
                    artifacts.extend(repo_artifacts)
                except Exception as e:
                    logger.warning(f"Error retrieving artifacts from {repo_name}: {e}")
                    continue
            
            logger.info(f"Retrieved {len(artifacts)} artifacts from GitHub")
            return artifacts
            
        except Exception as e:
            logger.error(f"Error retrieving GitHub artifacts: {e}")
            return []
    
    def get_google_drive_artifacts(
        self, 
        file_types: Optional[List[str]] = None,
        limit: int = 20
    ) -> List[ExternalArtifact]:
        """
        Get artifacts from Google Drive.
        
        Args:
            file_types: List of MIME types to include
            limit: Maximum number of files to retrieve
            
        Returns:
            List[ExternalArtifact]: Google Drive artifacts
        """
        if not self.google_drive_integration:
            logger.warning("Google Drive integration not configured")
            return []
        
        try:
            artifacts = self.google_drive_integration.get_documents(file_types, limit)
            logger.info(f"Retrieved {len(artifacts)} artifacts from Google Drive")
            return artifacts
            
        except Exception as e:
            logger.error(f"Error retrieving Google Drive artifacts: {e}")
            return []
    
    def get_all_artifacts(
        self, 
        github_repos: Optional[List[str]] = None,
        github_file_extensions: Optional[List[str]] = None,
        google_drive_file_types: Optional[List[str]] = None,
        max_artifacts: int = 100
    ) -> List[ExternalArtifact]:
        """
        Get artifacts from all configured external sources.
        
        Args:
            github_repos: GitHub repositories to include
            github_file_extensions: GitHub file extensions to include
            google_drive_file_types: Google Drive file types to include
            max_artifacts: Maximum total artifacts to retrieve
            
        Returns:
            List[ExternalArtifact]: All external artifacts
        """
        all_artifacts = []
        
        # Get GitHub artifacts
        github_artifacts = self.get_github_artifacts(
            github_repos, github_file_extensions, max_files_per_repo=20
        )
        all_artifacts.extend(github_artifacts)
        
        # Get Google Drive artifacts
        google_artifacts = self.get_google_drive_artifacts(
            google_drive_file_types, limit=20
        )
        all_artifacts.extend(google_artifacts)
        
        # Limit total artifacts
        if len(all_artifacts) > max_artifacts:
            all_artifacts = all_artifacts[:max_artifacts]
        
        logger.info(f"Retrieved {len(all_artifacts)} total artifacts from external sources")
        return all_artifacts
    
    def convert_to_processed_content(self, artifacts: List[ExternalArtifact]) -> List[ProcessedContent]:
        """
        Convert external artifacts to ProcessedContent objects.
        
        Args:
            artifacts: List of external artifacts
            
        Returns:
            List[ProcessedContent]: Processed content objects
        """
        processed_contents = []
        
        for artifact in artifacts:
            try:
                # Create file metadata
                metadata = FileMetadata(
                    filename=artifact.name,
                    file_size=len(artifact.content.encode('utf-8')),
                    file_type=f".{artifact.source}",
                    mime_type="text/plain",
                    file_hash=hash(artifact.content) % (2**32),  # Simple hash
                    processing_time=0.0,
                    text_length=len(artifact.content)
                )
                
                # Create processed content
                processed_content = ProcessedContent(
                    text=artifact.content,
                    metadata=metadata,
                    structured_data={
                        "source": artifact.source,
                        "external_id": artifact.id,
                        "url": artifact.url,
                        "metadata": artifact.metadata
                    }
                )
                
                processed_contents.append(processed_content)
                
            except Exception as e:
                logger.warning(f"Error converting artifact {artifact.id}: {e}")
                continue
        
        logger.info(f"Converted {len(processed_contents)} artifacts to processed content")
        return processed_contents
    
    def get_integration_status(self) -> Dict[str, Any]:
        """
        Get status of external integrations.
        
        Returns:
            Dict[str, Any]: Integration status information
        """
        status = {
            "github": {
                "configured": self.github_integration is not None,
                "username": self.config.github_username if self.github_integration else None
            },
            "google_drive": {
                "configured": self.google_drive_integration is not None,
                "folder_id": self.config.google_drive_folder_id if self.google_drive_integration else None
            }
        }
        
        return status


# Global external integration service instance
_external_integration_instance: Optional[ExternalIntegrationService] = None


def get_external_integration_service() -> ExternalIntegrationService:
    """
    Get the global external integration service instance.
    
    Returns:
        ExternalIntegrationService: Global external integration service instance
    """
    global _external_integration_instance
    if _external_integration_instance is None:
        _external_integration_instance = ExternalIntegrationService()
    return _external_integration_instance


def initialize_external_integration_service(config: Optional[IntegrationConfig] = None) -> ExternalIntegrationService:
    """
    Initialize the global external integration service.
    
    Args:
        config: Integration configuration
        
    Returns:
        ExternalIntegrationService: Initialized external integration service instance
    """
    global _external_integration_instance
    _external_integration_instance = ExternalIntegrationService(config)
    return _external_integration_instance
