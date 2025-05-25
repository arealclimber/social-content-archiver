from bs4 import BeautifulSoup
import json
import os
import re
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
        author_name = og_title.get('content').replace(' - Xiaohongshu', '').replace(' - 小红书', '')
    
    # Extract user profile base URL from og:url meta tag
    user_profile_base = ""
    og_url = soup.find('meta', attrs={'name': 'og:url'})
    if og_url and og_url.get('content'):
        user_profile_base = og_url.get('content')
    
    # Target user profile base
    target_profile = "https://www.xiaohongshu.com/user/profile/60f05b47000000000100858d"
    
    # Find all links that match the article pattern
    all_links = soup.find_all('a', href=True)
    article_links = []
    
    for link in all_links:
        href = link.get('href')
        if href:
            # Normalize the URL to full format
            if href.startswith('/'):
                full_url = f'https://www.xiaohongshu.com{href}'
            elif href.startswith('https://'):
                full_url = href
            else:
                full_url = f'https://www.xiaohongshu.com/{href}'
            
            # Check if it starts with the target profile and has a note_id
            if full_url.startswith(target_profile + '/'):
                # Extract the part after the profile URL
                remaining_part = full_url[len(target_profile + '/'):]
                # Check if it contains a note_id (hex string of at least 16 characters)
                note_id_match = re.match(r'^([0-9a-f]{16,})', remaining_part)
                if note_id_match:
                    article_links.append(full_url)
    
    # Remove duplicates while preserving order
    unique_links = []
    seen = set()
    for link in article_links:
        # Extract the note_id part (after the user_id) for comparison
        # Pattern: /user/profile/{user_id}/{note_id}?...
        note_id_match = re.search(r'/user/profile/[0-9a-f]+/([0-9a-f]{16,})', link)
        if note_id_match:
            note_id = note_id_match.group(1)
            if note_id not in seen:
                unique_links.append(link)
                seen.add(note_id)
    
    # Find all 'a' tags with class 'title' and extract span text
    titles = []
    title_links = soup.find_all('a', class_='title')
    for title_link in title_links:
        span = title_link.find('span')
        if span and span.text:
            titles.append(span.text.strip())
    
    return {
        "filename": filename,
        "author_name": author_name,
        "user_profile_base": user_profile_base,
        "links": unique_links,
        "links_count": len(unique_links),
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
    all_note_ids = set()  # Track all unique note IDs globally
    
    # Process all HTML files in the folder
    for html_file in html_dir.glob("*.html"):
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
                result = parse_html_links(html_content, html_file.name)
                results.append(result)
                
                # Add unique links to global list
                for link in result['links']:
                    note_id_match = re.search(r'/user/profile/[0-9a-f]+/([0-9a-f]{16,})', link)
                    if note_id_match:
                        note_id = note_id_match.group(1)
                        if note_id not in all_note_ids:
                            all_links.append(link)
                            all_note_ids.add(note_id)
                
                print(f"Processed file: {html_file.name}")
                print(f"  Found {result['links_count']} unique article links in this file")
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
    print(f"Collected {len(all_links)} unique article links globally")

# Test HTML fragment
test_html = '''
<div class=active-tag style=width:64px;left:367px></div></div></div></div><div class=feeds-tab-container style="--932db6be:all 0.4s cubic-bezier(0.2,0,0.25,1) 0s" data-v-6bdf495c><div class=transform-container style=transform:translate(0px,0px);width:1722px data-v-6bdf495c><div class=tab-content-item style=height:auto;width:837px;overflow:scroll data-v-6bdf495c data-v-2df074e3><div id=userPostedFeeds class=feeds-container style=width:100%;height:10874px;visibility:visible data-v-7aab4d45><section data-v-14f91c23 data-v-7aab4d45 class=note-item data-width=1440 data-height=1920 data-index=65 style=transform:translate(287px,9180px);--53f1d28e:263px;--2db87601:16px;--1013328c:blur(42.5px)><div data-v-14f91c23><a data-v-14f91c23 href=https://www.xiaohongshu.com/explore/66dd697000000000270041f1 style=display:none></a><a data-v-14f91c23 class="cover ld mask" target=_self href="https://www.xiaohongshu.com/user/profile/60f05b47000000000100858d/66dd697000000000270041f1?xsec_token=AB9AdfNKi9WLesqu75iyU9X49jY4IV8bFsDQ7QpLg77yg=&amp;xsec_source=pc_user" style=height:351px><img data-v-14f91c23 src="data:image/webp;base64,">
'''

if __name__ == "__main__":
    process_html_files()
