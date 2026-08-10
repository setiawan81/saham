"""
utils/stock_page.py — Shared stock detail page renderer
"""
import streamlit as st
import pandas as pd
from utils.analysis import fetch_ohlcv, fetch_info, add_indicators, compute_signal, fmt_rp
from utils.charts import make_stock_chart
from utils.ui import signal_box, score_breakdown, target_box, risk_box

def render_stock_page(stock_dict: dict, page_title: str, page_icon: str):
    st.markdown(f"# {page_icon} {page_title}")

    # ── SELECTOR ─────────────────────────────────────────────────────────────
    codes = list(stock_dict.keys())
    names = [f"{c} — {stock_dict[c]['name']}" for c in codes]

    col_sel, col_tf, col_ind = st.columns([2, 1.2, 2.5])
    with col_sel:
        choice = st.selectbox("Pilih Saham", names, label_visibility="collapsed")
        code   = codes[names.index(choice)]
    with col_tf:
        period_map = {"1 Minggu": "5d", "1 Bulan": "1mo", "3 Bulan": "3mo",
                      "6 Bulan": "6mo", "1 Tahun": "1y"}
        tf = st.selectbox("Periode", list(period_map.keys()),
                          index=2, label_visibility="collapsed")
        period = period_map[tf]
    with col_ind:
        c1, c2, c3, c4, c5 = st.columns(5)
        show_ma20 = c1.checkbox("MA20", True)
        show_ma50 = c2.checkbox("MA50", True)
        show_ema  = c3.checkbox("EMA12", False)
        show_bb   = c4.checkbox("Bollinger", False)
        chart_type = c5.radio("Chart", ["Line", "Candle"], index=0, label_visibility="collapsed", horizontal=True)
        chart_type = "candlestick" if chart_type == "Candle" else "line"

    c_rsi, c_macd = st.columns(2)
    show_rsi  = c_rsi.checkbox("RSI (14)", True)
    show_macd = c_macd.checkbox("MACD", True)

    # ── FETCH ─────────────────────────────────────────────────────────────────
    with st.spinner(f"Mengambil data {code}..."):
        df   = fetch_ohlcv(code, period)
        info = fetch_info(code)

    if df.empty:
        st.error(f"Data {code} tidak tersedia. Coba lagi nanti.")
        return

    df = add_indicators(df)
    an = compute_signal(df)

    last = df["close"].iloc[-1]
    prev = df["close"].iloc[-2]
    chg  = last - prev
    pct  = chg / prev * 100

    # ── STOCK HEADER ─────────────────────────────────────────────────────────
    col_h1, col_h2, col_h3, col_h4, col_h5, col_h6 = st.columns(6)
    col_h1.metric("💰 Harga",    f"Rp {last:,.0f}", f"{pct:+.2f}%")
    col_h2.metric("📂 Open",     f"Rp {df['open'].iloc[-1]:,.0f}")
    col_h3.metric("⬆ High",     f"Rp {df['high'].iloc[-1]:,.0f}")
    col_h4.metric("⬇ Low",      f"Rp {df['low'].iloc[-1]:,.0f}")
    col_h5.metric("📦 1 Lot",   f"Rp {last*100:,.0f}")
    col_h6.metric("🏭 Sektor",   stock_dict[code]["sector"])

    st.markdown("---")

    # ── CHART + ANALYSIS ─────────────────────────────────────────────────────
    chart_col, an_col = st.columns([2.4, 1])

    with chart_col:
        fig = make_stock_chart(df,
                               show_ma20=show_ma20, show_ma50=show_ma50,
                               show_ema=show_ema, show_bb=show_bb,
                               show_rsi=show_rsi, show_macd=show_macd,
                               chart_type=chart_type)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with an_col:
        # Signal
        signal_box(an["signal"], an["confidence"], an["score"], an["rr"])
        # Score breakdown
        st.markdown('<div class="card-title" style="color:#64748b;font-size:.68rem;font-weight:700;text-transform:uppercase;letter-spacing:.7px">📊 Score Detail</div>', unsafe_allow_html=True)
        score_breakdown(an["scores"])
        # Target
        target_box(an["price"], an["tp"], an["sl"], an["hi52"], an["lo52"], an["pct52"])
        # Risk
        risk_box(an["risk"], an["atr_pct"])

    # ── FUNDAMENTAL ──────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 📋 Data Fundamental")

    def safe_info(key, fmt="val", mult=1, suffix=""):
        v = info.get(key)
        if v is None:
            return "N/A"
        try:
            fv = float(v) * mult
            if fmt == "pct":  return f"{fv:.1f}%"
            if fmt == "rp":   return f"Rp {fv:,.0f}"
            if fmt == "rp_b": return f"Rp {fv/1e12:.1f} T" if fv >= 1e12 else (f"Rp {fv/1e9:.1f} M")
            return f"{fv:.2f}{suffix}"
        except:
            return str(v)

    f1, f2, f3, f4, f5, f6, f7, f8 = st.columns(8)
    f1.metric("P/E Ratio",    safe_info("trailingPE"))
    f2.metric("P/B Ratio",    safe_info("priceToBook"))
    f3.metric("EPS",          safe_info("trailingEps", "rp"))
    f4.metric("Div Yield",    safe_info("dividendYield", "pct", 100))
    f5.metric("Market Cap",   safe_info("marketCap", "rp_b"))
    f6.metric("Beta",         safe_info("beta"))
    f7.metric("ROE",          safe_info("returnOnEquity", "pct", 100))
    f8.metric("D/E Ratio",    safe_info("debtToEquity", "val", 0.01))

    # Analyst consensus
    n_analyst = info.get("numberOfAnalystOpinions", 0)
    rec_key   = str(info.get("recommendationKey") or "hold").lower()
    if n_analyst and n_analyst > 0:
        st.markdown("---")
        st.markdown("### 👥 Konsensus Analis")
        if rec_key in ["strong_buy", "buy"]:
            ab, ah, as_ = int(n_analyst*.65), int(n_analyst*.25), n_analyst - int(n_analyst*.65) - int(n_analyst*.25)
        elif rec_key == "hold":
            ah, ab, as_ = int(n_analyst*.55), int(n_analyst*.30), n_analyst - int(n_analyst*.55) - int(n_analyst*.30)
        else:
            as_, ah, ab = int(n_analyst*.50), int(n_analyst*.30), n_analyst - int(n_analyst*.50) - int(n_analyst*.30)
        tot = ab + ah + as_ or 1
        ca, ch, cs, ct = st.columns(4)
        ca.metric("🟢 BUY",  ab, f"{ab/tot*100:.0f}%")
        ch.metric("🟡 HOLD", ah, f"{ah/tot*100:.0f}%")
        cs.metric("🔴 SELL", as_, f"{as_/tot*100:.0f}%")
        ct.metric("👥 Total", tot, "analis")

        tp_analyst = info.get("targetMeanPrice")
        if tp_analyst:
            st.info(f"🎯 **Target Konsensus Analis:** Rp {float(tp_analyst):,.0f}  |  Upside: {(float(tp_analyst)-last)/last*100:+.1f}%")
