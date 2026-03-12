"""
Converter Service Module.

This module provides the core conversion functionality using the markitdown library.
It handles file validation, conversion, and output generation.
"""

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

from markitdown import MarkItDown

from src.core.exceptions import (
    ConversionError,
    FileAccessError,
    OutputDirectoryError,
    UnsupportedFileError,
)
from src.core.image_processor import BaseImageProcessor, get_default_image_processor
from src.core.pdf_processor import PDFProcessor, is_pdf_processor_available
from src.core.post_processor import MarkdownPostProcessor, get_post_processor
from src.utils.logger import get_audit_logger, get_logger

logger = get_logger(__name__)
audit_logger = get_audit_logger()


@dataclass
class ConversionResult:
    """
    Result of a file conversion operation.

    Attributes:
        success: Whether the conversion was successful.
        source_path: Path to the source file.
        output_path: Path to the generated markdown file (if successful).
        elapsed_time: Time taken for conversion in seconds.
        error_message: Error description if conversion failed.
        markdown_content: The converted markdown content.
    """
    success: bool
    source_path: Path
    output_path: Optional[Path] = None
    elapsed_time: float = 0.0
    error_message: Optional[str] = None
    markdown_content: Optional[str] = None


@dataclass
class BatchConversionResult:
    """
    Result of a batch conversion operation.

    Attributes:
        total_files: Total number of files processed.
        successful: Number of successful conversions.
        failed: Number of failed conversions.
        results: List of individual conversion results.
        total_time: Total time taken for all conversions.
    """
    total_files: int = 0
    successful: int = 0
    failed: int = 0
    results: list[ConversionResult] = field(default_factory=list)
    total_time: float = 0.0


