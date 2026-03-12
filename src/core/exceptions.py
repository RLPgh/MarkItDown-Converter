"""
Custom Exceptions Module.

This module defines all custom exceptions used throughout the
MarkItDown Converter application.
"""

from pathlib import Path
from typing import Optional


class MarkItDownConverterError(Exception):
    """Base exception for all MarkItDown Converter errors."""
    
    def __init__(self, message: str, original_error: Optional[Exception] = None) -> None:
        """
        Initialize the base exception.

        Args:
            message: Human-readable error description.
            original_error: The original exception that caused this error, if any.
        """
        super().__init__(message)
        self.message = message
        self.original_error = original_error


class UnsupportedFileError(MarkItDownConverterError):
    """Raised when a file type is not supported for conversion."""
    
    def __init__(self, file_path: Path, supported_extensions: Optional[list[str]] = None) -> None:
        """
        Initialize the unsupported file error.

        Args:
            file_path: Path to the unsupported file.
            supported_extensions: List of supported file extensions for reference.
        """
        self.file_path = file_path
        self.extension = file_path.suffix.lower()
        self.supported_extensions = supported_extensions or []
        
        message = f"File type '{self.extension}' is not supported: {file_path.name}"
        if self.supported_extensions:
            message += f". Supported types: {', '.join(self.supported_extensions)}"
        
        super().__init__(message)


class ConversionError(MarkItDownConverterError):
    """Raised when file conversion fails."""
    
    def __init__(
        self, 
        file_path: Path, 
        reason: str,
        original_error: Optional[Exception] = None
    ) -> None:
        """
        Initialize the conversion error.

        Args:
            file_path: Path to the file that failed to convert.
            reason: Human-readable reason for the failure.
            original_error: The original exception that caused the failure.
        """
        self.file_path = file_path
        self.reason = reason
        
        message = f"Conversion failed for '{file_path.name}': {reason}"
        super().__init__(message, original_error)


class FileAccessError(MarkItDownConverterError):
    """Raised when a file cannot be accessed or read."""
    
    def __init__(self, file_path: Path, operation: str = "access") -> None:
        """
        Initialize the file access error.

        Args:
            file_path: Path to the inaccessible file.
            operation: The operation that failed (e.g., 'read', 'write', 'access').
        """
        self.file_path = file_path
        self.operation = operation
        
        message = f"Cannot {operation} file: {file_path}"
        super().__init__(message)


class OutputDirectoryError(MarkItDownConverterError):
    """Raised when there's an issue with the output directory."""
    
    def __init__(self, directory: Path, reason: str) -> None:
        """
        Initialize the output directory error.

        Args:
            directory: Path to the problematic directory.
            reason: Human-readable reason for the error.
        """
        self.directory = directory
        self.reason = reason
        
        message = f"Output directory error at '{directory}': {reason}"
        super().__init__(message)


class ImageProcessingError(MarkItDownConverterError):
    """Raised when image processing/OCR fails."""
    
    def __init__(
        self, 
        image_path: Path, 
        reason: str,
        original_error: Optional[Exception] = None
    ) -> None:
        """
        Initialize the image processing error.

        Args:
            image_path: Path to the image that failed processing.
            reason: Human-readable reason for the failure.
            original_error: The original exception that caused the failure.
        """
        self.image_path = image_path
        self.reason = reason
        
        message = f"Image processing failed for '{image_path.name}': {reason}"
        super().__init__(message, original_error)
