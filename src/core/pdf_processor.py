"""
PDF Processor Module.

This module provides enhanced PDF to Markdown conversion using pymupdf4llm,
which offers superior table extraction and formatting compared to basic PDF parsers.
"""

import re
from pathlib import Path
from typing import Optional

from src.utils.logger import get_logger

logger = get_logger(__name__)

# Try to import pymupdf4llm
try:
    import pymupdf4llm
    PYMUPDF4LLM_AVAILABLE = True
except ImportError:
    PYMUPDF4LLM_AVAILABLE = False
    logger.warning("pymupdf4llm not available. Install with: pip install pymupdf4llm")


class PDFProcessor:
    """
    Enhanced PDF processor using pymupdf4llm.
    
    This processor provides better extraction of:
    - Tables with proper Markdown formatting
    - Multi-column layouts
    - Headers and footers handling
    - Image references
    
    Attributes:
        available: Whether pymupdf4llm is installed and available.
    """
    
    def __init__(
        self,
        page_chunks: bool = False,
        write_images: bool = False,
        image_path: Optional[str] = None,
        show_progress: bool = False,
    ) -> None:
        """
        Initialize the PDF processor.
        
        Args:
            page_chunks: If True, return list of per-page markdown strings.
            write_images: If True, extract and save images from the PDF.
            image_path: Directory to save extracted images (if write_images=True).
            show_progress: If True, show progress bar during conversion.
        """
        self._page_chunks = page_chunks
        self._write_images = write_images
        self._image_path = image_path
        self._show_progress = show_progress
    
    @property
    def available(self) -> bool:
        """Check if pymupdf4llm is available."""
        return PYMUPDF4LLM_AVAILABLE
    
    def convert(self, pdf_path: Path) -> str:
        """
        Convert a PDF file to Markdown with enhanced table support.
        
        Args:
            pdf_path: Path to the PDF file.
            
        Returns:
            Markdown string with properly formatted tables.
            
        Raises:
            RuntimeError: If pymupdf4llm is not available.
            FileNotFoundError: If the PDF file doesn't exist.
            Exception: If conversion fails.
        """
        if not PYMUPDF4LLM_AVAILABLE:
            raise RuntimeError(
                "pymupdf4llm is not installed. "
                "Install with: pip install pymupdf4llm"
            )
        
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        logger.info(f"Converting PDF with pymupdf4llm: {pdf_path.name}")
        
        try:
            # Convert PDF to Markdown
            md_text = pymupdf4llm.to_markdown(
                str(pdf_path),
                page_chunks=self._page_chunks,
                write_images=self._write_images,
                image_path=self._image_path,
                show_progress=self._show_progress,
            )
            
            # If page_chunks is True, join the pages
            if self._page_chunks and isinstance(md_text, list):
                md_text = "\n\n---\n\n".join(md_text)
            
            # Post-process to clean up common issues
            md_text = self._post_process(md_text)
            
            logger.info(f"Successfully converted PDF: {pdf_path.name}")
            return md_text
            
        except Exception as e:
            logger.error(f"Failed to convert PDF {pdf_path.name}: {e}")
            raise
    
    def _post_process(self, markdown: str) -> str:
        """
        Post-process the markdown to fix common issues.
        
        Handles:
        - Page break artifacts and separators
        - Tables split across pages (merges them)
        - Multi-line cell content (merges into single cells)
        - Excessive whitespace and empty lines
        - Repeated headers from page breaks
        
        Args:
            markdown: Raw markdown from pymupdf4llm.
            
        Returns:
            Cleaned markdown string.
        """
        # Step 1: Pre-process to fix multi-line table cells
        markdown = self._fix_multiline_cells(markdown)
        
        # Step 2: Remove page break markers and horizontal rules
        lines = markdown.split("\n")
        cleaned_lines = []
        
        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()
            
            # Skip page separator lines (---, ___, ***)
            if stripped in ("---", "___", "***", "* * *", "- - -"):
                if cleaned_lines and cleaned_lines[-1].strip().startswith("|"):
                    pass  # Might be table content
                else:
                    i += 1
                    continue
            
            # Skip common page number patterns
            if stripped.isdigit() or (len(stripped) < 10 and stripped.replace("-", "").replace("/", "").isdigit()):
                i += 1
                continue
            
            # Skip excessive empty lines
            if not stripped:
                if cleaned_lines and not cleaned_lines[-1].strip():
                    i += 1
                    continue
            
            cleaned_lines.append(line)
            i += 1
        
        # Step 3: Merge split tables
        merged_lines = self._merge_split_tables(cleaned_lines)
        
        # Step 4: Clean up excessive whitespace in non-table lines
        final_lines = []
        for line in merged_lines:
            if not line.strip().startswith("|"):
                line = " ".join(line.split())
            final_lines.append(line)
        
        # Step 5: Remove leading/trailing empty lines
        while final_lines and not final_lines[0].strip():
            final_lines.pop(0)
        while final_lines and not final_lines[-1].strip():
            final_lines.pop()
        
        return "\n".join(final_lines)
    
    def _fix_multiline_cells(self, markdown: str) -> str:
        """
        Fix table cells that span multiple lines.
        
        PDF extraction often splits cell content across multiple lines when
        the text wraps in the original PDF. This method detects such cases
        and merges the content back into single cells.
        
        Args:
            markdown: Raw markdown text.
            
        Returns:
            Markdown with fixed table cells.
        """
        lines = markdown.split("\n")
        result = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()
            
            # Check if this is a table row
            if stripped.startswith("|") and stripped.endswith("|"):
                # Check if this is a separator row (|---|---|)
                if re.match(r'^\|[\s\-:]+\|$', stripped.replace('|', '|').replace(' ', '')):
                    result.append(line)
                    i += 1
                    continue
                
                # Count columns in this row
                col_count = stripped.count("|") - 1
                
                # Look ahead for continuation lines (lines that should be part of cells)
                current_row = stripped
                i += 1
                
                while i < len(lines):
                    next_line = lines[i].strip()
                    
                    # If it's another table row with same column count, stop
                    if next_line.startswith("|") and next_line.endswith("|"):
                        next_col_count = next_line.count("|") - 1
                        if next_col_count == col_count:
                            break
                        # Different column count - might be continuation
                        # Try to merge if it looks like partial content
                        if next_col_count < col_count and not re.match(r'^\|[\s\-:]+\|$', next_line):
                            current_row = self._merge_table_rows(current_row, next_line, col_count)
                            i += 1
                            continue
                        break
                    
                    # If it's a separator row, stop
                    if next_line.startswith("|") and "-" in next_line:
                        break
                    
                    # If it's empty or non-table content, stop
                    if not next_line or not self._looks_like_cell_continuation(next_line):
                        break
                    
                    # This might be continuation text - try to merge
                    current_row = self._append_to_last_cell(current_row, next_line)
                    i += 1
                
                result.append(current_row)
            else:
                result.append(line)
                i += 1
        
        return "\n".join(result)
    
    def _looks_like_cell_continuation(self, text: str) -> bool:
        """
        Check if text looks like it could be continuation of a table cell.
        
        Args:
            text: Text to check.
            
        Returns:
            True if text might be cell continuation.
        """
        # If it starts with common non-continuation patterns, return False
        if text.startswith("#") or text.startswith("*") or text.startswith("-"):
            return False
        # If it's very short text without pipes, might be continuation
        if "|" not in text and len(text) < 100:
            return True
        return False
    
    def _merge_table_rows(self, row1: str, row2: str, expected_cols: int) -> str:
        """
        Merge two table rows that should be one.
        
        Args:
            row1: First row.
            row2: Second row (partial).
            expected_cols: Expected number of columns.
            
        Returns:
            Merged row.
        """
        cells1 = [c.strip() for c in row1.strip().strip("|").split("|")]
        cells2 = [c.strip() for c in row2.strip().strip("|").split("|")]
        
        # Pad cells2 if needed
        while len(cells2) < len(cells1):
            cells2.append("")
        
        # Merge cells - append content from cells2 to cells1
        merged = []
        for c1, c2 in zip(cells1, cells2):
            if c2:
                merged.append(f"{c1} {c2}".strip())
            else:
                merged.append(c1)
        
        return "| " + " | ".join(merged) + " |"
    
    def _append_to_last_cell(self, row: str, text: str) -> str:
        """
        Append text to the last cell of a table row.
        
        Args:
            row: Table row.
            text: Text to append.
            
        Returns:
            Row with appended text.
        """
        cells = [c.strip() for c in row.strip().strip("|").split("|")]
        if cells:
            cells[-1] = f"{cells[-1]} {text}".strip()
        return "| " + " | ".join(cells) + " |"
        
        return "\n".join(final_lines)
    
    def _merge_split_tables(self, lines: list[str]) -> list[str]:
        """
        Merge tables that were split across pages.
        
        When a table spans multiple pages, pymupdf4llm may output:
        - Table header + some rows
        - Page break content
        - Table header again (repeated) + remaining rows
        
        This method detects and merges such tables.
        
        Args:
            lines: List of markdown lines.
            
        Returns:
            Lines with merged tables.
        """
        result = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # Check if this is a table row
            if line.strip().startswith("|") and line.strip().endswith("|"):
                # Collect the entire table
                table_lines = [line]
                table_header = line.strip()
                i += 1
                
                while i < len(lines):
                    current = lines[i].strip()
                    
                    if current.startswith("|") and current.endswith("|"):
                        # Check if this is a repeated header (table continuation)
                        if current == table_header and len(table_lines) > 2:
                            # Skip repeated header
                            i += 1
                            # Also skip the separator line if present
                            if i < len(lines) and lines[i].strip().startswith("|") and "-" in lines[i]:
                                i += 1
                            continue
                        table_lines.append(lines[i])
                        i += 1
                    elif not current:
                        # Empty line - might be end of table or just spacing
                        # Look ahead to see if table continues
                        look_ahead = i + 1
                        while look_ahead < len(lines) and not lines[look_ahead].strip():
                            look_ahead += 1
                        
                        if look_ahead < len(lines) and lines[look_ahead].strip().startswith("|"):
                            # Table continues, skip empty lines
                            i = look_ahead
                        else:
                            # Table ends
                            break
                    else:
                        # Non-table content, table ends
                        break
                
                result.extend(table_lines)
            else:
                result.append(line)
                i += 1
        
        return result


def get_pdf_processor() -> Optional[PDFProcessor]:
    """
    Get a PDF processor instance if available.
    
    Returns:
        PDFProcessor instance if pymupdf4llm is available, None otherwise.
    """
    if PYMUPDF4LLM_AVAILABLE:
        return PDFProcessor()
    return None


def is_pdf_processor_available() -> bool:
    """Check if the enhanced PDF processor is available."""
    return PYMUPDF4LLM_AVAILABLE
