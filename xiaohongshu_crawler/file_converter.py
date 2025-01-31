"""
文件轉換模組，負責將內容轉換為不同格式（如PDF、EPUB、Markdown）
"""

import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image
import requests
from ebooklib import epub
import shutil
from datetime import datetime
from .utils import sanitize_filename, get_system_fonts_path

class FontManager:
    """字體管理類，負責處理中文字體的查找和註冊"""
    
    def __init__(self):
        self.chinese_fonts = [
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
        self.default_fonts = {
            'noto_sans': 'NotoSansCJK-Regular.otf',
            'noto_serif': 'NotoSerifCJK-Regular.otf'
        }
    
    def find_chinese_font(self):
        """
        查找可用的中文字體。
        
        Returns:
            str or None: 中文字體文件路徑，如果未找到則返回None
        """
        # 檢查專案預設字體
        fonts_dir = 'fonts'
        if not os.path.exists(fonts_dir):
            os.makedirs(fonts_dir)
        
        # 檢查並下載預設字體
        for font_type, font_name in self.default_fonts.items():
            font_path = os.path.join(fonts_dir, font_name)
            if not os.path.exists(font_path):
                self._download_font(font_type, font_name, font_path)
        
        # 在系統字體目錄中尋找中文字體
        system_font = self._find_system_font()
        if system_font:
            return system_font
        
        # 如果找不到系統字體，使用預設字體
        default_font_path = os.path.join(fonts_dir, self.default_fonts['noto_sans'])
        if os.path.exists(default_font_path):
            print(f"使用預設字體: {default_font_path}")
            return default_font_path
        
        print("錯誤：無法找到任何可用的中文字體")
        return None
    
    def _download_font(self, font_type, font_name, font_path):
        """下載字體文件"""
        print(f"下載預設字體 {font_name}...")
        try:
            if font_type == 'noto_sans':
                url = 'https://raw.githubusercontent.com/googlefonts/noto-cjk/main/Sans/SubsetOTF/TC/NotoSansTC-Regular.otf'
            else:
                url = 'https://raw.githubusercontent.com/googlefonts/noto-cjk/main/Serif/SubsetOTF/TC/NotoSerifTC-Regular.otf'
            
            response = requests.get(url)
            with open(font_path, 'wb') as f:
                f.write(response.content)
            print(f"字體 {font_name} 下載完成")
        except Exception as e:
            print(f"下載字體 {font_name} 失敗: {e}")
    
    def _find_system_font(self):
        """在系統中查找可用的中文字體"""
        for font_dir in get_system_fonts_path():
            if os.path.exists(font_dir):
                print(f"搜尋字體目錄: {font_dir}")
                for font_name in self.chinese_fonts:
                    font_path = os.path.join(font_dir, font_name)
                    if os.path.exists(font_path):
                        try:
                            test_font = TTFont('TestFont', font_path)
                            print(f"找到可用的系統字體: {font_path}")
                            return font_path
                        except:
                            continue
        return None

class PDFConverter:
    """PDF轉換器，負責將內容轉換為PDF格式"""
    
    def __init__(self):
        self.font_manager = FontManager()
        self.TITLE_FONT_SIZE = 16
        self.INFO_FONT_SIZE = 10
        self.CONTENT_FONT_SIZE = 16
        self.LINE_HEIGHT = self.CONTENT_FONT_SIZE * 1.3
        self.MARGIN = 50
    
    def create_pdf(self, text, image_info, note_id, title, url, author, edit_date, output_folder='pdfs'):
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
        # 準備輸出路徑
        safe_title = sanitize_filename(title)
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        
        filename = f"{safe_title}.pdf" if safe_title else f"{note_id}.pdf"
        output_path = os.path.join(output_folder, filename)
        
        # 設置字體
        font_path = self.font_manager.find_chinese_font()
        if not font_path:
            return None
        
        font_name = 'CustomFont'
        try:
            pdfmetrics.registerFont(TTFont(font_name, font_path))
        except Exception as e:
            print(f"註冊字體失敗: {e}")
            return None
        
        # 創建PDF文件
        c = canvas.Canvas(output_path, pagesize=A4)
        width, height = A4
        
        # 設置 metadata
        self._set_metadata(c, title, author, url)
        
        # 繪製內容
        y = self._draw_title(c, title, font_name, width, height)
        y = self._draw_info(c, url, author, edit_date, font_name, width, y)
        self._draw_content(c, text, font_name, width, height, y)
        self._draw_images(c, image_info, width, height)
        
        try:
            c.save()
            print(f"PDF已生成：{output_path}")
            return output_path
        except Exception as e:
            print(f"保存PDF時發生錯誤: {e}")
            return None
    
    def _set_metadata(self, canvas, title, author, url):
        """設置PDF文件的metadata"""
        canvas.setTitle(title)
        canvas.setAuthor(author if author else "")
        canvas.setCreator(author if author else "")
        canvas.setSubject(url)
    
    def _draw_title(self, canvas, title, font_name, width, height):
        """繪製標題"""
        y = height - self.MARGIN
        canvas.setFont(font_name, self.TITLE_FONT_SIZE)
        
        # 處理標題換行
        title_width = canvas.stringWidth(title, font_name, self.TITLE_FONT_SIZE)
        if title_width > width - 2 * self.MARGIN:
            words = list(title)
            current_line = ""
            title_lines = []
            for word in words:
                test_line = current_line + word
                if canvas.stringWidth(test_line, font_name, self.TITLE_FONT_SIZE) < width - 2 * self.MARGIN:
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
            canvas.drawString(self.MARGIN, y, line)
            y -= self.TITLE_FONT_SIZE * 1.5
        
        return y - 20
    
    def _draw_info(self, canvas, url, author, edit_date, font_name, width, y):
        """繪製文章信息"""
        canvas.setFont(font_name, self.INFO_FONT_SIZE)
        
        # 處理URL換行
        url_prefix = "網址："
        remaining_width = width - 2 * self.MARGIN - canvas.stringWidth(url_prefix, font_name, self.INFO_FONT_SIZE)
        url_parts = []
        current_part = ""
        
        for char in url:
            test_part = current_part + char
            if canvas.stringWidth(test_part, font_name, self.INFO_FONT_SIZE) < remaining_width:
                current_part = test_part
            else:
                url_parts.append(current_part)
                current_part = char
        if current_part:
            url_parts.append(current_part)
        
        # 繪製URL
        canvas.drawString(self.MARGIN, y, url_prefix)
        y -= self.INFO_FONT_SIZE * 1.5
        for part in url_parts:
            canvas.drawString(self.MARGIN + 20, y, part)
            y -= self.INFO_FONT_SIZE * 1.5
        
        # 繪製作者和日期
        if author:
            canvas.drawString(self.MARGIN, y, f"作者：{author}")
            y -= self.INFO_FONT_SIZE * 1.5
        if edit_date:
            canvas.drawString(self.MARGIN, y, f"編輯日期：{edit_date}")
            y -= self.INFO_FONT_SIZE * 1.5
        
        return y - 20
    
    def _draw_content(self, canvas, text, font_name, width, height, y):
        """繪製正文內容"""
        canvas.setFont(font_name, self.CONTENT_FONT_SIZE)
        current_y = y
        
        for paragraph in text.split('\n'):
            if not paragraph.strip():
                current_y -= self.LINE_HEIGHT
                continue
            
            words = list(paragraph)
            current_line = ""
            
            for word in words:
                test_line = current_line + word
                if canvas.stringWidth(test_line, font_name, self.CONTENT_FONT_SIZE) < width - 2 * self.MARGIN:
                    current_line = test_line
                else:
                    if current_y < self.MARGIN + self.LINE_HEIGHT:
                        canvas.showPage()
                        canvas.setFont(font_name, self.CONTENT_FONT_SIZE)
                        current_y = height - self.MARGIN
                    canvas.drawString(self.MARGIN, current_y, current_line)
                    current_y -= self.LINE_HEIGHT
                    current_line = word
            
            if current_line:
                if current_y < self.MARGIN + self.LINE_HEIGHT:
                    canvas.showPage()
                    canvas.setFont(font_name, self.CONTENT_FONT_SIZE)
                    current_y = height - self.MARGIN
                canvas.drawString(self.MARGIN, current_y, current_line)
                current_y -= self.LINE_HEIGHT * 1.5
        
        canvas.showPage()
    
    def _draw_images(self, canvas, image_info, width, height):
        """繪製圖片"""
        for img_info in image_info:
            try:
                img_path = img_info['path']
                if img_info['size_kb'] <= 1:
                    continue
                
                img = Image.open(img_path)
                img_width, img_height = img.size
                aspect = img_height / float(img_width)
                
                available_width = width - 2 * self.MARGIN
                available_height = height - 2 * self.MARGIN
                
                if img_width > available_width:
                    img_width = available_width
                    img_height = img_width * aspect
                
                if img_height > available_height:
                    img_height = available_height
                    img_width = img_height / aspect
                
                x = (width - img_width) / 2
                y = (height - img_height) / 2
                
                canvas.drawImage(img_path, x, y, width=img_width, height=img_height)
                canvas.showPage()
                
            except Exception as e:
                print(f"處理圖片時發生錯誤 {img_path}: {e}")
                continue

class EPUBConverter:
    """EPUB轉換器，負責將內容轉換為EPUB格式"""
    
    def create_epub(self, text, image_info, note_id, title, url, author, edit_date, output_folder='epubs'):
        """
        創建EPUB文件。
        
        Args:
            text (str): 文章文本內容
            image_info (list): 圖片信息列表
            note_id (str): 文章ID
            title (str): 文章標題
            url (str): 文章URL
            author (str): 作者
            edit_date (str): 編輯日期
            output_folder (str): EPUB輸出目錄
            
        Returns:
            str or None: EPUB文件路徑，如果創建失敗則返回None
        """
        try:
            if not os.path.exists(output_folder):
                os.makedirs(output_folder)
            
            safe_title = sanitize_filename(title)
            filename = f"{safe_title}.epub" if safe_title else f"{note_id}.epub"
            output_path = os.path.join(output_folder, filename)
            
            # 創建EPUB書籍
            book = epub.EpubBook()
            
            # 設置metadata
            book.set_title(title)
            book.set_language('zh-TW')
            book.add_author(author if author else "未知作者")
            book.add_metadata('DC', 'date', edit_date if edit_date else datetime.now().strftime('%Y-%m-%d'))
            book.add_metadata('DC', 'source', url)
            
            # 創建章節
            chapter = epub.EpubHtml(title='content', file_name='content.xhtml', lang='zh-TW')
            
            # 準備HTML內容
            content = f'<h1>{title}</h1>\n'
            content += f'<p>作者：{author}</p>\n' if author else ''
            content += f'<p>編輯日期：{edit_date}</p>\n' if edit_date else ''
            content += f'<p>來源：<a href="{url}">{url}</a></p>\n'
            content += '<hr/>\n'
            
            # 添加文本內容
            paragraphs = text.split('\n')
            for p in paragraphs:
                if p.strip():
                    content += f'<p>{p}</p>\n'
            
            # 添加圖片
            for idx, img_info in enumerate(image_info):
                try:
                    if img_info['size_kb'] <= 1:
                        continue
                    
                    # 複製圖片到臨時目錄
                    img_filename = f'image_{idx+1}.jpg'
                    img = epub.EpubImage()
                    img.file_name = f'images/{img_filename}'
                    
                    with open(img_info['path'], 'rb') as f:
                        img.content = f.read()
                    
                    book.add_item(img)
                    content += f'<p><img src="images/{img_filename}" alt="圖片 {idx+1}"/></p>\n'
                    
                except Exception as e:
                    print(f"處理EPUB圖片時發生錯誤 {img_info['path']}: {e}")
                    continue
            
            chapter.content = content
            book.add_item(chapter)
            
            # 添加導航
            book.add_item(epub.EpubNcx())
            book.add_item(epub.EpubNav())
            
            # 定義閱讀順序
            book.spine = ['nav', chapter]
            
            # 生成EPUB
            epub.write_epub(output_path, book, {})
            print(f"EPUB已生成：{output_path}")
            return output_path
            
        except Exception as e:
            print(f"生成EPUB時發生錯誤: {e}")
            return None

class MarkdownConverter:
    """Markdown轉換器，負責將內容轉換為Markdown格式"""
    
    def create_markdown(self, text, image_info, note_id, title, url, author, edit_date, output_folder='markdowns'):
        """
        創建Markdown文件。
        
        Args:
            text (str): 文章文本內容
            image_info (list): 圖片信息列表
            note_id (str): 文章ID
            title (str): 文章標題
            url (str): 文章URL
            author (str): 作者
            edit_date (str): 編輯日期
            output_folder (str): Markdown輸出目錄
            
        Returns:
            str or None: Markdown文件路徑，如果創建失敗則返回None
        """
        try:
            if not os.path.exists(output_folder):
                os.makedirs(output_folder)
            
            # 生成時間戳記格式的資料夾名稱
            timestamp = datetime.now().strftime('%m%d_%H_%M_%S')
            
            safe_title = sanitize_filename(title)
            filename = f"{safe_title}.md" if safe_title else f"{note_id}.md"
            output_path = os.path.join(output_folder, filename)
            
            # 創建圖片目錄，使用時間戳記
            images_dir = os.path.join(output_folder, 'images', timestamp)
            if not os.path.exists(images_dir):
                os.makedirs(images_dir)
            
            # 生成Markdown內容
            content = f"# {title}\n\n"
            content += f"作者：{author}\n\n" if author else ""
            content += f"編輯日期：{edit_date}\n\n" if edit_date else ""
            content += f"來源：[{url}]({url})\n\n"
            content += "---\n\n"
            
            # 添加文本內容
            content += text.strip() + "\n\n"
            
            # 複製並添加圖片
            for idx, img_info in enumerate(image_info):
                try:
                    if img_info['size_kb'] <= 1:
                        continue
                    
                    # 複製圖片，使用原始檔名但加上序號
                    original_filename = os.path.basename(img_info['path'])
                    img_filename = f'{idx+1:02d}_{original_filename}'
                    img_path = os.path.join(images_dir, img_filename)
                    shutil.copy2(img_info['path'], img_path)
                    
                    # 添加圖片引用，使用相對路徑
                    relative_path = os.path.join('images', timestamp, img_filename).replace('\\', '/')
                    content += f"\n![圖片 {idx+1}]({relative_path})\n"
                    
                except Exception as e:
                    print(f"處理Markdown圖片時發生錯誤 {img_info['path']}: {e}")
                    continue
            
            # 保存Markdown文件
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"Markdown已生成：{output_path}")
            print(f"圖片已保存至：{images_dir}")
            return output_path
            
        except Exception as e:
            print(f"生成Markdown時發生錯誤: {e}")
            return None

def create_pdf(text, image_info, note_id, title, url, author, edit_date, output_folder='pdfs'):
    """創建PDF文件的便捷函數"""
    converter = PDFConverter()
    return converter.create_pdf(text, image_info, note_id, title, url, author, edit_date, output_folder)

def create_epub(text, image_info, note_id, title, url, author, edit_date, output_folder='epubs'):
    """創建EPUB文件的便捷函數"""
    converter = EPUBConverter()
    return converter.create_epub(text, image_info, note_id, title, url, author, edit_date, output_folder)

def create_markdown(text, image_info, note_id, title, url, author, edit_date, output_folder='markdowns'):
    """創建Markdown文件的便捷函數"""
    converter = MarkdownConverter()
    return converter.create_markdown(text, image_info, note_id, title, url, author, edit_date, output_folder) 
