"""
HTML解析模組，負責解析網頁內容並提取所需信息
"""

from bs4 import BeautifulSoup
import os

def parse_content(html, note_id):
    """
    解析HTML內容，提取文章信息。
    
    Args:
        html (str): 頁面HTML內容
        note_id (str): 文章ID
        
    Returns:
        tuple: (文章文本, 圖片URL列表, 標題, 作者, 編輯日期)
    """
    soup = BeautifulSoup(html, 'html.parser')
    
    # 創建 debug_html 資料夾（如果不存在）
    debug_folder = 'debug_html'
    if not os.path.exists(debug_folder):
        os.makedirs(debug_folder)
    
    # 保存 debug HTML
    debug_file = os.path.join(debug_folder, f'debug_{note_id}.html')
    with open(debug_file, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"已保存 debug HTML 到: {debug_file}")
    
    text = ""
    images = []
    title = ""
    author = ""
    edit_date = ""
    
    # 從 title 標籤獲取標題
    title_tag = soup.find('title')
    if title_tag:
        title = title_tag.get_text().replace(' - 小红书', '')
    
    # 尋找作者和日期
    author_selectors = ['.user-name', '.author-name', '.nickname']
    date_selectors = ['.publish-date', '.create-time', '.timestamp']
    
    for selector in author_selectors:
        author_elem = soup.select_one(selector)
        if author_elem:
            author = author_elem.get_text(strip=True)
            break
    
    for selector in date_selectors:
        date_elem = soup.select_one(selector)
        if date_elem:
            edit_date = date_elem.get_text(strip=True)
            break
    
    # 尋找內容
    content_selectors = [
        'div[class*="note-content"]',
        'div[class*="content"]',
        'article',
        '.content',
        '.note-content',
        '.desc'
    ]
    
    for selector in content_selectors:
        content = soup.select_one(selector)
        if content:
            text += content.get_text(strip=True) + "\n"
            break
    
    if not text:
        text = "無法提取內容"
    
    # 獲取 og:image meta 標籤的圖片
    og_images = soup.find_all('meta', property='og:image') or soup.find_all('meta', attrs={'name': 'og:image'})
    for img in og_images:
        src = img.get('content')
        if src:
            # 確保使用 HTTPS
            if src.startswith('//'):
                src = 'https:' + src
            elif src.startswith('http://'):
                src = 'https://' + src[7:]
            elif not src.startswith('http'):
                src = 'https://' + src.lstrip('/')
            
            # 保持原始參數，不進行修改
            if src not in images:
                images.append(src)
    
    print(f"從 og:image 標籤找到 {len(images)} 張圖片")
    return text, images, title, author, edit_date 
