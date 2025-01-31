"""
This module is used to crawl Xiaohongshu articles and convert them to PDF format. Main features include:

1. Read Xiaohongshu URL list from file
2. Use Selenium to simulate browser access to each URL
3. Extract article content (title, author, date, text, and images)
4. Download all images from the article
5. Generate PDF files containing text content and images

Workflow:
1. Read URL list
2. For each URL:
   - Use Selenium to get page content
   - Parse HTML to extract required information
   - Download article images
   - Create PDF file containing text and images
3. After processing, generate PDF files in specified directory

Dependencies:
- selenium: For browser simulation
- beautifulsoup4: For HTML parsing
- reportlab: For PDF generation
- Pillow: For image processing
- requests: For downloading images

Usage:
1. Add Xiaohongshu URLs to normal-url-to-be-crawled.md file (one per line)
2. Run script: python main.py
3. PDF files will be generated in pdfs/ directory
"""

import requests
from bs4 import BeautifulSoup
import os
import time
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image
import re
import platform
import subprocess
from pathlib import Path
import shutil


TOGGLE_FOR_INVERT_IMAGE_ORDER = False

def sanitize_filename(filename):
    """
    Clean filename by removing illegal characters.
    
    Args:
        filename (str): Original filename
        
    Returns:
        str: Cleaned filename, not exceeding 100 characters
    """
    # Define all punctuation marks to be replaced
    punctuation = '<>:"/\\|?*.,!，。！？、；：""''（）()[]【】《》〈〉『』「」'
    for char in punctuation:
        filename = filename.replace(char, '-')
    # Remove consecutive - symbols
    while '--' in filename:
        filename = filename.replace('--', '-')
    # Remove - from start and end
    filename = filename.strip('-')
    return filename[:100]

def setup_driver():
    """
    Configure Chrome WebDriver settings.
    
    Returns:
        webdriver.Chrome: Configured Chrome WebDriver instance
    """
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    return webdriver.Chrome(options=chrome_options)

