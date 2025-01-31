"""
Main program module, responsible for coordinating the work of each module and processing URL lists
"""

import os
import argparse
from .browser import fetch_xiaohongshu_content, get_author_notes
from .parser import parse_content
from .image_handler import download_images
from .file_converter import create_pdf, create_epub, create_markdown
from .utils import extract_note_id

def process_url(url, formats=None):
    """
    Process a single URL, completing the entire workflow from crawling to file generation.
    
    Args:
        url (str): Article URL
        formats (list): List of file formats to generate, possible values: ['pdf', 'epub', 'markdown']
        
    Returns:
        dict: Dictionary containing file paths for each format, None for formats that failed to process
    """
    if formats is None:
        formats = ['pdf']  # Default to PDF only
    
    note_id = extract_note_id(url)
    print(f"Processing note ID: {note_id}")
    
    html = fetch_xiaohongshu_content(url)
    if not html:
        print(f"Unable to fetch note content: {url}")
        return {fmt: None for fmt in formats}
    
    text, image_urls, title, author, edit_date = parse_content(html, note_id)
    if not image_urls:
        print(f"No images found: {url}")
        return {fmt: None for fmt in formats}
    
    image_info = download_images(image_urls, note_id, title)
    if not image_info:
        print(f"No images successfully downloaded: {url}")
        return {fmt: None for fmt in formats}
    
    results = {}
    
    # Generate files in different formats
    if 'pdf' in formats:
        pdf_path = create_pdf(text, image_info, note_id, title, url, author, edit_date)
        results['pdf'] = pdf_path
        
    if 'epub' in formats:
        epub_path = create_epub(text, image_info, note_id, title, url, author, edit_date)
        results['epub'] = epub_path
        
    if 'markdown' in formats:
        md_path = create_markdown(text, image_info, note_id, title, url, author, edit_date)
        results['markdown'] = md_path
    
    return results

def process_author(author_url, formats=None):
    """
    Process all notes from an author.
    
    Args:
        author_url (str): Author's profile URL
        formats (list): List of file formats to generate, possible values: ['pdf', 'epub', 'markdown']
    """
    print(f"\nStarting to process author page: {author_url}")
    urls = get_author_notes(author_url)
    
    if not urls:
        print("No notes found")
        return
    
    print(f"\nFound {len(urls)} notes in total")
    success_count = {fmt: 0 for fmt in formats}
    
    for idx, url in enumerate(urls, 1):
        print(f"\nProcessing note {idx}/{len(urls)}: {url}")
        results = process_url(url, formats)
        
        for fmt in formats:
            if results[fmt]:
                print(f"Successfully generated {fmt.upper()}: {results[fmt]}")
                success_count[fmt] += 1
            else:
                print(f"Failed to generate {fmt.upper()}: {url}")
    
    print("\nProcessing completed!")
    for fmt in formats:
        print(f"{fmt.upper()} format: Successfully converted {success_count[fmt]}/{len(urls)} notes")

def main():
    """
    Main function, reads URL list and processes each URL.
    """
    parser = argparse.ArgumentParser(description='Xiaohongshu Article Crawler and Converter')
    parser.add_argument('--formats', nargs='+', choices=['pdf', 'epub', 'markdown'],
                      default=['pdf'], help='File formats to generate, options: pdf, epub, markdown')
    args = parser.parse_args()
    
    with open('note-urls.md', 'r', encoding='utf-8') as f:
        content = f.read()
    
    urls = []
    for line in content.split('\n'):
        if 'xiaohongshu.com' in line:
            url = line.strip('- ').strip()
            urls.append(url)
    
    if not urls:
        print("No Xiaohongshu URLs found")
        return
    
    for url in urls:
        print(f"\nStarting to process URL: {url}")
        results = process_url(url, args.formats)
        
        for fmt in args.formats:
            if results[fmt]:
                print(f"Successfully generated {fmt.upper()}: {results[fmt]}")
            else:
                print(f"Failed to generate {fmt.upper()}: {url}")

if __name__ == "__main__":
    main() 
