"""
utils/analysis.py — Data fetching, indicators, signal engine
"""
import pandas as pd
import numpy as np
import yfinance as yf
import streamlit as st

# ── STOCK LISTS ──────────────────────────────────────────────────────────────
PREMIUM = {
    "BBCA": {"name": "Bank Central Asia Tbk",        "sector": "Perbankan"},
    "BBRI": {"name": "Bank Rakyat Indonesia Tbk",    "sector": "Perbankan"},
    "BMRI": {"name": "Bank Mandiri Tbk",             "sector": "Perbankan"},
    "TLKM": {"name": "Telekomunikasi Indonesia Tbk", "sector": "Telekomunikasi"},
    "ASII": {"name": "Astra International Tbk",      "sector": "Otomotif"},
    "UNVR": {"name": "Unilever Indonesia Tbk",       "sector": "Konsumer"},
    "BYAN": {"name": "Bayan Resources Tbk",          "sector": "Pertambangan"},
    "INDF": {"name": "Indofood Sukses Makmur Tbk",   "sector": "Konsumer"},
    "BBNI": {"name": "Bank Negara Indonesia Tbk",    "sector": "Perbankan"},
    "ICBP": {"name": "Indofood CBP Sukses Makmur",   "sector": "Konsumer"},
}

MAHASISWA = {
    "GOTO": {"name": "GoTo Gojek Tokopedia Tbk",    "sector": "Teknologi"},
    "WTON": {"name": "Wijaya Karya Beton Tbk",       "sector": "Konstruksi"},
    "ELSA": {"name": "Elnusa Tbk",                   "sector": "Energi"},
    "PWON": {"name": "Pakuwon Jati Tbk",             "sector": "Properti"},
    "MNCN": {"name": "Media Nusantara Citra Tbk",    "sector": "Media"},
    "BJTM": {"name": "Bank Jatim Tbk",               "sector": "Perbankan"},
    "SMRA": {"name": "Summarecon Agung Tbk",         "sector": "Properti"},
    "HMSP": {"name": "H.M. Sampoerna Tbk",           "sector": "Konsumer"},
    "BBTN": {"name": "Bank Tabungan Negara Tbk",     "sector": "Perbankan"},
    "ANTM": {"name": "Aneka Tambang Tbk",            "sector": "Pertambangan"},
}

ALL_STOCKS = {**PREMIUM, **MAHASISWA}

# ── DATA FETCHING (with retry & rate-limit handling) ──────────────────────────
import time as _time
import logging as _logging

_logger = _logging.getLogger(__name__)

def _retry_fetch(func, max_retries=3, base_delay=1.0):
    """Wrapper that retries Yahoo Finance calls with exponential backoff."""
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            err_msg = str(e).lower()
            is_rate_limit = any(kw in err_msg for kw in ["rate", "limit", "429", "too many"])
            if attempt < max_retries - 1 and is_rate_limit:
                delay = base_delay * (2 ** attempt)
                _logger.warning(f"Yahoo Finance rate limited, retry {attempt+1}/{max_retries} in {delay}s")
                _time.sleep(delay)
            elif attempt < max_retries - 1:
                _time.sleep(0.5)  # brief pause for transient errors
            else:
                raise
    return None

