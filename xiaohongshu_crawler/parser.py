"""
HTML parsing module, responsible for parsing webpage content and extracting required information
"""

from bs4 import BeautifulSoup
import os

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
        title = title_tag.get_text().replace(' - 小红书', '')
    
    # Find author and date
    author_selectors = ['.user-name', '.author-name', '.nickname', '.username']
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
