"""
小紅書文章爬蟲和PDF生成工具

這個包提供了一套工具，用於：
1. 爬取小紅書文章
2. 解析文章內容
3. 下載文章圖片
4. 生成PDF文件
"""

from .browser import fetch_xiaohongshu_content
from .parser import parse_content
from .pdf_generator import create_pdf
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
