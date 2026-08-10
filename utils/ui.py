"""
utils/ui.py — Shared UI components & CSS
"""
import streamlit as st

GLOBAL_CSS = """
<style>
/* ── BASE ───────────────────────────────────────────── */
.stApp { background: #0f1117 !important; }
section[data-testid="stSidebar"] { background: #0d1117 !important; border-right: 1px solid #1e2d45; }
.block-container { padding: 1.2rem 1.5rem 2rem !important; }

/* ── METRIC CARDS ───────────────────────────────────── */
[data-testid="metric-container"] {
    background: #1a1d2e;
    border: 1px solid #2d3561;
    border-radius: 10px;
    padding: 12px 16px !important;
}
[data-testid="metric-container"] label { color: #64748b !important; font-size: .72rem !important; }
[data-testid="metric-container"] [data-testid="stMetricValue"] { font-size: 1.25rem !important; font-weight: 800; }

/* ── SIGNAL BADGES ──────────────────────────────────── */
.badge { display:inline-block; padding:4px 16px; border-radius:20px; font-weight:800;
         font-size:.78rem; letter-spacing:.6px; }
.badge-buy  { background:rgba(0,211,149,.14); color:#00d395; border:1px solid #00d395; }
.badge-sell { background:rgba(255,69,96,.14);  color:#ff4560; border:1px solid #ff4560; }
.badge-hold { background:rgba(254,182,36,.14); color:#feb624; border:1px solid #feb624; }

/* ── CARDS ──────────────────────────────────────────── */
.card {
    background: #1a1d2e;
    border: 1px solid #2d3561;
    border-radius: 12px;
    padding: 16px 18px;
    margin-bottom: 12px;
}
.card-title { color:#64748b; font-size:.68rem; font-weight:700;
              text-transform:uppercase; letter-spacing:.7px; margin-bottom:8px; }

/* ── SIGNAL BIG BOX ─────────────────────────────────── */
.sig-box { border-radius:12px; padding:16px; text-align:center; margin-bottom:12px; }
.sig-box-buy  { background:rgba(0,211,149,.08);  border:1px solid rgba(0,211,149,.35); }
.sig-box-sell { background:rgba(255,69,96,.08);  border:1px solid rgba(255,69,96,.35); }
.sig-box-hold { background:rgba(254,182,36,.08); border:1px solid rgba(254,182,36,.35); }
.sig-label { font-size:1.6rem; font-weight:900; letter-spacing:2px; }
.sig-desc  { font-size:.72rem; color:#94a3b8; margin-top:5px; line-height:1.5; }
.sig-nums  { display:flex; justify-content:center; gap:20px; margin-top:10px; }
.sn-val  { font-size:1rem; font-weight:800; }
.sn-lbl  { font-size:.6rem; color:#64748b; }

/* ── SCORE BAR ──────────────────────────────────────── */
.score-row { display:flex; align-items:center; justify-content:space-between;
             padding:4px 0; border-bottom:1px solid rgba(45,53,97,.5); font-size:.7rem; }
.score-row:last-child { border:none; }
.score-lbl { color:#64748b; }
.score-right { display:flex; align-items:center; gap:6px; }
.score-bar  { width:44px; height:3px; background:#0f1117; border-radius:2px; display:inline-block; }
.score-fill { height:100%; border-radius:2px; }

/* ── RANGE BAR ──────────────────────────────────────── */
.range-wrap { position:relative; margin:6px 0 2px; }
.range-track { height:5px; border-radius:3px; background:linear-gradient(90deg,#ff4560,#feb624,#00d395); }
.range-dot { position:absolute; top:-4px; width:12px; height:12px; border-radius:50%;
             border:2px solid #1a1d2e; transform:translateX(-50%); }
.range-lbl  { display:flex; justify-content:space-between; font-size:.6rem; color:#64748b; margin-top:2px; }

/* ── RISK SEGS ──────────────────────────────────────── */
.risk-segs { display:flex; gap:2px; height:7px; border-radius:3px; overflow:hidden; margin:4px 0; }
.risk-seg  { flex:1; border-radius:1px; }
.risk-meta { font-size:.63rem; color:#64748b; margin-top:3px; }

/* ── TABLE ──────────────────────────────────────────── */
.stDataFrame { border-radius:8px; overflow:hidden; }
thead tr th { background:#1a1d2e !important; color:#94a3b8 !important; font-size:.72rem !important; }
tbody tr:nth-child(even) { background:rgba(26,29,46,.5) !important; }

/* ── DIVIDER ────────────────────────────────────────── */
hr { border-color:#2d3561 !important; }

/* ── INPUT ──────────────────────────────────────────── */
.stSelectbox > div, .stNumberInput > div { background:#1a1d2e !important; border-color:#2d3561 !important; }
.stTextInput input { background:#1a1d2e !important; border-color:#2d3561 !important; }

/* ── MARKET STATUS ──────────────────────────────────── */
.mkt-open  { color:#00d395; font-weight:700; font-size:.75rem; }
.mkt-close { color:#ff4560; font-weight:700; font-size:.75rem; }
</style>
"""

