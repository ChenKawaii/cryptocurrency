import os
import time
import psycopg
from datetime import datetime
from dotenv import load_dotenv
from coingecko_sdk import Coingecko

# 加载同目录下的 .env 文件
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

DATABASE_URL = os.environ.get("DATABASE_URL")
COINGECKO_API_KEY = os.environ.get("COINGECKO_DEMO_API_KEY")

coins = ["bitcoin", "ethereum"]


def get_conn():
    return psycopg.connect(
        host=os.environ.get("DB_HOST"),
        port=os.environ.get("DB_PORT"),
        user=os.environ.get("DB_USER"),
        password=os.environ.get("DB_PASSWORD"),
        dbname=os.environ.get("DB_NAME"),
    )

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS prices(
            asset TEXT NOT NULL,
            ts BIGINT NOT NULL,
            price_usd DOUBLE PRECISION NOT NULL,
            PRIMARY KEY(asset, ts)
        )
    """)
    conn.commit()
    cur.close()
    conn.close()


def fetch_and_store():
    client = Coingecko(
        demo_api_key=COINGECKO_API_KEY,
        environment="demo",
    )
    data = client.simple.price.get(vs_currencies="usd", ids=",".join(coins))
    ts = int(time.time())

    conn = get_conn()
    cur = conn.cursor()
    for coin, price_obj in data.items():
        price = price_obj.usd
        cur.execute(
            "INSERT INTO prices (asset, ts, price_usd) VALUES (%s, %s, %s) "
            "ON CONFLICT (asset, ts) DO UPDATE SET price_usd = EXCLUDED.price_usd",
            (coin, ts, price),
        )
        print(f"{datetime.now().strftime('%H:%M:%S')}  {coin}: ${price:,}")
    conn.commit()
    cur.close()
    conn.close()


def show_recent_prices():
    conn = get_conn()
    cur = conn.cursor()
    for coin in coins:
        cur.execute(
            "SELECT ts, price_usd FROM prices WHERE asset = %s ORDER BY ts DESC LIMIT 5",
            (coin,),
        )
        rows = cur.fetchall()
        print(f"Recent prices for {coin}:")
        for ts, price_usd in rows:
            print(f"  {datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')} - ${price_usd:,.2f}")
    cur.close()
    conn.close()


if __name__ == "__main__":
    init_db()
    fetch_and_store()
    show_recent_prices()