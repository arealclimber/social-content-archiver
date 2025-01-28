#!/usr/bin/env python3
"""
小紅書文章爬蟲和PDF生成工具的入口點
"""

import os
import sys

# 添加當前目錄到Python路徑
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from xiaohongshu_crawler.main import main

if __name__ == "__main__":
    main() 
