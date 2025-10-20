"""
Tests for file processing utilities.

This module contains comprehensive tests for the file processor functionality,
including text extraction from various file formats and error handling.
"""

import pytest
import io
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from fastapi import UploadFile

# Import the modules to test
from backend.utils.file_processor import (
    FileProcessor,
    FileMetadata,
    ProcessedContent,
    get_file_processor,
    initialize_file_processor,
    reset_file_processor
)


class TestFileMetadata:
    """Test FileMetadata dataclass."""
    
    def test_file_metadata_creation(self):
        """Test FileMetadata creation with all fields."""
        metadata = FileMetadata(
            filename="test.pdf",
            file_size=1024,
            file_type=".pdf",
            mime_type="application/pdf",
            file_hash="abc123",
            processing_time=1.5,
            text_length=500,
            page_count=2
        )
        
        assert metadata.filename == "test.pdf"
        assert metadata.file_size == 1024
        assert metadata.file_type == ".pdf"
        assert metadata.mime_type == "application/pdf"
        assert metadata.file_hash == "abc123"
        assert metadata.processing_time == 1.5
        assert metadata.text_length == 500
        assert metadata.page_count == 2
        assert metadata.error is None
    
    def test_file_metadata_with_error(self):
        """Test FileMetadata creation with error."""
        metadata = FileMetadata(
            filename="test.pdf",
            file_size=0,
            file_type=".pdf",
            mime_type="application/pdf",
            file_hash="",
            processing_time=0.5,
            text_length=0,
            error="Processing failed"
        )
        
        assert metadata.error == "Processing failed"
        assert metadata.file_size == 0


class TestProcessedContent:
    """Test ProcessedContent dataclass."""
    
    def test_processed_content_creation(self):
        """Test ProcessedContent creation."""
        metadata = FileMetadata(
            filename="test.pdf",
            file_size=1024,
            file_type=".pdf",
            mime_type="application/pdf",
            file_hash="abc123",
            processing_time=1.5,
            text_length=500
        )
        
        content = ProcessedContent(
            text="This is test content",
            metadata=metadata
        )
        
        assert content.text == "This is test content"
        assert content.metadata.filename == "test.pdf"
        assert content.structured_data is None
        assert content.extracted_entities is None


