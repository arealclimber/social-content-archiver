"""
通用工具模組，提供各種輔助函數
"""

from urllib.parse import urlparse
import platform
import os
from pathlib import Path

def sanitize_filename(filename):
    """
    清理文件名，移除不合法字符。
    
    Args:
        filename (str): 原始文件名
        
    Returns:
        str: 清理後的文件名，長度不超過100字符
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
    從URL中提取文章ID。
    
    Args:
        url (str): 文章URL
        
    Returns:
        str: 文章ID
    """
    path = urlparse(url).path
    return path.split('/')[-1].split('?')[0]

def get_system_fonts_path():
    """
    獲取系統字體目錄路徑。
    
    Returns:
        list: 系統字體目錄路徑列表
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