def fetch_xiaohongshu_content(url):
    """
    Use Selenium to fetch Xiaohongshu page content.
    
    Args:
        url (str): Xiaohongshu article URL
        
    Returns:
        str or None: Page HTML content, returns None if fetch fails
    """
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36')
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': '''
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            })
        '''
    })
    
    try:
        driver.get(url)
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        last_height = driver.execute_script("return document.body.scrollHeight")
        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
        
        time.sleep(5)
        return driver.page_source
    except Exception as e:
        print(f"Failed to fetch page: {e}")
        return None
    finally:
        driver.quit()

def parse_content(html, note_id):
    """
    Parse HTML content and extract article information.
    
    Args:
        html (str): Page HTML content
        note_id (str): Article ID
        
    Returns:
        tuple: (article text, image URL list, title, author, edit date)
    """
    soup = BeautifulSoup(html, 'html.parser')
    
    # Create debug_html folder (if it doesn't exist)
    debug_folder = 'debug_html'
    if not os.path.exists(debug_folder):
        os.makedirs(debug_folder)
    
    # Save debug HTML
    debug_file = os.path.join(debug_folder, f'debug_{note_id}.html')
    with open(debug_file, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"Debug HTML saved to: {debug_file}")
    
    text = ""
    images = []
    title = ""
    author = ""
    edit_date = ""
    
    # Get title from title tag
    title_tag = soup.find('title')
    if title_tag:
        title = title_tag.get_text().replace(' - Xiaohongshu', '')
    
    # Find author and date
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
    
    # Find content
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
        text = "Content could not be extracted"
    
    # Get images from og:image meta tags
    og_images = soup.find_all('meta', property='og:image') or soup.find_all('meta', attrs={'name': 'og:image'})
    for img in og_images:
        src = img.get('content')
        if src:
            # Ensure HTTPS is used
            if src.startswith('//'):
                src = 'https:' + src
            elif src.startswith('http://'):
                src = 'https://' + src[7:]
            elif not src.startswith('http'):
                src = 'https://' + src.lstrip('/')
            
            # Keep original parameters, no modifications
            if src not in images:
                images.append(src)
    
    print(f"Found {len(images)} images from og:image tags")
    return text, images, title, author, edit_date

def download_images(image_urls, note_id, title, folder='images'):
    """
    Download all images from an article.
    
    Args:
        image_urls (list): List of image URLs
        note_id (str): Article ID
        title (str): Article title
        folder (str): Image save directory
        
    Returns:
        list: List of dictionaries containing image information, each dictionary includes path and size_kb
    """
    safe_title = sanitize_filename(title)
    folder_name = f"{safe_title}_{note_id}" if safe_title else note_id
    note_folder = os.path.join(folder, folder_name)
    if not os.path.exists(note_folder):
        os.makedirs(note_folder)
    
    image_info = []
    
    # Record error messages
    error_log = []
    
    for idx, url in enumerate(image_urls):
        try:
            print(f"Downloading image {idx+1}/{len(image_urls)}: {url}")
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                'Referer': 'https://www.xiaohongshu.com/',
                'Accept': 'image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache',
                'Sec-Ch-Ua': '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
                'Sec-Ch-Ua-Mobile': '?0',
                'Sec-Ch-Ua-Platform': '"macOS"',
                'Sec-Fetch-Dest': 'image',
                'Sec-Fetch-Mode': 'no-cors',
                'Sec-Fetch-Site': 'cross-site'
            }
            
            session = requests.Session()
            response = session.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                img_path = os.path.join(note_folder, f'image_{idx+1}.jpg')
                with open(img_path, 'wb') as handler:
                    handler.write(response.content)
                
                file_size_kb = os.path.getsize(img_path) / 1024
                image_info.append({
                    'path': img_path,
                    'size_kb': file_size_kb
                })
                print(f"Image saved: {img_path}, Size: {file_size_kb:.2f}KB")
            else:
                error_msg = f"Download failed:\nURL: {url}\nTitle: {title}\nImage {idx+1} of {len(image_urls)} failed\nStatus code: {response.status_code}\nResponse content: {response.text[:200]}\n"
                error_log.append(error_msg)
                print(f"Failed to download image, status code: {response.status_code}, URL: {url}")
                print(f"Response content: {response.text[:200]}")
            
            time.sleep(1)
            
        except Exception as e:
            error_msg = f"Download failed:\nURL: {url}\nTitle: {title}\nImage {idx+1} of {len(image_urls)} failed\nError message: {str(e)}\n"
            error_log.append(error_msg)
            print(f"Error occurred while downloading image {url}: {str(e)}")
            continue
    
    # Write to error.txt if there are errors
    if error_log:
        with open('error.txt', 'a', encoding='utf-8') as f:
            f.write('\n'.join(error_log) + '\n' + '-' * 50 + '\n')
    
    if not image_info:
        print("No images were successfully downloaded")
    else:
        print(f"Successfully downloaded {len(image_info)} images")
    
    return image_info

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

def find_chinese_font():
    """
    Find available Chinese fonts.
    
    Returns:
        str or None: Chinese font file path, returns None if not found
    """
    # Common Chinese font names, prioritize TTF format
    chinese_fonts = [
        # macOS common Chinese fonts
        'Songti.ttc',
        'STHeiti Light.ttc',
        'Hiragino Sans GB.ttc',
        # Windows common Chinese fonts
        'simsun.ttc',
        'simhei.ttf',
        'msyh.ttf',
        'simkai.ttf',
        # Linux common Chinese fonts
        'wqy-microhei.ttc',
        'wqy-zenhei.ttc',
        'NotoSansCJK-Regular.ttc',
        'NotoSansSC-Regular.otf'
    ]
    
    # Check project default fonts
    fonts_dir = 'fonts'
    if not os.path.exists(fonts_dir):
        os.makedirs(fonts_dir)
    
    # Default font files
    default_fonts = {
        'noto_sans': 'NotoSansCJK-Regular.otf',
        'noto_serif': 'NotoSerifCJK-Regular.otf'
    }
    
    # Check and download default fonts
    for font_type, font_name in default_fonts.items():
        font_path = os.path.join(fonts_dir, font_name)
        if not os.path.exists(font_path):
            print(f"Downloading default font {font_name}...")
            if font_type == 'noto_sans':
                url = 'https://raw.githubusercontent.com/googlefonts/noto-cjk/main/Sans/SubsetOTF/TC/NotoSansTC-Regular.otf'
            else:
                url = 'https://raw.githubusercontent.com/googlefonts/noto-cjk/main/Serif/SubsetOTF/TC/NotoSerifTC-Regular.otf'
            
            try:
                response = requests.get(url)
                with open(font_path, 'wb') as f:
                    f.write(response.content)
                print(f"Font {font_name} download completed")
            except Exception as e:
                print(f"Failed to download font {font_name}: {e}")
    
    # Look for Chinese fonts in system font directory
    for font_dir in get_system_fonts_path():
        if os.path.exists(font_dir):
            print(f"Searching font directory: {font_dir}")
            for font_name in chinese_fonts:
                font_path = os.path.join(font_dir, font_name)
                if os.path.exists(font_path):
                    try:
                        # Test if font is usable
                        test_font = TTFont('TestFont', font_path)
                        print(f"Found available system font: {font_path}")
                        return font_path
                    except:
                        continue
    
    # If system font not found, use default font
    default_font_path = os.path.join(fonts_dir, default_fonts['noto_sans'])
    if os.path.exists(default_font_path):
        print(f"Using default font: {default_font_path}")
        return default_font_path
    
    print("Error: No available Chinese fonts found")
    return None

def create_pdf(text, image_info, note_id, title, url, author, edit_date, output_folder='pdfs'):
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
    safe_title = sanitize_filename(title)
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    filename = f"{safe_title}_{note_id}.pdf" if safe_title else f"{note_id}.pdf"
    output_path = os.path.join(output_folder, filename)
    
    # Find and register Chinese font
    font_path = find_chinese_font()
    if not font_path:
        print("Error: Cannot find or download suitable Chinese font")
        return None
    
    font_name = 'CustomFont'
    try:
        pdfmetrics.registerFont(TTFont(font_name, font_path))
    except Exception as e:
        print(f"Font registration failed: {e}")
        return None
    
    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4
    
    # Set font size and line spacing
    TITLE_FONT_SIZE = 16
    INFO_FONT_SIZE = 10
    CONTENT_FONT_SIZE = 16  
    LINE_HEIGHT = CONTENT_FONT_SIZE * 1.3
    MARGIN = 50
    
    def create_page():
        if c.getPageNumber() > 0:
            c.showPage()
        c.setFont(font_name, CONTENT_FONT_SIZE)  # Reset font
        return height - MARGIN
    
    # Handle title
    y = height - MARGIN
    c.setFont(font_name, TITLE_FONT_SIZE)
    title_width = c.stringWidth(title, font_name, TITLE_FONT_SIZE)
    if title_width > width - 2 * MARGIN:
        # Handle title line breaks
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
    
    # Draw title
    for line in title_lines:
        if y < MARGIN + LINE_HEIGHT:
            y = create_page()
            c.setFont(font_name, TITLE_FONT_SIZE)  # Reset title font
        c.drawString(MARGIN, y, line)
        y -= TITLE_FONT_SIZE * 1.5
    
    y -= 20  # Space between title and info
    
    # Draw information
    info_lines = []
    
    # Handle URL line breaks
    url_prefix = "URL: "
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
    
    # Add URL to info lines
    info_lines.append(url_prefix)
    for i, part in enumerate(url_parts):
        info_lines.append("    " + part)  # Add indentation
    
    # Add other information
    if author:
        info_lines.append(f"Author: {author}")
    if edit_date:
        info_lines.append(f"Edit date: {edit_date}")
    
    # Draw all info lines
    for line in info_lines:
        if y < MARGIN + LINE_HEIGHT:
            y = create_page()
        c.setFont(font_name, INFO_FONT_SIZE)  # Set info font
        c.drawString(MARGIN, y, line)
        y -= INFO_FONT_SIZE * 1.5
    
    y -= 20  # Space between info and content
    
    # Handle content
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
                c.setFont(font_name, CONTENT_FONT_SIZE)  # Ensure correct font setting
                c.drawString(MARGIN, current_y, current_line)
                current_y -= LINE_HEIGHT
                current_line = word
        
        if current_line:
            if current_y < MARGIN + LINE_HEIGHT:
                current_y = create_page()
            c.setFont(font_name, CONTENT_FONT_SIZE)  # Ensure correct font setting
            c.drawString(MARGIN, current_y, current_line)
            current_y -= LINE_HEIGHT * 1.5  # Paragraph spacing
    
    c.showPage()
    
    # Handle images
    for img_info in image_info:
        try:
            img_path = img_info['path']
            if img_info['size_kb'] <= 1:  # Skip images smaller than 1KB
                continue
                
            img = Image.open(img_path)
            img_width, img_height = img.size
            aspect = img_height / float(img_width)
            
            # Calculate image size on page
            available_width = width - 2 * MARGIN
            available_height = height - 2 * MARGIN
            
            if img_width > available_width:
                img_width = available_width
                img_height = img_width * aspect
            
            if img_height > available_height:
                img_height = available_height
                img_width = img_height / aspect
            
            # Center image
            x = (width - img_width) / 2
            y = (height - img_height) / 2
            
            c.drawImage(img_path, x, y, width=img_width, height=img_height)
            c.showPage()
            
        except Exception as e:
            print(f"Error occurred while processing image {img_path}: {e}")
            continue
    
    try:
        c.save()
        print(f"PDF generated: {output_path}")
        return output_path
    except Exception as e:
        print(f"Error occurred while saving PDF: {e}")
        return None

def extract_note_id(url):
    """
    Extract article ID from URL.
    
    Args:
        url (str): Article URL
        
    Returns:
        str: Article ID
    """
    path = urlparse(url).path
    return path.split('/')[-1].split('?')[0]

def process_url(url):
    """
    Process a single URL, completing the entire workflow from crawling to PDF generation.
    
    Args:
        url (str): Article URL
        
    Returns:
        str or None: Generated PDF file path, returns None if processing fails
    """
    note_id = extract_note_id(url)
    print(f"Processing note ID: {note_id}")
    
    html = fetch_xiaohongshu_content(url)
    if not html:
        print(f"Unable to fetch note content: {url}")
        return
    
    text, image_urls, title, author, edit_date = parse_content(html, note_id)
    if not image_urls:
        print(f"No images found: {url}")
        return
    
    image_info = download_images(image_urls, note_id, title)
    if not image_info:
        print(f"No images successfully downloaded: {url}")
        return
    
    pdf_path = create_pdf(text, image_info, note_id, title, url, author, edit_date)
    
    return pdf_path

def main():
    """
    Main function, reads URL list and processes each URL.
    """
    with open('note-urls.md', 'r', encoding='utf-8') as f:
        content = f.read()
    
    urls = []
    for line in content.split('\n'):
        if 'xiaohongshu.com' in line:
            url = line.strip('- ').strip()
            urls.append(url)
    
    if not urls:
        print("No Xiaohongshu URLs found")
        return
    
    for url in urls:
        print(f"\nStarting to process URL: {url}")
        pdf_path = process_url(url)
        if pdf_path:
            print(f"Successfully generated PDF: {pdf_path}")
        else:
            print(f"Processing failed: {url}")

if __name__ == "__main__":
    main() 
