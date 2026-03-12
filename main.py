#!/usr/bin/env python3
"""
MarkItDown Converter - Main Entry Point.

This application converts various file formats (PDF, DOCX, XLSX, PPTX, HTML, etc.)
to Markdown using Microsoft's markitdown library.

Usage:
    python main.py

Requirements:
    - Python 3.10+
    - Dependencies listed in requirements.txt

Author:
    MarkItDown Converter Team

License:
    MIT License
"""

import sys
from pathlib import Path

# Ensure the src directory is in the Python path
sys.path.insert(0, str(Path(__file__).parent))

import flet as ft

from src.ui.app_layout import create_app
from src.utils.logger import get_logger

logger = get_logger(__name__)


def main() -> None:
    """
    Main entry point for the MarkItDown Converter application.

    Initializes the Flet application and starts the main event loop.
    """
    logger.info("=" * 60)
    logger.info("MarkItDown Converter - Starting Application")
    logger.info("=" * 60)
    
    try:
        ft.app(
            target=create_app,
            name="MarkItDown Converter",
            assets_dir="assets",
        )
    except KeyboardInterrupt:
        logger.info("Application terminated by user")
    except Exception as e:
        logger.critical(f"Application crashed: {e}", exc_info=True)
        raise
    finally:
        logger.info("Application shutdown complete")


if __name__ == "__main__":
    main()
