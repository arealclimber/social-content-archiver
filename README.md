# 小紅書文章爬蟲與 PDF 生成工具

這是一個用於爬取小紅書文章並將其轉換為 PDF 的工具。本工具可以批量處理作者頁面和文章，並生成易於閱讀的 PDF 文件。

## 功能特點

- 支援從小紅書作者頁面批量獲取文章連結
- 自動解析作者頁面 HTML 並提取文章資訊
- 支援將文章內容轉換為 PDF 格式
- 提供多種資料輸出格式（JSON、Markdown）

## 系統需求

- Python 3.10.12 或更高版本
- 相關 Python 套件：
  - requests 2.31.0：HTTP 請求處理
  - beautifulsoup4 4.12.3：HTML 解析
  - fpdf 1.7.2：PDF 生成
  - selenium 4.17.2：網頁自動化
  - webdriver_manager 4.0.1：WebDriver 管理
  - reportlab 4.1.0：PDF 進階處理
  - Pillow 10.2.0：圖片處理

## 安裝方法

1. 克隆此專案：

```bash
git clone [專案網址]
cd crawl-website-make-pdf
```

2. 安裝依賴套件：

```bash
pip install -r requirements.txt
```

## 專案結構

```
.
├── xiaohongshu_crawler/    # 核心爬蟲模組
├── fonts/                  # PDF 生成用字體檔案
├── images/                 # 下載的圖片暫存目錄
├── pdfs/                   # 生成的 PDF 輸出目錄
├── author_html_manually/   # 手動保存的作者頁面 HTML
├── author_link_archive/    # 作者連結存檔
├── debug_html/            # 除錯用 HTML 檔案
├── run.py                 # 主程式入口
├── parse_author_html.py   # HTML 解析工具
├── requirements.txt       # 依賴套件清單
└── README.md             # 本文件
```

## 使用方法

### 1. 執行主程式

將要爬取的小紅書網址用 bullet-point 格式寫入 `note-urls.md` 檔案，然後執行：

```bash
python run.py
```

這將會：

- 下載圖片到 images/
- 產生 PDF 放到 pdfs/

### 2. 解析作者頁面 HTML

將作者頁面的 HTML 檔案放入 `author_html_manually` 資料夾，然後執行：

```bash
python parse_author_html.py
```

這將會：

- 解析所有 HTML 檔案中的文章連結
- 生成 `notes_in_author.json` 檔案，包含詳細的解析結果
- 生成 `notes_in_author.md` 檔案，包含所有文章連結

## 輸出檔案說明

- `notes_in_author.json`：包含作者名稱、文章連結和標題等詳細資訊
- `notes_in_author.md`：包含所有文章連結的 Markdown 格式清單
- `author_links.json`：作者頁面連結的 JSON 格式存檔
- `author_links.md`：作者頁面連結的 Markdown 格式清單
- 生成的 PDF 檔案將存放在 `pdfs` 目錄中
- 下載的圖片暫存於 `images` 目錄中

## 注意事項

- 請遵守小紅書的使用條款和爬蟲規則
- 建議設定適當的爬蟲間隔，避免對伺服器造成過大負擔
- 本工具僅供學習和研究使用
- 使用前請確保已安裝所有必要的字體檔案（位於 `fonts` 目錄）

## 授權條款

[待補充]

## 貢獻指南

歡迎提交 Issue 和 Pull Request 來改善這個專案。如果您發現任何問題或有改進建議，請隨時提出。
