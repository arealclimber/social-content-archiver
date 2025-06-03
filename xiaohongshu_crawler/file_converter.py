"""
File conversion module, responsible for converting content into different formats (such as PDF, EPUB, Markdown)
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
    """Font management class, responsible for handling Chinese font discovery and registration"""
    
    def __init__(self):
        # Prioritize TTF fonts over OTF fonts (ReportLab doesn't support PostScript outlines)
        self.chinese_fonts = [
            # System TTF fonts (higher priority)
            'NotoSansCJK-Regular.ttf',
            'NotoSerifCJK-Regular.ttf', 
            'wqy-microhei.ttc',
            'wqy-zenhei.ttc',
            'simsun.ttc',
            'simhei.ttf',
            'msyh.ttf',
            'simkai.ttf',
            # macOS fonts
            'Songti.ttc',
            'STHeiti Light.ttc',
            'Hiragino Sans GB.ttc',
            # Fallback OTF fonts (lower priority)
            'NotoSansCJK-Regular.otf',
            'NotoSansSC-Regular.otf'
        ]
        self.default_fonts = {
            'noto_sans': 'NotoSansCJK-Regular.ttf',  # Changed to TTF
            'noto_serif': 'NotoSerifCJK-Regular.ttf'  # Changed to TTF
        }
    
    def find_chinese_font(self):
        """
        Find available Chinese fonts.
        
        Returns:
            str or None: Chinese font file path, returns None if not found
        """
        # Check project default fonts
        fonts_dir = 'fonts'
        if not os.path.exists(fonts_dir):
            os.makedirs(fonts_dir)
        
        # Look for Chinese fonts in system font directory first
        system_font = self._find_system_font()
        if system_font:
            return system_font
        
        # Check and download default fonts if no system font found
        for font_type, font_name in self.default_fonts.items():
            font_path = os.path.join(fonts_dir, font_name)
            if not os.path.exists(font_path):
                self._download_font(font_type, font_name, font_path)
        
        # If system font not found, use default font
        default_font_path = os.path.join(fonts_dir, self.default_fonts['noto_sans'])
        if os.path.exists(default_font_path):
            print(f"Using default font: {default_font_path}")
            return default_font_path
        
        print("Error: No available Chinese fonts found")
        return None
    
    def _download_font(self, font_type, font_name, font_path):
        """Download font file"""
        print(f"Downloading default font {font_name}...")
        try:
            if font_type == 'noto_sans':
                # Use TTF version instead of OTF
                url = 'https://github.com/googlefonts/noto-cjk/raw/main/Sans/OTC/NotoSansCJK-Regular.ttc'
            else:
                url = 'https://github.com/googlefonts/noto-cjk/raw/main/Serif/OTC/NotoSerifCJK-Regular.ttc'
            
            response = requests.get(url)
            with open(font_path, 'wb') as f:
                f.write(response.content)
            print(f"Font {font_name} download completed")
        except Exception as e:
            print(f"Failed to download font {font_name}: {e}")
    
    def _find_system_font(self):
        """Search for available Chinese fonts in the system"""
        # Add Docker/Linux system font paths
        system_paths = get_system_fonts_path()
        system_paths.extend([
            '/usr/share/fonts/truetype',
            '/usr/share/fonts/truetype/noto',
            '/usr/share/fonts/opentype/noto'
        ])
        
        for font_dir in system_paths:
            if os.path.exists(font_dir):
                print(f"Searching font directory: {font_dir}")
                # Search recursively in subdirectories
                for root, dirs, files in os.walk(font_dir):
                    for font_name in self.chinese_fonts:
                        font_path = os.path.join(root, font_name)
                        if os.path.exists(font_path):
                            try:
                                # Test if font can be loaded
                                test_font = TTFont('TestFont', font_path)
                                print(f"Found available system font: {font_path}")
                                return font_path
                            except Exception as e:
                                print(f"Font test failed for {font_path}: {e}")
                                continue
        return None

class PDFConverter:
    """PDF converter, responsible for converting content to PDF format"""
    
    def __init__(self):
        self.font_manager = FontManager()
        self.TITLE_FONT_SIZE = 16
        self.INFO_FONT_SIZE = 10
        self.CONTENT_FONT_SIZE = 16
        self.LINE_HEIGHT = self.CONTENT_FONT_SIZE * 1.3
        self.MARGIN = 50
    
    def create_pdf(self, text, image_info, note_id, title, url, author, edit_date, output_folder='pdfs'):
        """
        Create PDF file containing article content and images.
        
        Args:
            text (str): Article text content
            image_info (list): List of image information
            note_id (str): Article ID
            title (str): Article title
            url (str): Article URL
            author (str): Author
            edit_date (str): Edit date
            output_folder (str): PDF output directory
            
        Returns:
            str or None: PDF file path, returns None if creation fails
        """
        # Prepare output path
        safe_title = sanitize_filename(title)
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        
        filename = f"{safe_title}.pdf" if safe_title else f"{note_id}.pdf"
        output_path = os.path.join(output_folder, filename)
        
        # Set font
        font_path = self.font_manager.find_chinese_font()
        if not font_path:
            return None
        
        font_name = 'CustomFont'
        try:
            pdfmetrics.registerFont(TTFont(font_name, font_path))
        except Exception as e:
            print(f"Font registration failed: {e}")
            return None
        
        # Create PDF file
        c = canvas.Canvas(output_path, pagesize=A4)
        width, height = A4
        
        # Set metadata
        self._set_metadata(c, title, author, url)
        
        # Draw content
        y = self._draw_title(c, title, font_name, width, height)
        y = self._draw_info(c, url, author, edit_date, font_name, width, y)
        self._draw_content(c, text, font_name, width, height, y)
        self._draw_images(c, image_info, width, height)
        
        try:
            c.save()
            print(f"PDF generated: {output_path}")
            return output_path
        except Exception as e:
            print(f"Error occurred while saving PDF: {e}")
            return None
    
    def _set_metadata(self, canvas, title, author, url):
        """Set PDF file metadata"""
        canvas.setTitle(title)
        canvas.setAuthor(author if author else "")
        canvas.setCreator(author if author else "")
        canvas.setSubject(url)
    
    def _draw_title(self, canvas, title, font_name, width, height):
        """Draw title"""
        y = height - self.MARGIN
        canvas.setFont(font_name, self.TITLE_FONT_SIZE)
        
        # Handle title line breaks
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
        
        # Draw title
        for line in title_lines:
            canvas.drawString(self.MARGIN, y, line)
            y -= self.TITLE_FONT_SIZE * 1.5
        
        return y - 20
    
    def _draw_info(self, canvas, url, author, edit_date, font_name, width, y):
        """Draw article information"""
        canvas.setFont(font_name, self.INFO_FONT_SIZE)
        
        # Handle URL line breaks
        url_prefix = "URL: "
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
        
        # Draw URL
        canvas.drawString(self.MARGIN, y, url_prefix)
        y -= self.INFO_FONT_SIZE * 1.5
        for part in url_parts:
            canvas.drawString(self.MARGIN + 20, y, part)
            y -= self.INFO_FONT_SIZE * 1.5
        
        # Draw author and date
        if author:
            canvas.drawString(self.MARGIN, y, f"Author: {author}")
            y -= self.INFO_FONT_SIZE * 1.5
        if edit_date:
            canvas.drawString(self.MARGIN, y, f"Edit date: {edit_date}")
            y -= self.INFO_FONT_SIZE * 1.5
        
        return y - 20
    
    def _draw_content(self, canvas, text, font_name, width, height, y):
        """Draw main content"""
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
        """Draw images"""
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
                print(f"Error occurred while processing image {img_path}: {e}")
                continue

class EPUBConverter:
    """EPUB converter, responsible for converting content to EPUB format"""
    
    def create_epub(self, text, image_info, note_id, title, url, author, edit_date, output_folder='epubs'):
        """
        Create EPUB file.
        
        Args:
            text (str): Article text content
            image_info (list): List of image information
            note_id (str): Article ID
            title (str): Article title
            url (str): Article URL
            author (str): Author
            edit_date (str): Edit date
            output_folder (str): EPUB output directory
            
        Returns:
            str or None: EPUB file path, returns None if creation fails
        """
        try:
            if not os.path.exists(output_folder):
                os.makedirs(output_folder)
            
            safe_title = sanitize_filename(title)
            filename = f"{safe_title}.epub" if safe_title else f"{note_id}.epub"
            output_path = os.path.join(output_folder, filename)
            
            # Create EPUB book
            book = epub.EpubBook()
            
            # Set metadata
            book.set_title(title)
            book.set_language('zh-TW')
            book.add_author(author if author else "Unknown author")
            book.add_metadata('DC', 'date', edit_date if edit_date else datetime.now().strftime('%Y-%m-%d'))
            book.add_metadata('DC', 'source', url)
            
            # Create chapter
            chapter = epub.EpubHtml(title='content', file_name='content.xhtml', lang='zh-TW')
            
            # Prepare HTML content
            content = f'<h1>{title}</h1>\n'
            content += f'<p>Author: {author}</p>\n' if author else ''
            content += f'<p>Edit date: {edit_date}</p>\n' if edit_date else ''
            content += f'<p>Source: <a href="{url}">{url}</a></p>\n'
            content += '<hr/>\n'
            
            # Add text content
            paragraphs = text.split('\n')
            for p in paragraphs:
                if p.strip():
                    content += f'<p>{p}</p>\n'
            
            # Add images
            for idx, img_info in enumerate(image_info):
                try:
                    if img_info['size_kb'] <= 1:
                        continue
                    
                    # Copy image to temporary directory
                    img_filename = f'image_{idx+1}.jpg'
                    img = epub.EpubImage()
                    img.file_name = f'images/{img_filename}'
                    
                    with open(img_info['path'], 'rb') as f:
                        img.content = f.read()
                    
                    book.add_item(img)
                    content += f'<p><img src="images/{img_filename}" alt="Image {idx+1}"/></p>\n'
                    
                except Exception as e:
                    print(f"Error occurred while processing EPUB image {img_info['path']}: {e}")
                    continue
            
            chapter.content = content
            book.add_item(chapter)
            
            # Add navigation
            book.add_item(epub.EpubNcx())
            book.add_item(epub.EpubNav())
            
            # Define reading order
            book.spine = ['nav', chapter]
            
            # Generate EPUB
            epub.write_epub(output_path, book, {})
            print(f"EPUB generated: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"Error occurred while generating EPUB: {e}")
            return None

class MarkdownConverter:
    """Markdown converter, responsible for converting content to Markdown format"""
    
    def create_markdown(self, text, image_info, note_id, title, url, author, edit_date, output_folder='markdowns'):
        """
        Create Markdown file.
        
        Args:
            text (str): Article text content
            image_info (list): List of image information
            note_id (str): Article ID
            title (str): Article title
            url (str): Article URL
            author (str): Author
            edit_date (str): Edit date
            output_folder (str): Markdown output directory
            
        Returns:
            str or None: Markdown file path, returns None if creation fails
        """
        try:
            if not os.path.exists(output_folder):
                os.makedirs(output_folder)
            
            # Generate timestamp-based folder name
            timestamp = datetime.now().strftime('%m%d_%H_%M_%S')
            
            safe_title = sanitize_filename(title)
            filename = f"{safe_title}.md" if safe_title else f"{note_id}.md"
            output_path = os.path.join(output_folder, filename)
            
            # Create image directory, using timestamp
            images_dir = os.path.join(output_folder, 'images', timestamp)
            if not os.path.exists(images_dir):
                os.makedirs(images_dir)
            
            # Generate Markdown content
            content = f"# {title}\n\n"
            content += f"Author: {author}\n\n" if author else ""
            content += f"Edit date: {edit_date}\n\n" if edit_date else ""
            content += f"Source: [{url}]({url})\n\n"
            content += "---\n\n"
            
            # Add text content
            content += text.strip() + "\n\n"
            
            # Copy and add images
            for idx, img_info in enumerate(image_info):
                try:
                    if img_info['size_kb'] <= 1:
                        continue
                    
                    # Copy image, using original filename but adding index
                    original_filename = os.path.basename(img_info['path'])
                    img_filename = f'{idx+1:02d}_{original_filename}'
                    img_path = os.path.join(images_dir, img_filename)
                    shutil.copy2(img_info['path'], img_path)
                    
                    # Add image reference, using relative path
                    relative_path = os.path.join('images', timestamp, img_filename).replace('\\', '/')
                    content += f"\n![Image {idx+1}]({relative_path})\n"
                    
                except Exception as e:
                    print(f"Error occurred while processing Markdown image {img_info['path']}: {e}")
                    continue
            
            # Save Markdown file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"Markdown generated: {output_path}")
            print(f"Images saved to: {images_dir}")
            return output_path
            
        except Exception as e:
            print(f"Error occurred while generating Markdown: {e}")
            return None

def create_pdf(text, image_info, note_id, title, url, author, edit_date, output_folder='pdfs'):
    """Convenient function to create PDF file"""
    converter = PDFConverter()
    return converter.create_pdf(text, image_info, note_id, title, url, author, edit_date, output_folder)

def create_epub(text, image_info, note_id, title, url, author, edit_date, output_folder='epubs'):
    """Convenient function to create EPUB file"""
    converter = EPUBConverter()
    return converter.create_epub(text, image_info, note_id, title, url, author, edit_date, output_folder)

def create_markdown(text, image_info, note_id, title, url, author, edit_date, output_folder='markdowns'):
    """Convenient function to create Markdown file"""
    converter = MarkdownConverter()
    return converter.create_markdown(text, image_info, note_id, title, url, author, edit_date, output_folder) 
