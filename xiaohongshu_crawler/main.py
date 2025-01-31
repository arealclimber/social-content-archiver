"""
主程式模組，負責協調各個模組的工作並處理URL列表
"""

import os
import argparse
from .browser import fetch_xiaohongshu_content, get_author_notes
from .parser import parse_content
from .image_handler import download_images
from .file_converter import create_pdf, create_epub, create_markdown
from .utils import extract_note_id

def process_url(url, formats=None):
    """
    處理單個URL，完成從爬取到生成文件的完整流程。
    
    Args:
        url (str): 文章URL
        formats (list): 要生成的文件格式列表，可選值：['pdf', 'epub', 'markdown']
        
    Returns:
        dict: 包含各種格式文件路徑的字典，如果處理失敗則對應格式的值為None
    """
    if formats is None:
        formats = ['pdf']  # 默認只生成PDF
    
    note_id = extract_note_id(url)
    print(f"處理筆記 ID: {note_id}")
    
    html = fetch_xiaohongshu_content(url)
    if not html:
        print(f"無法獲取筆記內容: {url}")
        return {fmt: None for fmt in formats}
    
    text, image_urls, title, author, edit_date = parse_content(html, note_id)
    if not image_urls:
        print(f"沒有找到圖片: {url}")
        return {fmt: None for fmt in formats}
    
    image_info = download_images(image_urls, note_id, title)
    if not image_info:
        print(f"沒有成功下載的圖片: {url}")
        return {fmt: None for fmt in formats}
    
    results = {}
    
    # 生成各種格式的文件
    if 'pdf' in formats:
        pdf_path = create_pdf(text, image_info, note_id, title, url, author, edit_date)
        results['pdf'] = pdf_path
        
    if 'epub' in formats:
        epub_path = create_epub(text, image_info, note_id, title, url, author, edit_date)
        results['epub'] = epub_path
        
    if 'markdown' in formats:
        md_path = create_markdown(text, image_info, note_id, title, url, author, edit_date)
        results['markdown'] = md_path
    
    return results

def process_author(author_url, formats=None):
    """
    處理作者的所有筆記。
    
    Args:
        author_url (str): 作者主頁URL
        formats (list): 要生成的文件格式列表，可選值：['pdf', 'epub', 'markdown']
    """
    print(f"\n開始處理作者頁面: {author_url}")
    urls = get_author_notes(author_url)
    
    if not urls:
        print("沒有找到任何筆記")
        return
    
    print(f"\n共找到 {len(urls)} 篇筆記")
    success_count = {fmt: 0 for fmt in formats}
    
    for idx, url in enumerate(urls, 1):
        print(f"\n處理第 {idx}/{len(urls)} 篇筆記: {url}")
        results = process_url(url, formats)
        
        for fmt in formats:
            if results[fmt]:
                print(f"成功生成 {fmt.upper()}: {results[fmt]}")
                success_count[fmt] += 1
            else:
                print(f"生成 {fmt.upper()} 失敗: {url}")
    
    print("\n處理完成！")
    for fmt in formats:
        print(f"{fmt.upper()} 格式：成功轉換 {success_count[fmt]}/{len(urls)} 篇筆記")

def main():
    """
    主函數，讀取URL列表並處理每個URL。
    """
    parser = argparse.ArgumentParser(description='小紅書文章爬蟲和轉換工具')
    parser.add_argument('--formats', nargs='+', choices=['pdf', 'epub', 'markdown'],
                      default=['pdf'], help='要生成的文件格式，可選：pdf, epub, markdown')
    args = parser.parse_args()
    
    with open('note-urls.md', 'r', encoding='utf-8') as f:
        content = f.read()
    
    urls = []
    for line in content.split('\n'):
        if 'xiaohongshu.com' in line:
            url = line.strip('- ').strip()
            urls.append(url)
    
    if not urls:
        print("沒有找到小紅書網址")
        return
    
    for url in urls:
        print(f"\n開始處理網址: {url}")
        results = process_url(url, args.formats)
        
        for fmt in args.formats:
            if results[fmt]:
                print(f"成功生成 {fmt.upper()}: {results[fmt]}")
            else:
                print(f"生成 {fmt.upper()} 失敗: {url}")

if __name__ == "__main__":
    main() 
