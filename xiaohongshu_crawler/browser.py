"""
瀏覽器模組，負責與網頁互動和內容獲取
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import json
import re
import os

def setup_driver():
    """
    設置Chrome WebDriver的配置。
    
    Returns:
        webdriver.Chrome: 配置好的Chrome WebDriver實例
    """
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36')
    chrome_options.add_argument('--window-size=1920,1080')
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': '''
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            })
        '''
    })
    return driver

def fetch_xiaohongshu_content(url):
    """
    使用Selenium獲取小紅書頁面內容。
    
    Args:
        url (str): 小紅書文章URL
        
    Returns:
        str or None: 頁面HTML內容，如果獲取失敗則返回None
    """
    driver = setup_driver()
    
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

def get_author_notes(author_url):
    """
    獲取作者的所有筆記URL。
    
    Args:
        author_url (str): 作者主頁URL
        
    Returns:
        list: 筆記URL列表
    """
    driver = setup_driver()
    note_urls = []
    
    try:
        print(f"正在訪問作者頁面: {author_url}")
        driver.get(author_url)
        
        # 等待頁面主要內容加載
        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='main']"))
            )
        except TimeoutException:
            print("頁面加載超時，嘗試繼續處理...")
        
        print("等待頁面完全加載（5秒）...")
        time.sleep(5)  # 給予更多時間加載
        
        # 先嘗試滾動一次，觸發動態加載
        driver.execute_script("window.scrollTo(0, 300);")
        time.sleep(2)
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(2)
        
        print("正在保存初始HTML...")
        # 保存初始HTML以供調試
        initial_html = driver.page_source
        debug_folder = 'debug_html'
        if not os.path.exists(debug_folder):
            os.makedirs(debug_folder)
        
        author_id = author_url.split('/')[-1]
        with open(os.path.join(debug_folder, f'author_page_{author_id}.html'), 'w', encoding='utf-8') as f:
            f.write(initial_html)
        print(f"已保存作者頁面HTML到: debug_html/author_page_{author_id}.html")
        
        scroll_count = 0
        max_scroll_attempts = 30  # 最大滾動次數
        no_new_content_count = 0
        
        while scroll_count < max_scroll_attempts:
            # 獲取當前頁面上的所有筆記連結
            try:
                # 使用更精確的選擇器，包括 cover ld mask 相關元素
                note_elements = driver.find_elements(By.CSS_SELECTOR, 
                    "a[href*='/explore/'], a[href*='/discovery/'], a[href*='/note/'], .cover.ld.mask, [class*='note-item']")
                
                current_count = len(note_urls)
                
                for element in note_elements:
                    try:
                        # 嘗試從元素或其父元素獲取href
                        href = element.get_attribute('href')
                        if not href:
                            # 如果元素本身沒有href，嘗試查找父元素或子元素
                            parent = element.find_element(By.XPATH, "./..")
                            href = parent.get_attribute('href')
                        if not href:
                            # 嘗試查找子元素中的連結
                            links = element.find_elements(By.TAG_NAME, "a")
                            for link in links:
                                href = link.get_attribute('href')
                                if href:
                                    break
                        
                        if href and ('explore' in href or 'discovery' in href or 'note' in href):
                            if href not in note_urls:
                                note_urls.append(href)
                    except Exception as e:
                        print(f"處理單個元素時發生錯誤: {e}")
                        continue
                
                if len(note_urls) > current_count:
                    print(f"已找到 {len(note_urls)} 篇筆記")
                    no_new_content_count = 0
                else:
                    no_new_content_count += 1
                
                # 每次滾動後保存當前HTML（增加等待時間）
                if scroll_count % 5 == 0:  # 每5次滾動保存一次
                    print(f"等待頁面穩定（3秒）...")
                    time.sleep(3)  # 等待頁面穩定
                    current_html = driver.page_source
                    with open(os.path.join(debug_folder, f'author_page_{author_id}_scroll_{scroll_count}.html'), 'w', encoding='utf-8') as f:
                        f.write(current_html)
                    print(f"已保存滾動後的HTML到: debug_html/author_page_{author_id}_scroll_{scroll_count}.html")
                
                if no_new_content_count >= 3:  # 如果連續3次沒有新內容，就停止
                    print("已經沒有新的筆記了")
                    print("等待最終頁面加載（5秒）...")
                    time.sleep(5)  # 最終保存前多等待
                    # 保存最終HTML
                    final_html = driver.page_source
                    with open(os.path.join(debug_folder, f'author_page_{author_id}_final.html'), 'w', encoding='utf-8') as f:
                        f.write(final_html)
                    print(f"已保存最終HTML到: debug_html/author_page_{author_id}_final.html")
                    break
                
            except Exception as e:
                print(f"解析筆記時發生錯誤: {e}")
            
            # 滾動頁面
            try:
                last_height = driver.execute_script("return document.body.scrollHeight")
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)  # 增加等待時間
                
                # 檢查是否已滾動到底
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    no_new_content_count += 1
                else:
                    no_new_content_count = 0
                
                # 隨機上下滾動以模擬真實用戶行為
                if scroll_count % 3 == 0:
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.8);")
                    time.sleep(1)
                
            except Exception as e:
                print(f"滾動頁面時發生錯誤: {e}")
            
            scroll_count += 1
        
        # 確保URL格式正確
        cleaned_urls = []
        for url in note_urls:
            if url and isinstance(url, str):
                if not url.startswith('http'):
                    url = f"https://www.xiaohongshu.com{url}"
                cleaned_urls.append(url)
        
        return list(set(cleaned_urls))  # 去重
        
    except Exception as e:
        print(f"獲取作者筆記失敗: {e}")
        return []
    finally:
        driver.quit() 