class ConverterService:
    """
    Service class for converting files to Markdown.

    This class encapsulates the markitdown library and provides a clean
    interface for file conversion operations.

    Attributes:
        SUPPORTED_EXTENSIONS: Tuple of supported file extensions.
    """
    
    SUPPORTED_EXTENSIONS: tuple[str, ...] = (
        # Documents
        ".pdf", ".docx", ".doc", ".pptx", ".ppt", ".xlsx", ".xls",
        # Web
        ".html", ".htm",
        # Text
        ".txt", ".rtf", ".csv", ".json", ".xml",
        # Images (basic support)
        ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".webp",
        # Audio (requires additional dependencies)
        ".mp3", ".wav", ".m4a",
        # Archives
        ".zip",
    )
    
    def __init__(
        self, 
        image_processor: Optional[BaseImageProcessor] = None,
        enable_llm_vision: bool = False,
        use_enhanced_pdf: bool = True,
    ) -> None:
        """
        Initialize the converter service.

        Args:
            image_processor: Custom image processor for handling images.
                If None, uses the default processor.
            enable_llm_vision: Whether to enable LLM-based vision for images.
                Requires API key configuration.
            use_enhanced_pdf: Whether to use enhanced PDF processing with
                pymupdf4llm for better table extraction. Defaults to True.
        """
        self._markitdown = MarkItDown()
        self._image_processor = image_processor or get_default_image_processor()
        self._post_processor = get_post_processor()
        self._enable_llm_vision = enable_llm_vision
        self._use_enhanced_pdf = use_enhanced_pdf and is_pdf_processor_available()
        self._pdf_processor = PDFProcessor() if self._use_enhanced_pdf else None
        
        logger.info(f"ConverterService initialized with image processor: "
                   f"{self._image_processor.name}")
        if self._use_enhanced_pdf:
            logger.info("Enhanced PDF processing enabled (pymupdf4llm)")
    
    @property
    def supported_extensions(self) -> tuple[str, ...]:
        """Return the list of supported file extensions."""
        return self.SUPPORTED_EXTENSIONS
    
    def is_supported(self, file_path: Path) -> bool:
        """
        Check if a file type is supported for conversion.

        Args:
            file_path: Path to the file to check.

        Returns:
            bool: True if the file type is supported, False otherwise.
        """
        return file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS
    
    def validate_file(self, file_path: Path) -> None:
        """
        Validate a file before conversion.

        Args:
            file_path: Path to the file to validate.

        Raises:
            FileAccessError: If the file doesn't exist or can't be read.
            UnsupportedFileError: If the file type is not supported.
        """
        if not file_path.exists():
            raise FileAccessError(file_path, "access (file not found)")
        
        if not file_path.is_file():
            raise FileAccessError(file_path, "access (not a file)")
        
        if not self.is_supported(file_path):
            raise UnsupportedFileError(file_path, list(self.SUPPORTED_EXTENSIONS))
    
    def validate_output_directory(self, output_dir: Path) -> None:
        """
        Validate and prepare the output directory.

        Args:
            output_dir: Path to the output directory.

        Raises:
            OutputDirectoryError: If the directory can't be created or accessed.
        """
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            raise OutputDirectoryError(output_dir, "Permission denied")
        except OSError as e:
            raise OutputDirectoryError(output_dir, str(e))
    
    def convert_file(
        self, 
        file_path: Path, 
        output_dir: Optional[Path] = None,
        save_to_file: bool = True
    ) -> ConversionResult:
        """
        Convert a single file to Markdown.

        Args:
            file_path: Path to the file to convert.
            output_dir: Directory where the output file will be saved.
                If None and save_to_file is True, saves in the same directory as source.
            save_to_file: Whether to save the result to a file.

        Returns:
            ConversionResult: The result of the conversion operation.

        Raises:
            ConversionError: If conversion fails critically.
        """
        start_time = time.time()
        
        try:
            # Validate input file
            self.validate_file(file_path)
            
            logger.info(f"Starting conversion for: {file_path.name}")
            
            # Determine output path
            output_path = None
            if save_to_file:
                if output_dir is None:
                    output_dir = file_path.parent
                self.validate_output_directory(output_dir)
                output_path = output_dir / f"{file_path.stem}.md"
            
            # Perform conversion
            # Use enhanced PDF processor for PDF files if available
            if file_path.suffix.lower() == ".pdf" and self._pdf_processor:
                logger.info(f"Using enhanced PDF processor for: {file_path.name}")
                markdown_content = self._pdf_processor.convert(file_path)
            else:
                result = self._markitdown.convert(str(file_path))
                markdown_content = result.text_content
                # Apply post-processing for non-PDF files
                markdown_content = self._post_processor.process(
                    markdown_content, 
                    file_path.suffix
                )
            
            # Check if it's an image and needs special processing
            if file_path.suffix.lower() in self._image_processor.SUPPORTED_FORMATS:
                image_result = self._image_processor.process_image(file_path)
                if image_result.success and image_result.text_content:
                    # Append OCR content if available
                    markdown_content = f"{markdown_content}\n\n## Extracted Text (OCR)\n\n{image_result.text_content}"
            
            # Save to file if requested
            if save_to_file and output_path:
                output_path.write_text(markdown_content, encoding="utf-8")
                logger.info(f"Saved conversion result to: {output_path}")
            
            elapsed = time.time() - start_time
            
            # Audit log
            audit_logger.info(
                f"SUCCESS | {file_path.name} -> {output_path.name if output_path else 'memory'} | "
                f"{elapsed:.2f}s | {len(markdown_content)} chars"
            )
            
            return ConversionResult(
                success=True,
                source_path=file_path,
                output_path=output_path,
                elapsed_time=elapsed,
                markdown_content=markdown_content
            )
            
        except UnsupportedFileError as e:
            elapsed = time.time() - start_time
            logger.warning(str(e))
            audit_logger.error(f"FAILED | {file_path.name} | UnsupportedFileError | {e.extension}")
            
            return ConversionResult(
                success=False,
                source_path=file_path,
                elapsed_time=elapsed,
                error_message=str(e)
            )
            
        except FileAccessError as e:
            elapsed = time.time() - start_time
            logger.error(str(e))
            audit_logger.error(f"FAILED | {file_path.name} | FileAccessError")
            
            return ConversionResult(
                success=False,
                source_path=file_path,
                elapsed_time=elapsed,
                error_message=str(e)
            )
            
        except Exception as e:
            elapsed = time.time() - start_time
            logger.critical(f"Conversion failed for {file_path.name}: {e}", exc_info=True)
            audit_logger.error(f"FAILED | {file_path.name} | {type(e).__name__} | {str(e)[:100]}")
            
            raise ConversionError(file_path, str(e), e)
    
    def convert_batch(
        self,
        files: list[Path],
        output_dir: Path,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
        error_callback: Optional[Callable[[Path, str], None]] = None
    ) -> BatchConversionResult:
        """
        Convert multiple files to Markdown.

        Args:
            files: List of file paths to convert.
            output_dir: Directory where output files will be saved.
            progress_callback: Callback function called after each file.
                Receives (current_index, total_files, current_file_name).
            error_callback: Callback function called when a file fails.
                Receives (file_path, error_message).

        Returns:
            BatchConversionResult: Summary of the batch conversion.
        """
        batch_result = BatchConversionResult(total_files=len(files))
        batch_start = time.time()
        
        logger.info(f"Starting batch conversion of {len(files)} files")
        
        for index, file_path in enumerate(files):
            try:
                # Report progress
                if progress_callback:
                    progress_callback(index + 1, len(files), file_path.name)
                
                # Convert file
                result = self.convert_file(file_path, output_dir)
                batch_result.results.append(result)
                
                if result.success:
                    batch_result.successful += 1
                else:
                    batch_result.failed += 1
                    if error_callback:
                        error_callback(file_path, result.error_message or "Unknown error")
                        
            except ConversionError as e:
                batch_result.failed += 1
                batch_result.results.append(ConversionResult(
                    success=False,
                    source_path=file_path,
                    error_message=str(e)
                ))
                if error_callback:
                    error_callback(file_path, str(e))
        
        batch_result.total_time = time.time() - batch_start
        
        logger.info(
            f"Batch conversion complete: {batch_result.successful}/{batch_result.total_files} "
            f"successful in {batch_result.total_time:.2f}s"
        )
        
        return batch_result


def get_supported_extensions_display() -> str:
    """
    Get a formatted string of supported extensions for display.

    Returns:
        str: Comma-separated list of supported extensions.
    """
    return ", ".join(ConverterService.SUPPORTED_EXTENSIONS)
