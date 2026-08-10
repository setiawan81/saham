"""
app.py — StockVision Pro | Dashboard Utama
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from pathlib import Path
from utils.analysis import (
    fetch_ihsg, fetch_ohlcv, add_indicators, compute_signal,
    ALL_STOCKS, PREMIUM, MAHASISWA, signal_emoji, signal_color, fmt_rp
)
from utils.ui import inject_css, market_status

# ── Google Analytics ──────────────────────────────────────────────────────────
GA_TRACKING_ID = "G-BKLEQBB11T"
GA_SCRIPT = f"""
<script async src="https://www.googletagmanager.com/gtag/js?id={GA_TRACKING_ID}"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', '{GA_TRACKING_ID}');
</script>
"""

index_path = Path(st.__file__).parent / "static" / "index.html"
try:
    html_content = index_path.read_text()
    if GA_TRACKING_ID not in html_content:
        new_html = html_content.replace("<head>", f"<head>\n{GA_SCRIPT}")
        index_path.write_text(new_html)
except Exception:
    pass  # Silently skip if no write permission

st.set_page_config(
    page_title="StockVision Pro",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📈 StockVision Pro")
    st.markdown("Aplikasi analisis saham IDX real-time berbasis sinyal teknikal.")
    st.markdown("---")
    st.markdown("### 📌 Navigasi")
    st.markdown("""
- **🏠 Dashboard** — Ringkasan pasar
- **📈 Saham Premium** — BBCA, BMRI, dll
- **🎓 Saham Mahasiswa** — GOTO, ANTM, dll
- **🔍 Screening** — Filter sinyal BUY
- **⚖️ Bandingkan** — Komparasi 2 saham
- **📅 Dividen** — Kalender dividen
- **📊 Historis Sinyal** — Akurasi sinyal
- **💼 Portfolio** — Lacak portofolio kamu
- **🗺️ Heatmap** — Peta performa saham
    """)
    st.markdown("---")
    mkt_msg, is_open = market_status()
    st.markdown(f"**Status Pasar:**  \n{mkt_msg}")
    st.markdown("---")
    st.caption("⚠️ Disclaimer: Bukan saran investasi. Gunakan dengan bijak.")

# ── HEADER ────────────────────────────────────────────────────────────────────
st.markdown("# 🏠 Dashboard — Ringkasan Pasar IDX")

# IHSG
with st.spinner("Mengambil data IHSG..."):
    ihsg_val, ihsg_chg = fetch_ihsg()

col1, col2, col3, col4 = st.columns(4)
with col1:
    if ihsg_val:
        st.metric("📊 IHSG", f"{ihsg_val:,.2f}",
                  f"{ihsg_chg:+.2f}%" if ihsg_chg else None,
                  delta_color="normal")
    else:
        st.metric("📊 IHSG", "—", "Data tidak tersedia")
with col2:
    total_premium   = len(PREMIUM)
    total_mahasiswa = len(MAHASISWA)
    st.metric("📈 Saham Premium",   f"{total_premium} saham",  "BBCA · BMRI · TLKM")
with col3:
    st.metric("🎓 Saham Mahasiswa", f"{total_mahasiswa} saham", "GOTO · ANTM · WTON")
with col4:
    st.metric("🕐 Status Pasar", "BUKA" if is_open else "TUTUP", mkt_msg)

st.markdown("---")

# ── QUICK SCAN ────────────────────────────────────────────────────────────────
st.markdown("### ⚡ Quick Signal Scan — Semua Saham")
st.caption("Data diambil real-time dari Yahoo Finance. Klik halaman masing-masing untuk analisis lengkap.")

col_p, col_m = st.columns(2)

def render_quick_table(stock_dict, label):
    rows = []
    progress = st.progress(0, text=f"Scanning {label}...")
    total = len(stock_dict)
    for i, (code, meta) in enumerate(stock_dict.items()):
        df = fetch_ohlcv(code, "3mo")
        if df.empty:
            rows.append({"Kode": code, "Nama": meta["name"][:25], "Sektor": meta["sector"],
                         "Harga": "—", "Change": "—", "Signal": "—", "Confidence": "—"})
        else:
            df  = add_indicators(df)
            an  = compute_signal(df)
            last = df["close"].iloc[-1]
            prev = df["close"].iloc[-2]
            chg  = (last - prev) / prev * 100
            rows.append({
                "Kode":       code,
                "Nama":       meta["name"][:22] + ".." if len(meta["name"]) > 22 else meta["name"],
                "Harga":      f"Rp {last:,.0f}",
                "Change":     f"{chg:+.2f}%",
                "Signal":     f"{signal_emoji(an['signal'])} {an['signal']}",
                "Confidence": f"{an['confidence']}%",
            })
        progress.progress((i + 1) / total, text=f"Scanning {code}...")
    progress.empty()
    return pd.DataFrame(rows)

with col_p:
    st.markdown("#### 📈 Saham Premium")
    with st.spinner(""):
        df_p = render_quick_table(PREMIUM, "Premium")
    st.dataframe(df_p, use_container_width=True, hide_index=True,
                 column_config={
                     "Signal": st.column_config.TextColumn("Signal", width="small"),
                     "Confidence": st.column_config.TextColumn("Conf.", width="small"),
                 })

with col_m:
    st.markdown("#### 🎓 Saham Mahasiswa")
    with st.spinner(""):
        df_m = render_quick_table(MAHASISWA, "Mahasiswa")
    st.dataframe(df_m, use_container_width=True, hide_index=True)

# ── MARKET SUMMARY ────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### 📊 Ringkasan Sinyal")

all_rows = pd.concat([df_p, df_m], ignore_index=True)
sig_counts = all_rows[all_rows["Signal"] != "—"]["Signal"].value_counts()

c1, c2, c3 = st.columns(3)
buy_count  = sum(1 for s in all_rows["Signal"] if "BUY"  in str(s))
sell_count = sum(1 for s in all_rows["Signal"] if "SELL" in str(s))
hold_count = sum(1 for s in all_rows["Signal"] if "HOLD" in str(s))

with c1:
    st.markdown(f"""<div class="card" style="text-align:center">
    <div style="font-size:2rem;font-weight:900;color:#00d395">{buy_count}</div>
    <div style="color:#64748b;font-size:.75rem">🟢 Sinyal BELI</div>
    </div>""", unsafe_allow_html=True)
with c2:
    st.markdown(f"""<div class="card" style="text-align:center">
    <div style="font-size:2rem;font-weight:900;color:#feb624">{hold_count}</div>
    <div style="color:#64748b;font-size:.75rem">🟡 Sinyal TAHAN</div>
    </div>""", unsafe_allow_html=True)
with c3:
    st.markdown(f"""<div class="card" style="text-align:center">
    <div style="font-size:2rem;font-weight:900;color:#ff4560">{sell_count}</div>
    <div style="color:#64748b;font-size:.75rem">🔴 Sinyal JUAL</div>
    </div>""", unsafe_allow_html=True)

st.markdown("---")
st.markdown("### 💡 Tips Penggunaan")
st.info("""
**⏰ Waktu terbaik buka app:**
- 🌅 **Pagi 08:00–08:45 WIB** → Sebelum pasar buka, analisis & rencanakan order
- 🌙 **Malam 20:00+ WIB** → Setelah pasar tutup, evaluasi & siapkan strategi besok

**📌 Cara baca sinyal:**
- 🟢 **BELI** → Momentum positif, pertimbangkan beli saat market buka
- 🟡 **TAHAN** → Sinyal campuran, tunggu lebih lanjut
- 🔴 **JUAL** → Tekanan turun, pertimbangkan kurangi posisi
""")
