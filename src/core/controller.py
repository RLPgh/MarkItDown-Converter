"""
Conversion Controller Module.

This module provides the controller layer that orchestrates the conversion
process and manages communication between the UI and the core services.
"""

import threading
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Callable, Optional

from src.core.converter import BatchConversionResult, ConverterService, ConversionResult
from src.core.exceptions import ConversionError
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ConversionState(Enum):
    """Enum representing the current state of the conversion process."""
    IDLE = auto()
    VALIDATING = auto()
    CONVERTING = auto()
    COMPLETED = auto()
    ERROR = auto()
    CANCELLED = auto()


@dataclass
class FileItem:
    """
    Represents a file in the conversion queue.

    Attributes:
        path: Path to the file.
        name: Display name of the file.
        size: File size in bytes.
        extension: File extension.
        is_supported: Whether the file type is supported.
        status: Current conversion status.
        error_message: Error message if conversion failed.
    """
    path: Path
    name: str
    size: int
    extension: str
    is_supported: bool = True
    status: str = "pending"
    error_message: Optional[str] = None
    
    @classmethod
    def from_path(cls, file_path: Path, converter: ConverterService) -> "FileItem":
        """
        Create a FileItem from a file path.

        Args:
            file_path: Path to the file.
            converter: ConverterService instance to check support.

        Returns:
            FileItem: The created file item.
        """
        return cls(
            path=file_path,
            name=file_path.name,
            size=file_path.stat().st_size if file_path.exists() else 0,
            extension=file_path.suffix.lower(),
            is_supported=converter.is_supported(file_path)
        )


@dataclass
class ConversionProgress:
    """
    Progress information for the conversion process.

    Attributes:
        current_file: Name of the file currently being processed.
        current_index: Index of the current file (1-based).
        total_files: Total number of files to process.
        percentage: Overall progress percentage.
        successful: Number of successful conversions so far.
        failed: Number of failed conversions so far.
    """
    current_file: str = ""
    current_index: int = 0
    total_files: int = 0
    percentage: float = 0.0
    successful: int = 0
    failed: int = 0


