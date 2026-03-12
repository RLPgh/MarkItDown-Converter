"""Core package initialization."""

from src.core.controller import ConversionController, ConversionProgress, ConversionState, FileItem
from src.core.converter import (
    BatchConversionResult,
    ConverterService,
    ConversionResult,
    get_supported_extensions_display,
)
from src.core.exceptions import (
    ConversionError,
    FileAccessError,
    ImageProcessingError,
    MarkItDownConverterError,
    OutputDirectoryError,
    UnsupportedFileError,
)
from src.core.image_processor import (
    BaseImageProcessor,
    ImageProcessingResult,
    PlaceholderImageProcessor,
    TesseractImageProcessor,
    get_default_image_processor,
)

__all__ = [
    # Controller
    "ConversionController",
    "ConversionProgress",
    "ConversionState",
    "FileItem",
    # Converter
    "ConverterService",
    "ConversionResult",
    "BatchConversionResult",
    "get_supported_extensions_display",
    # Exceptions
    "MarkItDownConverterError",
    "UnsupportedFileError",
    "ConversionError",
    "FileAccessError",
    "OutputDirectoryError",
    "ImageProcessingError",
    # Image Processing
    "BaseImageProcessor",
    "ImageProcessingResult",
    "PlaceholderImageProcessor",
    "TesseractImageProcessor",
    "get_default_image_processor",
]
