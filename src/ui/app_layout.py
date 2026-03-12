"""
Application Layout Module.

This module provides the main Flet UI components for the MarkItDown Converter
application, including drag-and-drop support, file selection, and progress tracking.
"""

from pathlib import Path
from typing import Callable, Optional

import flet as ft

from src.core.controller import (
    ConversionController,
    ConversionProgress,
    ConversionState,
    FileItem,
)
from src.core.converter import BatchConversionResult, ConversionResult, ConverterService
from src.utils.logger import get_logger
from src.__version__ import __version__

logger = get_logger(__name__)


def _format_size(size_bytes: int) -> str:
    """Format file size for display."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def create_file_list_item(
    file_item: FileItem,
    on_remove: Callable[[Path], None]
) -> ft.Container:
    """
    Create a file list item control.

    Args:
        file_item: The file item data.
        on_remove: Callback when remove button is clicked.

    Returns:
        ft.Container: The file list item control.
    """
    # Status icons
    status_icons = {
        "pending": ft.Icon(ft.Icons.HOURGLASS_EMPTY, color=ft.Colors.GREY_400, size=20),
        "converting": ft.Icon(ft.Icons.SYNC, color=ft.Colors.BLUE_400, size=20),
        "completed": ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN_400, size=20),
        "failed": ft.Icon(ft.Icons.ERROR, color=ft.Colors.RED_400, size=20),
    }
    status_icon = status_icons.get(
        file_item.status, 
        ft.Icon(ft.Icons.HELP, color=ft.Colors.GREY_400, size=20)
    )

    # File type icon based on extension
    ext_icons = {
        ".pdf": ft.Icons.PICTURE_AS_PDF,
        ".docx": ft.Icons.DESCRIPTION,
        ".doc": ft.Icons.DESCRIPTION,
        ".xlsx": ft.Icons.TABLE_CHART,
        ".xls": ft.Icons.TABLE_CHART,
        ".pptx": ft.Icons.SLIDESHOW,
        ".ppt": ft.Icons.SLIDESHOW,
        ".html": ft.Icons.CODE,
        ".htm": ft.Icons.CODE,
        ".txt": ft.Icons.TEXT_SNIPPET,
        ".png": ft.Icons.IMAGE,
        ".jpg": ft.Icons.IMAGE,
        ".jpeg": ft.Icons.IMAGE,
    }
    
    file_icon = ext_icons.get(
        file_item.extension.lower(), 
        ft.Icons.INSERT_DRIVE_FILE
    )
    
    # Determine colors based on support status
    text_color = ft.Colors.WHITE if file_item.is_supported else ft.Colors.GREY_500
    bg_color = ft.Colors.with_opacity(0.1, ft.Colors.WHITE) if file_item.is_supported else ft.Colors.with_opacity(0.05, ft.Colors.RED)
    
    return ft.Container(
        content=ft.Row(
            controls=[
                ft.Icon(file_icon, color=text_color, size=24),
                ft.Column(
                    controls=[
                        ft.Text(
                            file_item.name,
                            color=text_color,
                            size=14,
                            weight=ft.FontWeight.W_500,
                            max_lines=1,
                            overflow=ft.TextOverflow.ELLIPSIS,
                        ),
                        ft.Text(
                            _format_size(file_item.size) + 
                            (f" • {file_item.error_message}" if file_item.error_message else ""),
                            color=ft.Colors.GREY_500 if file_item.is_supported else ft.Colors.RED_300,
                            size=12,
                        ),
                    ],
                    spacing=2,
                    expand=True,
                ),
                status_icon,
                ft.IconButton(
                    icon=ft.Icons.CLOSE,
                    icon_color=ft.Colors.GREY_400,
                    icon_size=18,
                    on_click=lambda _: on_remove(file_item.path),
                    tooltip="Remove file",
                ),
            ],
            spacing=12,
            alignment=ft.MainAxisAlignment.START,
        ),
        padding=ft.padding.symmetric(horizontal=16, vertical=12),
        bgcolor=bg_color,
        border_radius=8,
        margin=ft.margin.only(bottom=8),
    )


class MarkItDownApp:
    """
    Main application class for MarkItDown Converter.

    This class manages the Flet UI and coordinates with the ConversionController.
    """
    
    def __init__(self, page: ft.Page) -> None:
        """
        Initialize the application.

        Args:
            page: The Flet page instance.
        """
        self.page = page
        self.controller = ConversionController()
        
        # UI References
        self.file_list: Optional[ft.Column] = None
        self.progress_bar: Optional[ft.ProgressBar] = None
        self.progress_text: Optional[ft.Text] = None
        self.log_list: Optional[ft.ListView] = None
        self.convert_button: Optional[ft.ElevatedButton] = None
        self.output_path_text: Optional[ft.Text] = None
        self.stats_row: Optional[ft.Row] = None
        
        # File pickers
        self.file_picker = ft.FilePicker(on_result=self._on_files_picked)
        self.folder_picker = ft.FilePicker(on_result=self._on_folder_picked)
        self.scan_folder_picker = ft.FilePicker(on_result=self._on_scan_folder_picked)
        
        self._setup_page()
        self._setup_callbacks()
    
    def _setup_page(self) -> None:
        """Configure the page settings."""
        self.page.title = "MarkItDown Converter"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.bgcolor = "#1a1a2e"
        self.page.padding = 0
        self.page.window.width = 900
        self.page.window.height = 700
        self.page.window.min_width = 700
        self.page.window.min_height = 500
        
        # Add file pickers to overlay
        self.page.overlay.extend([self.file_picker, self.folder_picker, self.scan_folder_picker])
    
    def _setup_callbacks(self) -> None:
        """Set up controller callbacks."""
        self.controller.set_on_state_change(self._on_state_change)
        self.controller.set_on_progress(self._on_progress_update)
        self.controller.set_on_file_complete(self._on_file_complete)
        self.controller.set_on_batch_complete(self._on_batch_complete)
        self.controller.set_on_log_message(self._on_log_message)
        self.controller.set_on_error(self._on_error)
    
    def build(self) -> ft.Control:
        """Build and return the main application layout."""
        return ft.Container(
            content=ft.Column(
                controls=[
                    self._build_header(),
                    ft.Divider(height=1, color=ft.Colors.with_opacity(0.2, ft.Colors.WHITE)),
                    ft.Row(
                        controls=[
                            self._build_left_panel(),
                            ft.VerticalDivider(width=1, color=ft.Colors.with_opacity(0.2, ft.Colors.WHITE)),
                            self._build_right_panel(),
                        ],
                        expand=True,
                        spacing=0,
                    ),
                ],
                spacing=0,
                expand=True,
            ),
            expand=True,
            bgcolor="#1a1a2e",
        )
    
    def _build_header(self) -> ft.Control:
        """Build the application header."""
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.TRANSFORM, color=ft.Colors.BLUE_400, size=32),
                    ft.Text(
                        "MarkItDown Converter",
                        size=24,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.WHITE,
                    ),
                    ft.Container(expand=True),
                    ft.Text(
                        f"v{__version__}",
                        size=12,
                        color=ft.Colors.GREY_500,
                        tooltip="Powered by Microsoft markitdown + pymupdf4llm",
                    ),
                ],
                alignment=ft.MainAxisAlignment.START,
            ),
            padding=ft.padding.symmetric(horizontal=24, vertical=16),
            bgcolor="#16213e",
        )
    
    def _build_left_panel(self) -> ft.Control:
        """Build the left panel with file list and controls."""
        # Drop zone / File list
        self.file_list = ft.Column(
            controls=[],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
            spacing=0,
            visible=False,
        )
        
        # Empty state / Drop zone
        self.empty_state = ft.Column(
            controls=[
                ft.Icon(ft.Icons.CLOUD_UPLOAD, size=64, color=ft.Colors.GREY_600),
                ft.Text(
                    "Click 'Add Files' to select documents",
                    size=18,
                    color=ft.Colors.GREY_500,
                    weight=ft.FontWeight.W_500,
                ),
                ft.Text(
                    "Supports multiple file selection",
                    size=14,
                    color=ft.Colors.GREY_600,
                ),
                ft.Container(height=16),
                ft.Text(
                    "PDF, DOCX, XLSX, PPTX, HTML, TXT, Images...",
                    size=12,
                    color=ft.Colors.GREY_700,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Text(
                    "No limit on number of files per batch",
                    size=11,
                    color=ft.Colors.BLUE_400,
                    text_align=ft.TextAlign.CENTER,
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True,
        )
        
        file_area = ft.Container(
            content=ft.Stack(
                controls=[
                    self.empty_state,
                    self.file_list,
                ],
                expand=True,
            ),
            expand=True,
            border=ft.border.all(2, ft.Colors.with_opacity(0.3, ft.Colors.BLUE_400)),
            border_radius=12,
            padding=16,
            bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.BLUE_400),
        )
        
        # Stats row
        self.stats_row = ft.Row(
            controls=[
                ft.Text("0 files", size=12, color=ft.Colors.GREY_500),
                ft.Container(expand=True),
                ft.TextButton(
                    "Clear All",
                    on_click=self._on_clear_files,
                    style=ft.ButtonStyle(color=ft.Colors.GREY_500),
                ),
            ],
            visible=False,
        )
        
        # Source buttons (add files)
        source_buttons_row = ft.Row(
            controls=[
                ft.ElevatedButton(
                    "Add Files",
                    icon=ft.Icons.NOTE_ADD,
                    on_click=self._on_add_files_click,
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.BLUE_700,
                        color=ft.Colors.WHITE,
                    ),
                    tooltip="Select individual files to convert",
                ),
                ft.ElevatedButton(
                    "Scan Folder",
                    icon=ft.Icons.FOLDER_COPY,
                    on_click=self._on_scan_folder_click,
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.BLUE_700,
                        color=ft.Colors.WHITE,
                    ),
                    tooltip="Scan a folder for all supported files",
                ),
            ],
            spacing=12,
        )
        
        # Output folder button (destination)
        output_button_row = ft.Row(
            controls=[
                ft.ElevatedButton(
                    "Output Folder",
                    icon=ft.Icons.SAVE,
                    on_click=self._on_select_output_click,
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.ORANGE_800,
                        color=ft.Colors.WHITE,
                    ),
                    tooltip="Select where to save converted Markdown files",
                ),
            ],
        )
        
        # Output directory display
        self.output_path_text = ft.Text(
            "No output folder selected",
            size=12,
            color=ft.Colors.GREY_500,
            max_lines=1,
            overflow=ft.TextOverflow.ELLIPSIS,
        )
        
        output_row = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.FOLDER, size=16, color=ft.Colors.GREY_500),
                    self.output_path_text,
                ],
                spacing=8,
            ),
            padding=ft.padding.symmetric(horizontal=12, vertical=8),
            bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.WHITE),
            border_radius=8,
        )
        
        # Progress section
        self.progress_bar = ft.ProgressBar(
            value=0,
            bgcolor=ft.Colors.GREY_800,
            color=ft.Colors.BLUE_400,
            visible=False,
        )
        
        self.progress_text = ft.Text(
            "",
            size=12,
            color=ft.Colors.GREY_400,
            visible=False,
        )
        
        # Convert button - wrapped in Row to control width properly
        self.convert_button = ft.ElevatedButton(
            "Convert to Markdown",
            icon=ft.Icons.PLAY_ARROW,
            on_click=self._on_convert_click,
            disabled=True,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.GREEN_700,
                color=ft.Colors.WHITE,
            ),
            height=44,
            width=250,
        )
        
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Container(
                        content=file_area,
                        expand=True,
                    ),
                    self.stats_row,
                    ft.Container(height=8),
                    source_buttons_row,
                    ft.Container(height=12),
                    output_button_row,
                    ft.Container(height=4),
                    output_row,
                    ft.Container(height=8),
                    self.progress_bar,
                    self.progress_text,
                    ft.Container(height=8),
                    self.convert_button,
                ],
                spacing=0,
                expand=True,
            ),
            padding=24,
            expand=2,
            bgcolor="#1a1a2e",
        )
    
    def _build_right_panel(self) -> ft.Control:
        """Build the right panel with logs."""
        self.log_list = ft.ListView(
            controls=[],
            expand=True,
            spacing=4,
            auto_scroll=True,
        )
        
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.TERMINAL, size=18, color=ft.Colors.GREY_500),
                            ft.Text(
                                "Conversion Log",
                                size=14,
                                weight=ft.FontWeight.W_500,
                                color=ft.Colors.GREY_400,
                            ),
                            ft.Container(expand=True),
                            ft.IconButton(
                                icon=ft.Icons.DELETE_SWEEP,
                                icon_size=18,
                                icon_color=ft.Colors.GREY_600,
                                tooltip="Clear logs",
                                on_click=self._on_clear_logs,
                            ),
                        ],
                    ),
                    ft.Divider(height=1, color=ft.Colors.with_opacity(0.1, ft.Colors.WHITE)),
                    ft.Container(
                        content=self.log_list,
                        expand=True,
                        bgcolor=ft.Colors.with_opacity(0.3, ft.Colors.BLACK),
                        border_radius=8,
                        padding=12,
                    ),
                ],
                spacing=8,
                expand=True,
            ),
            padding=24,
            expand=1,
            bgcolor="#16213e",
        )
    
    # ==================== Event Handlers ====================
    
    def _on_add_files_click(self, e: ft.ControlEvent) -> None:
        """Handle add files button click."""
        # No usamos allowed_extensions porque Flet tiene problemas con el filtro
        # La validación se hace después en el controller
        self.file_picker.pick_files(
            allow_multiple=True,
            file_type=ft.FilePickerFileType.ANY,
        )
    
    def _on_scan_folder_click(self, e: ft.ControlEvent) -> None:
        """Handle scan folder button click - opens folder picker for scanning."""
        self.scan_folder_picker.get_directory_path()
    
    def _on_select_output_click(self, e: ft.ControlEvent) -> None:
        """Handle select output folder button click."""
        self.folder_picker.get_directory_path()
    
    def _on_files_picked(self, e: ft.FilePickerResultEvent) -> None:
        """Handle file picker result."""
        if e.files:
            paths = [Path(f.path) for f in e.files if f.path]
            self.controller.add_files(paths)
            self._update_file_list()
    
    def _on_scan_folder_picked(self, e: ft.FilePickerResultEvent) -> None:
        """Handle scan folder picker result - scans folder for supported files."""
        if e.path:
            folder_path = Path(e.path)
            supported_extensions = ConverterService.SUPPORTED_EXTENSIONS
            
            # Scan folder recursively for supported files
            found_files: list[Path] = []
            for ext in supported_extensions:
                found_files.extend(folder_path.rglob(f"*{ext}"))
            
            if found_files:
                self.controller.add_files(found_files)
                self._update_file_list()
                self._on_log_message("info", f"Scanned folder: {folder_path.name}")
                self._on_log_message("info", f"Found {len(found_files)} supported files")
            else:
                self._on_log_message("warning", f"No supported files found in {folder_path.name}")
                self.page.update()
    
    def _on_folder_picked(self, e: ft.FilePickerResultEvent) -> None:
        """Handle folder picker result."""
        if e.path:
            if self.controller.set_output_directory(Path(e.path)):
                self.output_path_text.value = e.path
                self.output_path_text.color = ft.Colors.GREEN_400
                self._update_convert_button()
                self.page.update()
    
    def _on_convert_click(self, e: ft.ControlEvent) -> None:
        """Handle convert button click."""
        if self.controller.state == ConversionState.CONVERTING:
            self.controller.cancel_conversion()
            self.convert_button.text = "Cancelling..."
            self.convert_button.disabled = True
        else:
            self.controller.start_conversion()
    
    def _on_clear_files(self, e: ft.ControlEvent) -> None:
        """Handle clear files button click."""
        self.controller.clear_files()
        self._update_file_list()
    
    def _on_clear_logs(self, e: ft.ControlEvent) -> None:
        """Handle clear logs button click."""
        self.log_list.controls.clear()
        self.page.update()
    
    # ==================== Controller Callbacks ====================
    
    def _on_state_change(self, state: ConversionState) -> None:
        """Handle controller state change."""
        if state == ConversionState.CONVERTING:
            self.convert_button.text = "Cancel"
            self.convert_button.icon = ft.Icons.STOP
            self.convert_button.style = ft.ButtonStyle(
                bgcolor=ft.Colors.RED_700,
                color=ft.Colors.WHITE,
            )
            self.convert_button.disabled = False
            self.progress_bar.visible = True
            self.progress_text.visible = True
            
        elif state == ConversionState.COMPLETED:
            self.convert_button.text = "Convert to Markdown"
            self.convert_button.icon = ft.Icons.PLAY_ARROW
            self.convert_button.style = ft.ButtonStyle(
                bgcolor=ft.Colors.GREEN_700,
                color=ft.Colors.WHITE,
            )
            self._update_convert_button()
            
        elif state == ConversionState.CANCELLED:
            self.convert_button.text = "Convert to Markdown"
            self.convert_button.icon = ft.Icons.PLAY_ARROW
            self.convert_button.style = ft.ButtonStyle(
                bgcolor=ft.Colors.GREEN_700,
                color=ft.Colors.WHITE,
            )
            self._update_convert_button()
            self.progress_bar.value = 0
            
        elif state == ConversionState.IDLE:
            self.progress_bar.visible = False
            self.progress_text.visible = False
            self.progress_bar.value = 0
            self._update_convert_button()
        
        self.page.update()
    
    def _on_progress_update(self, progress: ConversionProgress) -> None:
        """Handle progress update from controller."""
        self.progress_bar.value = progress.percentage / 100
        self.progress_text.value = (
            f"Processing {progress.current_index}/{progress.total_files}: "
            f"{progress.current_file} ({progress.successful}✓ {progress.failed}✗)"
        )
        self.page.update()
    
    def _on_file_complete(self, file_item: FileItem, result: ConversionResult) -> None:
        """Handle individual file completion."""
        self._update_file_list()
    
    def _on_batch_complete(self, result: BatchConversionResult) -> None:
        """Handle batch conversion completion."""
        import subprocess
        import sys
        
        # Show summary dialog
        def close_dialog(e: ft.ControlEvent) -> None:
            dialog.open = False
            self.page.update()
        
        def open_output_folder(e: ft.ControlEvent) -> None:
            """Open the output folder in file explorer."""
            dialog.open = False
            self.page.update()
            if self.controller.output_directory:
                if sys.platform == "win32":
                    subprocess.Popen(["explorer", str(self.controller.output_directory)])
                elif sys.platform == "darwin":
                    subprocess.Popen(["open", str(self.controller.output_directory)])
                else:
                    subprocess.Popen(["xdg-open", str(self.controller.output_directory)])
        
        # Build result summary
        if result.failed == 0:
            icon = ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN_400, size=48)
            title_text = "Conversion Complete!"
        else:
            icon = ft.Icon(ft.Icons.WARNING, color=ft.Colors.ORANGE_400, size=48)
            title_text = "Conversion Finished with Errors"
        
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([icon, ft.Text(title_text, weight=ft.FontWeight.BOLD)], spacing=12),
            content=ft.Column([
                ft.Text(
                    f"✓ Successfully converted: {result.successful} files\n"
                    f"✗ Failed: {result.failed} files\n"
                    f"⏱ Total time: {result.total_time:.2f} seconds",
                    size=14,
                ),
            ], tight=True),
            actions=[
                ft.TextButton("Close", on_click=close_dialog),
                ft.ElevatedButton(
                    "Open Output Folder",
                    icon=ft.Icons.FOLDER_OPEN,
                    on_click=open_output_folder,
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.BLUE_700,
                        color=ft.Colors.WHITE,
                    ),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()
    
    def _on_log_message(self, level: str, message: str) -> None:
        """Handle log message from controller."""
        colors = {
            "info": ft.Colors.GREY_400,
            "warning": ft.Colors.ORANGE_400,
            "error": ft.Colors.RED_400,
        }
        
        icons = {
            "info": ft.Icons.INFO_OUTLINE,
            "warning": ft.Icons.WARNING_OUTLINED,
            "error": ft.Icons.ERROR_OUTLINE,
        }
        
        log_entry = ft.Row(
            controls=[
                ft.Icon(
                    icons.get(level, ft.Icons.CIRCLE),
                    size=14,
                    color=colors.get(level, ft.Colors.GREY_400),
                ),
                ft.Text(
                    message,
                    size=12,
                    color=colors.get(level, ft.Colors.GREY_400),
                    selectable=True,
                    max_lines=2,
                    overflow=ft.TextOverflow.ELLIPSIS,
                ),
            ],
            spacing=8,
        )
        
        self.log_list.controls.append(log_entry)
        
        # Limit log entries
        if len(self.log_list.controls) > 100:
            self.log_list.controls.pop(0)
        
        self.page.update()
    
    def _on_error(self, message: str) -> None:
        """Handle error from controller."""
        self.page.open(
            ft.SnackBar(
                content=ft.Text(message),
                bgcolor=ft.Colors.RED_700,
            )
        )
    
    # ==================== UI Helpers ====================
    
    def _update_file_list(self) -> None:
        """Update the file list display."""
        self.file_list.controls.clear()
        
        for file_item in self.controller.files:
            self.file_list.controls.append(
                create_file_list_item(file_item, self._remove_file)
            )
        
        # Update stats and visibility
        total_files = len(self.controller.files)
        supported = sum(1 for f in self.controller.files if f.is_supported)
        
        if total_files > 0:
            self.stats_row.visible = True
            self.stats_row.controls[0].value = f"{total_files} files ({supported} supported)"
            self.empty_state.visible = False
            self.file_list.visible = True
        else:
            self.stats_row.visible = False
            self.empty_state.visible = True
            self.file_list.visible = False
        
        self._update_convert_button()
        self.page.update()
    
    def _remove_file(self, file_path: Path) -> None:
        """Remove a file from the list."""
        self.controller.remove_file(file_path)
        self._update_file_list()
    
    def _update_convert_button(self) -> None:
        """Update the convert button state."""
        self.convert_button.disabled = not self.controller.is_ready


def create_app(page: ft.Page) -> None:
    """
    Create and run the MarkItDown Converter application.

    This is the entry point for Flet.

    Args:
        page: The Flet page instance.
    """
    # Set window title and icon
    page.title = "MDTransformer"
    page.window.icon = "icon.ico"  # Requires assets directory to be passed in ft.app

    app = MarkItDownApp(page)
    page.add(app.build())
    page.update()
