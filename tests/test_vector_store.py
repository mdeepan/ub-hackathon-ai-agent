"""
Tests for vector storage management.

This module tests the VectorStore class and ChromaDB integration
including document storage, semantic search, and collection management.
"""

import pytest
import tempfile
import os
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

from backend.database.vector_store import (
    VectorStore, 
    get_vector_store, 
    initialize_vector_store, 
    reset_vector_store
)


class TestVectorStore:
    """Test cases for VectorStore class."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Create a temporary directory for ChromaDB
        self.temp_dir = tempfile.mkdtemp()
        self.vector_store = VectorStore(self.temp_dir)
    
    def teardown_method(self):
        """Clean up after each test method."""
        # Remove temporary directory
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_initialization_with_custom_path(self):
        """Test vector store initialization with custom path."""
        assert self.vector_store.persist_directory == Path(self.temp_dir)
        assert self.vector_store.persist_directory.exists()
        assert self.vector_store.client is not None
    
    def test_initialization_with_default_path(self):
        """Test vector store initialization with default path."""
        vector_store = VectorStore()
        expected_path = Path(__file__).parent.parent / "data" / "chroma"
        assert vector_store.persist_directory == expected_path
        assert vector_store.persist_directory.exists()
    
    def test_ensure_chroma_directory_creation(self):
        """Test that ChromaDB directory is created if it doesn't exist."""
        temp_dir = tempfile.mkdtemp()
        chroma_path = os.path.join(temp_dir, "nested", "dir", "chroma")
        
        try:
            vector_store = VectorStore(chroma_path)
            assert Path(chroma_path).exists()
        finally:
            # Clean up
            shutil.rmtree(temp_dir)
    
    def test_get_collection_existing(self):
        """Test getting an existing collection."""
        collection_name = "test_collection"
        
        # Create a collection first
        collection = self.vector_store.get_collection(collection_name)
        assert collection is not None
        assert collection.name == collection_name
        
        # Get the same collection again
        same_collection = self.vector_store.get_collection(collection_name)
        assert same_collection.name == collection_name
    
    def test_get_collection_create_if_not_exists(self):
        """Test getting a collection with create_if_not_exists=True."""
        collection_name = "new_collection"
        collection = self.vector_store.get_collection(collection_name, create_if_not_exists=True)
        assert collection is not None
        assert collection.name == collection_name
    
    def test_get_collection_do_not_create(self):
        """Test getting a collection with create_if_not_exists=False."""
        collection_name = "nonexistent_collection"
        
        with pytest.raises(Exception):
            self.vector_store.get_collection(collection_name, create_if_not_exists=False)
    
    def test_add_documents_basic(self):
        """Test adding documents to a collection."""
        collection_name = "test_documents"
        documents = [
            "This is a test document about machine learning.",
            "Another document about data science and AI.",
            "A third document about software engineering."
        ]
        
        ids = self.vector_store.add_documents(collection_name, documents)
        
        assert len(ids) == 3
        assert all(isinstance(id, str) for id in ids)
        
        # Verify documents were added
        collection_info = self.vector_store.get_collection_info(collection_name)
        assert collection_info['document_count'] == 3
    
    def test_add_documents_with_metadata(self):
        """Test adding documents with metadata."""
        collection_name = "test_metadata"
        documents = ["Test document"]
        metadatas = [{"category": "test", "priority": "high"}]
        ids = ["test_id_1"]
        
        returned_ids = self.vector_store.add_documents(
            collection_name, documents, metadatas, ids
        )
        
        assert returned_ids == ids
        
        # Verify document with metadata
        doc = self.vector_store.get_document_by_id(collection_name, ids[0])
        assert doc is not None
        assert doc['document'] == documents[0]
        assert doc['metadata']['category'] == "test"
        assert doc['metadata']['priority'] == "high"
        assert 'created_at' in doc['metadata']
    
    def test_add_documents_with_custom_ids(self):
        """Test adding documents with custom IDs."""
        collection_name = "test_custom_ids"
        documents = ["Document 1", "Document 2"]
        custom_ids = ["custom_1", "custom_2"]
        
        returned_ids = self.vector_store.add_documents(
            collection_name, documents, ids=custom_ids
        )
        
        assert returned_ids == custom_ids
        
        # Verify documents can be retrieved by custom IDs
        doc1 = self.vector_store.get_document_by_id(collection_name, "custom_1")
        doc2 = self.vector_store.get_document_by_id(collection_name, "custom_2")
        
        assert doc1['document'] == "Document 1"
        assert doc2['document'] == "Document 2"
    
    def test_search_documents_basic(self):
        """Test basic document search functionality."""
        collection_name = "test_search"
        documents = [
            "Machine learning is a subset of artificial intelligence.",
            "Data science involves statistics and programming.",
            "Software engineering focuses on building applications."
        ]
        
        # Add documents
        self.vector_store.add_documents(collection_name, documents)
        
        # Search for similar documents
        results = self.vector_store.search_documents(
            collection_name, "artificial intelligence", n_results=2
        )
        
        assert len(results['documents']) <= 2
        assert len(results['metadatas']) <= 2
        assert len(results['distances']) <= 2
        assert len(results['ids']) <= 2
        
        # All result lists should have the same length
        result_length = len(results['documents'])
        assert len(results['metadatas']) == result_length
        assert len(results['distances']) == result_length
        assert len(results['ids']) == result_length
    
    def test_search_documents_with_filter(self):
        """Test document search with metadata filter."""
        collection_name = "test_search_filter"
        documents = [
            "Machine learning document",
            "Data science document",
            "Software engineering document"
        ]
        metadatas = [
            {"category": "ai", "level": "beginner"},
            {"category": "data", "level": "intermediate"},
            {"category": "software", "level": "advanced"}
        ]
        
        # Add documents with metadata
        self.vector_store.add_documents(collection_name, documents, metadatas)
        
        # Search with filter
        results = self.vector_store.search_documents(
            collection_name, 
            "programming", 
            n_results=5,
            where={"category": "software"}
        )
        
        # Should only return software-related documents
        for metadata in results['metadatas']:
            assert metadata['category'] == "software"
    
    def test_get_document_by_id_existing(self):
        """Test retrieving an existing document by ID."""
        collection_name = "test_get_by_id"
        documents = ["Test document content"]
        ids = ["test_doc_1"]
        
        self.vector_store.add_documents(collection_name, documents, ids=ids)
        
        doc = self.vector_store.get_document_by_id(collection_name, "test_doc_1")
        
        assert doc is not None
        assert doc['id'] == "test_doc_1"
        assert doc['document'] == "Test document content"
        assert isinstance(doc['metadata'], dict)
    
    def test_get_document_by_id_nonexistent(self):
        """Test retrieving a non-existent document by ID."""
        collection_name = "test_get_nonexistent"
        
        doc = self.vector_store.get_document_by_id(collection_name, "nonexistent_id")
        
        assert doc is None
    
    def test_update_document_existing(self):
        """Test updating an existing document."""
        collection_name = "test_update"
        documents = ["Original content"]
        ids = ["update_doc_1"]
        
        # Add document
        self.vector_store.add_documents(collection_name, documents, ids=ids)
        
        # Update document
        success = self.vector_store.update_document(
            collection_name, 
            "update_doc_1", 
            document="Updated content",
            metadata={"updated": True}
        )
        
        assert success is True
        
        # Verify update
        doc = self.vector_store.get_document_by_id(collection_name, "update_doc_1")
        assert doc['document'] == "Updated content"
        assert doc['metadata']['updated'] is True
        assert 'updated_at' in doc['metadata']
    
    def test_update_document_nonexistent(self):
        """Test updating a non-existent document."""
        collection_name = "test_update_nonexistent"
        
        success = self.vector_store.update_document(
            collection_name, 
            "nonexistent_id", 
            document="New content"
        )
        
        assert success is False
    
    def test_delete_document_existing(self):
        """Test deleting an existing document."""
        collection_name = "test_delete"
        documents = ["Document to delete"]
        ids = ["delete_doc_1"]
        
        # Add document
        self.vector_store.add_documents(collection_name, documents, ids=ids)
        
        # Verify document exists
        doc = self.vector_store.get_document_by_id(collection_name, "delete_doc_1")
        assert doc is not None
        
        # Delete document
        success = self.vector_store.delete_document(collection_name, "delete_doc_1")
        assert success is True
        
        # Verify document is deleted
        doc = self.vector_store.get_document_by_id(collection_name, "delete_doc_1")
        assert doc is None
    
    def test_get_collection_info_existing(self):
        """Test getting information about an existing collection."""
        collection_name = "test_info"
        documents = ["Doc 1", "Doc 2", "Doc 3"]
        
        # Add documents
        self.vector_store.add_documents(collection_name, documents)
        
        info = self.vector_store.get_collection_info(collection_name)
        
        assert info['name'] == collection_name
        assert info['document_count'] == 3
        assert info['exists'] is True
    
    def test_get_collection_info_nonexistent(self):
        """Test getting information about a non-existent collection."""
        collection_name = "nonexistent_collection"
        
        info = self.vector_store.get_collection_info(collection_name)
        
        assert info['name'] == collection_name
        assert info['document_count'] == 0
        assert info['exists'] is False
    
    def test_list_collections(self):
        """Test listing all collections."""
        # Create multiple collections
        collections = ["collection_1", "collection_2", "collection_3"]
        for collection_name in collections:
            self.vector_store.add_documents(collection_name, ["test doc"])
        
        collection_list = self.vector_store.list_collections()
        
        # Should have at least the collections we created
        collection_names = [info['name'] for info in collection_list]
        for collection_name in collections:
            assert collection_name in collection_names
    
    def test_reset_collection(self):
        """Test resetting a collection."""
        collection_name = "test_reset"
        documents = ["Doc 1", "Doc 2", "Doc 3"]
        
        # Add documents
        self.vector_store.add_documents(collection_name, documents)
        
        # Verify documents exist
        info = self.vector_store.get_collection_info(collection_name)
        assert info['document_count'] == 3
        
        # Reset collection
        success = self.vector_store.reset_collection(collection_name)
        assert success is True
        
        # Verify collection is empty
        info = self.vector_store.get_collection_info(collection_name)
        assert info['document_count'] == 0
    
    def test_get_vector_store_info(self):
        """Test getting comprehensive vector store information."""
        # Add some test data
        self.vector_store.add_documents("test_collection", ["test document"])
        
        info = self.vector_store.get_vector_store_info()
        
        assert 'persist_directory' in info
        assert 'directory_exists' in info
        assert 'collections' in info
        assert 'total_collections' in info
        assert 'total_documents' in info
        
        assert info['directory_exists'] is True
        assert info['total_collections'] >= 1
        assert info['total_documents'] >= 1


