#!/usr/bin/env python3
"""
小紅書文章爬蟲和轉換工具的入口點
"""

import os
import sys

# 添加當前目錄到Python路徑
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from xiaohongshu_crawler.main import main

if __name__ == "__main__":
    print("注意：建議使用 'python -m xiaohongshu_crawler [選項]' 來執行程式")
    print("例如：python -m xiaohongshu_crawler --formats pdf epub markdown")
    print("\n繼續使用舊的執行方式...\n")
    main() 