def inject_css():
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

def signal_box(signal: str, confidence: int, score: int, rr: float):
    desc = {
        "BUY":  "Kondisi teknikal mendukung kenaikan. Pertimbangkan untuk membeli.",
        "SELL": "Tekanan jual kuat. Pertimbangkan untuk mengurangi posisi.",
        "HOLD": "Sinyal campuran. Tunggu konfirmasi lebih lanjut.",
    }.get(signal, "")
    icon = {"BUY": "🟢 BELI", "SELL": "🔴 JUAL", "HOLD": "🟡 TAHAN"}.get(signal, signal)
    col  = {"BUY": "#00d395", "SELL": "#ff4560", "HOLD": "#feb624"}.get(signal, "#94a3b8")
    cls  = {"BUY": "buy", "SELL": "sell", "HOLD": "hold"}.get(signal, "hold")
    st.markdown(f"""
    <div class="sig-box sig-box-{cls}">
      <div class="sig-label" style="color:{col}">{icon}</div>
      <div class="sig-desc">{desc}</div>
      <div class="sig-nums">
        <div><div class="sn-val" style="color:{col}">{confidence}%</div><div class="sn-lbl">Confidence</div></div>
        <div><div class="sn-val">{'+' if score>=0 else ''}{score}</div><div class="sn-lbl">Score</div></div>
        <div><div class="sn-val">{rr}x</div><div class="sn-lbl">R/R</div></div>
      </div>
    </div>""", unsafe_allow_html=True)

def score_breakdown(scores: dict):
    labels_map = {
        "RSI": "RSI", "MACD": "MACD", "MA Trend": "MA Trend",
        "vs MA20": "vs MA20", "Momentum": "Momentum", "Volume": "Volume",
    }
    def col(s): return "#00d395" if s > 0 else ("#ff4560" if s < 0 else "#475569")
    def lbl(s): return "Kuat Bullish" if s==2 else ("Lemah Bullish" if s==1 else ("Netral" if s==0 else ("Lemah Bearish" if s==-1 else "Kuat Bearish")))

    rows_html = ""
    for k, v in scores.items():
        pct = int(abs(v) / 2 * 100)
        rows_html += f"""
        <div class="score-row">
          <span class="score-lbl">{labels_map.get(k, k)}</span>
          <div class="score-right">
            <span class="score-bar"><span class="score-fill" style="width:{pct}%;background:{col(v)};display:block"></span></span>
            <span style="color:{col(v)};font-weight:700;font-size:.68rem;width:90px;text-align:right">{lbl(v)}</span>
          </div>
        </div>"""
    st.markdown(f'<div class="card">{rows_html}</div>', unsafe_allow_html=True)

