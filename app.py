import streamlit as st
import psycopg
import os
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

st.title("加密货币价格追踪")

@st.cache_data(ttl=300)  # 缓存 5 分钟，避免每次刷新都查库
def load_data():
    conn = psycopg.connect(
        host=os.environ.get("DB_HOST"),
        port=os.environ.get("DB_PORT"),
        user=os.environ.get("DB_USER"),
        password=os.environ.get("DB_PASSWORD"),
        dbname=os.environ.get("DB_NAME"),
    )
    df = pd.read_sql(
        "SELECT asset, to_timestamp(ts) AS time, price_usd FROM prices ORDER BY ts",
        conn,
    )
    conn.close()
    return df

df = load_data()

# 按币种分开展示
for coin in df["asset"].unique():
    subset = df[df["asset"] == coin].set_index("time")
    st.subheader(coin.upper())
    st.line_chart(subset["price_usd"])
    st.caption(f"最新价格：${subset['price_usd'].iloc[-1]:,.2f}")