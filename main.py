import requests
from bs4 import BeautifulSoup
from fpdf import FPDF
import os
import time
from urllib.parse import urlparse
import json
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
import io

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
        # 等待頁面加載
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # 模擬滾動以加載更多內容
        last_height = driver.execute_script("return document.body.scrollHeight")
        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
        
        # 等待一下確保動態內容加載完成
        time.sleep(5)
        return driver.page_source
    except Exception as e:
        print(f"獲取頁面失敗: {e}")
        return None
    finally:
        driver.quit()

def parse_content(html):
    soup = BeautifulSoup(html, 'html.parser')
    
    # 儲存 HTML 以便檢查
    with open('debug.html', 'w', encoding='utf-8') as f:
        f.write(html)
    
    # 嘗試不同的選擇器來找到內容
    text = ""
    
    # 嘗試找到標題
    title_selectors = ['.title', 'h1', '.content h1', '.note-content h1']
    for selector in title_selectors:
        title = soup.select_one(selector)
        if title:
            text += title.get_text(strip=True) + "\n\n"
            break
    
    # 嘗試找到主要內容
    content_selectors = ['.content', '.note-content', 'article', '.desc']
    for selector in content_selectors:
        content = soup.select_one(selector)
        if content:
            text += content.get_text(strip=True) + "\n"
            break
    
    if not text:
        text = "無法提取內容"
    
    # 嘗試不同的方式找圖片
    images = []
    img_selectors = [
        'img.note-image', 
        'img[data-src]', 
        'img[src*="xhscdn"]',
        '.note-content img',
        '.content img',
        'article img'
    ]
    
    for img_selector in img_selectors:
        images.extend(soup.select(img_selector))
    
    image_urls = []
    for img in images:
        src = img.get('data-src') or img.get('src')
        if src and (src.startswith('http') or src.startswith('//')):
            if src.startswith('//'):
                src = 'https:' + src
            if src not in image_urls:  # 避免重複
                image_urls.append(src)
    
    return text, image_urls

def download_images(image_urls, note_id, folder='images'):
    note_folder = os.path.join(folder, note_id)
    if not os.path.exists(note_folder):
        os.makedirs(note_folder)
    
    local_paths = []
    for idx, url in enumerate(image_urls):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                # 計算檔案大小（以KB為單位）
                file_size_kb = len(response.content) / 1024
                
                # 只有當檔案大於40KB時才保存並加入到local_paths
                if file_size_kb > 40:
                    img_path = os.path.join(note_folder, f'image_{idx+1}.jpg')
                    with open(img_path, 'wb') as handler:
                        handler.write(response.content)
                    local_paths.append(img_path)
                    print(f"已保存大於40KB的圖片: {img_path}, 大小: {file_size_kb:.2f}KB")
                else:
                    print(f"跳過小於40KB的圖片, 大小: {file_size_kb:.2f}KB")
                
                time.sleep(0.5)  # 避免請求過快
        except Exception as e:
            print(f"下載圖片失敗 {url}: {e}")
    return local_paths

def create_pdf(text, image_paths, note_id, output_folder='pdfs'):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    output_path = os.path.join(output_folder, f'{note_id}.pdf')
    
    # 註冊中文字體
    try:
        pdfmetrics.registerFont(TTFont('fireflysung', 'fireflysung.ttf'))
    except:
        print("無法載入中文字體，將使用預設字體")
    
    # 創建 PDF
    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4
    
    # 添加文字
    textobject = c.beginText()
    textobject.setTextOrigin(50, height - 50)
    try:
        textobject.setFont('fireflysung', 12)
    except:
        textobject.setFont('Helvetica', 12)
    
    # 處理文字換行
    words = text.split()
    lines = []
    current_line = []
    
    for word in words:
        current_line.append(word)
        if len(' '.join(current_line)) > 70:  # 根據頁面寬度調整
            lines.append(' '.join(current_line[:-1]))
            current_line = [current_line[-1]]
    if current_line:
        lines.append(' '.join(current_line))
    
    for line in lines:
        textobject.textLine(line)
    
    c.drawText(textobject)
    c.showPage()
    
    # 添加圖片
    for img_path in image_paths:
        try:
            img = Image.open(img_path)
            # 調整圖片大小以適應頁面
            img_width, img_height = img.size
            aspect = img_height / float(img_width)
            
            # 設定最大寬度為頁面寬度的 90%
            max_width = width * 0.9
            max_height = height * 0.9
            
            new_width = min(img_width, max_width)
            new_height = new_width * aspect
            
            # 如果高度超出頁面，則根據高度調整
            if new_height > max_height:
                new_height = max_height
                new_width = new_height / aspect
            
            # 計算居中位置
            x = (width - new_width) / 2
            y = (height - new_height) / 2
            
            c.drawImage(img_path, x, y, width=new_width, height=new_height)
            c.showPage()
        except Exception as e:
            print(f"處理圖片時發生錯誤 {img_path}: {e}")
    
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
    
    text, image_urls = parse_content(html)
    if not image_urls:
        print(f"沒有找到圖片: {url}")
        return
    
    image_paths = download_images(image_urls, note_id)
    if not image_paths:
        print(f"沒有成功下載的圖片: {url}")
        return
    
    pdf_path = create_pdf(text, image_paths, note_id)
    return pdf_path

def main():
    # 從 spec.md 讀取網址
    with open('spec.md', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 提取所有網址
    urls = []
    for line in content.split('\n'):
        if 'xiaohongshu.com' in line:
            url = line.strip('- ').strip()
            urls.append(url)
    
    if not urls:
        print("沒有找到小紅書網址")
        return
    
    # 處理每個網址
    for url in urls:
        print(f"\n開始處理網址: {url}")
        pdf_path = process_url(url)
        if pdf_path:
            print(f"成功生成 PDF: {pdf_path}")
        else:
            print(f"處理失敗: {url}")

if __name__ == "__main__":
    main() 
