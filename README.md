# Xiaohongshu Article Crawler and Multi-Format Converter

A tool for crawling Xiaohongshu articles and converting them into multiple formats. This tool can batch process author pages and articles, generating easy-to-read PDF, EPUB, and Markdown files.

## Features

- Support batch retrieval of article links from Xiaohongshu author pages
- Automatically parse author page HTML and extract article information
- Support multiple output formats:
  - PDF: Suitable for printing and reading
  - EPUB: Suitable for e-book readers
  - Markdown: Suitable for further editing and version control
- Provide multiple data output formats (JSON, Markdown)

## System Requirements

- Python 3.10.12 or higher
- Related Python packages:
  - requests 2.31.0: HTTP request handling
  - beautifulsoup4 4.12.3: HTML parsing
  - selenium 4.17.2: Web automation
  - webdriver_manager 4.0.1: WebDriver management
  - reportlab 4.1.0: Advanced PDF processing
  - Pillow 10.2.0: Image processing
  - ebooklib 0.18.0: EPUB generation

## Installation

1. Clone this project:

```bash
git clone [project URL]
cd crawl-website-make-pdf
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Project Structure

```
.
├── xiaohongshu_crawler/    # Core crawler module
├── fonts/                  # Font files
├── images/                 # Downloaded image temporary directory
├── pdfs/                   # PDF output directory
├── epubs/                  # EPUB output directory
├── markdowns/             # Markdown output directory
├── author_html_manually/   # Manually saved author page HTML
├── author_link_archive/    # Author link archive
├── debug_html/            # Debug HTML files
├── run.py                 # Main program entry
├── parse_author_html.py   # HTML parsing tool
├── requirements.txt       # Dependency list
└── README.md             # This document
```

## Usage

### 1. Run Main Program

Write the Xiaohongshu URLs you want to crawl in bullet-point format in the `note-urls.md` file, then execute the following command:

#### Basic Usage (PDF only):

```bash
python -m xiaohongshu_crawler
```

#### Generate Specific Formats:

```bash
# Generate EPUB only
python -m xiaohongshu_crawler --formats epub

# Generate PDF and Markdown
python -m xiaohongshu_crawler --formats pdf markdown

# Generate all supported formats
python -m xiaohongshu_crawler --formats pdf epub markdown
```

This will:

- Download images to the `images/` directory
- Generate files according to specified formats:
  - PDF files saved in `pdfs/` directory
  - EPUB files saved in `epubs/` directory
  - Markdown files saved in `markdowns/` directory (images saved in `markdowns/images/` subdirectory)

### 2. Parse Author Page HTML

Place the author page HTML files in the `author_html_manually` folder, then execute:

```bash
python parse_author_html.py
```

This will:

- Parse article links from all HTML files
- Generate `notes_in_author.json` file containing detailed parsing results
- Generate `notes_in_author.md` file containing all article links

## Output File Description

- `notes_in_author.json`: Contains detailed information including author name, article links, and titles
- `notes_in_author.md`: Markdown format list of all article links
- `author_links.json`: JSON format archive of author page links
- `author_links.md`: Markdown format list of author page links
- Generated files will be stored in corresponding directories based on format:
  - PDF files: `pdfs/`
  - EPUB files: `epubs/`
  - Markdown files: `markdowns/`
- Downloaded images are temporarily stored in the `images/` directory

## Output Format Description

### PDF Format

- Suitable for printing and reading
- Contains complete article content, images, and metadata
- Automatic Chinese font handling
- Automatic pagination and layout

### EPUB Format

- Suitable for reading on e-book readers
- Supports table of contents navigation
- Preserves original image quality
- Includes complete metadata

### Markdown Format

- Suitable for further editing and version control
- Images referenced using relative paths
- Preserves original format and structure
- Easy to convert to other formats

## Notes

- Please comply with Xiaohongshu's terms of use and crawler rules
- Recommended to set appropriate crawling intervals to avoid overloading the server
- This tool is for learning and research purposes only
- Make sure all necessary font files are installed (located in the `fonts` directory)

## License

[To be added]

## Contributing Guide

Welcome to submit Issues and Pull Requests to improve this project. If you find any problems or have suggestions for improvement, please feel free to raise them.
