from bs4 import BeautifulSoup
import json
import os
from pathlib import Path

def normalize_url(url):
    # 檢查並處理URL前綴
    if url and not url.startswith('https://www.xiaohongshu.com'):
        # 如果是以 / 開頭的相對路徑，直接加上域名
        if url.startswith('/'):
            return f'https://www.xiaohongshu.com{url}'
        # 如果不是以 / 開頭，加上 / 再加域名
        return f'https://www.xiaohongshu.com/{url}'
    return url

def parse_html_links(html_content, filename):
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 提取作者名稱
    author_name = ""
    og_title = soup.find('meta', attrs={'name': 'og:title'})
    if og_title and og_title.get('content'):
        author_name = og_title.get('content').replace(' - 小红书', '')
    
    # 找到所有 class 為 'cover ld mask' 的 a 標籤
    links = soup.find_all('a', class_='cover ld mask')
    
    # 找到所有 class 為 'title' 的 a 標籤，並提取其中的 span 文字
    titles = []
    title_links = soup.find_all('a', class_='title')
    for title_link in title_links:
        span = title_link.find('span')
        if span and span.text:
            titles.append(span.text.strip())
    
    # 提取所有href並進行URL正規化
    hrefs = [normalize_url(link.get('href')) for link in links if link.get('href')]
    
    return {
        "filename": filename,
        "author_name": author_name,
        "links": hrefs,
        "links_count": len(hrefs),
        "titles": titles,
        "titles_count": len(titles)
    }

def process_html_files():
    # 指定HTML檔案所在的資料夾
    html_dir = Path("author_html_manually")
    
    # 確保資料夾存在
    if not html_dir.exists():
        print(f"資料夾 {html_dir} 不存在")
        return
    
    results = []
    all_links = []  # 收集所有連結
    
    # 處理資料夾中的所有HTML檔案
    for html_file in html_dir.glob("*.html"):
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
                result = parse_html_links(html_content, html_file.name)
                results.append(result)
                all_links.extend(result['links'])  # 將此檔案的連結加入總清單
                print(f"已處理檔案: {html_file.name}")
        except Exception as e:
            print(f"處理檔案 {html_file.name} 時發生錯誤: {str(e)}")
    
    # 將結果寫入JSON檔案
    output_file = "notes_in_author.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    # 將所有連結寫入Markdown檔案
    markdown_file = "notes_in_author.md"
    with open(markdown_file, 'w', encoding='utf-8') as f:
        for link in all_links:
            f.write(f"- {link}\n")
    
    print(f"\n處理完成！")
    print(f"JSON結果已寫入 {output_file}")
    print(f"Markdown連結清單已寫入 {markdown_file}")
    print(f"共處理 {len(results)} 個檔案")
    print(f"共收集 {len(all_links)} 個連結")

# 測試用的HTML片段
test_html = '''
<div class=active-tag style=width:64px;left:367px></div></div></div></div><div class=feeds-tab-container style="--932db6be:all 0.4s cubic-bezier(0.2,0,0.25,1) 0s" data-v-6bdf495c><div class=transform-container style=transform:translate(0px,0px);width:1722px data-v-6bdf495c><div class=tab-content-item style=height:auto;width:837px;overflow:scroll data-v-6bdf495c data-v-2df074e3><div id=userPostedFeeds class=feeds-container style=width:100%;height:10874px;visibility:visible data-v-7aab4d45><section data-v-14f91c23 data-v-7aab4d45 class=note-item data-width=1440 data-height=1920 data-index=65 style=transform:translate(287px,9180px);--53f1d28e:263px;--2db87601:16px;--1013328c:blur(42.5px)><div data-v-14f91c23><a data-v-14f91c23 href=https://www.xiaohongshu.com/explore/66dd697000000000270041f1 style=display:none></a><a data-v-14f91c23 class="cover ld mask" target=_self href="https://www.xiaohongshu.com/user/profile/60f05b47000000000100858d/66dd697000000000270041f1?xsec_token=AB9AdfNKi9WLesqu75iyU9X49jY4IV8bFsDQ7QpLg77yg=&amp;xsec_source=pc_user" style=height:351px><img data-v-14f91c23 src="data:image/webp;base64,">
'''

if __name__ == "__main__":
    process_html_files()
