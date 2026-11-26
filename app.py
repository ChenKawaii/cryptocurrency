import streamlit as st
import psycopg
import os
import time
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

st.title("加密货币价格追踪")


@st.cache_data(ttl=300)
def load_data():
    conn = psycopg.connect(
        host=os.environ.get("DB_HOST"),
        port=os.environ.get("DB_PORT"),
        user=os.environ.get("DB_USER"),
        password=os.environ.get("DB_PASSWORD"),
        dbname=os.environ.get("DB_NAME"),
    )
    df = pd.read_sql(
        "SELECT asset, ts, to_timestamp(ts) AS time, price_usd FROM prices ORDER BY ts",
        conn,
    )
    conn.close()
    return df


@st.cache_data(ttl=300)
def load_metrics():
    conn = psycopg.connect(
        host=os.environ.get("DB_HOST"),
        port=os.environ.get("DB_PORT"),
        user=os.environ.get("DB_USER"),
        password=os.environ.get("DB_PASSWORD"),
        dbname=os.environ.get("DB_NAME"),
    )
    df = pd.read_sql("""
        WITH ranked AS (
            SELECT asset, ts, price_usd,
                   LAG(price_usd) OVER (PARTITION BY asset ORDER BY ts) AS prev_price
            FROM prices
        )
        SELECT asset, price_usd, prev_price,
               CASE WHEN prev_price IS NULL OR prev_price = 0 THEN NULL
                    ELSE ROUND(((price_usd - prev_price) / prev_price * 100)::numeric, 2)
               END AS pct_change
        FROM ranked
        WHERE ts = (SELECT MAX(ts) FROM prices p2 WHERE p2.asset = ranked.asset)
    """, conn)
    conn.close()
    return df


df = load_data()
metrics = load_metrics()

# 1. 指标卡：最新价格 + 较上次涨跌幅
cols = st.columns(len(metrics))
for col, (_, row) in zip(cols, metrics.iterrows()):
    delta = f"{row['pct_change']:+.2f}%" if pd.notna(row["pct_change"]) else None
    col.metric(label=row["asset"].upper(), value=f"${row['price_usd']:,.2f}", delta=delta)

st.divider()

# 2. 时间范围选择
range_option = st.radio(
    "时间范围",
    options=["最近 24 小时", "最近 7 天", "全部"],
    horizontal=True,
)

now_ts = int(time.time())
if range_option == "最近 24 小时":
    cutoff = now_ts - 24 * 3600
elif range_option == "最近 7 天":
    cutoff = now_ts - 7 * 24 * 3600
else:
    cutoff = 0

df_filtered = df[df["ts"] >= cutoff]

# 3. 归一化对比开关 + 画图
normalize = st.checkbox("归一化对比（起点 = 100）")

if df_filtered.empty:
    st.warning("所选时间范围内没有数据，请换一个范围。")
elif normalize:
    pivot = df_filtered.pivot_table(index="time", columns="asset", values="price_usd")
    normalized = pivot.div(pivot.iloc[0]).mul(100)
    st.line_chart(normalized)
else:
    for coin in df_filtered["asset"].unique():
        subset = df_filtered[df_filtered["asset"] == coin].set_index("time")
        st.subheader(coin.upper())
        st.line_chart(subset["price_usd"])
        st.caption(f"最新价格：${subset['price_usd'].iloc[-1]:,.2f}")