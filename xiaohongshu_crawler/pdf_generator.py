"""
PDF生成模組，負責將文章內容轉換為PDF格式
"""

import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image
import requests
from .utils import sanitize_filename, get_system_fonts_path

def find_chinese_font():
    """
    查找可用的中文字體。
    
    Returns:
        str or None: 中文字體文件路徑，如果未找到則返回None
    """
    # 常見的中文字體名稱，優先使用 TTF 格式
    chinese_fonts = [
        'Songti.ttc',
        'STHeiti Light.ttc',
        'Hiragino Sans GB.ttc',
        'simsun.ttc',
        'simhei.ttf',
        'msyh.ttf',
        'simkai.ttf',
        'wqy-microhei.ttc',
        'wqy-zenhei.ttc',
        'NotoSansCJK-Regular.ttc',
        'NotoSansSC-Regular.otf'
    ]
    
    # 檢查專案預設字體
    fonts_dir = 'fonts'
    if not os.path.exists(fonts_dir):
        os.makedirs(fonts_dir)
    
    # 預設字體檔案
    default_fonts = {
        'noto_sans': 'NotoSansCJK-Regular.otf',
        'noto_serif': 'NotoSerifCJK-Regular.otf'
    }
    
    # 檢查並下載預設字體
    for font_type, font_name in default_fonts.items():
        font_path = os.path.join(fonts_dir, font_name)
        if not os.path.exists(font_path):
            print(f"下載預設字體 {font_name}...")
            if font_type == 'noto_sans':
                url = 'https://raw.githubusercontent.com/googlefonts/noto-cjk/main/Sans/SubsetOTF/TC/NotoSansTC-Regular.otf'
            else:
                url = 'https://raw.githubusercontent.com/googlefonts/noto-cjk/main/Serif/SubsetOTF/TC/NotoSerifTC-Regular.otf'
            
            try:
                response = requests.get(url)
                with open(font_path, 'wb') as f:
                    f.write(response.content)
                print(f"字體 {font_name} 下載完成")
            except Exception as e:
                print(f"下載字體 {font_name} 失敗: {e}")
    
    # 在系統字體目錄中尋找中文字體
    for font_dir in get_system_fonts_path():
        if os.path.exists(font_dir):
            print(f"搜尋字體目錄: {font_dir}")
            for font_name in chinese_fonts:
                font_path = os.path.join(font_dir, font_name)
                if os.path.exists(font_path):
                    try:
                        test_font = TTFont('TestFont', font_path)
                        print(f"找到可用的系統字體: {font_path}")
                        return font_path
                    except:
                        continue
    
    # 如果找不到系統字體，使用預設字體
    default_font_path = os.path.join(fonts_dir, default_fonts['noto_sans'])
    if os.path.exists(default_font_path):
        print(f"使用預設字體: {default_font_path}")
        return default_font_path
    
    print("錯誤：無法找到任何可用的中文字體")
    return None

