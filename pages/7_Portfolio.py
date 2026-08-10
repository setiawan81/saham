import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
import pandas as pd
from utils.analysis import ALL_STOCKS, fetch_ohlcv, add_indicators, compute_signal, signal_emoji
from utils.charts import make_portfolio_pie
from utils.ui import inject_css

st.set_page_config(page_title="Portfolio", page_icon="💼", layout="wide")
inject_css()

st.markdown("# 💼 Portfolio Tracker")
st.markdown("Input saham yang kamu pegang, lihat P&L real-time dan rekomendasi.")

# ── SESSION STATE ─────────────────────────────────────────────────────────────
if "portfolio" not in st.session_state:
    st.session_state.portfolio = []

# ── ADD POSITION ──────────────────────────────────────────────────────────────
st.markdown("### ➕ Tambah Posisi")
with st.form("add_form", clear_on_submit=True):
    codes = list(ALL_STOCKS.keys())
    names = [f"{c} — {ALL_STOCKS[c]['name']}" for c in codes]
    c1, c2, c3, c4 = st.columns([2.5, 1.5, 1, 1])
    with c1:
        choice = st.selectbox("Saham", names)
        code   = codes[names.index(choice)]
    with c2:
        buy_price = st.number_input("Harga Beli (Rp)", min_value=1, value=1000, step=10)
    with c3:
        lots = st.number_input("Jumlah Lot", min_value=1, value=1, step=1)
    with c4:
        buy_date = st.date_input("Tanggal Beli")

    submitted = st.form_submit_button("✅ Tambahkan", type="primary", use_container_width=True)
    if submitted:
        st.session_state.portfolio.append({
            "code":      code,
            "name":      ALL_STOCKS[code]["name"],
            "sector":    ALL_STOCKS[code]["sector"],
            "buy_price": buy_price,
            "lots":      lots,
            "shares":    lots * 100,
            "buy_date":  str(buy_date),
            "modal":     buy_price * lots * 100,
        })
        st.success(f"✅ {code} ditambahkan ke portfolio!")

# ── REMOVE POSITION ───────────────────────────────────────────────────────────
if st.session_state.portfolio:
    with st.expander("🗑️ Hapus Posisi"):
        remove_labels = [f"{p['code']} ({p['lots']} lot @ Rp {p['buy_price']:,})" for p in st.session_state.portfolio]
        to_remove = st.multiselect("Pilih yang ingin dihapus", remove_labels)
        if st.button("Hapus", type="secondary"):
            indices = [remove_labels.index(r) for r in to_remove]
            st.session_state.portfolio = [p for i, p in enumerate(st.session_state.portfolio) if i not in indices]
            st.rerun()

st.markdown("---")

# ── PORTFOLIO DISPLAY ─────────────────────────────────────────────────────────
if not st.session_state.portfolio:
    st.markdown("""<div class="card" style="text-align:center;padding:36px">
      <div style="font-size:3rem">💼</div>
      <div style="color:#64748b;margin-top:8px;font-size:.95rem">Portfolio kosong.<br>Tambahkan posisi saham kamu di atas.</div>
    </div>""", unsafe_allow_html=True)
    st.stop()

# Fetch current prices
with st.spinner("Mengambil harga terkini..."):
    rows = []
    total_modal = 0
    total_nilai = 0
    total_profit = 0

    for pos in st.session_state.portfolio:
        df = fetch_ohlcv(pos["code"], "3mo")
        if df.empty:
            current = pos["buy_price"]
            sig = "HOLD"
            conf = 50
        else:
            current = float(df["close"].iloc[-1])
            df2 = add_indicators(df)
            an = compute_signal(df2)
            sig  = an["signal"]
            conf = an["confidence"]

        modal  = pos["buy_price"] * pos["shares"]
        nilai  = current * pos["shares"]
        profit = nilai - modal
        pct    = profit / modal * 100 if modal > 0 else 0

        total_modal  += modal
        total_nilai  += nilai
        total_profit += profit

        rows.append({
            "Signal":     f"{signal_emoji(sig)} {sig}",
            "Kode":       pos["code"],
            "Lot":        pos["lots"],
            "Harga Beli": f"Rp {pos['buy_price']:,.0f}",
            "Harga Skrg": f"Rp {current:,.0f}",
            "Modal":      f"Rp {modal:,.0f}",
            "Nilai Skrg": f"Rp {nilai:,.0f}",
            "P&L":        f"Rp {profit:,.0f}",
            "Return %":   f"{pct:+.2f}%",
            "Conf.":      f"{conf}%",
            "_profit":    profit,
            "_pct":       pct,
            "_code":      pos["code"],
            "_nilai":     nilai,
            "_sig":       sig,
        })

