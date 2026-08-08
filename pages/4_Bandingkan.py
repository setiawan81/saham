import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
import pandas as pd
from utils.analysis import ALL_STOCKS, fetch_ohlcv, add_indicators, compute_signal, signal_emoji, signal_color
from utils.charts import make_stock_chart, make_compare_chart
from utils.ui import inject_css

st.set_page_config(page_title="Bandingkan", page_icon="⚖️", layout="wide")
inject_css()

st.markdown("# ⚖️ Bandingkan 2 Saham")

codes = list(ALL_STOCKS.keys())
names = [f"{c} — {ALL_STOCKS[c]['name']}" for c in codes]

col1, col2, col3 = st.columns([2, 2, 1])
with col1:
    s1 = st.selectbox("Saham 1", names, index=0)
    c1 = codes[names.index(s1)]
with col2:
    s2 = st.selectbox("Saham 2", names, index=4)
    c2 = codes[names.index(s2)]
with col3:
    period_map = {"1 Bln": "1mo", "3 Bln": "3mo", "6 Bln": "6mo", "1 Thn": "1y"}
    tf = st.selectbox("Periode", list(period_map.keys()), index=2)
    period = period_map[tf]

if c1 == c2:
    st.warning("Pilih dua saham yang berbeda!")
    st.stop()

with st.spinner("Mengambil data..."):
    df1 = fetch_ohlcv(c1, period)
    df2 = fetch_ohlcv(c2, period)

if df1.empty or df2.empty:
    st.error("Data tidak tersedia untuk salah satu saham.")
    st.stop()

df1 = add_indicators(df1)
df2 = add_indicators(df2)
an1 = compute_signal(df1)
an2 = compute_signal(df2)

# ── HEADER COMPARISON ─────────────────────────────────────────────────────────
st.markdown("---")
left, right = st.columns(2)

def render_header(code, df, an, col):
    last = df["close"].iloc[-1]
    prev = df["close"].iloc[-2]
    pct  = (last - prev) / prev * 100
    sig  = an["signal"]
    col.markdown(f"### {signal_emoji(sig)} {code}")
    col.markdown(f"**{ALL_STOCKS[code]['name']}**  \n*{ALL_STOCKS[code]['sector']}*")
    col.metric("Harga", f"Rp {last:,.0f}", f"{pct:+.2f}%")
    col.markdown(f"""<div class="card" style="text-align:center">
      <div class="badge badge-{'buy' if sig=='BUY' else 'sell' if sig=='SELL' else 'hold'}">{sig}</div>
      <div style="margin-top:6px;font-size:.75rem">Confidence: <b style="color:{signal_color(sig)}">{an['confidence']}%</b>
      &nbsp;|&nbsp; Score: <b>{an['score']:+d}</b></div>
    </div>""", unsafe_allow_html=True)

render_header(c1, df1, an1, left)
render_header(c2, df2, an2, right)

# ── COMPARE CHART ─────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### 📈 Perbandingan Performa (Base = 100)")
fig_cmp = make_compare_chart(df1, df2, c1, c2)
st.plotly_chart(fig_cmp, use_container_width=True, config={"displayModeBar": False})

# ── SIDE BY SIDE CHARTS ───────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### 📊 Grafik Individual")
ch_left, ch_right = st.columns(2)

with ch_left:
    st.markdown(f"**{c1}**")
    fig1 = make_stock_chart(df1, show_rsi=True, show_macd=False)
    st.plotly_chart(fig1, use_container_width=True, config={"displayModeBar": False})

with ch_right:
    st.markdown(f"**{c2}**")
    fig2 = make_stock_chart(df2, show_rsi=True, show_macd=False)
    st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

# ── METRICS COMPARISON TABLE ──────────────────────────────────────────────────
st.markdown("---")
st.markdown("### 📋 Perbandingan Metrik")

last1  = df1["close"].iloc[-1]
last2  = df2["close"].iloc[-1]
ret1   = (df1["close"].iloc[-1] / df1["close"].iloc[0] - 1) * 100
ret2   = (df2["close"].iloc[-1] / df2["close"].iloc[0] - 1) * 100
vol1   = df1["close"].pct_change().std() * 100
vol2   = df2["close"].pct_change().std() * 100

rows = [
    {"Metrik": "Harga Terakhir",     c1: f"Rp {last1:,.0f}",            c2: f"Rp {last2:,.0f}"},
    {"Metrik": "Return Periode",     c1: f"{ret1:+.1f}%",               c2: f"{ret2:+.1f}%"},
    {"Metrik": "Volatilitas Harian", c1: f"{vol1:.2f}%",                c2: f"{vol2:.2f}%"},
    {"Metrik": "52W High",           c1: f"Rp {df1['high'].max():,.0f}", c2: f"Rp {df2['high'].max():,.0f}"},
    {"Metrik": "52W Low",            c1: f"Rp {df1['low'].min():,.0f}",  c2: f"Rp {df2['low'].min():,.0f}"},
    {"Metrik": "RSI",                c1: f"{an1['rsi']:.1f}",            c2: f"{an2['rsi']:.1f}"},
    {"Metrik": "Signal",             c1: f"{signal_emoji(an1['signal'])} {an1['signal']}", c2: f"{signal_emoji(an2['signal'])} {an2['signal']}"},
    {"Metrik": "Confidence",         c1: f"{an1['confidence']}%",        c2: f"{an2['confidence']}%"},
    {"Metrik": "Risk Score",         c1: f"{an1['risk']}/10",            c2: f"{an2['risk']}/10"},
    {"Metrik": "Target Harga",       c1: f"Rp {an1['tp']:,.0f}",         c2: f"Rp {an2['tp']:,.0f}"},
    {"Metrik": "Stop Loss",          c1: f"Rp {an1['sl']:,.0f}",         c2: f"Rp {an2['sl']:,.0f}"},
    {"Metrik": "R/R Ratio",          c1: f"{an1['rr']}x",               c2: f"{an2['rr']}x"},
]

st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

# ── VERDICT ───────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### 🏆 Verdict")

score_total = {"BUY": 2, "HOLD": 1, "SELL": 0}
s1_pts = an1["confidence"] * score_total.get(an1["signal"], 1)
s2_pts = an2["confidence"] * score_total.get(an2["signal"], 1)

if s1_pts > s2_pts:
    winner = c1
    reason = f"{signal_emoji(an1['signal'])} {an1['signal']} dengan confidence {an1['confidence']}%"
elif s2_pts > s1_pts:
    winner = c2
    reason = f"{signal_emoji(an2['signal'])} {an2['signal']} dengan confidence {an2['confidence']}%"
else:
    winner = None

if winner:
    st.success(f"🏆 **{winner}** lebih menarik saat ini — {reason}")
else:
    st.info("⚖️ Kedua saham memiliki potensi yang setara.")
