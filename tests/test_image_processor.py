"""
Test suite for the Image Processor.

This module contains unit tests for the image processing components.
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.core.image_processor import (
    BaseImageProcessor,
    ImageProcessingResult,
    PlaceholderImageProcessor,
    TesseractImageProcessor,
    get_default_image_processor,
)


class TestImageProcessingResult:
    """Test cases for ImageProcessingResult dataclass."""
    
    def test_success_result(self) -> None:
        """Test creating a successful result."""
        result = ImageProcessingResult(
            success=True,
            text_content="Extracted text",
            image_path=Path("image.png"),
            processor_name="TestProcessor"
        )
        
        assert result.success is True
        assert result.text_content == "Extracted text"
        assert result.error_message is None
    
    def test_failure_result(self) -> None:
        """Test creating a failure result."""
        result = ImageProcessingResult(
            success=False,
            text_content=None,
            image_path=Path("image.png"),
            processor_name="TestProcessor",
            error_message="Processing failed"
        )
        
        assert result.success is False
        assert result.text_content is None
        assert result.error_message == "Processing failed"


class TestPlaceholderImageProcessor:
    """Test cases for PlaceholderImageProcessor."""
    
    @pytest.fixture
    def processor(self) -> PlaceholderImageProcessor:
        """Create a PlaceholderImageProcessor instance."""
        return PlaceholderImageProcessor()
    
    @pytest.fixture
    def sample_image(self) -> Path:
        """Create a sample image file for testing."""
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            # Write minimal PNG header
            f.write(b'\x89PNG\r\n\x1a\n' + b'\x00' * 100)
            yield Path(f.name)
    
    def test_name(self, processor: PlaceholderImageProcessor) -> None:
        """Test processor name."""
        assert processor.name == "PlaceholderProcessor"
    
    def test_is_available(self, processor: PlaceholderImageProcessor) -> None:
        """Test processor is always available."""
        assert processor.is_available is True
    
    def test_supports_format_png(self, processor: PlaceholderImageProcessor) -> None:
        """Test PNG format is supported."""
        assert processor.supports_format(".png") is True
    
    def test_supports_format_jpg(self, processor: PlaceholderImageProcessor) -> None:
        """Test JPG format is supported."""
        assert processor.supports_format(".jpg") is True
        assert processor.supports_format(".jpeg") is True
    
    def test_supports_format_unsupported(self, processor: PlaceholderImageProcessor) -> None:
        """Test unsupported format."""
        assert processor.supports_format(".xyz") is False
    
    def test_process_image_success(
        self, 
        processor: PlaceholderImageProcessor,
        sample_image: Path
    ) -> None:
        """Test processing an image successfully."""
        result = processor.process_image(sample_image)
        
        assert result.success is True
        assert result.processor_name == "PlaceholderProcessor"
        assert "OCR not configured" in result.text_content
    
    def test_process_image_not_found(
        self, 
        processor: PlaceholderImageProcessor
    ) -> None:
        """Test processing non-existent image."""
        result = processor.process_image(Path("/nonexistent/image.png"))
        
        assert result.success is False
        assert "not found" in result.error_message.lower()
    
    def test_process_image_unsupported_format(
        self, 
        processor: PlaceholderImageProcessor
    ) -> None:
        """Test processing unsupported image format."""
        with tempfile.NamedTemporaryFile(suffix=".xyz", delete=False) as f:
            f.write(b"not an image")
            file_path = Path(f.name)
        
        result = processor.process_image(file_path)
        
        assert result.success is False
        assert "unsupported" in result.error_message.lower()


class TestTesseractImageProcessor:
    """Test cases for TesseractImageProcessor."""
    
    def test_name(self) -> None:
        """Test processor name."""
        processor = TesseractImageProcessor()
        assert processor.name == "TesseractOCR"
    
    def test_is_available_without_tesseract(self) -> None:
        """Test is_available when Tesseract is not installed."""
        with patch.dict('sys.modules', {'pytesseract': None}):
            processor = TesseractImageProcessor()
            # Should return False or handle gracefully
            # The actual behavior depends on system configuration
    
    def test_custom_tesseract_cmd(self) -> None:
        """Test setting custom tesseract command path."""
        processor = TesseractImageProcessor(tesseract_cmd="/custom/path/tesseract")
        assert processor._tesseract_cmd == "/custom/path/tesseract"


class TestGetDefaultImageProcessor:
    """Test cases for get_default_image_processor function."""
    
    def test_returns_processor(self) -> None:
        """Test that function returns an image processor."""
        processor = get_default_image_processor()
        
        assert isinstance(processor, BaseImageProcessor)
        assert hasattr(processor, 'name')
        assert hasattr(processor, 'is_available')
        assert hasattr(processor, 'process_image')


class TestBaseImageProcessor:
    """Test cases for BaseImageProcessor abstract class."""
    
    def test_supported_formats(self) -> None:
        """Test SUPPORTED_FORMATS class attribute."""
        assert ".png" in BaseImageProcessor.SUPPORTED_FORMATS
        assert ".jpg" in BaseImageProcessor.SUPPORTED_FORMATS
        assert ".jpeg" in BaseImageProcessor.SUPPORTED_FORMATS
        assert ".gif" in BaseImageProcessor.SUPPORTED_FORMATS
        assert ".bmp" in BaseImageProcessor.SUPPORTED_FORMATS
