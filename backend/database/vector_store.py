"""
Vector storage management for the Personal Learning Agent.

This module provides ChromaDB integration for vector storage and semantic search
capabilities, including document embedding, similarity search, and collection management.
"""

import chromadb
from chromadb.config import Settings
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
import logging
import uuid
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VectorStore:
    """
    ChromaDB vector storage manager for semantic search and document embeddings.
    """
    
    def __init__(self, persist_directory: Optional[str] = None):
        """
        Initialize ChromaDB vector store.
        
        Args:
            persist_directory: Directory to persist ChromaDB data. If None, uses default path.
        """
        if persist_directory is None:
            # Default to data/chroma/ directory
            project_root = Path(__file__).parent.parent.parent
            persist_directory = project_root / "data" / "chroma"
        
        self.persist_directory = Path(persist_directory)
        self._ensure_chroma_directory()
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Collection names for different data types
        self.collections = {
            'skills_content': 'skills_learning_content',
            'user_artifacts': 'user_work_artifacts',
            'learning_paths': 'learning_paths',
            'skills_taxonomy': 'skills_taxonomy'
        }
        
        logger.info(f"Vector store initialized: {self.persist_directory}")
    
    def _ensure_chroma_directory(self) -> None:
        """Ensure the ChromaDB directory exists."""
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        logger.info(f"ChromaDB directory ensured: {self.persist_directory}")
    
    def get_collection(self, collection_name: str, create_if_not_exists: bool = True):
        """
        Get or create a ChromaDB collection.
        
        Args:
            collection_name: Name of the collection
            create_if_not_exists: Whether to create collection if it doesn't exist
            
        Returns:
            chromadb.Collection: ChromaDB collection object
        """
        try:
            collection = self.client.get_collection(collection_name)
            logger.debug(f"Retrieved existing collection: {collection_name}")
            return collection
        except Exception as e:
            if create_if_not_exists:
                logger.info(f"Creating new collection: {collection_name}")
                collection = self.client.create_collection(
                    name=collection_name,
                    metadata={"description": f"Collection for {collection_name}"}
                )
                return collection
            else:
                logger.error(f"Collection {collection_name} not found and create_if_not_exists=False")
                raise e
    
    def add_documents(
        self, 
        collection_name: str, 
        documents: List[str], 
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None
    ) -> List[str]:
        """
        Add documents to a collection with automatic embedding.
        
        Args:
            collection_name: Name of the collection
            documents: List of document texts
            metadatas: Optional list of metadata dictionaries
            ids: Optional list of document IDs
            
        Returns:
            List[str]: List of document IDs
        """
        collection = self.get_collection(collection_name)
        
        # Generate IDs if not provided
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in documents]
        
        # Add timestamp to metadata if not present
        if metadatas is None:
            metadatas = [{} for _ in documents]
        
        for i, metadata in enumerate(metadatas):
            if 'created_at' not in metadata:
                metadata['created_at'] = datetime.now().isoformat()
            if 'document_type' not in metadata:
                metadata['document_type'] = collection_name
        
        try:
            collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            logger.info(f"Added {len(documents)} documents to collection {collection_name}")
            return ids
        except Exception as e:
            logger.error(f"Error adding documents to {collection_name}: {e}")
            raise
    
    def search_documents(
        self, 
        collection_name: str, 
        query_text: str, 
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Search for similar documents using semantic similarity.
        
        Args:
            collection_name: Name of the collection to search
            query_text: Query text for semantic search
            n_results: Number of results to return
            where: Optional metadata filter
            
        Returns:
            Dict containing search results with documents, metadatas, distances, and ids
        """
        collection = self.get_collection(collection_name, create_if_not_exists=False)
        
        try:
            results = collection.query(
                query_texts=[query_text],
                n_results=n_results,
                where=where
            )
            
            # Flatten results for easier access
            search_results = {
                'documents': results['documents'][0] if results['documents'] else [],
                'metadatas': results['metadatas'][0] if results['metadatas'] else [],
                'distances': results['distances'][0] if results['distances'] else [],
                'ids': results['ids'][0] if results['ids'] else []
            }
            
            logger.debug(f"Found {len(search_results['documents'])} results for query in {collection_name}")
            return search_results
            
        except Exception as e:
            logger.error(f"Error searching collection {collection_name}: {e}")
            raise
    
    def get_document_by_id(self, collection_name: str, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific document by ID.
        
        Args:
            collection_name: Name of the collection
            document_id: ID of the document to retrieve
            
        Returns:
            Dict containing document data or None if not found
        """
        try:
            collection = self.get_collection(collection_name, create_if_not_exists=False)
        except Exception:
            logger.warning(f"Collection {collection_name} not found")
            return None
        
        try:
            results = collection.get(ids=[document_id])
            
            if results['documents']:
                return {
                    'id': results['ids'][0],
                    'document': results['documents'][0],
                    'metadata': results['metadatas'][0] if results['metadatas'] else {}
                }
            else:
                logger.warning(f"Document {document_id} not found in collection {collection_name}")
                return None
                
        except Exception as e:
            logger.error(f"Error retrieving document {document_id} from {collection_name}: {e}")
            raise
    
    def update_document(
        self, 
        collection_name: str, 
        document_id: str, 
        document: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update an existing document.
        
        Args:
            collection_name: Name of the collection
            document_id: ID of the document to update
            document: New document text (optional)
            metadata: New metadata (optional)
            
        Returns:
            bool: True if update successful, False otherwise
        """
        try:
            collection = self.get_collection(collection_name, create_if_not_exists=False)
        except Exception:
            logger.warning(f"Collection {collection_name} not found")
            return False
        
        try:
            # Get existing document
            existing = self.get_document_by_id(collection_name, document_id)
            if not existing:
                logger.warning(f"Cannot update non-existent document {document_id}")
                return False
            
            # Prepare update data
            update_data = {}
            if document is not None:
                update_data['documents'] = [document]
            if metadata is not None:
                # Merge with existing metadata
                existing_metadata = existing.get('metadata', {})
                existing_metadata.update(metadata)
                existing_metadata['updated_at'] = datetime.now().isoformat()
                update_data['metadatas'] = [existing_metadata]
            
            if update_data:
                collection.update(
                    ids=[document_id],
                    **update_data
                )
                logger.info(f"Updated document {document_id} in collection {collection_name}")
                return True
            else:
                logger.warning(f"No update data provided for document {document_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating document {document_id} in {collection_name}: {e}")
            raise
    
    def delete_document(self, collection_name: str, document_id: str) -> bool:
        """
        Delete a document from a collection.
        
        Args:
            collection_name: Name of the collection
            document_id: ID of the document to delete
            
        Returns:
            bool: True if deletion successful, False otherwise
        """
        collection = self.get_collection(collection_name, create_if_not_exists=False)
        
        try:
            collection.delete(ids=[document_id])
            logger.info(f"Deleted document {document_id} from collection {collection_name}")
            return True
        except Exception as e:
            logger.error(f"Error deleting document {document_id} from {collection_name}: {e}")
            raise
    
    def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """
        Get information about a collection.
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            Dict containing collection information
        """
        try:
            collection = self.get_collection(collection_name, create_if_not_exists=False)
            count = collection.count()
            
            info = {
                'name': collection_name,
                'document_count': count,
                'exists': True
            }
            
            return info
            
        except Exception as e:
            logger.warning(f"Collection {collection_name} not found: {e}")
            return {
                'name': collection_name,
                'document_count': 0,
                'exists': False
            }
    
    def list_collections(self) -> List[Dict[str, Any]]:
        """
        List all collections and their information.
        
        Returns:
            List of collection information dictionaries
        """
        try:
            collections = self.client.list_collections()
            collection_info = []
            
            for collection in collections:
                info = self.get_collection_info(collection.name)
                collection_info.append(info)
            
            logger.debug(f"Found {len(collection_info)} collections")
            return collection_info
            
        except Exception as e:
            logger.error(f"Error listing collections: {e}")
            return []
    
    def reset_collection(self, collection_name: str) -> bool:
        """
        Reset (delete all documents from) a collection.
        
        Args:
            collection_name: Name of the collection to reset
            
        Returns:
            bool: True if reset successful, False otherwise
        """
        try:
            collection = self.get_collection(collection_name, create_if_not_exists=False)
            # Get all document IDs first
            all_docs = collection.get()
            if all_docs['ids']:
                collection.delete(ids=all_docs['ids'])
            logger.info(f"Reset collection {collection_name}")
            return True
        except Exception as e:
            logger.error(f"Error resetting collection {collection_name}: {e}")
            return False
    
    def get_vector_store_info(self) -> Dict[str, Any]:
        """
        Get comprehensive information about the vector store.
        
        Returns:
            Dict containing vector store information
        """
        info = {
            'persist_directory': str(self.persist_directory),
            'directory_exists': self.persist_directory.exists(),
            'collections': self.list_collections(),
            'total_collections': 0,
            'total_documents': 0
        }
        
        if self.persist_directory.exists():
            info['total_collections'] = len(info['collections'])
            info['total_documents'] = sum(
                collection['document_count'] for collection in info['collections']
            )
        
        return info


# Global vector store instance
_vector_store_instance: Optional[VectorStore] = None


def get_vector_store() -> VectorStore:
    """
    Get the global vector store instance.
    
    Returns:
        VectorStore: Global vector store instance
    """
    global _vector_store_instance
    if _vector_store_instance is None:
        _vector_store_instance = VectorStore()
    return _vector_store_instance


def initialize_vector_store(persist_directory: Optional[str] = None) -> VectorStore:
    """
    Initialize the global vector store.
    
    Args:
        persist_directory: Directory to persist ChromaDB data
        
    Returns:
        VectorStore: Initialized vector store instance
    """
    global _vector_store_instance
    _vector_store_instance = VectorStore(persist_directory)
    return _vector_store_instance


def reset_vector_store() -> None:
    """Reset the global vector store instance (useful for testing)."""
    global _vector_store_instance
    _vector_store_instance = None
