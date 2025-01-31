"""
Xiaohongshu Article Crawler and PDF Generator

This package provides a set of tools for:
1. Crawling Xiaohongshu articles
2. Parsing article content
3. Downloading article images
4. Generating PDF files
"""

from .browser import fetch_xiaohongshu_content
from .parser import parse_content
from .file_converter import create_pdf
from .image_handler import download_images
from .utils import sanitize_filename, extract_note_id

__version__ = '1.0.0'
__all__ = [
    'fetch_xiaohongshu_content',
    'parse_content',
    'create_pdf',
    'download_images',
    'sanitize_filename',
    'extract_note_id',
] 
