from coingecko_sdk import Coingecko
## CG-K74VLRVdqnG4i6KSpUBUpJQJ
import sqlite3, time
from datetime import datetime
import os
from dotenv import load_dotenv

# 获取脚本所在目录，数据库就存在那里
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "crypto_prices.db")
load_dotenv(os.path.join(BASE_DIR, ".env"))

import sys
sys.stdout = open(r"c:\Users\admin\Desktop\czy_proj\py\cryptocurrency\run.log", "a", encoding="utf-8")
sys.stderr = sys.stdout


coins = ['bitcoin', 'ethereum']

# 1.初始化数据库
def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS prices(
            asset TEXT NOT NULL,
            ts INTEGER NOT NULL,
            price_usd REAL NOT NULL,
            PRIMARY KEY(asset, ts)
            )
    """)
    conn.commit()
    conn.close()

# 2.获取价格入库
def fetch_and_store():
    client = Coingecko(
        demo_api_key=os.getenv("COINGECKO_DEMO_API_KEY"),
        environment="demo",
    )
    data = client.simple.price.get(vs_currencies="usd", ids=",".join(coins))
    ts = int(time.time())
    
    con = sqlite3.connect(DB_PATH)
    for coin, price_dict in data.items():
        price = price_dict.usd
        con.execute(
            "INSERT OR REPLACE INTO prices (asset, ts, price_usd) VALUES (?, ?, ?)",
            (coin, ts, price)
        )
        print(f"{datetime.now().strftime('%H:%M:%S')}  {coin}: ${price:,}")
    con.commit()
    con.close()

# 3.查最近5条价格
def show_recent_prices():
    conn = sqlite3.connect(DB_PATH)
    for coin in coins:
        cursor = conn.execute("SELECT ts, price_usd FROM prices WHERE asset=? ORDER BY ts DESC LIMIT 5", (coin,))
        print(f"Recent prices for {coin}:")
        for row in cursor:
            ts, price_usd = row
            print(f"  {datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')} - ${price_usd:,.2f}")
    conn.close()

if __name__ == "__main__":
    init_db()
    fetch_and_store()
    show_recent_prices()

