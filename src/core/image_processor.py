"""
Image Processor Module.

This module provides an abstract interface for image processing capabilities,
allowing for future integration of OCR engines like pytesseract.

The architecture follows the Strategy Pattern, enabling seamless swapping
of image processing implementations.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Protocol, runtime_checkable

from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ImageProcessingResult:
    """
    Result of an image processing operation.

    Attributes:
        success: Whether the processing was successful.
        text_content: Extracted text content, if any.
        image_path: Path to the processed image.
        processor_name: Name of the processor used.
        error_message: Error message if processing failed.
    """
    success: bool
    text_content: Optional[str]
    image_path: Path
    processor_name: str
    error_message: Optional[str] = None


@runtime_checkable
class ImageProcessor(Protocol):
    """
    Protocol defining the interface for image processors.

    This protocol allows for different implementations of image processing,
    such as OCR engines, to be used interchangeably.
    """
    
    @property
    def name(self) -> str:
        """Return the name of the image processor."""
        ...
    
    @property
    def is_available(self) -> bool:
        """Check if the processor is available and properly configured."""
        ...
    
    def process_image(self, image_path: Path) -> ImageProcessingResult:
        """
        Process an image and extract text content.

        Args:
            image_path: Path to the image file to process.

        Returns:
            ImageProcessingResult: The result of the processing operation.
        """
        ...
    
    def supports_format(self, file_extension: str) -> bool:
        """
        Check if the processor supports a specific image format.

        Args:
            file_extension: The file extension (e.g., '.png', '.jpg').

        Returns:
            bool: True if the format is supported, False otherwise.
        """
        ...


class BaseImageProcessor(ABC):
    """
    Abstract base class for image processors.

    Provides common functionality and defines the interface that all
    image processor implementations must follow.
    """
    
    SUPPORTED_FORMATS: tuple[str, ...] = (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".webp")
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of the image processor."""
        pass
    
    @property
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the processor is available and properly configured."""
        pass
    
    @abstractmethod
    def _extract_text(self, image_path: Path) -> str:
        """
        Internal method to extract text from an image.

        Args:
            image_path: Path to the image file.

        Returns:
            str: Extracted text content.

        Raises:
            ImageProcessingError: If text extraction fails.
        """
        pass
    
    def process_image(self, image_path: Path) -> ImageProcessingResult:
        """
        Process an image and extract text content.

        Args:
            image_path: Path to the image file to process.

        Returns:
            ImageProcessingResult: The result of the processing operation.
        """
        logger.info(f"Processing image: {image_path.name}")
        
        if not image_path.exists():
            return ImageProcessingResult(
                success=False,
                text_content=None,
                image_path=image_path,
                processor_name=self.name,
                error_message=f"Image file not found: {image_path}"
            )
        
        if not self.supports_format(image_path.suffix):
            return ImageProcessingResult(
                success=False,
                text_content=None,
                image_path=image_path,
                processor_name=self.name,
                error_message=f"Unsupported image format: {image_path.suffix}"
            )
        
        if not self.is_available:
            return ImageProcessingResult(
                success=False,
                text_content=None,
                image_path=image_path,
                processor_name=self.name,
                error_message=f"Processor '{self.name}' is not available"
            )
        
        try:
            text_content = self._extract_text(image_path)
            logger.info(f"Successfully processed image: {image_path.name}")
            return ImageProcessingResult(
                success=True,
                text_content=text_content,
                image_path=image_path,
                processor_name=self.name
            )
        except Exception as e:
            logger.error(f"Failed to process image {image_path.name}: {e}")
            return ImageProcessingResult(
                success=False,
                text_content=None,
                image_path=image_path,
                processor_name=self.name,
                error_message=str(e)
            )
    
    def supports_format(self, file_extension: str) -> bool:
        """
        Check if the processor supports a specific image format.

        Args:
            file_extension: The file extension (e.g., '.png', '.jpg').

        Returns:
            bool: True if the format is supported, False otherwise.
        """
        return file_extension.lower() in self.SUPPORTED_FORMATS


class PlaceholderImageProcessor(BaseImageProcessor):
    """
    Placeholder implementation that logs image detection without OCR.

    This implementation is used when no OCR engine is configured.
    It logs that an image was found but does not perform actual text extraction.
    """
    
    @property
    def name(self) -> str:
        """Return the name of the image processor."""
        return "PlaceholderProcessor"
    
    @property
    def is_available(self) -> bool:
        """Always available as it's a placeholder."""
        return True
    
    def _extract_text(self, image_path: Path) -> str:
        """
        Log that an image was detected (no actual OCR).

        Args:
            image_path: Path to the image file.

        Returns:
            str: Placeholder text indicating an image was found.
        """
        logger.info(f"[IMAGE DETECTED] Found image: {image_path.name} "
                   f"(Size: {image_path.stat().st_size / 1024:.2f} KB)")
        
        return f"![Image: {image_path.name}]({image_path.name})\n\n" \
               f"*[OCR not configured - Image content not extracted]*"


class TesseractImageProcessor(BaseImageProcessor):
    """
    Image processor using Tesseract OCR engine.

    This implementation uses pytesseract to extract text from images.
    Requires tesseract-ocr to be installed on the system.

    Note:
        To use this processor, install pytesseract:
        pip install pytesseract
        
        And install Tesseract OCR:
        - Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki
        - Linux: apt-get install tesseract-ocr
        - macOS: brew install tesseract
    """
    
    def __init__(self, tesseract_cmd: Optional[str] = None) -> None:
        """
        Initialize the Tesseract processor.

        Args:
            tesseract_cmd: Path to the tesseract executable.
                If None, uses the default system path.
        """
        self._tesseract_cmd = tesseract_cmd
        self._is_available: Optional[bool] = None
    
    @property
    def name(self) -> str:
        """Return the name of the image processor."""
        return "TesseractOCR"
    
    @property
    def is_available(self) -> bool:
        """Check if Tesseract is available."""
        if self._is_available is not None:
            return self._is_available
        
        try:
            import pytesseract
            
            if self._tesseract_cmd:
                pytesseract.pytesseract.tesseract_cmd = self._tesseract_cmd
            
            # Test if tesseract is accessible
            pytesseract.get_tesseract_version()
            self._is_available = True
            logger.info("Tesseract OCR is available")
        except ImportError:
            # Silently ignore if not installed to avoid scaring users
            self._is_available = False
        except Exception as e:
            logger.debug(f"Tesseract OCR is not configured: {e}")
            self._is_available = False
            
        return self._is_available
            
    def _extract_text(self, image_path: Path) -> str:
        """
        Extract text from an image using Tesseract OCR.
        
        Args:
            image_path: Path to the image file.

        Returns:
            str: Extracted text content.

        Raises:
            ImportError: If pytesseract is not installed.
            Exception: If OCR processing fails.
        """
        import pytesseract
        from PIL import Image
        
        if self._tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = self._tesseract_cmd
        
        with Image.open(image_path) as img:
            text = pytesseract.image_to_string(img)
        
        logger.info(f"Extracted {len(text)} characters from {image_path.name}")
        return text.strip()


def get_default_image_processor() -> BaseImageProcessor:
    """
    Get the default image processor based on system capabilities.

    Returns the Tesseract processor if available, otherwise falls back
    to the placeholder processor.

    Returns:
        BaseImageProcessor: The appropriate image processor instance.
    """
    tesseract = TesseractImageProcessor()
    
    if tesseract.is_available:
        logger.info("Using Tesseract OCR for image processing")
        return tesseract
    
    logger.info("Using placeholder image processor (no OCR)")
    return PlaceholderImageProcessor()
