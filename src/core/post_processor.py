"""
Post-Processor Module.

This module provides post-processing utilities to clean and improve
the Markdown output from various converters (markitdown, pymupdf4llm, etc.).
"""

import re
from pathlib import Path
from typing import Optional

from src.utils.logger import get_logger

logger = get_logger(__name__)


class MarkdownPostProcessor:
    """
    Post-processor for cleaning and improving Markdown output.
    
    Handles common issues across different file formats:
    - Excessive whitespace and empty lines
    - Broken tables and lists
    - Inconsistent heading levels
    - Special character encoding issues
    """
    
    def __init__(self) -> None:
        """Initialize the post-processor."""
        pass
    
    def process(self, markdown: str, source_format: str) -> str:
        """
        Process markdown based on source format.
        
        Args:
            markdown: Raw markdown content.
            source_format: File extension of source (e.g., '.docx', '.xlsx').
            
        Returns:
            Cleaned markdown content.
        """
        # Apply general cleanup first
        result = self._general_cleanup(markdown)
        
        # Apply format-specific processing
        format_lower = source_format.lower()
        
        if format_lower in ('.xlsx', '.xls', '.csv'):
            result = self._process_spreadsheet(result)
        elif format_lower in ('.docx', '.doc', '.rtf'):
            result = self._process_document(result)
        elif format_lower in ('.pptx', '.ppt'):
            result = self._process_presentation(result)
        elif format_lower in ('.html', '.htm'):
            result = self._process_html(result)
        
        return result
    
    def _general_cleanup(self, markdown: str) -> str:
        """
        Apply general cleanup to markdown.
        
        Args:
            markdown: Raw markdown.
            
        Returns:
            Cleaned markdown.
        """
        lines = markdown.split('\n')
        result = []
        
        for i, line in enumerate(lines):
            # Remove trailing whitespace
            line = line.rstrip()
            
            # Skip multiple consecutive empty lines (keep max 2)
            if not line.strip():
                if len(result) >= 2 and not result[-1].strip() and not result[-2].strip():
                    continue
            
            result.append(line)
        
        # Join and apply regex-based fixes
        text = '\n'.join(result)
        
        # Fix broken markdown links
        text = re.sub(r'\]\s+\(', '](', text)
        
        # Fix broken bold/italic (e.g., "** text **" -> "**text**")
        text = re.sub(r'\*\*\s+', '**', text)
        text = re.sub(r'\s+\*\*', '**', text)
        text = re.sub(r'\*\s+', '*', text)
        text = re.sub(r'\s+\*', '*', text)
        
        # Remove excessive spaces (but not in code blocks)
        lines = text.split('\n')
        in_code_block = False
        cleaned_lines = []
        
        for line in lines:
            if line.strip().startswith('```'):
                in_code_block = not in_code_block
            
            if not in_code_block and not line.strip().startswith('|'):
                # Collapse multiple spaces to single space
                line = re.sub(r'  +', ' ', line)
            
            cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines).strip()
    
    def _process_spreadsheet(self, markdown: str) -> str:
        """
        Process spreadsheet-origin markdown (Excel, CSV).
        
        Args:
            markdown: Markdown from spreadsheet.
            
        Returns:
            Improved markdown with proper tables.
        """
        lines = markdown.split('\n')
        result = []
        in_table = False
        table_lines = []
        
        for line in lines:
            stripped = line.strip()
            
            # Detect table rows
            if stripped.startswith('|') and stripped.endswith('|'):
                if not in_table:
                    in_table = True
                    table_lines = []
                table_lines.append(line)
            else:
                if in_table:
                    # Process accumulated table
                    processed_table = self._normalize_table(table_lines)
                    result.extend(processed_table)
                    in_table = False
                    table_lines = []
                result.append(line)
        
        # Handle table at end of file
        if in_table:
            processed_table = self._normalize_table(table_lines)
            result.extend(processed_table)
        
        return '\n'.join(result)
    
    def _normalize_table(self, table_lines: list[str]) -> list[str]:
        """
        Normalize a markdown table.
        
        Ensures:
        - Consistent column widths
        - Proper separator line after header
        - Aligned cells
        - Handles merged cells and empty cells
        
        Args:
            table_lines: List of table row strings.
            
        Returns:
            Normalized table lines.
        """
        if not table_lines:
            return []
        
        # Parse all rows into cells
        rows = []
        for line in table_lines:
            # Handle escaped pipes within cells
            cells = []
            current_cell = ""
            escaped = False
            
            line_content = line.strip().strip('|')
            for char in line_content:
                if char == '\\' and not escaped:
                    escaped = True
                    current_cell += char
                elif char == '|' and not escaped:
                    cells.append(current_cell.strip())
                    current_cell = ""
                else:
                    escaped = False
                    current_cell += char
            cells.append(current_cell.strip())
            rows.append(cells)
        
        if not rows:
            return table_lines

        # Remove completely empty rows (ghost rows or fragments from line breaks)
        filtered_rows = []
        for row in rows:
            # A row is empty if all its cells are empty strings or just whitespace
            if not all(not cell.strip() for cell in row):
                filtered_rows.append(row)
                
        # If all rows were empty, or there's nothing left
        if not filtered_rows:
            return table_lines
            
        rows = filtered_rows

        # Determine max columns
        max_cols = max(len(row) for row in rows)
        
        # Pad rows to have same number of columns
        for row in rows:
            while len(row) < max_cols:
                row.append('')
        
        # Calculate column widths (minimum 3 for proper markdown)
        col_widths = []
        for col_idx in range(max_cols):
            max_width = 3  # Minimum width
            for row in rows:
                if col_idx < len(row):
                    # Account for content length, handle special chars
                    content_len = len(row[col_idx])
                    max_width = max(max_width, content_len)
            col_widths.append(min(max_width, 50))  # Cap at 50 chars
        
        # Check if there's already a separator row
        has_separator = False
        separator_idx = -1
        for i, row in enumerate(rows):
            if all(re.match(r'^[-:]+$', cell) or not cell for cell in row):
                has_separator = True
                separator_idx = i
                break
        
        # Build output
        result = []
        for i, row in enumerate(rows):
            if i == separator_idx:
                # Format separator
                sep_cells = ['-' * w for w in col_widths]
                result.append('| ' + ' | '.join(sep_cells) + ' |')
            else:
                # Format regular row
                formatted_cells = [cell.ljust(col_widths[j]) for j, cell in enumerate(row)]
                result.append('| ' + ' | '.join(formatted_cells) + ' |')
        
        # Add separator after first row if missing
        if not has_separator and len(result) > 0:
            sep_cells = ['-' * w for w in col_widths]
            separator = '| ' + ' | '.join(sep_cells) + ' |'
            result.insert(1, separator)
        
        return result
    
    def _process_document(self, markdown: str) -> str:
        """
        Process Word document markdown.
        
        Args:
            markdown: Markdown from Word document.
            
        Returns:
            Improved markdown.
        """
        lines = markdown.split('\n')
        result = []
        
        for line in lines:
            # Fix heading levels (ensure space after #)
            if line.strip().startswith('#'):
                match = re.match(r'^(#+)(\S)', line)
                if match:
                    line = match.group(1) + ' ' + line[len(match.group(1)):]
            
            # Convert Windows-style line endings that might appear as text
            line = line.replace('\\r\\n', '\n').replace('\\n', '\n')
            
            result.append(line)
        
        return '\n'.join(result)
    
    def _process_presentation(self, markdown: str) -> str:
        """
        Process PowerPoint markdown.
        
        Args:
            markdown: Markdown from presentation.
            
        Returns:
            Improved markdown with clear slide separation.
        """
        lines = markdown.split('\n')
        result = []
        slide_count = 0
        
        for line in lines:
            # Detect slide markers and improve them
            if line.strip().startswith('# ') or line.strip().startswith('## '):
                if result and result[-1].strip():  # Add separator before new slide
                    result.append('')
                    result.append('---')
                    result.append('')
                slide_count += 1
            
            result.append(line)
        
        return '\n'.join(result)
    
    def _process_html(self, markdown: str) -> str:
        """
        Process HTML-origin markdown.
        
        Args:
            markdown: Markdown from HTML.
            
        Returns:
            Cleaned markdown.
        """
        # Remove leftover HTML tags that weren't converted
        text = re.sub(r'</?(?:div|span|p|br|font)[^>]*>', '', markdown, flags=re.IGNORECASE)
        
        # Clean up HTML entities that might remain
        html_entities = {
            '&nbsp;': ' ',
            '&amp;': '&',
            '&lt;': '<',
            '&gt;': '>',
            '&quot;': '"',
            '&#39;': "'",
            '&ndash;': '–',
            '&mdash;': '—',
        }
        
        for entity, char in html_entities.items():
            text = text.replace(entity, char)
        
        return text


def get_post_processor() -> MarkdownPostProcessor:
    """Get a MarkdownPostProcessor instance."""
    return MarkdownPostProcessor()
