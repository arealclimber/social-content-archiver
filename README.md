# Social Content Archiver

A comprehensive tool for crawling and converting content from social media platforms and novel websites into multiple formats. Currently supports Xiaohongshu (小紅書) with plans to expand to other platforms.

## 🌟 Features

- **Multi-Platform Support**: Currently supports Xiaohongshu, with extensible architecture for other platforms
- **Multiple Output Formats**:
  - PDF: Suitable for printing and reading )
  - EPUB: Compatible with e-book readers
  - Markdown: Perfect for editing and version control
- **Batch Processing**: Process individual articles or entire author collections
- **Collection Processing**: Extract articles from Xiaohongshu collection pages
- **Discord Bot Integration**: Real-time processing through Discord commands
- **Cloud Deployment Ready**: Supports AWS and GCP deployment
- **Smart Anti-Bot Handling**: Selenium-based crawling with anti-detection measures

## 🚀 Quick Start

### Prerequisites

- Python 3.10.12 or higher
- Chrome browser (for Selenium WebDriver)
- Discord Bot Token (optional for Discord integration)

### Installation

1. Clone the repository:

```bash
git clone https://github.com/your-username/social-content-archiver.git
cd social-content-archiver
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Set up environment variables (for Discord Bot):

```bash
cp .env.example .env
# Edit .env and add your DISCORD_TOKEN
```

## 📖 Usage

### Command Line Interface

#### Basic Usage

```bash
# Process URLs from note-urls.md (PDF only)
python -m xiaohongshu_crawler

# Generate specific formats
python -m xiaohongshu_crawler --formats pdf epub markdown