class ConversionController:
    """
    Controller for managing file conversion operations.

    This class acts as an intermediary between the UI and the core
    conversion service, handling state management and threading.

    Attributes:
        state: Current state of the conversion process.
        files: List of files in the conversion queue.
        output_directory: Target directory for converted files.
    """
    
    def __init__(self) -> None:
        """Initialize the conversion controller."""
        self._converter = ConverterService()
        self._state = ConversionState.IDLE
        self._files: list[FileItem] = []
        self._output_directory: Optional[Path] = None
        self._conversion_thread: Optional[threading.Thread] = None
        self._cancel_requested = False
        
        # Callbacks
        self._on_state_change: Optional[Callable[[ConversionState], None]] = None
        self._on_progress: Optional[Callable[[ConversionProgress], None]] = None
        self._on_file_complete: Optional[Callable[[FileItem, ConversionResult], None]] = None
        self._on_batch_complete: Optional[Callable[[BatchConversionResult], None]] = None
        self._on_error: Optional[Callable[[str], None]] = None
        self._on_log_message: Optional[Callable[[str, str], None]] = None
        
        logger.info("ConversionController initialized")
    
    @property
    def state(self) -> ConversionState:
        """Get the current conversion state."""
        return self._state
    
    @property
    def files(self) -> list[FileItem]:
        """Get the list of files in the queue."""
        return self._files.copy()
    
    @property
    def output_directory(self) -> Optional[Path]:
        """Get the current output directory."""
        return self._output_directory
    
    @property
    def supported_extensions(self) -> tuple[str, ...]:
        """Get the list of supported file extensions."""
        return self._converter.supported_extensions
    
    @property
    def has_files(self) -> bool:
        """Check if there are files in the queue."""
        return len(self._files) > 0
    
    @property
    def has_supported_files(self) -> bool:
        """Check if there are supported files in the queue."""
        return any(f.is_supported for f in self._files)
    
    @property
    def is_ready(self) -> bool:
        """Check if ready to start conversion."""
        return (
            self.has_supported_files and 
            self._output_directory is not None and
            self._state == ConversionState.IDLE
        )
    
    # ==================== Callback Registration ====================
    
    def set_on_state_change(self, callback: Callable[[ConversionState], None]) -> None:
        """Set callback for state changes."""
        self._on_state_change = callback
    
    def set_on_progress(self, callback: Callable[[ConversionProgress], None]) -> None:
        """Set callback for progress updates."""
        self._on_progress = callback
    
    def set_on_file_complete(
        self, 
        callback: Callable[[FileItem, ConversionResult], None]
    ) -> None:
        """Set callback for individual file completion."""
        self._on_file_complete = callback
    
    def set_on_batch_complete(
        self, 
        callback: Callable[[BatchConversionResult], None]
    ) -> None:
        """Set callback for batch completion."""
        self._on_batch_complete = callback
    
    def set_on_error(self, callback: Callable[[str], None]) -> None:
        """Set callback for errors."""
        self._on_error = callback
    
    def set_on_log_message(self, callback: Callable[[str, str], None]) -> None:
        """Set callback for log messages (level, message)."""
        self._on_log_message = callback
    
    # ==================== State Management ====================
    
    def _set_state(self, new_state: ConversionState) -> None:
        """
        Update the conversion state and notify listeners.

        Args:
            new_state: The new state to set.
        """
        old_state = self._state
        self._state = new_state
        logger.info(f"State changed: {old_state.name} -> {new_state.name}")
        
        if self._on_state_change:
            self._on_state_change(new_state)
    
    def _log(self, level: str, message: str) -> None:
        """
        Log a message and notify the UI.

        Args:
            level: Log level (info, warning, error).
            message: The message to log.
        """
        getattr(logger, level)(message)
        if self._on_log_message:
            self._on_log_message(level, message)
    
    # ==================== File Management ====================
    
    def add_files(self, file_paths: list[Path]) -> int:
        """
        Add files to the conversion queue.

        Args:
            file_paths: List of file paths to add.

        Returns:
            int: Number of files successfully added.
        """
        added = 0
        
        for file_path in file_paths:
            # Skip if already in queue
            if any(f.path == file_path for f in self._files):
                self._log("warning", f"File already in queue: {file_path.name}")
                continue
            
            # Skip if not a file
            if not file_path.is_file():
                self._log("warning", f"Not a file: {file_path}")
                continue
            
            file_item = FileItem.from_path(file_path, self._converter)
            self._files.append(file_item)
            added += 1
            
            if file_item.is_supported:
                self._log("info", f"Added: {file_item.name}")
            else:
                self._log("warning", f"Added (unsupported): {file_item.name}")
        
        return added
    
    def remove_file(self, file_path: Path) -> bool:
        """
        Remove a file from the conversion queue.

        Args:
            file_path: Path of the file to remove.

        Returns:
            bool: True if file was removed, False if not found.
        """
        for i, file_item in enumerate(self._files):
            if file_item.path == file_path:
                del self._files[i]
                self._log("info", f"Removed: {file_item.name}")
                return True
        return False
    
    def clear_files(self) -> None:
        """Clear all files from the queue."""
        self._files.clear()
        self._log("info", "File queue cleared")
    
    def set_output_directory(self, directory: Path) -> bool:
        """
        Set the output directory for converted files.

        Args:
            directory: Path to the output directory.

        Returns:
            bool: True if directory is valid, False otherwise.
        """
        try:
            directory.mkdir(parents=True, exist_ok=True)
            self._output_directory = directory
            self._log("info", f"Output directory set: {directory}")
            return True
        except Exception as e:
            self._log("error", f"Invalid output directory: {e}")
            if self._on_error:
                self._on_error(f"Cannot set output directory: {e}")
            return False
    
    # ==================== Conversion Operations ====================
    
    def start_conversion(self) -> bool:
        """
        Start the batch conversion process.

        Returns:
            bool: True if conversion started, False if not ready.
        """
        if not self.is_ready:
            self._log("error", "Not ready to start conversion")
            return False
        
        if self._conversion_thread and self._conversion_thread.is_alive():
            self._log("warning", "Conversion already in progress")
            return False
        
        self._cancel_requested = False
        self._conversion_thread = threading.Thread(
            target=self._run_conversion,
            daemon=True
        )
        self._conversion_thread.start()
        
        return True
    
    def cancel_conversion(self) -> None:
        """Request cancellation of the current conversion."""
        if self._state == ConversionState.CONVERTING:
            self._cancel_requested = True
            self._log("info", "Cancellation requested...")
    
    def _run_conversion(self) -> None:
        """
        Execute the batch conversion in a background thread.

        This method runs in a separate thread to prevent UI freezing.
        """
        self._set_state(ConversionState.CONVERTING)
        
        # Filter to only supported files
        files_to_convert = [f for f in self._files if f.is_supported]
        total_files = len(files_to_convert)
        
        if total_files == 0:
            self._log("warning", "No supported files to convert")
            self._set_state(ConversionState.IDLE)
            return
        
        self._log("info", f"Starting conversion of {total_files} files...")
        
        progress = ConversionProgress(total_files=total_files)
        successful = 0
        failed = 0
        results: list[ConversionResult] = []
        
        for index, file_item in enumerate(files_to_convert):
            # Check for cancellation
            if self._cancel_requested:
                self._log("info", "Conversion cancelled by user")
                self._set_state(ConversionState.CANCELLED)
                return
            
            # Update progress
            progress.current_file = file_item.name
            progress.current_index = index + 1
            progress.percentage = ((index + 1) / total_files) * 100
            progress.successful = successful
            progress.failed = failed
            
            if self._on_progress:
                self._on_progress(progress)
            
            # Perform conversion
            try:
                file_item.status = "converting"
                result = self._converter.convert_file(
                    file_item.path, 
                    self._output_directory
                )
                results.append(result)
                
                if result.success:
                    file_item.status = "completed"
                    successful += 1
                    self._log("info", f"✓ Converted: {file_item.name}")
                else:
                    file_item.status = "failed"
                    file_item.error_message = result.error_message
                    failed += 1
                    self._log("error", f"✗ Failed: {file_item.name} - {result.error_message}")
                
                if self._on_file_complete:
                    self._on_file_complete(file_item, result)
                    
            except ConversionError as e:
                file_item.status = "failed"
                file_item.error_message = str(e)
                failed += 1
                results.append(ConversionResult(
                    success=False,
                    source_path=file_item.path,
                    error_message=str(e)
                ))
                self._log("error", f"✗ Error: {file_item.name} - {e}")
        
        # Update final progress
        progress.percentage = 100.0
        progress.successful = successful
        progress.failed = failed
        
        if self._on_progress:
            self._on_progress(progress)
        
        # Create batch result
        batch_result = BatchConversionResult(
            total_files=total_files,
            successful=successful,
            failed=failed,
            results=results
        )
        
        if self._on_batch_complete:
            self._on_batch_complete(batch_result)
        
        self._log(
            "info", 
            f"Conversion complete: {successful}/{total_files} successful"
        )
        
        self._set_state(ConversionState.COMPLETED)
    
    def reset(self) -> None:
        """Reset the controller to initial state."""
        if self._state == ConversionState.CONVERTING:
            self.cancel_conversion()
            if self._conversion_thread:
                self._conversion_thread.join(timeout=2.0)
        
        self._files.clear()
        self._output_directory = None
        self._cancel_requested = False
        self._set_state(ConversionState.IDLE)
        
        self._log("info", "Controller reset")
