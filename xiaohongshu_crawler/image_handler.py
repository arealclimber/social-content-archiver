"""
Image processing module, responsible for downloading and processing images
"""

import os
import requests
from .utils import sanitize_filename

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
            
        except Exception as e:
            error_msg = f"Download failed:\nURL: {url}\nTitle: {title}\nImage {idx+1} of {len(image_urls)} failed\nError message: {str(e)}\n"
            error_log.append(error_msg)
            print(f"Error occurred while downloading image {url}: {str(e)}")
            continue
    
    # Write to error.txt if there are any errors
    if error_log:
        with open('error.txt', 'a', encoding='utf-8') as f:
            f.write('\n'.join(error_log) + '\n' + '-' * 50 + '\n')
    
    if not image_info:
        print("No images were successfully downloaded")
    else:
        print(f"Successfully downloaded {len(image_info)} images")
    
    return image_info 