@st.cache_data(ttl=600, show_spinner=False)
def fetch_ohlcv(code: str, period: str = "1y") -> pd.DataFrame:
    try:
        def _fetch():
            return yf.Ticker(code + ".JK").history(period=period)
        df = _retry_fetch(_fetch)
        if df is None or df.empty:
            return pd.DataFrame()
        df = df[["Open", "High", "Low", "Close", "Volume"]].copy()
        df.index = pd.to_datetime(df.index).tz_localize(None)
        df.columns = ["open", "high", "low", "close", "volume"]
        return df.dropna()
    except Exception as e:
        _logger.warning(f"fetch_ohlcv({code}) failed: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=900, show_spinner=False)
def fetch_info(code: str) -> dict:
    try:
        def _fetch():
            return yf.Ticker(code + ".JK").info or {}
        result = _retry_fetch(_fetch)
        return result if result else {}
    except Exception:
        return {}

@st.cache_data(ttl=600, show_spinner=False)
def fetch_ihsg() -> tuple:
    try:
        def _fetch():
            return yf.Ticker("^JKSE").history(period="5d")
        df = _retry_fetch(_fetch)
        if df is None or len(df) < 2:
            return None, None
        last = float(df["Close"].iloc[-1])
        prev = float(df["Close"].iloc[-2])
        return last, (last - prev) / prev * 100
    except Exception:
        return None, None

@st.cache_data(ttl=900, show_spinner=False)
def fetch_dividends(code: str) -> pd.DataFrame:
    try:
        def _fetch():
            return yf.Ticker(code + ".JK").dividends
        divs = _retry_fetch(_fetch)
        if divs is None or divs.empty:
            return pd.DataFrame()
        df = divs.reset_index()
        df.columns = ["date", "dividend"]
        df["date"] = pd.to_datetime(df["date"]).dt.tz_convert(None)
        return df.sort_values("date", ascending=False).reset_index(drop=True)
    except Exception:
        return pd.DataFrame()

# ── INDICATORS ────────────────────────────────────────────────────────────────
def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    # Moving averages
    df["ma20"]  = df["close"].rolling(20).mean()
    df["ma50"]  = df["close"].rolling(50).mean()
    df["ema12"] = df["close"].ewm(span=12, adjust=False).mean()
    df["ema26"] = df["close"].ewm(span=26, adjust=False).mean()
    # Bollinger
    bb_std       = df["close"].rolling(20).std()
    df["bb_mid"] = df["close"].rolling(20).mean()
    df["bb_up"]  = df["bb_mid"] + 2 * bb_std
    df["bb_lo"]  = df["bb_mid"] - 2 * bb_std
    # RSI
    delta = df["close"].diff()
    gain  = delta.clip(lower=0).rolling(14).mean()
    loss  = (-delta.clip(upper=0)).rolling(14).mean()
    df["rsi"] = 100 - (100 / (1 + gain / loss.replace(0, np.nan)))
    # MACD
    df["macd"]      = df["ema12"] - df["ema26"]
    df["macd_sig"]  = df["macd"].ewm(span=9, adjust=False).mean()
    df["macd_hist"] = df["macd"] - df["macd_sig"]
    # ATR
    hl = df["high"] - df["low"]
    hc = (df["high"] - df["close"].shift()).abs()
    lc = (df["low"]  - df["close"].shift()).abs()
    df["atr"] = pd.concat([hl, hc, lc], axis=1).max(axis=1).rolling(14).mean()
    return df

# ── SIGNAL ENGINE ─────────────────────────────────────────────────────────────
def compute_signal(df: pd.DataFrame) -> dict:
    if df.empty or len(df) < 30:
        return {"signal": "HOLD", "score": 0, "confidence": 50,
                "scores": {}, "price": 0, "tp": 0, "sl": 0,
                "rr": 0, "rsi": 50, "hi52": 0, "lo52": 0,
                "pct52": 50, "risk": 5, "atr_pct": 0}

    row  = df.iloc[-1]
    prev = df.iloc[-2]
    sc   = {}

    # 1. RSI
    rsi = float(row["rsi"]) if not pd.isna(row["rsi"]) else 50.0
    sc["RSI"]      = 2 if rsi<30 else (1 if rsi<42 else (-2 if rsi>70 else (-1 if rsi>62 else 0)))

    # 2. MACD
    lm, ls, pm, ps = row["macd"], row["macd_sig"], prev["macd"], prev["macd_sig"]
    if any(pd.isna(x) for x in [lm, ls, pm, ps]):
        sc["MACD"] = 0
    elif pm < ps and lm > ls:
        sc["MACD"] = 2 if lm > 0 else 1
    elif pm > ps and lm < ls:
        sc["MACD"] = -2 if lm < 0 else -1
    else:
        sc["MACD"] = 0

    # 3. MA Trend
    m20, m50 = row["ma20"], row["ma50"]
    if not pd.isna(m20) and not pd.isna(m50) and m50 != 0:
        mt = (m20 - m50) / m50 * 100
        sc["MA Trend"] = 2 if mt>2 else (1 if mt>0 else (-2 if mt<-2 else -1))
    else:
        sc["MA Trend"] = 0

    # 4. Price vs MA20
    price = float(row["close"])
    if not pd.isna(m20) and m20 != 0:
        sc["vs MA20"] = 1 if price > m20*1.01 else (0 if price > m20 else -1)
    else:
        sc["vs MA20"] = 0

    # 5. Momentum 5d
    p5 = float(df["close"].iloc[-6]) if len(df) >= 6 else price
    mom = (price - p5) / p5 * 100 if p5 != 0 else 0
    sc["Momentum"]  = 2 if mom>3 else (1 if mom>1 else (-2 if mom<-3 else (-1 if mom<-1 else 0)))

    # 6. Volume
    avg_vol  = df["volume"].iloc[-20:].mean()
    vr       = float(row["volume"]) / avg_vol if avg_vol > 0 else 1
    sc["Volume"] = (1 if float(row["close"]) > float(prev["close"]) else -1) if vr > 1.5 else 0

    total      = sum(sc.values())
    signal     = "BUY" if total >= 3 else ("SELL" if total <= -3 else "HOLD")
    confidence = min(95, int(40 + abs(total) / 12 * 55))

    # Target & Stop Loss
    atr     = float(row["atr"]) if not pd.isna(row["atr"]) else price * 0.02
    atr_pct = atr / price * 100 if price > 0 else 2.0
    tp = round(price * (1 + atr_pct/100*3)) if signal=="BUY" else (round(price * (1 - atr_pct/100*3)) if signal=="SELL" else round(price * 1.02))
    sl = round(price - atr * 2)
    rr = round(abs(tp - price) / max(abs(price - sl), 1), 1)

    hi52  = float(df["high"].iloc[-252:].max())  if len(df) >= 252 else float(df["high"].max())
    lo52  = float(df["low"].iloc[-252:].min())   if len(df) >= 252 else float(df["low"].min())
    pct52 = int((price - lo52) / (hi52 - lo52) * 100) if hi52 > lo52 else 50
    risk  = max(1, min(10, int(atr_pct * 1.8 + (2 if rsi > 70 else (-1 if rsi < 30 else 0)))))

    return dict(signal=signal, score=total, confidence=confidence, scores=sc,
                price=price, tp=tp, sl=sl, rr=rr, rsi=rsi, atr_pct=round(atr_pct,2),
                hi52=hi52, lo52=lo52, pct52=pct52, risk=risk)

def get_analysis(code: str, period: str = "1y"):
    df = fetch_ohlcv(code, period)
    if df.empty:
        return pd.DataFrame(), {}
    df = add_indicators(df)
    an = compute_signal(df)
    return df, an

# ── SIGNAL HISTORY ────────────────────────────────────────────────────────────
def signal_history(df: pd.DataFrame, lookback_days=90) -> pd.DataFrame:
    """Compute daily signals for past N days and check if they were correct."""
    if df.empty or len(df) < 60:
        return pd.DataFrame()
    df = add_indicators(df)
    results = []
    indices = df.index[-lookback_days:]
    for i, dt in enumerate(indices):
        idx = df.index.get_loc(dt)
        if idx < 30:
            continue
        slice_df = df.iloc[:idx+1]
        an = compute_signal(slice_df)
        sig = an["signal"]
        # Outcome: price 5 days later
        future_idx = idx + 5
        if future_idx < len(df):
            future_price = float(df["close"].iloc[future_idx])
            current_price = float(df["close"].iloc[idx])
            ret = (future_price - current_price) / current_price * 100
            if sig == "BUY":
                correct = ret > 0
            elif sig == "SELL":
                correct = ret < 0
            else:
                correct = abs(ret) < 2
            results.append({
                "Tanggal": dt.strftime("%d %b %Y"),
                "Sinyal":  sig,
                "Harga":   f"Rp {current_price:,.0f}",
                "Return 5H": f"{ret:+.1f}%",
                "Akurat": "✅" if correct else "❌",
                "_correct": correct,
                "_sig": sig,
            })
    return pd.DataFrame(results)

# ── FORMATTING HELPERS ────────────────────────────────────────────────────────
def fmt_rp(v):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "N/A"
    return f"Rp {int(v):,}".replace(",", ".")

def fmt_pct(v, decimals=2):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "N/A"
    return f"{v:+.{decimals}f}%"

def signal_color(sig):
    return {"BUY": "#00d395", "SELL": "#ff4560", "HOLD": "#feb624"}.get(sig, "#94a3b8")

def signal_emoji(sig):
    return {"BUY": "🟢", "SELL": "🔴", "HOLD": "🟡"}.get(sig, "⚪")