def target_box(price, tp, sl, hi52, lo52, pct52):
    up_pct  = (tp - price) / price * 100 if price else 0
    sl_pct  = (sl - price) / price * 100 if price else 0
    dot_col = "#00d395" if pct52 > 65 else ("#ff4560" if pct52 < 35 else "#feb624")
    st.markdown(f"""
    <div class="card">
      <div class="card-title">🎯 Target & Stop Loss</div>
      <div style="display:flex;justify-content:space-between;font-size:.75rem;margin-bottom:4px">
        <span style="color:#64748b">Target</span>
        <span style="color:#00d395;font-weight:700">Rp {tp:,.0f} ({up_pct:+.1f}%)</span>
      </div>
      <div style="display:flex;justify-content:space-between;font-size:.75rem;margin-bottom:4px">
        <span style="color:#64748b">Stop Loss</span>
        <span style="color:#ff4560;font-weight:700">Rp {sl:,.0f} ({sl_pct:+.1f}%)</span>
      </div>
      <div style="display:flex;justify-content:space-between;font-size:.75rem;margin-bottom:8px">
        <span style="color:#64748b">52W Range</span>
        <span style="color:#e2e8f0;font-weight:600">Rp {lo52:,.0f} – {hi52:,.0f}</span>
      </div>
      <div class="range-wrap">
        <div class="range-track"></div>
        <div class="range-dot" style="left:{pct52}%;background:{dot_col}"></div>
      </div>
      <div class="range-lbl"><span>Low</span><span style="color:{dot_col}">{pct52}% dari range</span><span>High</span></div>
    </div>""", unsafe_allow_html=True)

def risk_box(risk: int, atr_pct: float):
    seg_cols = ["#10b981","#34d399","#86efac","#fbbf24","#fb923c","#f97316","#ef4444","#dc2626","#b91c1c","#7f1d1d"]
    lbl  = "RENDAH" if risk<=3 else ("SEDANG" if risk<=6 else ("TINGGI" if risk<=8 else "SANGAT TINGGI"))
    col  = "#00d395" if risk<=3 else ("#feb624" if risk<=6 else ("#f97316" if risk<=8 else "#ff4560"))
    segs = "".join([f'<div class="risk-seg" style="background:{"'+seg_cols[i]+'" if i<risk else "rgba(45,53,97,.4)"}"></div>' for i in range(10)])
    st.markdown(f"""
    <div class="card">
      <div class="card-title">⚠️ Risk Meter</div>
      <div style="color:{col};font-weight:800;font-size:.8rem;text-align:center;margin-bottom:4px">RISIKO {lbl} ({risk}/10)</div>
      <div class="risk-segs">{segs}</div>
      <div style="display:flex;justify-content:space-between;font-size:.58rem;color:#64748b"><span>Rendah</span><span>Tinggi</span></div>
      <div class="risk-meta">ATR: {atr_pct:.2f}% dari harga</div>
    </div>""", unsafe_allow_html=True)

def market_status():
    from datetime import datetime, timezone, timedelta
    WIB = timezone(timedelta(hours=7))
    now = datetime.now(WIB)
    wd  = now.weekday()  # 0=Mon
    h, m = now.hour, now.minute
    mins = h * 60 + m
    open_1  = 9 * 60
    close_1 = 12 * 60
    open_2  = 13 * 60 + 30
    close_2 = 15 * 60
    if wd >= 5:
        return "🔴 Pasar Tutup (Weekend)", False
    if open_1 <= mins < close_1 or open_2 <= mins < close_2:
        return "🟢 Pasar Buka", True
    if mins < open_1:
        return f"⏳ Buka pukul 09:00 (sisa {(open_1-mins)//60}j {(open_1-mins)%60}m)", False
    if close_1 <= mins < open_2:
        return "🟡 Istirahat 12:00–13:30", False
    return "🔴 Pasar Tutup", False