class TestGlobalVectorStoreFunctions:
    """Test cases for global vector store functions."""
    
    def teardown_method(self):
        """Clean up after each test method."""
        reset_vector_store()
    
    def test_get_vector_store_creates_instance(self):
        """Test that get_vector_store creates a new instance if none exists."""
        reset_vector_store()
        vector_store = get_vector_store()
        assert isinstance(vector_store, VectorStore)
    
    def test_get_vector_store_returns_same_instance(self):
        """Test that get_vector_store returns the same instance."""
        vector_store1 = get_vector_store()
        vector_store2 = get_vector_store()
        assert vector_store1 is vector_store2
    
    def test_initialize_vector_store(self):
        """Test vector store initialization."""
        temp_dir = tempfile.mkdtemp()
        
        try:
            vector_store = initialize_vector_store(temp_dir)
            assert isinstance(vector_store, VectorStore)
            assert vector_store.persist_directory == Path(temp_dir)
            
            # Verify global instance is set
            global_vector_store = get_vector_store()
            assert global_vector_store is vector_store
        finally:
            # Clean up
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
    
    def test_reset_vector_store(self):
        """Test vector store reset."""
        # Get initial instance
        vector_store1 = get_vector_store()
        
        # Reset and get new instance
        reset_vector_store()
        vector_store2 = get_vector_store()
        
        # Should be different instances
        assert vector_store1 is not vector_store2


class TestVectorStoreErrorHandling:
    """Test cases for vector store error handling."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.temp_dir = tempfile.mkdtemp()
        self.vector_store = VectorStore(self.temp_dir)
    
    def teardown_method(self):
        """Clean up after each test method."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_add_documents_error_handling(self):
        """Test error handling in add_documents."""
        collection_name = "test_error"
        
        # Test with invalid data that might cause errors
        with pytest.raises(Exception):
            self.vector_store.add_documents(collection_name, [])
    
    def test_search_documents_error_handling(self):
        """Test error handling in search_documents."""
        collection_name = "nonexistent_collection"
        
        with pytest.raises(Exception):
            self.vector_store.search_documents(collection_name, "test query")
    
    def test_get_document_by_id_error_handling(self):
        """Test error handling in get_document_by_id."""
        collection_name = "nonexistent_collection"
        
        # Should return None for non-existent collection (graceful handling)
        result = self.vector_store.get_document_by_id(collection_name, "test_id")
        assert result is None


if __name__ == "__main__":
    pytest.main([__file__])
