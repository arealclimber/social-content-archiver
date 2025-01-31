import os
import discord
from discord.ext import commands
from dotenv import load_dotenv, find_dotenv
import asyncio
from xiaohongshu_crawler.main import process_url
import tempfile
import shutil
import re

# 使用絕對路徑載入 .env
current_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(current_dir, '.env')
print(f"Looking for .env at: {env_path}")

if os.path.exists(env_path):
    print(f"Found .env file at: {env_path}")
    load_dotenv(env_path, override=True)
else:
    print(f"Warning: .env file not found at {env_path}")
    # 嘗試使用 find_dotenv 作為備選方案
    dotenv_path = find_dotenv()
    if dotenv_path:
        print(f"Found .env using find_dotenv at: {dotenv_path}")
        load_dotenv(dotenv_path, override=True)

TOKEN = os.getenv('DISCORD_TOKEN')
print(f"Loaded TOKEN: {TOKEN}")

# Token 驗證
if not TOKEN:
    raise ValueError("未找到 Discord Token！請確保 .env 文件中包含有效的 DISCORD_TOKEN")

# 設定 Bot 的所有權限
intents = discord.Intents.default()
intents.message_content = True  # 允許讀取消息內容
intents.members = True          # 允許訪問成員信息
intents.presences = True        # 允許查看用戶狀態
intents.guilds = True          # 允許訪問伺服器信息
intents.messages = True        # 允許訪問消息
intents.reactions = True       # 允許使用反應

# 創建 Bot 實例，不使用命令前綴
class XiaohongshuBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=None,  # 不使用命令前綴
            intents=intents,
            description='小紅書爬蟲 Bot'
        )
    
    async def setup_hook(self):
        # Bot 啟動時的額外設置
        pass

bot = XiaohongshuBot()

def extract_xiaohongshu_url(text):
    """
    從文本中提取小紅書連結。
    支援的格式：
    1. https://www.xiaohongshu.com/...
    2. http://xhslink.com/...
    3. xhslink.com/...
    
    Args:
        text (str): 包含可能的小紅書連結的文本
        
    Returns:
        str or None: 有效的小紅書連結，如果沒有找到則返回 None
    """
    # 定義可能的 URL 模式
    patterns = [
        r'https?://(?:www\.)?xiaohongshu\.com/[^\s,，。？！\'"）】}]*',
        r'https?://(?:www\.)?xhslink\.com/[^\s,，。？！\'"）】}]*',
        r'xhslink\.com/[^\s,，。？！\'"）】}]*'
    ]
    
    # 嘗試匹配每個模式
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            url = matches[0]
            # 確保 xhslink.com 的連結有 https://
            if url.startswith('xhslink.com'):
                url = 'https://' + url
            return url
    
    return None

@bot.event
async def on_ready():
    print(f'Bot 已登入為: {bot.user.name}')
    print(f'Bot ID: {bot.user.id}')
    print(f'已啟用的權限: {intents.value}')
    print('------')
    
    # 顯示邀請連結
    invite_link = discord.utils.oauth_url(
        bot.user.id,
        permissions=discord.Permissions(
            send_messages=True,
            read_messages=True,
            attach_files=True,
            embed_links=True,
            read_message_history=True
        )
    )
    print(f'邀請 Bot 到伺服器的連結: {invite_link}')

@bot.event
async def on_message(message):
    # 忽略 Bot 自己的消息
    if message.author == bot.user:
        return
        
    # 檢查消息是否包含小紅書連結
    url = extract_xiaohongshu_url(message.content)
    if not url:
        return
    
    try:
        # 發送處理消息
        await message.channel.send(f"檢測到小紅書連結: {url}\n開始處理...")
        
        # 創建臨時目錄
        with tempfile.TemporaryDirectory() as temp_dir:
            print(f"創建臨時目錄: {temp_dir}")
            
            # 處理 URL，指定輸出目錄和所有格式
            result = await asyncio.to_thread(
                process_url,
                url,
                temp_dir,
                ['pdf', 'epub', 'markdown']
            )
            
            print(f"URL 處理結果: {result}")
            
            if not result:
                await message.channel.send("處理文章時發生錯誤，未能生成任何文件。")
                return
            
            # 檢查每個格式的文件
            for format_type, file_path in result.items():
                if file_path and os.path.exists(file_path):
                    try:
                        # 檢查文件大小
                        file_size = os.path.getsize(file_path)
                        print(f"{format_type.upper()} 文件大小: {file_size} bytes")
                        
                        if file_size > 8 * 1024 * 1024:  # 8MB limit
                            await message.channel.send(f"{format_type.upper()} 文件太大 ({file_size/1024/1024:.2f}MB)，超過 Discord 8MB 限制。")
                            continue
                        
                        # 發送文件
                        await message.channel.send(f"正在上傳 {format_type.upper()} 文件...")
                        await message.channel.send(file=discord.File(file_path))
                        print(f"{format_type.upper()} 文件發送成功")
                    except Exception as e:
                        error_msg = f"發送 {format_type.upper()} 文件時發生錯誤: {str(e)}"
                        print(error_msg)
                        await message.channel.send(error_msg)
                else:
                    await message.channel.send(f"未能生成 {format_type.upper()} 文件。")
            
            await message.channel.send("處理完成！")
        
    except Exception as e:
        error_message = f"處理過程中發生錯誤：{str(e)}"
        print(error_message)
        await message.channel.send(error_message)
        # 輸出完整的錯誤追蹤
        import traceback
        traceback.print_exc()

@bot.event
async def on_error(event, *args, **kwargs):
    print(f'發生錯誤在事件 {event}: {args} {kwargs}')

def run_bot():
    bot.run(TOKEN) 