total_pct = (total_nilai - total_modal) / total_modal * 100 if total_modal > 0 else 0

# ── SUMMARY METRICS ───────────────────────────────────────────────────────────
st.markdown("### 📊 Ringkasan Portfolio")
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("💰 Total Modal",     f"Rp {total_modal:,.0f}")
m2.metric("💹 Nilai Sekarang",  f"Rp {total_nilai:,.0f}", f"{total_pct:+.1f}%")
m3.metric("💵 Total P&L",       f"Rp {total_profit:,.0f}", delta_color="normal")
m4.metric("📦 Total Posisi",    len(rows))
m5.metric("📈 Posisi Profit",   sum(1 for r in rows if r["_profit"] > 0))

st.markdown("---")

# ── PIE CHART ─────────────────────────────────────────────────────────────────
col_pie, col_table = st.columns([1, 2])
with col_pie:
    st.markdown("### 🥧 Alokasi Portfolio")
    pie_labels = [r["Kode"] for r in rows]
    pie_values = [r["_nilai"] for r in rows]
    pie_colors = ["#3b82f6","#10b981","#f59e0b","#ef4444","#8b5cf6","#06b6d4","#ec4899","#84cc16","#fb923c","#a78bfa"]
    fig_pie = make_portfolio_pie(pie_labels, pie_values, pie_colors[:len(rows)])
    st.plotly_chart(fig_pie, use_container_width=True, config={"displayModeBar": False})

with col_table:
    st.markdown("### 📋 Detail Posisi")
    display_cols = ["Signal", "Kode", "Lot", "Harga Beli", "Harga Skrg", "Modal", "Nilai Skrg", "P&L", "Return %", "Conf."]
    df_port = pd.DataFrame([{k: v for k, v in r.items() if not k.startswith("_")} for r in rows])
    st.dataframe(df_port, use_container_width=True, hide_index=True)

# ── RECOMMENDATION ────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### 🤖 Rekomendasi per Posisi")

for r in rows:
    sig   = r["_sig"]
    col   = "#00d395" if sig == "BUY" else ("#ff4560" if sig == "SELL" else "#feb624")
    pct   = r["_pct"]
    action = ""
    if sig == "SELL" and pct < -5:
        action = "⚠️ Pertimbangkan **cut loss** sebelum turun lebih dalam."
    elif sig == "SELL" and pct > 10:
        action = "💡 Sudah untung & sinyal jual — pertimbangkan untuk **ambil profit**."
    elif sig == "BUY" and pct < 0:
        action = "📉 Posisi merugi tapi sinyal masih BUY — bisa **averaging down** dengan bijak."
    elif sig == "BUY" and pct > 0:
        action = "✅ Posisi untung & sinyal positif — pertimbangkan **tahan atau tambah**."
    elif sig == "HOLD":
        action = "⏳ Sinyal netral — **tahan** dan pantau perkembangan."

    pct_color = "#00d395" if pct > 0 else "#ff4560"
    st.markdown(f"""<div class="card" style="margin-bottom:8px">
      <div style="display:flex;justify-content:space-between;align-items:center">
        <div>
          <span style="font-weight:800;font-size:.95rem">{r['Kode']}</span>
          <span style="color:#64748b;font-size:.75rem;margin-left:8px">{r['Lot']} lot</span>
          <span class="badge badge-{'buy' if sig=='BUY' else 'sell' if sig=='SELL' else 'hold'}"
                style="margin-left:10px;font-size:.65rem">{sig}</span>
        </div>
        <div style="text-align:right">
          <span style="color:{pct_color};font-weight:700">{r['Return %']}</span>
          <span style="color:#64748b;font-size:.72rem;margin-left:8px">{r['P&L']}</span>
        </div>
      </div>
      <div style="color:#94a3b8;font-size:.73rem;margin-top:6px">{action}</div>
    </div>""", unsafe_allow_html=True)

# ── DISCLAIMER ────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption("⚠️ Portfolio tracker ini menyimpan data per sesi. Data akan hilang saat halaman di-refresh. Selalu konsultasikan keputusan investasi dengan pertimbangan matang.")
