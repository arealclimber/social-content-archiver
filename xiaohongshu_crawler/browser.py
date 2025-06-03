"""
Browser module, responsible for web page interaction and content retrieval
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
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
    Configure Chrome WebDriver settings.
    
    Returns:
        webdriver.Chrome: Configured Chrome WebDriver instance
    """
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--disable-plugins')
    chrome_options.add_argument('--disable-images')  # Speed up loading
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36')
    chrome_options.add_argument('--window-size=1920,1080')
    
    # Docker-specific options
    chrome_options.add_argument('--remote-debugging-port=9222')
    chrome_options.add_argument('--disable-background-timer-throttling')
    chrome_options.add_argument('--disable-backgrounding-occluded-windows')
    chrome_options.add_argument('--disable-renderer-backgrounding')
    
    # Set Chrome binary path if in Docker
    chrome_bin = os.environ.get('CHROME_BIN')
    if chrome_bin:
        chrome_options.binary_location = chrome_bin
    
    # Set up ChromeDriver service with explicit path
    chromedriver_path = os.environ.get('CHROMEDRIVER_PATH', '/usr/bin/chromedriver')
    service = Service(executable_path=chromedriver_path)
    
    driver = webdriver.Chrome(service=service, options=chrome_options)
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
    Use Selenium to fetch Xiaohongshu page content.
    
    Args:
        url (str): Xiaohongshu article URL
        
    Returns:
        str or None: Page HTML content, returns None if fetch fails
    """
    driver = setup_driver()
    
    try:
        print(f"Accessing URL: {url}")
        driver.get(url)
        
        # Wait for redirection to complete
        if 'xhslink.com' in url:
            print("Detected short URL, waiting for redirection...")
            time.sleep(5)  # Give enough time for redirection
            current_url = driver.current_url
            print(f"Redirected to: {current_url}")
        
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

def get_author_notes(author_url):
    """
    Get all note URLs from an author.
    
    Args:
        author_url (str): Author's profile URL
        
    Returns:
        list: List of note URLs
    """
    driver = setup_driver()
    note_urls = []
    
    try:
        print(f"Accessing author's page: {author_url}")
        driver.get(author_url)
        
        # Wait for main content to load
        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='main']"))
            )
        except TimeoutException:
            print("Page load timeout, attempting to continue...")
        
        print("Waiting for page to fully load (5 seconds)...")
        time.sleep(5)  # Give more time to load
        
        # First try to scroll once to trigger dynamic loading
        driver.execute_script("window.scrollTo(0, 300);")
        time.sleep(2)
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(2)
        
        print("Saving initial HTML...")
        # Save initial HTML for debugging
        initial_html = driver.page_source
        debug_folder = 'debug_html'
        if not os.path.exists(debug_folder):
            os.makedirs(debug_folder)
        
        author_id = author_url.split('/')[-1]
        with open(os.path.join(debug_folder, f'author_page_{author_id}.html'), 'w', encoding='utf-8') as f:
            f.write(initial_html)
        print(f"Author page HTML saved to: debug_html/author_page_{author_id}.html")
        
        scroll_count = 0
        max_scroll_attempts = 30  # Maximum number of scroll attempts
        no_new_content_count = 0
        
        while scroll_count < max_scroll_attempts:
            # Get all note links on current page
            try:
                # Use more precise selectors, including cover ld mask related elements
                note_elements = driver.find_elements(By.CSS_SELECTOR, 
                    "a[href*='/explore/'], a[href*='/discovery/'], a[href*='/note/'], .cover.ld.mask, [class*='note-item']")
                
                current_count = len(note_urls)
                
                for element in note_elements:
                    try:
                        # Try to get href from element or its parent
                        href = element.get_attribute('href')
                        if not href:
                            # If element itself has no href, try to find parent element or child elements
                            parent = element.find_element(By.XPATH, "./..")
                            href = parent.get_attribute('href')
                        if not href:
                            # Try to find links in child elements
                            links = element.find_elements(By.TAG_NAME, "a")
                            for link in links:
                                href = link.get_attribute('href')
                                if href:
                                    break
                        
                        if href and ('explore' in href or 'discovery' in href or 'note' in href):
                            if href not in note_urls:
                                note_urls.append(href)
                    except Exception as e:
                        print(f"Error processing individual element: {e}")
                        continue
                
                if len(note_urls) > current_count:
                    print(f"Found {len(note_urls)} notes")
                    no_new_content_count = 0
                else:
                    no_new_content_count += 1
                
                # Save current HTML after each scroll (with increased wait time)
                if scroll_count % 5 == 0:  # Save every 5 scrolls
                    print(f"Waiting for page to stabilize (3 seconds)...")
                    time.sleep(3)  # Wait for page to stabilize
                    current_html = driver.page_source
                    with open(os.path.join(debug_folder, f'author_page_{author_id}_scroll_{scroll_count}.html'), 'w', encoding='utf-8') as f:
                        f.write(current_html)
                    print(f"Scroll HTML saved to: debug_html/author_page_{author_id}_scroll_{scroll_count}.html")
                
                if no_new_content_count >= 3:  # Stop if no new content for 3 consecutive times
                    print("No more new notes")
                    print("Waiting for final page load (5 seconds)...")
                    time.sleep(5)  # Wait longer before final save
                    # Save final HTML
                    final_html = driver.page_source
                    with open(os.path.join(debug_folder, f'author_page_{author_id}_final.html'), 'w', encoding='utf-8') as f:
                        f.write(final_html)
                    print(f"Final HTML saved to: debug_html/author_page_{author_id}_final.html")
                    break
                
            except Exception as e:
                print(f"Error parsing notes: {e}")
            
            # Scroll page
            try:
                last_height = driver.execute_script("return document.body.scrollHeight")
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)  # Increase wait time
                
                # Check if scrolled to bottom
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    no_new_content_count += 1
                else:
                    no_new_content_count = 0
                
                # Random up and down scrolling to simulate real user behavior
                if scroll_count % 3 == 0:
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.8);")
                    time.sleep(1)
                
            except Exception as e:
                print(f"Error scrolling page: {e}")
            
            scroll_count += 1
        
        # Ensure correct URL format
        cleaned_urls = []
        for url in note_urls:
            if url and isinstance(url, str):
                if not url.startswith('http'):
                    url = f"https://www.xiaohongshu.com{url}"
                cleaned_urls.append(url)
        
        return list(set(cleaned_urls))  # Remove duplicates
        
    except Exception as e:
        print(f"Failed to get author's notes: {e}")
        return []
    finally:
        driver.quit() 
