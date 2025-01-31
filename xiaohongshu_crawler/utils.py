"""
General utility module, providing various helper functions
"""

from urllib.parse import urlparse
import platform
import os
from pathlib import Path

def sanitize_filename(filename):
    """
    Clean filename by removing illegal characters.
    
    Args:
        filename (str): Original filename
        
    Returns:
        str: Cleaned filename, not exceeding 100 characters
    """
    punctuation = '<>:"/\\|?*.,!，。！？、；：""''（）()[]【】《》〈〉『』「」'
    for char in punctuation:
        filename = filename.replace(char, '-')
    while '--' in filename:
        filename = filename.replace('--', '-')
    filename = filename.strip('-')
    return filename[:100]

def extract_note_id(url):
    """
    Extract article ID from URL.
    
    Args:
        url (str): Article URL
        
    Returns:
        str: Article ID
    """
    path = urlparse(url).path
    # Process xhslink.com format URLs
    if 'xhslink.com' in url:
        # Extract the last part of the path as note_id
        note_id = path.split('/')[-1]
        return note_id
    # Process general Xiaohongshu URLs
    return path.split('/')[-1].split('?')[0]

def get_system_fonts_path():
    """
    Get system font directory paths.
    
    Returns:
        list: List of system font directory paths
    """
    system = platform.system()
    if system == 'Darwin':  # macOS
        return [
            '/System/Library/Fonts',
            '/Library/Fonts',
            str(Path.home() / 'Library/Fonts')
        ]
    elif system == 'Windows':
        return [
            'C:\\Windows\\Fonts'
        ]
    else:  # Linux
        return [
            '/usr/share/fonts',
            '/usr/local/share/fonts',
            str(Path.home() / '.fonts')
        ] 
