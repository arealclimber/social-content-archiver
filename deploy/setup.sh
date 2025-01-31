#!/bin/bash

# 更新系統
sudo apt-get update
sudo apt-get upgrade -y

# 安裝 Python 和相關工具
sudo apt-get install -y python3-pip python3-venv git awscli

# 從 AWS Parameter Store 獲取配置
GIT_USERNAME=$(aws ssm get-parameter --name "/crawler-file-discord-bot/git-username" --with-decryption --query "Parameter.Value" --output text)
GIT_EMAIL=$(aws ssm get-parameter --name "/crawler-file-discord-bot/git-email" --with-decryption --query "Parameter.Value" --output text)
DISCORD_TOKEN=$(aws ssm get-parameter --name "/crawler-file-discord-bot/discord-token" --with-decryption --query "Parameter.Value" --output text)

# 驗證所有必要的參數
if [ -z "$GIT_USERNAME" ]; then
    echo "Error: Could not retrieve Git username from Parameter Store"
    exit 1
fi

if [ -z "$GIT_EMAIL" ]; then
    echo "Error: Could not retrieve Git email from Parameter Store"
    exit 1
fi

if [ -z "$DISCORD_TOKEN" ]; then
    echo "Error: Could not retrieve Discord token from Parameter Store"
    exit 1
fi

# 設置 Git
git config --global user.name "${GIT_USERNAME}"
git config --global user.email "${GIT_EMAIL}"

# 確保 SSH 目錄權限正確
mkdir -p ~/.ssh
chmod 700 ~/.ssh
touch ~/.ssh/known_hosts
chmod 644 ~/.ssh/known_hosts

# 添加 GitHub 到已知主機
ssh-keyscan -t rsa github.com >> ~/.ssh/known_hosts

# 安裝 Chrome 和 ChromeDriver（用於 Selenium）
sudo apt-get install -y wget unzip
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt install -y ./google-chrome-stable_current_amd64.deb
rm google-chrome-stable_current_amd64.deb

# 安裝中文字體
sudo apt-get install -y fonts-wqy-microhei fonts-wqy-zenhei

# 創建應用目錄
mkdir -p /home/ubuntu/crawler-file-discord-bot
cd /home/ubuntu/crawler-file-discord-bot

# 使用 SSH 克隆代碼
git clone git@github.com:arealclimber/crawl-website-make-pdf.git .

# 創建 .env 文件
cat > .env << EOL
# Discord Configuration
DISCORD_TOKEN=${DISCORD_TOKEN}

# Git Configuration
GIT_USERNAME=${GIT_USERNAME}
GIT_EMAIL=${GIT_EMAIL}
EOL

# 創建虛擬環境
python3 -m venv venv
source venv/bin/activate

# 安裝依賴
pip install -r requirements.txt

# 清理環境變數
unset DISCORD_TOKEN
unset GIT_USERNAME
unset GIT_EMAIL
