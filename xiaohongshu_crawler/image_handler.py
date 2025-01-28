"""
圖片處理模組，負責下載和處理圖片
"""

import os
import requests
from .utils import sanitize_filename

def download_images(image_urls, note_id, title, folder='images'):
    """
    下載文章中的所有圖片。
    
    Args:
        image_urls (list): 圖片URL列表
        note_id (str): 文章ID
        title (str): 文章標題
        folder (str): 圖片保存目錄
        
    Returns:
        list: 包含圖片信息的字典列表，每個字典包含path和size_kb
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
                error_msg = f"下載失敗：\n網址：{url}\n標題：{title}\n第 {idx+1} 張圖片下載失敗（共 {len(image_urls)} 張）\n狀態碼：{response.status_code}\n回應內容：{response.text[:200]}\n"
                error_log.append(error_msg)
                print(f"下載圖片失敗，狀態碼: {response.status_code}, URL: {url}")
                print(f"回應內容: {response.text[:200]}")
            
        except Exception as e:
            error_msg = f"下載失敗：\n網址：{url}\n標題：{title}\n第 {idx+1} 張圖片下載失敗（共 {len(image_urls)} 張）\n錯誤信息：{str(e)}\n"
            error_log.append(error_msg)
            print(f"下載圖片時發生錯誤 {url}: {str(e)}")
            continue
    
    # 如果有錯誤，寫入 error.txt
    if error_log:
        with open('error.txt', 'a', encoding='utf-8') as f:
            f.write('\n'.join(error_log) + '\n' + '-' * 50 + '\n')
    
    if not image_info:
        print("沒有成功下載任何圖片")
    else:
        print(f"成功下載 {len(image_info)} 張圖片")
    
    return image_info 
