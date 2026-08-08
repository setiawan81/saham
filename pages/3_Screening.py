import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
import pandas as pd
from utils.analysis import ALL_STOCKS, PREMIUM, MAHASISWA, fetch_ohlcv, add_indicators, compute_signal, signal_emoji
from utils.ui import inject_css

st.set_page_config(page_title="Screening", page_icon="🔍", layout="wide")
inject_css()

st.markdown("# 🔍 Screening Saham")
st.markdown("Filter saham berdasarkan sinyal teknikal secara otomatis.")

# ── FILTER ────────────────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
with col1:
    filter_sig = st.multiselect("Filter Sinyal", ["BUY", "HOLD", "SELL"],
                                default=["BUY"], help="Pilih sinyal yang ingin ditampilkan")
with col2:
    filter_cat = st.selectbox("Kategori Saham", ["Semua", "Premium", "Mahasiswa"])
with col3:
    min_conf = st.slider("Min. Confidence", 0, 95, 50, step=5)
with col4:
    sort_by = st.selectbox("Urutkan", ["Confidence ↓", "Harga ↓", "Change ↓", "Risk ↓"])

# ── SCAN ──────────────────────────────────────────────────────────────────────
if filter_cat == "Premium":
    target = PREMIUM
elif filter_cat == "Mahasiswa":
    target = MAHASISWA
else:
    target = ALL_STOCKS

if st.button("🔍 Scan Sekarang", type="primary", use_container_width=True):
    results = []
    prog = st.progress(0, text="Scanning...")
    total = len(target)

    for i, (code, meta) in enumerate(target.items()):
        df = fetch_ohlcv(code, "3mo")
        if not df.empty:
            df  = add_indicators(df)
            an  = compute_signal(df)
            last = df["close"].iloc[-1]
            prev = df["close"].iloc[-2]
            chg  = (last - prev) / prev * 100
            if an["signal"] in filter_sig and an["confidence"] >= min_conf:
                results.append({
                    "Signal":     f"{signal_emoji(an['signal'])} {an['signal']}",
                    "Kode":       code,
                    "Nama":       meta["name"][:28],
                    "Sektor":     meta["sector"],
                    "Harga":      f"Rp {last:,.0f}",
                    "1 Lot":      f"Rp {last*100:,.0f}",
                    "Change":     f"{chg:+.2f}%",
                    "Confidence": f"{an['confidence']}%",
                    "Score":      f"{an['score']:+d}",
                    "Target":     f"Rp {an['tp']:,.0f}",
                    "Stop Loss":  f"Rp {an['sl']:,.0f}",
                    "R/R":        f"{an['rr']}x",
                    "Risk":       f"{an['risk']}/10",
                    "_conf":      an["confidence"],
                    "_price":     last,
                    "_chg":       chg,
                    "_risk":      an["risk"],
                })
        prog.progress((i+1)/total, text=f"Scanning {code}...")

    prog.empty()

    if not results:
        st.warning("Tidak ada saham yang memenuhi filter. Coba longgarkan kriteria.")
    else:
        # Sort
        sk = {"Confidence ↓": "_conf", "Harga ↓": "_price",
              "Change ↓": "_chg", "Risk ↓": "_risk"}[sort_by]
        results.sort(key=lambda x: x[sk], reverse=True)

        # Remove helper cols
        display = [{k: v for k, v in r.items() if not k.startswith("_")} for r in results]
        df_result = pd.DataFrame(display)

        st.markdown(f"### ✅ Ditemukan {len(results)} saham")
        st.dataframe(df_result, use_container_width=True, hide_index=True)

        # Summary
        buy_n  = sum(1 for r in results if "BUY"  in r["Signal"])
        hold_n = sum(1 for r in results if "HOLD" in r["Signal"])
        sell_n = sum(1 for r in results if "SELL" in r["Signal"])

        c1, c2, c3 = st.columns(3)
        c1.metric("🟢 BUY",  buy_n)
        c2.metric("🟡 HOLD", hold_n)
        c3.metric("🔴 SELL", sell_n)
else:
    st.markdown("""
    <div class="card" style="text-align:center;padding:32px">
      <div style="font-size:2.5rem">🔍</div>
      <div style="color:#64748b;margin-top:8px">Klik tombol <b>Scan Sekarang</b> untuk mulai screening</div>
    </div>""", unsafe_allow_html=True)

# ── GUIDE ─────────────────────────────────────────────────────────────────────
with st.expander("ℹ️ Cara membaca hasil screening"):
    st.markdown("""
| Kolom | Penjelasan |
|-------|-----------|
| **Signal** | BUY / HOLD / SELL berdasarkan 6 indikator teknikal |
| **Confidence** | Seberapa yakin sinyal tersebut (semakin tinggi semakin kuat) |
| **Score** | Total skor dari -12 (sangat bearish) hingga +12 (sangat bullish) |
| **R/R** | Risk/Reward ratio — semakin tinggi semakin baik |
| **Risk** | Tingkat risiko 1-10 berdasarkan volatilitas (ATR) |
| **1 Lot** | Modal minimum untuk beli 1 lot (100 lembar) |
    """)
