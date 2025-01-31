import os
from discord_bot import run_bot

if __name__ == "__main__":
    # 確保環境變數已經被清除
    if 'DISCORD_TOKEN' in os.environ:
        del os.environ['DISCORD_TOKEN']
    
    # 重新運行 bot
    run_bot() 
