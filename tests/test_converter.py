"""
Test suite for the Converter Service.

This module contains unit tests for the ConverterService class.
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.core.converter import ConverterService, ConversionResult, BatchConversionResult
from src.core.exceptions import (
    ConversionError,
    FileAccessError,
    UnsupportedFileError,
)


class TestConverterService:
    """Test cases for ConverterService."""
    
    @pytest.fixture
    def converter(self) -> ConverterService:
        """Create a ConverterService instance for testing."""
        return ConverterService()
    
    @pytest.fixture
    def temp_dir(self) -> Path:
        """Create a temporary directory for test files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    @pytest.fixture
    def sample_txt_file(self, temp_dir: Path) -> Path:
        """Create a sample text file for testing."""
        file_path = temp_dir / "sample.txt"
        file_path.write_text("# Hello World\n\nThis is a test file.")
        return file_path
    
    # ==================== is_supported Tests ====================
    
    def test_is_supported_pdf(self, converter: ConverterService) -> None:
        """Test that PDF files are supported."""
        assert converter.is_supported(Path("document.pdf")) is True
    
    def test_is_supported_docx(self, converter: ConverterService) -> None:
        """Test that DOCX files are supported."""
        assert converter.is_supported(Path("document.docx")) is True
    
    def test_is_supported_xlsx(self, converter: ConverterService) -> None:
        """Test that XLSX files are supported."""
        assert converter.is_supported(Path("spreadsheet.xlsx")) is True
    
    def test_is_supported_html(self, converter: ConverterService) -> None:
        """Test that HTML files are supported."""
        assert converter.is_supported(Path("page.html")) is True
    
    def test_is_supported_unknown_extension(self, converter: ConverterService) -> None:
        """Test that unknown file types are not supported."""
        assert converter.is_supported(Path("file.xyz")) is False
    
    def test_is_supported_case_insensitive(self, converter: ConverterService) -> None:
        """Test that extension checking is case-insensitive."""
        assert converter.is_supported(Path("document.PDF")) is True
        assert converter.is_supported(Path("document.Docx")) is True
    
    # ==================== validate_file Tests ====================
    
    def test_validate_file_not_exists(self, converter: ConverterService) -> None:
        """Test validation of non-existent file."""
        with pytest.raises(FileAccessError):
            converter.validate_file(Path("/nonexistent/file.pdf"))
    
    def test_validate_file_unsupported(
        self, 
        converter: ConverterService, 
        temp_dir: Path
    ) -> None:
        """Test validation of unsupported file type."""
        unsupported_file = temp_dir / "file.xyz"
        unsupported_file.write_text("content")
        
        with pytest.raises(UnsupportedFileError):
            converter.validate_file(unsupported_file)
    
    def test_validate_file_valid(
        self, 
        converter: ConverterService, 
        sample_txt_file: Path
    ) -> None:
        """Test validation of valid file."""
        # Should not raise any exception
        converter.validate_file(sample_txt_file)
    
    # ==================== convert_file Tests ====================
    
    def test_convert_file_success(
        self, 
        converter: ConverterService, 
        sample_txt_file: Path,
        temp_dir: Path
    ) -> None:
        """Test successful file conversion."""
        result = converter.convert_file(sample_txt_file, temp_dir)
        
        assert result.success is True
        assert result.source_path == sample_txt_file
        assert result.output_path is not None
        assert result.output_path.exists()
        assert result.markdown_content is not None
    
    def test_convert_file_unsupported(
        self, 
        converter: ConverterService, 
        temp_dir: Path
    ) -> None:
        """Test conversion of unsupported file type."""
        unsupported_file = temp_dir / "file.xyz"
        unsupported_file.write_text("content")
        
        result = converter.convert_file(unsupported_file, temp_dir)
        
        assert result.success is False
        assert "not supported" in result.error_message.lower()
    
    def test_convert_file_not_found(
        self, 
        converter: ConverterService, 
        temp_dir: Path
    ) -> None:
        """Test conversion of non-existent file."""
        result = converter.convert_file(
            Path("/nonexistent/document.pdf"), 
            temp_dir
        )
        
        assert result.success is False
        assert result.error_message is not None
    
    def test_convert_file_without_saving(
        self, 
        converter: ConverterService, 
        sample_txt_file: Path
    ) -> None:
        """Test conversion without saving to file."""
        result = converter.convert_file(sample_txt_file, save_to_file=False)
        
        assert result.success is True
        assert result.output_path is None
        assert result.markdown_content is not None
    
    # ==================== convert_batch Tests ====================
    
    def test_convert_batch_empty_list(
        self, 
        converter: ConverterService, 
        temp_dir: Path
    ) -> None:
        """Test batch conversion with empty file list."""
        result = converter.convert_batch([], temp_dir)
        
        assert result.total_files == 0
        assert result.successful == 0
        assert result.failed == 0
    
    def test_convert_batch_with_callback(
        self, 
        converter: ConverterService, 
        sample_txt_file: Path,
        temp_dir: Path
    ) -> None:
        """Test batch conversion with progress callback."""
        progress_updates = []
        
        def progress_callback(current: int, total: int, name: str) -> None:
            progress_updates.append((current, total, name))
        
        result = converter.convert_batch(
            [sample_txt_file], 
            temp_dir, 
            progress_callback=progress_callback
        )
        
        assert result.total_files == 1
        assert len(progress_updates) == 1
        assert progress_updates[0] == (1, 1, sample_txt_file.name)


class TestConversionResult:
    """Test cases for ConversionResult dataclass."""
    
    def test_success_result(self) -> None:
        """Test creating a successful result."""
        result = ConversionResult(
            success=True,
            source_path=Path("test.pdf"),
            output_path=Path("test.md"),
            elapsed_time=1.5,
            markdown_content="# Test"
        )
        
        assert result.success is True
        assert result.error_message is None
    
    def test_failure_result(self) -> None:
        """Test creating a failure result."""
        result = ConversionResult(
            success=False,
            source_path=Path("test.pdf"),
            error_message="Conversion failed"
        )
        
        assert result.success is False
        assert result.output_path is None


class TestBatchConversionResult:
    """Test cases for BatchConversionResult dataclass."""
    
    def test_empty_batch_result(self) -> None:
        """Test creating an empty batch result."""
        result = BatchConversionResult()
        
        assert result.total_files == 0
        assert result.successful == 0
        assert result.failed == 0
        assert len(result.results) == 0
    
    def test_batch_result_with_results(self) -> None:
        """Test creating a batch result with items."""
        result = BatchConversionResult(
            total_files=3,
            successful=2,
            failed=1,
            total_time=5.0,
            results=[
                ConversionResult(success=True, source_path=Path("a.pdf")),
                ConversionResult(success=True, source_path=Path("b.pdf")),
                ConversionResult(success=False, source_path=Path("c.pdf")),
            ]
        )
        
        assert result.total_files == 3
        assert result.successful == 2
        assert result.failed == 1
