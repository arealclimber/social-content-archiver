"""
主程式模組，負責協調各個模組的工作並處理URL列表
"""

from .browser import fetch_xiaohongshu_content
from .parser import parse_content
from .image_handler import download_images
from .pdf_generator import create_pdf
from .utils import extract_note_id

def process_url(url):
    """
    處理單個URL，完成從爬取到生成PDF的完整流程。
    
    Args:
        url (str): 文章URL
        
    Returns:
        str or None: 生成的PDF文件路徑，如果處理失敗則返回None
    """
    note_id = extract_note_id(url)
    print(f"處理筆記 ID: {note_id}")
    
    html = fetch_xiaohongshu_content(url)
    if not html:
        print(f"無法獲取筆記內容: {url}")
        return
    
    text, image_urls, title, author, edit_date = parse_content(html, note_id)
    if not image_urls:
        print(f"沒有找到圖片: {url}")
        return
    
    image_info = download_images(image_urls, note_id, title)
    if not image_info:
        print(f"沒有成功下載的圖片: {url}")
        return
    
    pdf_path = create_pdf(text, image_info, note_id, title, url, author, edit_date)
    return pdf_path

def main():
    """
    主函數，讀取URL列表並處理每個URL。
    """
    with open('normal-url-to-be-crawled.md', 'r', encoding='utf-8') as f:
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
        pdf_path = process_url(url)
        if pdf_path:
            print(f"成功生成 PDF: {pdf_path}")
        else:
            print(f"處理失敗: {url}")

if __name__ == "__main__":
    main() 
