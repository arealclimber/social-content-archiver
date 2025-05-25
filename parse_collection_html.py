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

def parse_collection_html_links(html_content, filename):
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Extract collection name
    collection_name = ""
    og_title = soup.find('meta', attrs={'name': 'og:title'})
    if og_title and og_title.get('content'):
        collection_name = og_title.get('content').replace(' - Xiaohongshu', '').replace(' - 小红书', '')
    
    # Extract collection base URL from og:url meta tag
    collection_base = ""
    og_url = soup.find('meta', attrs={'name': 'og:url'})
    if og_url and og_url.get('content'):
        collection_base = og_url.get('content')
    
    # Find all links that match the board pattern
    all_links = soup.find_all('a', href=True)
    board_links = []
    
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
            
            # Check if it matches the board pattern: /board/{board_id}/{note_id}
            board_match = re.match(r'https://www\.xiaohongshu\.com/board/([0-9a-f]{16,})/([0-9a-f]{16,})', full_url)
            if board_match:
                board_id = board_match.group(1)
                note_id = board_match.group(2)
                # Clean URL by removing query parameters
                clean_url = f'https://www.xiaohongshu.com/board/{board_id}/{note_id}'
                board_links.append(clean_url)
    
    # Remove duplicates while preserving order
    unique_links = []
    seen = set()
    for link in board_links:
        # Extract the note_id part for comparison
        note_id_match = re.search(r'/board/[0-9a-f]+/([0-9a-f]{16,})', link)
        if note_id_match:
            note_id = note_id_match.group(1)
            if note_id not in seen:
                unique_links.append(link)
                seen.add(note_id)
    
    return {
        "filename": filename,
        "collection_name": collection_name,
        "collection_base": collection_base,
        "links": unique_links,
        "links_count": len(unique_links)
    }

def process_collection_html_files():
    # Specify the folder containing HTML files
    html_dir = Path("collection_html_manually")
    
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
                result = parse_collection_html_links(html_content, html_file.name)
                results.append(result)
                
                # Add unique links to global list
                for link in result['links']:
                    note_id_match = re.search(r'/board/[0-9a-f]+/([0-9a-f]{16,})', link)
                    if note_id_match:
                        note_id = note_id_match.group(1)
                        if note_id not in all_note_ids:
                            all_links.append(link)
                            all_note_ids.add(note_id)
                
                print(f"Processed file: {html_file.name}")
                print(f"  Found {result['links_count']} unique board links in this file")
        except Exception as e:
            print(f"Error processing file {html_file.name}: {str(e)}")
    
    # Write results to JSON file
    output_file = "notes_in_collection.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    # Write all links to Markdown file
    markdown_file = "notes_in_collection.md"
    with open(markdown_file, 'w', encoding='utf-8') as f:
        for link in all_links:
            f.write(f"- {link}\n")
    
    print(f"\nProcessing completed!")
    print(f"JSON results written to {output_file}")
    print(f"Markdown link list written to {markdown_file}")
    print(f"Processed {len(results)} files")
    print(f"Collected {len(all_links)} unique board links globally")

if __name__ == "__main__":
    process_collection_html_files() 
