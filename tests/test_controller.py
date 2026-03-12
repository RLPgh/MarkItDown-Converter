"""
Test suite for the Conversion Controller.

This module contains unit tests for the ConversionController class.
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.core.controller import (
    ConversionController,
    ConversionProgress,
    ConversionState,
    FileItem,
)


class TestFileItem:
    """Test cases for FileItem dataclass."""
    
    @pytest.fixture
    def temp_file(self) -> Path:
        """Create a temporary file for testing."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(b"test content")
            yield Path(f.name)
    
    def test_from_path_supported(self, temp_file: Path) -> None:
        """Test creating FileItem from supported file."""
        from src.core.converter import ConverterService
        converter = ConverterService()
        
        item = FileItem.from_path(temp_file, converter)
        
        assert item.path == temp_file
        assert item.name == temp_file.name
        assert item.extension == ".pdf"
        assert item.is_supported is True
        assert item.status == "pending"
    
    def test_file_item_defaults(self) -> None:
        """Test FileItem default values."""
        item = FileItem(
            path=Path("test.pdf"),
            name="test.pdf",
            size=1024,
            extension=".pdf"
        )
        
        assert item.is_supported is True
        assert item.status == "pending"
        assert item.error_message is None


class TestConversionProgress:
    """Test cases for ConversionProgress dataclass."""
    
    def test_default_progress(self) -> None:
        """Test default progress values."""
        progress = ConversionProgress()
        
        assert progress.current_file == ""
        assert progress.current_index == 0
        assert progress.total_files == 0
        assert progress.percentage == 0.0
    
    def test_progress_with_values(self) -> None:
        """Test progress with custom values."""
        progress = ConversionProgress(
            current_file="test.pdf",
            current_index=5,
            total_files=10,
            percentage=50.0,
            successful=4,
            failed=1
        )
        
        assert progress.current_file == "test.pdf"
        assert progress.percentage == 50.0


class TestConversionController:
    """Test cases for ConversionController."""
    
    @pytest.fixture
    def controller(self) -> ConversionController:
        """Create a ConversionController instance for testing."""
        return ConversionController()
    
    @pytest.fixture
    def temp_dir(self) -> Path:
        """Create a temporary directory for test files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    @pytest.fixture
    def sample_files(self, temp_dir: Path) -> list[Path]:
        """Create sample files for testing."""
        files = []
        for ext in [".txt", ".pdf", ".docx"]:
            file_path = temp_dir / f"test{ext}"
            file_path.write_text("test content")
            files.append(file_path)
        return files
    
    # ==================== State Tests ====================
    
    def test_initial_state(self, controller: ConversionController) -> None:
        """Test controller initial state."""
        assert controller.state == ConversionState.IDLE
        assert controller.has_files is False
        assert controller.is_ready is False
    
    def test_state_after_adding_files(
        self, 
        controller: ConversionController,
        sample_files: list[Path]
    ) -> None:
        """Test state after adding files."""
        controller.add_files(sample_files)
        
        assert controller.has_files is True
        assert controller.has_supported_files is True
    
    # ==================== File Management Tests ====================
    
    def test_add_files(
        self, 
        controller: ConversionController,
        sample_files: list[Path]
    ) -> None:
        """Test adding files to the queue."""
        added = controller.add_files(sample_files)
        
        assert added == len(sample_files)
        assert len(controller.files) == len(sample_files)
    
    def test_add_duplicate_files(
        self, 
        controller: ConversionController,
        sample_files: list[Path]
    ) -> None:
        """Test adding duplicate files is prevented."""
        controller.add_files(sample_files)
        added = controller.add_files(sample_files)  # Add again
        
        assert added == 0
        assert len(controller.files) == len(sample_files)
    
    def test_remove_file(
        self, 
        controller: ConversionController,
        sample_files: list[Path]
    ) -> None:
        """Test removing a file from the queue."""
        controller.add_files(sample_files)
        initial_count = len(controller.files)
        
        removed = controller.remove_file(sample_files[0])
        
        assert removed is True
        assert len(controller.files) == initial_count - 1
    
    def test_remove_nonexistent_file(
        self, 
        controller: ConversionController
    ) -> None:
        """Test removing a file that doesn't exist in queue."""
        removed = controller.remove_file(Path("/nonexistent/file.pdf"))
        
        assert removed is False
    
    def test_clear_files(
        self, 
        controller: ConversionController,
        sample_files: list[Path]
    ) -> None:
        """Test clearing all files."""
        controller.add_files(sample_files)
        controller.clear_files()
        
        assert controller.has_files is False
    
    # ==================== Output Directory Tests ====================
    
    def test_set_output_directory(
        self, 
        controller: ConversionController,
        temp_dir: Path
    ) -> None:
        """Test setting output directory."""
        result = controller.set_output_directory(temp_dir)
        
        assert result is True
        assert controller.output_directory == temp_dir
    
    def test_set_output_directory_creates_dir(
        self, 
        controller: ConversionController,
        temp_dir: Path
    ) -> None:
        """Test that setting output directory creates it if needed."""
        new_dir = temp_dir / "new_folder"
        
        result = controller.set_output_directory(new_dir)
        
        assert result is True
        assert new_dir.exists()
    
    # ==================== Ready State Tests ====================
    
    def test_is_ready_without_files(
        self, 
        controller: ConversionController,
        temp_dir: Path
    ) -> None:
        """Test is_ready is False without files."""
        controller.set_output_directory(temp_dir)
        
        assert controller.is_ready is False
    
    def test_is_ready_without_output_dir(
        self, 
        controller: ConversionController,
        sample_files: list[Path]
    ) -> None:
        """Test is_ready is False without output directory."""
        controller.add_files(sample_files)
        
        assert controller.is_ready is False
    
    def test_is_ready_complete(
        self, 
        controller: ConversionController,
        sample_files: list[Path],
        temp_dir: Path
    ) -> None:
        """Test is_ready is True when properly configured."""
        controller.add_files(sample_files)
        controller.set_output_directory(temp_dir)
        
        assert controller.is_ready is True
    
    # ==================== Callback Tests ====================
    
    def test_state_change_callback(
        self, 
        controller: ConversionController
    ) -> None:
        """Test state change callback is called."""
        callback = MagicMock()
        controller.set_on_state_change(callback)
        
        controller.reset()
        
        callback.assert_called()
    
    def test_log_message_callback(
        self, 
        controller: ConversionController,
        sample_files: list[Path]
    ) -> None:
        """Test log message callback is called."""
        callback = MagicMock()
        controller.set_on_log_message(callback)
        
        controller.add_files(sample_files)
        
        callback.assert_called()


class TestConversionState:
    """Test cases for ConversionState enum."""
    
    def test_all_states_exist(self) -> None:
        """Test all expected states exist."""
        assert ConversionState.IDLE is not None
        assert ConversionState.VALIDATING is not None
        assert ConversionState.CONVERTING is not None
        assert ConversionState.COMPLETED is not None
        assert ConversionState.ERROR is not None
        assert ConversionState.CANCELLED is not None
