import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
import pandas as pd
from utils.analysis import ALL_STOCKS, fetch_dividends, fetch_info, fetch_ohlcv
from utils.charts import make_dividend_chart
from utils.ui import inject_css

st.set_page_config(page_title="Dividen", page_icon="📅", layout="wide")
inject_css()

st.markdown("# 📅 Kalender Dividen IDX")
st.markdown("Lihat riwayat dan informasi dividen saham pilihan.")

codes = list(ALL_STOCKS.keys())
names = [f"{c} — {ALL_STOCKS[c]['name']}" for c in codes]

col1, col2 = st.columns([3, 1])
with col1:
    choice = st.selectbox("Pilih Saham", names)
    code   = codes[names.index(choice)]

with st.spinner("Mengambil data dividen..."):
    df_div = fetch_dividends(code)
    info   = fetch_info(code)
    df_price = fetch_ohlcv(code, "1y")

st.markdown("---")

# ── DIVIDEND METRICS ──────────────────────────────────────────────────────────
div_yield   = info.get("dividendYield") or 0
div_rate    = info.get("dividendRate") or 0
ex_date     = info.get("exDividendDate")
last_price  = float(df_price["close"].iloc[-1]) if not df_price.empty else 0

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("💰 Dividend Yield",    f"{div_yield*100:.2f}%" if div_yield else "N/A")
c2.metric("💵 Dividend Rate",     f"Rp {div_rate:,.0f}" if div_rate else "N/A")
c3.metric("📅 Ex-Dividend Date",  str(pd.Timestamp(ex_date, unit='s').date()) if ex_date else "N/A")
c4.metric("💹 Harga Sekarang",    f"Rp {last_price:,.0f}" if last_price else "N/A")
c5.metric("🏭 Payout Ratio",      f"{info.get('payoutRatio', 0)*100:.1f}%" if info.get('payoutRatio') else "N/A")

st.markdown("---")

# ── DIVIDEND CHART ────────────────────────────────────────────────────────────
if df_div.empty:
    st.warning(f"Data dividen untuk {code} tidak tersedia atau saham ini tidak membayar dividen.")
else:
    st.markdown(f"### 📊 Riwayat Dividen — {code}")
    df_chart = df_div.sort_values("date").tail(15)
    fig = make_dividend_chart(df_chart, code)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # ── DIVIDEND TABLE ────────────────────────────────────────────────────────
    st.markdown("### 📋 Detail Dividen")
    df_show = df_div.copy()
    df_show["date"] = df_show["date"].dt.strftime("%d %b %Y")
    df_show["dividend"] = df_show["dividend"].apply(lambda x: f"Rp {x:,.2f}")

    # Growth calculation
    if len(df_div) >= 2:
        vals = df_div.sort_values("date")["dividend"].values
        growths = [None] + [((vals[i]-vals[i-1])/vals[i-1]*100) for i in range(1, len(vals))]
        df_show["Growth"] = [f"{g:+.1f}%" if g is not None else "—" for g in reversed(growths)]

    df_show.columns = ["Tanggal", "Dividen per Lembar"] + (["Growth YoY"] if "Growth" in df_show.columns else [])
    st.dataframe(df_show, use_container_width=True, hide_index=True)

    # ── STATS ─────────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 📈 Statistik Dividen")
    raw = df_div["dividend"]
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Total Pembayaran",  len(raw))
    s2.metric("Dividen Tertinggi", f"Rp {raw.max():,.2f}")
    s3.metric("Dividen Terendah",  f"Rp {raw.min():,.2f}")
    s4.metric("Rata-rata",         f"Rp {raw.mean():,.2f}")

    if div_yield > 0.04:
        st.success(f"✅ Dividend yield {div_yield*100:.1f}% — Tergolong **tinggi**. Saham ini cocok untuk investor yang mencari passive income.")
    elif div_yield > 0.02:
        st.info(f"ℹ️ Dividend yield {div_yield*100:.1f}% — Tergolong **sedang**.")
    elif div_yield > 0:
        st.warning(f"⚠️ Dividend yield {div_yield*100:.1f}% — Tergolong **rendah**.")

# ── ALL DIVIDENDS SUMMARY ─────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### 📊 Perbandingan Dividend Yield Semua Saham")

if st.button("🔄 Load Semua Yield Dividen", use_container_width=True):
    rows = []
    prog = st.progress(0)
    for i, (cd, meta) in enumerate(ALL_STOCKS.items()):
        inf = fetch_info(cd)
        dy  = inf.get("dividendYield") or 0
        dr  = inf.get("dividendRate") or 0
        pr  = inf.get("payoutRatio") or 0
        df_p = fetch_ohlcv(cd, "5d")
        hp   = float(df_p["close"].iloc[-1]) if not df_p.empty else 0
        rows.append({
            "Kode":    cd,
            "Nama":    meta["name"][:25],
            "Harga":   f"Rp {hp:,.0f}",
            "Div Yield": f"{dy*100:.2f}%" if dy else "0%",
            "Div Rate":  f"Rp {dr:,.0f}" if dr else "N/A",
            "Payout":    f"{pr*100:.0f}%" if pr else "N/A",
            "_yield":    dy,
        })
        prog.progress((i+1)/len(ALL_STOCKS))
    prog.empty()
    rows.sort(key=lambda x: x["_yield"], reverse=True)
    display = [{k: v for k, v in r.items() if k != "_yield"} for r in rows]
    st.dataframe(pd.DataFrame(display), use_container_width=True, hide_index=True)
