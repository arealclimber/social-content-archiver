from bs4 import BeautifulSoup
import json
import os
from pathlib import Path

def normalize_url(url):
    # Check and process URL prefix
    if url and not url.startswith('https://www.xiaohongshu.com'):
        # If it's a relative path starting with /, add domain directly
        if url.startswith('/'):
            return f'https://www.xiaohongshu.com{url}'
        # If it doesn't start with /, add / then domain
        return f'https://www.xiaohongshu.com/{url}'
    return url

def parse_html_links(html_content, filename):
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Extract author name
    author_name = ""
    og_title = soup.find('meta', attrs={'name': 'og:title'})
    if og_title and og_title.get('content'):
        author_name = og_title.get('content').replace(' - Xiaohongshu', '')
    
    # Find all 'a' tags with class 'cover ld mask'
    links = soup.find_all('a', class_='cover ld mask')
    
    # Find all 'a' tags with class 'title' and extract span text
    titles = []
    title_links = soup.find_all('a', class_='title')
    for title_link in title_links:
        span = title_link.find('span')
        if span and span.text:
            titles.append(span.text.strip())
    
    # Extract all hrefs and normalize URLs
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
    # Specify the folder containing HTML files
    html_dir = Path("author_html_manually")
    
    # Ensure folder exists
    if not html_dir.exists():
        print(f"Folder {html_dir} does not exist")
        return
    
    results = []
    all_links = []  # Collect all links
    
    # Process all HTML files in the folder
    for html_file in html_dir.glob("*.html"):
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
                result = parse_html_links(html_content, html_file.name)
                results.append(result)
                all_links.extend(result['links'])  # Add links from this file to total list
                print(f"Processed file: {html_file.name}")
        except Exception as e:
            print(f"Error processing file {html_file.name}: {str(e)}")
    
    # Write results to JSON file
    output_file = "notes_in_author.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    # Write all links to Markdown file
    markdown_file = "notes_in_author.md"
    with open(markdown_file, 'w', encoding='utf-8') as f:
        for link in all_links:
            f.write(f"- {link}\n")
    
    print(f"\nProcessing completed!")
    print(f"JSON results written to {output_file}")
    print(f"Markdown link list written to {markdown_file}")
    print(f"Processed {len(results)} files")
    print(f"Collected {len(all_links)} links")

# Test HTML fragment
test_html = '''
<div class=active-tag style=width:64px;left:367px></div></div></div></div><div class=feeds-tab-container style="--932db6be:all 0.4s cubic-bezier(0.2,0,0.25,1) 0s" data-v-6bdf495c><div class=transform-container style=transform:translate(0px,0px);width:1722px data-v-6bdf495c><div class=tab-content-item style=height:auto;width:837px;overflow:scroll data-v-6bdf495c data-v-2df074e3><div id=userPostedFeeds class=feeds-container style=width:100%;height:10874px;visibility:visible data-v-7aab4d45><section data-v-14f91c23 data-v-7aab4d45 class=note-item data-width=1440 data-height=1920 data-index=65 style=transform:translate(287px,9180px);--53f1d28e:263px;--2db87601:16px;--1013328c:blur(42.5px)><div data-v-14f91c23><a data-v-14f91c23 href=https://www.xiaohongshu.com/explore/66dd697000000000270041f1 style=display:none></a><a data-v-14f91c23 class="cover ld mask" target=_self href="https://www.xiaohongshu.com/user/profile/60f05b47000000000100858d/66dd697000000000270041f1?xsec_token=AB9AdfNKi9WLesqu75iyU9X49jY4IV8bFsDQ7QpLg77yg=&amp;xsec_source=pc_user" style=height:351px><img data-v-14f91c23 src="data:image/webp;base64,">
'''

if __name__ == "__main__":
    process_html_files()
