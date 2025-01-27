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
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from PIL import Image

def sanitize_filename(filename):
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename[:100]

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    return webdriver.Chrome(options=chrome_options)

def fetch_xiaohongshu_content(url):
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
        print(f"獲取頁面失敗: {e}")
        return None
    finally:
        driver.quit()

def parse_content(html, note_id):
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
            
            # 處理圖片 URL
            base_url = src.split('!')[0]  # 移除現有參數
            if 'xhscdn.com' in base_url:
                # 添加必要的參數
                src = f"{base_url}!nd_dft_wlteh_webp_3"
            
            if src not in images:
                images.append(src)
    
    print(f"從 og:image 標籤找到 {len(images)} 張圖片")
    return text, images, title, author, edit_date

def download_images(image_urls, note_id, title, folder='images'):
    safe_title = sanitize_filename(title)
    folder_name = f"{safe_title}_{note_id}" if safe_title else note_id
    note_folder = os.path.join(folder, folder_name)
    if not os.path.exists(note_folder):
        os.makedirs(note_folder)
    
    image_info = []
    for idx, url in enumerate(image_urls):
        try:
            print(f"正在下載圖片 {idx+1}/{len(image_urls)}: {url}")
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
                print(f"已保存圖片: {img_path}, 大小: {file_size_kb:.2f}KB")
            else:
                print(f"下載圖片失敗，狀態碼: {response.status_code}, URL: {url}")
                print(f"回應內容: {response.text[:200]}")  # 只顯示前200個字符
            
            time.sleep(1)  # 增加延遲時間
            
        except Exception as e:
            print(f"下載圖片時發生錯誤 {url}: {str(e)}")
            continue
    
    if not image_info:
        print("沒有成功下載任何圖片")
    else:
        print(f"成功下載 {len(image_info)} 張圖片")
    
    return image_info

def create_pdf(text, image_info, note_id, title, url, author, edit_date, output_folder='pdfs'):
    safe_title = sanitize_filename(title)
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    filename = f"{safe_title}_{note_id}.pdf" if safe_title else f"{note_id}.pdf"
    output_path = os.path.join(output_folder, filename)
    
    # 使用內建的 CID 字體
    pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))
    
    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4
    
    # 第一頁：標題和資訊
    textobject = c.beginText()
    textobject.setTextOrigin(50, height - 50)
    textobject.setFont('STSong-Light', 16)
    
    textobject.textLine(title)
    textobject.moveCursor(0, 20)
    
    textobject.setFont('STSong-Light', 12)
    
    textobject.textLine(f"網址：{url}")
    textobject.moveCursor(0, 10)
    
    if author:
        textobject.textLine(f"作者：{author}")
        textobject.moveCursor(0, 10)
    
    if edit_date:
        textobject.textLine(f"編輯日期：{edit_date}")
        textobject.moveCursor(0, 10)
    
    c.drawText(textobject)
    c.showPage()
    
    # 第二頁：內容
    textobject = c.beginText()
    textobject.setTextOrigin(50, height - 50)
    textobject.setFont('STSong-Light', 12)
    
    # 改進文本分行處理
    def split_text_to_lines(text, max_chars=40):
        lines = []
        current_line = ""
        
        for char in text:
            current_line += char
            if len(current_line) >= max_chars:
                lines.append(current_line)
                current_line = ""
        
        if current_line:
            lines.append(current_line)
        
        return lines
    
    lines = split_text_to_lines(text)
    for line in lines:
        textobject.textLine(line)
    
    c.drawText(textobject)
    c.showPage()
    
    # 圖片頁面
    valid_images = [img for img in image_info if img['size_kb'] > 1]
    TOGGLE_FOR_INVERT_IMAGE_ORDER = False
    
    if valid_images:
        if TOGGLE_FOR_INVERT_IMAGE_ORDER:
            first_image = valid_images.pop(0)
            valid_images.append(first_image)
        
        for img_info in valid_images:
            try:
                img_path = img_info['path']
                img = Image.open(img_path)
                img_width, img_height = img.size
                aspect = img_height / float(img_width)
                
                max_width = width * 0.9
                max_height = height * 0.9
                
                new_width = min(img_width, max_width)
                new_height = new_width * aspect
                
                if new_height > max_height:
                    new_height = max_height
                    new_width = new_height / aspect
                
                x = (width - new_width) / 2
                y = (height - new_height) / 2
                
                c.drawImage(img_path, x, y, width=new_width, height=new_height)
                c.showPage()
                print(f"已加入PDF的圖片: {img_path}, 大小: {img_info['size_kb']:.2f}KB")
            except Exception as e:
                print(f"處理圖片時發生錯誤 {img_path}: {e}")
    else:
        print("沒有找到大於40KB的圖片")
    
    c.save()
    print(f"PDF已生成：{output_path}")
    return output_path

def extract_note_id(url):
    path = urlparse(url).path
    return path.split('/')[-1].split('?')[0]

def process_url(url):
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
    with open('spec.md', 'r', encoding='utf-8') as f:
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