def create_pdf(text, image_info, note_id, title, url, author, edit_date, output_folder='pdfs'):
    """
    創建PDF文件，包含文章內容和圖片。
    
    Args:
        text (str): 文章文本內容
        image_info (list): 圖片信息列表
        note_id (str): 文章ID
        title (str): 文章標題
        url (str): 文章URL
        author (str): 作者
        edit_date (str): 編輯日期
        output_folder (str): PDF輸出目錄
        
    Returns:
        str or None: PDF文件路徑，如果創建失敗則返回None
    """
    safe_title = sanitize_filename(title)
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    filename = f"{safe_title}.pdf" if safe_title else f"{note_id}.pdf"
    output_path = os.path.join(output_folder, filename)
    
    # 尋找並註冊中文字體
    font_path = find_chinese_font()
    if not font_path:
        print("錯誤：無法找到或下載合適的中文字體")
        return None
    
    font_name = 'CustomFont'
    try:
        pdfmetrics.registerFont(TTFont(font_name, font_path))
    except Exception as e:
        print(f"註冊字體失敗: {e}")
        return None
    
    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4
    
    # 設置 PDF metadata
    c.setTitle(title)
    print(f"author in create_pdf: {author}")
    c.setAuthor(author if author else "")
    # c.setCreator("小紅書文章爬蟲")
    c.setCreator(author if author else "")
    c.setSubject(url)
    
    # 設定字體大小和行距
    TITLE_FONT_SIZE = 16
    INFO_FONT_SIZE = 10
    CONTENT_FONT_SIZE = 16
    LINE_HEIGHT = CONTENT_FONT_SIZE * 1.3
    MARGIN = 50
    
    def create_page():
        if c.getPageNumber() > 0:
            c.showPage()
        c.setFont(font_name, CONTENT_FONT_SIZE)
        return height - MARGIN
    
    # 處理標題
    y = height - MARGIN
    c.setFont(font_name, TITLE_FONT_SIZE)
    title_width = c.stringWidth(title, font_name, TITLE_FONT_SIZE)
    if title_width > width - 2 * MARGIN:
        words = list(title)
        current_line = ""
        title_lines = []
        for word in words:
            test_line = current_line + word
            if c.stringWidth(test_line, font_name, TITLE_FONT_SIZE) < width - 2 * MARGIN:
                current_line = test_line
            else:
                title_lines.append(current_line)
                current_line = word
        if current_line:
            title_lines.append(current_line)
    else:
        title_lines = [title]
    
    # 繪製標題
    for line in title_lines:
        if y < MARGIN + LINE_HEIGHT:
            y = create_page()
            c.setFont(font_name, TITLE_FONT_SIZE)
        c.drawString(MARGIN, y, line)
        y -= TITLE_FONT_SIZE * 1.5
    
    y -= 20
    
    # 繪製資訊
    info_lines = []
    url_prefix = "網址："
    remaining_width = width - 2 * MARGIN - c.stringWidth(url_prefix, font_name, INFO_FONT_SIZE)
    url_parts = []
    current_part = ""
    
    for char in url:
        test_part = current_part + char
        if c.stringWidth(test_part, font_name, INFO_FONT_SIZE) < remaining_width:
            current_part = test_part
        else:
            url_parts.append(current_part)
            current_part = char
    if current_part:
        url_parts.append(current_part)
    
    info_lines.append(url_prefix)
    for i, part in enumerate(url_parts):
        info_lines.append("    " + part)
    
    if author:
        info_lines.append(f"作者：{author}")
    if edit_date:
        info_lines.append(f"編輯日期：{edit_date}")
    
    for line in info_lines:
        if y < MARGIN + LINE_HEIGHT:
            y = create_page()
        c.setFont(font_name, INFO_FONT_SIZE)
        c.drawString(MARGIN, y, line)
        y -= INFO_FONT_SIZE * 1.5
    
    y -= 20
    
    # 處理正文
    paragraphs = text.split('\n')
    current_y = y
    
    for paragraph in paragraphs:
        if not paragraph.strip():
            current_y -= LINE_HEIGHT
            continue
            
        words = list(paragraph)
        current_line = ""
        
        for word in words:
            test_line = current_line + word
            if c.stringWidth(test_line, font_name, CONTENT_FONT_SIZE) < width - 2 * MARGIN:
                current_line = test_line
            else:
                if current_y < MARGIN + LINE_HEIGHT:
                    current_y = create_page()
                c.setFont(font_name, CONTENT_FONT_SIZE)
                c.drawString(MARGIN, current_y, current_line)
                current_y -= LINE_HEIGHT
                current_line = word
        
        if current_line:
            if current_y < MARGIN + LINE_HEIGHT:
                current_y = create_page()
            c.setFont(font_name, CONTENT_FONT_SIZE)
            c.drawString(MARGIN, current_y, current_line)
            current_y -= LINE_HEIGHT * 1.5
    
    c.showPage()
    
    # 處理圖片
    for img_info in image_info:
        try:
            img_path = img_info['path']
            if img_info['size_kb'] <= 1:
                continue
                
            img = Image.open(img_path)
            img_width, img_height = img.size
            aspect = img_height / float(img_width)
            
            available_width = width - 2 * MARGIN
            available_height = height - 2 * MARGIN
            
            if img_width > available_width:
                img_width = available_width
                img_height = img_width * aspect
            
            if img_height > available_height:
                img_height = available_height
                img_width = img_height / aspect
            
            x = (width - img_width) / 2
            y = (height - img_height) / 2
            
            c.drawImage(img_path, x, y, width=img_width, height=img_height)
            c.showPage()
            
        except Exception as e:
            print(f"處理圖片時發生錯誤 {img_path}: {e}")
            continue
    
    try:
        c.save()
        print(f"PDF已生成：{output_path}")
        return output_path
    except Exception as e:
        print(f"保存PDF時發生錯誤: {e}")
        return None 