class TestFileProcessor:
    """Test FileProcessor class."""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing."""
        config = Mock()
        config.get_settings.return_value = Mock(
            data_dir="/tmp/test_data"
        )
        return config
    
    @pytest.fixture
    def file_processor(self, mock_config):
        """Create FileProcessor instance for testing."""
        with patch('backend.utils.file_processor.get_config', return_value=mock_config):
            with patch('pathlib.Path.mkdir'):
                return FileProcessor(mock_config)
    
    def test_file_processor_initialization(self, mock_config):
        """Test FileProcessor initialization."""
        with patch('backend.utils.file_processor.get_config', return_value=mock_config):
            with patch('pathlib.Path.mkdir'):
                processor = FileProcessor(mock_config)
                
                assert processor.config == mock_config
                assert processor.upload_dir == Path("/tmp/test_data") / "uploads"
    
    def test_supported_extensions(self, file_processor):
        """Test supported file extensions."""
        extensions = file_processor.SUPPORTED_EXTENSIONS
        
        assert '.pdf' in extensions
        assert '.docx' in extensions
        assert '.txt' in extensions
        assert '.html' in extensions
        assert '.json' in extensions
        assert '.csv' in extensions
    
    def test_max_file_size(self, file_processor):
        """Test maximum file size limit."""
        assert file_processor.MAX_FILE_SIZE == 10 * 1024 * 1024  # 10MB
    
    def test_validate_file_valid(self, file_processor):
        """Test file validation with valid file."""
        mock_file = Mock()
        mock_file.filename = "test.pdf"
        mock_file.size = 1024
        mock_file.content_type = "application/pdf"
        
        is_valid, error = file_processor.validate_file(mock_file)
        
        assert is_valid is True
        assert error == ""
    
    def test_validate_file_no_filename(self, file_processor):
        """Test file validation with no filename."""
        mock_file = Mock()
        mock_file.filename = None
        mock_file.size = None
        mock_file.content_type = None
        
        is_valid, error = file_processor.validate_file(mock_file)
        
        assert is_valid is False
        assert "No filename provided" in error
    
    def test_validate_file_unsupported_extension(self, file_processor):
        """Test file validation with unsupported extension."""
        mock_file = Mock()
        mock_file.filename = "test.xyz"
        mock_file.size = None
        mock_file.content_type = None
        
        is_valid, error = file_processor.validate_file(mock_file)
        
        assert is_valid is False
        assert "Unsupported file type" in error
    
    def test_validate_file_too_large(self, file_processor):
        """Test file validation with file too large."""
        mock_file = Mock()
        mock_file.filename = "test.pdf"
        mock_file.size = file_processor.MAX_FILE_SIZE + 1
        
        is_valid, error = file_processor.validate_file(mock_file)
        
        assert is_valid is False
        assert "File size exceeds maximum limit" in error
    
    def test_calculate_file_hash(self, file_processor):
        """Test file hash calculation."""
        content = b"test content"
        hash1 = file_processor.calculate_file_hash(content)
        hash2 = file_processor.calculate_file_hash(content)
        
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hash length
    
    def test_extract_text_from_txt(self, file_processor):
        """Test text extraction from TXT file."""
        content = b"This is a test text file.\nIt has multiple lines.\n"
        
        text, line_count = file_processor.extract_text_from_txt(content)
        
        assert "This is a test text file" in text
        assert "It has multiple lines" in text
        assert line_count == 2
    
    def test_extract_text_from_txt_encoding_error(self, file_processor):
        """Test text extraction from TXT file with encoding issues."""
        # Create content with invalid UTF-8
        content = b"\xff\xfe\x00\x00This is test content"
        
        text, line_count = file_processor.extract_text_from_txt(content)
        
        # Should handle encoding error gracefully
        assert len(text) > 0
        assert line_count >= 1
    
    def test_extract_text_from_json(self, file_processor):
        """Test text extraction from JSON file."""
        json_data = {
            "title": "Test Document",
            "content": "This is test content",
            "metadata": {
                "author": "Test Author",
                "date": "2024-01-01"
            }
        }
        content = json.dumps(json_data).encode('utf-8')
        
        text, object_count = file_processor.extract_text_from_json(content)
        
        assert "title" in text
        assert "Test Document" in text
        assert "author" in text
        assert object_count > 0
    
    def test_extract_text_from_json_invalid(self, file_processor):
        """Test text extraction from invalid JSON file."""
        content = b"{ invalid json content"
        
        with pytest.raises(Exception) as exc_info:
            file_processor.extract_text_from_json(content)
        
        assert "JSON processing failed" in str(exc_info.value)
    
    @patch('backend.utils.file_processor.PyPDF2.PdfReader')
    def test_extract_text_from_pdf(self, mock_pdf_reader, file_processor):
        """Test text extraction from PDF file."""
        # Mock PDF reader
        mock_page = Mock()
        mock_page.extract_text.return_value = "This is PDF content"
        
        mock_reader_instance = Mock()
        mock_reader_instance.pages = [mock_page, mock_page]
        mock_pdf_reader.return_value = mock_reader_instance
        
        content = b"fake pdf content"
        
        text, page_count = file_processor.extract_text_from_pdf(content)
        
        assert "This is PDF content" in text
        assert page_count == 2
    
    @patch('backend.utils.file_processor.Document')
    def test_extract_text_from_docx(self, mock_document, file_processor):
        """Test text extraction from DOCX file."""
        # Mock DOCX document
        mock_paragraph = Mock()
        mock_paragraph.text = "This is DOCX content"
        
        mock_doc_instance = Mock()
        mock_doc_instance.paragraphs = [mock_paragraph, mock_paragraph]
        mock_document.return_value = mock_doc_instance
        
        content = b"fake docx content"
        
        text, page_count = file_processor.extract_text_from_docx(content)
        
        assert "This is DOCX content" in text
        assert page_count >= 1
    
    @patch('backend.utils.file_processor.Presentation')
    def test_extract_text_from_pptx(self, mock_presentation, file_processor):
        """Test text extraction from PPTX file."""
        # Mock PPTX presentation
        mock_shape = Mock()
        mock_shape.text = "This is PPTX content"
        
        mock_slide = Mock()
        mock_slide.shapes = [mock_shape]
        
        mock_presentation_instance = Mock()
        mock_presentation_instance.slides = [mock_slide]
        mock_presentation.return_value = mock_presentation_instance
        
        content = b"fake pptx content"
        
        text, slide_count = file_processor.extract_text_from_pptx(content)
        
        assert "This is PPTX content" in text
        assert slide_count == 1
    
    @patch('backend.utils.file_processor.openpyxl.load_workbook')
    def test_extract_text_from_xlsx(self, mock_load_workbook, file_processor):
        """Test text extraction from XLSX file."""
        # Mock Excel workbook
        mock_sheet = Mock()
        mock_sheet.iter_rows.return_value = [
            ["Header1", "Header2"],
            ["Value1", "Value2"]
        ]
        
        mock_workbook = Mock()
        mock_workbook.sheetnames = ["Sheet1"]
        mock_workbook.__getitem__ = Mock(return_value=mock_sheet)
        mock_load_workbook.return_value = mock_workbook
        
        content = b"fake xlsx content"
        
        text, sheet_count = file_processor.extract_text_from_xlsx(content)
        
        assert "Sheet1" in text
        assert "Header1" in text
        assert "Value1" in text
        assert sheet_count == 1
    
    def test_extract_text_from_html(self, file_processor):
        """Test text extraction from HTML file."""
        html_content = """
        <html>
            <head><title>Test Page</title></head>
            <body>
                <h1>Main Title</h1>
                <p>This is a paragraph with <strong>bold text</strong>.</p>
                <script>console.log('This should be removed');</script>
            </body>
        </html>
        """.encode('utf-8')
        
        text, element_count = file_processor.extract_text_from_html(html_content)
        
        assert "Main Title" in text
        assert "This is a paragraph with bold text" in text
        assert "console.log" not in text  # Script content should be removed
        assert element_count > 0
    
    def test_extract_text_from_markdown(self, file_processor):
        """Test text extraction from Markdown file."""
        md_content = """
        # Main Title
        
        This is a **bold** paragraph.
        
        ## Subtitle
        
        - List item 1
        - List item 2
        """.encode('utf-8')
        
        text, line_count = file_processor.extract_text_from_markdown(md_content)
        
        assert "Main Title" in text
        assert "This is a" in text and "paragraph" in text  # Check parts separately since markdown processing changes formatting
        assert "List item 1" in text
        assert line_count >= 6
    
    @patch('backend.utils.file_processor.pd.read_csv')
    def test_extract_text_from_csv(self, mock_read_csv, file_processor):
        """Test text extraction from CSV file."""
        # Mock pandas DataFrame
        mock_df = Mock()
        mock_df.to_string.return_value = "Name,Age\nJohn,25\nJane,30"
        mock_df.__len__ = Mock(return_value=2)
        mock_read_csv.return_value = mock_df
        
        content = b"Name,Age\nJohn,25\nJane,30"
        
        text, row_count = file_processor.extract_text_from_csv(content)
        
        assert "Name" in text
        assert "John" in text
        assert row_count == 2
    
    def test_process_file_txt(self, file_processor):
        """Test processing a TXT file."""
        # Create mock UploadFile
        content = b"This is test content for processing."
        mock_file = Mock()
        mock_file.filename = "test.txt"
        mock_file.file = Mock()
        mock_file.file.read.return_value = content
        mock_file.size = len(content)
        mock_file.content_type = "text/plain"
        
        result = file_processor.process_file(mock_file)
        
        assert isinstance(result, ProcessedContent)
        assert result.text == "This is test content for processing."
        assert result.metadata.filename == "test.txt"
        assert result.metadata.file_type == ".txt"
        assert result.metadata.file_size == len(content)
        assert result.metadata.error is None
    
    def test_process_file_invalid(self, file_processor):
        """Test processing an invalid file."""
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "test.xyz"  # Unsupported extension
        
        with pytest.raises(Exception) as exc_info:
            file_processor.process_file(mock_file)
        
        assert "Unsupported file type" in str(exc_info.value)
    
    def test_process_multiple_files(self, file_processor):
        """Test processing multiple files."""
        # Create mock files
        content1 = b"First file content"
        content2 = b"Second file content"
        
        mock_file1 = Mock()
        mock_file1.filename = "test1.txt"
        mock_file1.file = Mock()
        mock_file1.file.read.return_value = content1
        mock_file1.size = len(content1)
        mock_file1.content_type = "text/plain"
        
        mock_file2 = Mock()
        mock_file2.filename = "test2.txt"
        mock_file2.file = Mock()
        mock_file2.file.read.return_value = content2
        mock_file2.size = len(content2)
        mock_file2.content_type = "text/plain"
        
        results = file_processor.process_multiple_files([mock_file1, mock_file2])
        
        assert len(results) == 2
        assert results[0].text == "First file content"
        assert results[1].text == "Second file content"
    
    def test_get_supported_formats(self, file_processor):
        """Test getting supported formats."""
        formats = file_processor.get_supported_formats()
        
        assert isinstance(formats, dict)
        assert '.pdf' in formats
        assert '.txt' in formats
        assert '.docx' in formats
    
    def test_get_processing_stats(self, file_processor):
        """Test getting processing statistics."""
        stats = file_processor.get_processing_stats()
        
        assert 'supported_formats' in stats
        assert 'max_file_size_mb' in stats
        assert 'upload_directory' in stats
        assert 'supported_extensions' in stats
        assert stats['max_file_size_mb'] == 10.0


class TestGlobalFunctions:
    """Test global utility functions."""
    
    def test_get_file_processor(self):
        """Test getting global file processor instance."""
        # Reset global instance
        reset_file_processor()
        
        with patch('backend.utils.file_processor.get_config') as mock_get_config:
            mock_config = Mock()
            mock_config.get_settings.return_value = Mock(data_dir="/tmp/test_data")
            mock_get_config.return_value = mock_config
            
            with patch('pathlib.Path.mkdir'):
                processor1 = get_file_processor()
                processor2 = get_file_processor()
                
                # Should return the same instance
                assert processor1 is processor2
                assert isinstance(processor1, FileProcessor)
    
    def test_initialize_file_processor(self):
        """Test initializing file processor with config."""
        mock_config = Mock()
        mock_config.get_settings.return_value = Mock(data_dir="/tmp/test_data")
        
        with patch('backend.utils.file_processor.get_config', return_value=mock_config):
            with patch('pathlib.Path.mkdir'):
                processor = initialize_file_processor(mock_config)
                
                assert isinstance(processor, FileProcessor)
                assert processor.config == mock_config
    
    def test_reset_file_processor(self):
        """Test resetting file processor."""
        with patch('backend.utils.file_processor.get_config') as mock_get_config:
            mock_config = Mock()
            mock_config.get_settings.return_value = Mock(data_dir="/tmp/test_data")
            mock_get_config.return_value = mock_config
            
            with patch('pathlib.Path.mkdir'):
                # Get initial instance
                processor1 = get_file_processor()
                
                # Reset
                reset_file_processor()
                
                # Get new instance
                processor2 = get_file_processor()
                
                # Should be different instances
                assert processor1 is not processor2


class TestIntegration:
    """Integration tests for file processing."""
    
    @pytest.fixture
    def temp_file(self):
        """Create temporary file for testing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("This is a test file for integration testing.\nIt has multiple lines.\n")
            temp_path = f.name
        
        yield temp_path
        
        # Cleanup
        os.unlink(temp_path)
    
    def test_end_to_end_file_processing(self, temp_file):
        """Test end-to-end file processing."""
        mock_config = Mock()
        mock_config.get_settings.return_value = Mock(data_dir="/tmp/test_data")
        
        with patch('backend.utils.file_processor.get_config', return_value=mock_config):
            with patch('pathlib.Path.mkdir'):
                processor = FileProcessor(mock_config)
                
                # Read file content
                with open(temp_file, 'rb') as f:
                    content = f.read()
                
                # Create mock UploadFile
                mock_file = Mock()
                mock_file.filename = "test.txt"
                mock_file.file = Mock()
                mock_file.file.read.return_value = content
                mock_file.size = len(content)
                mock_file.content_type = "text/plain"
                
                # Process file
                result = processor.process_file(mock_file)
                
                # Verify results
                assert result.text == "This is a test file for integration testing.\nIt has multiple lines."
                assert result.metadata.filename == "test.txt"
                assert result.metadata.file_type == ".txt"
                assert result.metadata.file_size == len(content)
                assert result.metadata.error is None


if __name__ == "__main__":
    pytest.main([__file__])
