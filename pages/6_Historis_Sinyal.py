import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
import pandas as pd
from utils.analysis import ALL_STOCKS, fetch_ohlcv, add_indicators, signal_history, signal_emoji
from utils.ui import inject_css

st.set_page_config(page_title="Historis Sinyal", page_icon="📊", layout="wide")
inject_css()

st.markdown("# 📊 Historis & Akurasi Sinyal")
st.markdown("Lihat sinyal yang dihasilkan di masa lalu dan seberapa akurat hasilnya (berdasarkan harga 5 hari setelah sinyal).")

codes = list(ALL_STOCKS.keys())
names = [f"{c} — {ALL_STOCKS[c]['name']}" for c in codes]

col1, col2 = st.columns([3, 1])
with col1:
    choice = st.selectbox("Pilih Saham", names)
    code   = codes[names.index(choice)]
with col2:
    lookback = st.selectbox("Periode Analisis", [30, 60, 90], index=1, format_func=lambda x: f"{x} hari terakhir")

with st.spinner("Menghitung historis sinyal..."):
    df_raw = fetch_ohlcv(code, "1y")

if df_raw.empty:
    st.error("Data tidak tersedia.")
    st.stop()

df_hist = signal_history(df_raw, lookback_days=lookback)

if df_hist.empty:
    st.warning("Data tidak cukup untuk analisis historis sinyal.")
    st.stop()

st.markdown("---")

# ── ACCURACY STATS ────────────────────────────────────────────────────────────
total   = len(df_hist)
correct = df_hist["_correct"].sum()
acc     = correct / total * 100 if total > 0 else 0

buy_df  = df_hist[df_hist["_sig"] == "BUY"]
sell_df = df_hist[df_hist["_sig"] == "SELL"]
hold_df = df_hist[df_hist["_sig"] == "HOLD"]

acc_buy  = buy_df["_correct"].mean()  * 100 if len(buy_df)  > 0 else 0
acc_sell = sell_df["_correct"].mean() * 100 if len(sell_df) > 0 else 0
acc_hold = hold_df["_correct"].mean() * 100 if len(hold_df) > 0 else 0

st.markdown("### 🎯 Ringkasan Akurasi")
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("📊 Total Sinyal",    total)
c2.metric("✅ Akurasi Overall", f"{acc:.1f}%",    delta=None)
c3.metric("🟢 Akurasi BUY",    f"{acc_buy:.1f}%",  f"{len(buy_df)} sinyal")
c4.metric("🟡 Akurasi HOLD",   f"{acc_hold:.1f}%", f"{len(hold_df)} sinyal")
c5.metric("🔴 Akurasi SELL",   f"{acc_sell:.1f}%", f"{len(sell_df)} sinyal")

# Comment
if acc >= 60:
    st.success(f"✅ Sinyal untuk {code} cukup **akurat** ({acc:.1f}%). Bisa dijadikan referensi.")
elif acc >= 45:
    st.info(f"ℹ️ Sinyal untuk {code} memiliki akurasi **sedang** ({acc:.1f}%). Gunakan dengan pertimbangan lain.")
else:
    st.warning(f"⚠️ Akurasi sinyal untuk {code} masih **rendah** ({acc:.1f}%). Saham ini mungkin sulit diprediksi secara teknikal.")

st.markdown("---")

# ── DISTRIBUTION ──────────────────────────────────────────────────────────────
st.markdown("### 📊 Distribusi Sinyal")
col_d1, col_d2 = st.columns(2)

sig_dist = df_hist["_sig"].value_counts().reset_index()
sig_dist.columns = ["Sinyal", "Jumlah"]
sig_dist["Emoji"] = sig_dist["Sinyal"].map({"BUY": "🟢", "SELL": "🔴", "HOLD": "🟡"})
sig_dist["Label"] = sig_dist["Emoji"] + " " + sig_dist["Sinyal"]

with col_d1:
    st.markdown("**Jumlah Sinyal per Tipe**")
    st.dataframe(sig_dist[["Label", "Jumlah"]], hide_index=True, use_container_width=True)

with col_d2:
    st.markdown("**Akurasi per Tipe Sinyal**")
    acc_data = pd.DataFrame([
        {"Sinyal": "🟢 BUY",  "Akurasi": f"{acc_buy:.1f}%",  "Benar": buy_df["_correct"].sum(),  "Salah": len(buy_df)  - buy_df["_correct"].sum()},
        {"Sinyal": "🟡 HOLD", "Akurasi": f"{acc_hold:.1f}%", "Benar": hold_df["_correct"].sum(), "Salah": len(hold_df) - hold_df["_correct"].sum()},
        {"Sinyal": "🔴 SELL", "Akurasi": f"{acc_sell:.1f}%", "Benar": sell_df["_correct"].sum(), "Salah": len(sell_df) - sell_df["_correct"].sum()},
    ])
    st.dataframe(acc_data, hide_index=True, use_container_width=True)

st.markdown("---")

# ── HISTORY TABLE ─────────────────────────────────────────────────────────────
st.markdown("### 📋 Riwayat Sinyal Detail")

filter_sig2 = st.multiselect("Filter Sinyal", ["BUY", "HOLD", "SELL"],
                              default=["BUY", "HOLD", "SELL"])
df_show = df_hist[df_hist["_sig"].isin(filter_sig2)].copy()
df_show["Sinyal"] = df_show["_sig"].map(lambda s: f"{signal_emoji(s)} {s}")

display_cols = ["Tanggal", "Sinyal", "Harga", "Return 5H", "Akurat"]
st.dataframe(df_show[display_cols], use_container_width=True, hide_index=True)

# ── HOW IT WORKS ──────────────────────────────────────────────────────────────
with st.expander("ℹ️ Cara kerja perhitungan akurasi"):
    st.markdown("""
Untuk setiap hari di periode analisis:
1. App menghitung sinyal menggunakan data historis **hingga hari itu** (no look-ahead)
2. Lalu mengecek harga **5 hari kemudian**
3. Sinyal **BUY** dianggap akurat jika harga naik dalam 5 hari
4. Sinyal **SELL** dianggap akurat jika harga turun dalam 5 hari
5. Sinyal **HOLD** dianggap akurat jika perubahan harga < 2% dalam 5 hari

⚠️ Akurasi historis **tidak menjamin** performa di masa depan.
    """)