# Generate EPUB only
python -m xiaohongshu_crawler --formats epub
```

#### URL File Format

Create a `note-urls.md` file with URLs in bullet-point format:

```markdown
- https://www.xiaohongshu.com/explore/article-id-1
- https://www.xiaohongshu.com/explore/article-id-2
- https://xhslink.com/short-link
```

### Discord Bot

The Discord Bot provides real-time content processing through Discord messages.

#### Setup Discord Bot

1. **Create Discord Application**:

   - Go to [Discord Developer Portal](https://discord.com/developers/applications)
   - Create a new application
   - Go to "Bot" section and create a bot
   - Copy the bot token

2. **Configure Environment**:

   ```bash
   echo "DISCORD_TOKEN=your_bot_token_here" > .env
   ```

3. **Run the Bot**:

   ```bash
   python run_discord_bot.py
   ```

4. **Invite Bot to Server**:
   - Use the invite link generated in the console
   - Grant necessary permissions: Send Messages, Read Messages, Attach Files

#### Using the Discord Bot

Simply send a message containing a Xiaohongshu URL to any channel where the bot is present:

```
Check out this article: https://www.xiaohongshu.com/explore/article-id
```

The bot will:

- ✅ React with 🔄 while processing
- 📁 Generate PDF, EPUB, and Markdown files
- 📤 Upload files directly to Discord
- ✅ React with ✅ when complete

### Author Page Processing

For processing entire author collections:

1. **Automatic Method** (may face anti-bot measures):

   ```python
   from xiaohongshu_crawler.main import process_author
   process_author("https://www.xiaohongshu.com/user/profile/author-id")
   ```

2. **Manual HTML Method** (recommended for reliability):
   - Use chrome plugin [SingleFile](https://chromewebstore.google.com/detail/singlefile/mpiodijhokgodhhofbcjdecpffjipkle?hl=en) to save author page HTML manually to `author_html_manually/`
   - Run: `python parse_author_html.py`
   - The output will be in the `notes_in_author.md` file
   - Copy the content to `note-urls.md`
   - Run the command: `python -m xiaohongshu_crawler`

### Collection Page Processing

For processing Xiaohongshu collection pages (board URLs):

1. **Manual HTML Method** (recommended approach):

   - Navigate to the collection page (e.g., `https://www.xiaohongshu.com/board/collection-id`)
   - Use chrome plugin [SingleFile](https://chromewebstore.google.com/detail/singlefile/mpiodijhokgodhhofbcjdecpffjipkle?hl=en) to save the collection page HTML to `collection_html_manually/`
   - Run: `python parse_collection_html.py`
   - The output will be in the `notes_in_collection.md` file
   - Copy the content to `note-urls.md`
   - Run the command: `python -m xiaohongshu_crawler`

2. **What it extracts**:
   - Collection name and metadata
   - All article URLs in the format: `https://www.xiaohongshu.com/board/{board_id}/{note_id}`
   - Removes duplicates and query parameters
   - Generates both JSON (detailed info) in `notes_in_collection.json` and Markdown (URL list) outputs in `notes_in_collection.md`

## 🏗️ Project Structure

```
social-content-archiver/
├── xiaohongshu_crawler/     # Core crawler module
│   ├── browser.py           # Selenium browser automation
│   ├── parser.py            # HTML content parsing
│   ├── file_converter.py    # Multi-format file generation
│   ├── image_handler.py     # Image download and processing
│   └── utils.py             # Utility functions
├── deploy/                  # Deployment configurations
├── fonts/                   # Font files for PDF generation
├── pdfs/                    # PDF output directory
├── epubs/                   # EPUB output directory
├── markdowns/              # Markdown output directory
├── author_html_manually/   # Manual author page HTML files
├── collection_html_manually/ # Manual collection page HTML files
├── discord_bot.py          # Discord bot implementation
├── parse_author_html.py    # Author page HTML parser
├── parse_collection_html.py # Collection page HTML parser
├── notes_in_author.md      # Extracted author article URLs
├── notes_in_collection.md  # Extracted collection article URLs
└── requirements.txt        # Python dependencies
```

## 🔧 Configuration

### Anti-Bot Settings

The crawler includes several anti-detection measures:

- Custom User-Agent strings
- Random delays between requests
- Selenium WebDriver with stealth mode
- Automatic retry mechanisms

### Output Customization

Modify output settings in the respective converter classes:

- PDF: Font selection, page layout, image sizing
- EPUB: Metadata, chapter structure, styling
- Markdown: Image organization, relative paths

## 🛣️ Roadmap

### Planned Platform Support

- [ ] **Social Media**: Weibo, Twitter

### Planned Features

- [ ] **Cloud Deployment**: AWS, GCP
- [ ] **Containerization**: Docker

## ☁️ Cloud Deployment

### AWS Deployment

#### Option 1: EC2 Instance

1. **Launch EC2 Instance**:

   ```bash
   # Choose Ubuntu 22.04 LTS
   # Instance type: t3.medium or larger (for Chrome browser)
   # Security group: Allow inbound on port 22 (SSH)
   ```

2. **Setup Environment**:

   ```bash
   # Connect to EC2
   ssh -i your-key.pem ubuntu@your-ec2-ip

   # Install dependencies
   sudo apt update
   sudo apt install python3-pip chromium-browser chromium-chromedriver

   # Clone and setup project
   git clone https://github.com/your-username/social-content-archiver.git
   cd social-content-archiver
   pip3 install -r requirements.txt
   ```

3. **Configure Discord Bot**:

   ```bash
   echo "DISCORD_TOKEN=your_token" > .env
   ```

4. **Run with PM2** (process manager):
   ```bash
   sudo npm install -g pm2
   pm2 start "python3 run_discord_bot.py" --name discord-bot
   pm2 startup
   pm2 save
   ```

#### Option 2: AWS Lambda + ECS

For serverless deployment, use AWS Lambda for the Discord bot trigger and ECS for the processing tasks.

### GCP Deployment

#### Option 1: Compute Engine

1. **Create VM Instance**:

   ```bash
   # Use gcloud CLI or GCP Console
   gcloud compute instances create content-archiver \
     --image-family=ubuntu-2204-lts \
     --image-project=ubuntu-os-cloud \
     --machine-type=e2-medium \
     --zone=us-central1-a
   ```

2. **Setup Environment**:

   ```bash
   # SSH to instance
   gcloud compute ssh content-archiver --zone=us-central1-a

   # Install dependencies (same as EC2 setup above)
   ```

#### Option 2: Cloud Run

For containerized deployment:

1. **Create Dockerfile**:

   ```dockerfile
   FROM python:3.10-slim

   # Install Chrome
   RUN apt-get update && apt-get install -y \
       chromium \
       chromium-driver \
       && rm -rf /var/lib/apt/lists/*

   WORKDIR /app
   COPY requirements.txt .
   RUN pip install -r requirements.txt

   COPY . .
   CMD ["python", "run_discord_bot.py"]
   ```

2. **Deploy to Cloud Run**:
   ```bash
   gcloud run deploy content-archiver \
     --source . \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated
   ```

### Environment Variables for Production

```bash
# Required for running the discord bot
DISCORD_TOKEN=your_discord_bot_token
```

## ⚠️ Disclaimer

This tool is for educational use only. Please respect the terms of service of the platforms you're crawling and ensure compliance with applicable laws and regulations.

---

Made with ❤️ for content preservation and digital archiving.
