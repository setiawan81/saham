"""
utils/charts.py — Plotly chart builders
"""
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

C = dict(
    bg      = "#0f1117",
    card    = "#1a1d2e",
    grid    = "rgba(45,53,97,.35)",
    price   = "#3b82f6",
    area    = "rgba(59,130,246,.07)",
    ma20    = "#f59e0b",
    ma50    = "#ec4899",
    ema12   = "#06b6d4",
    bb      = "rgba(139,92,246,.55)",
    vol_up  = "rgba(0,211,149,.65)",
    vol_dn  = "rgba(255,69,96,.65)",
    rsi_c   = "rgba(167,139,250,.9)",
    macd_c  = "#3b82f6",
    sig_c   = "#f59e0b",
    hp      = "rgba(0,211,149,.6)",
    hn      = "rgba(255,69,96,.6)",
    green   = "#00d395",
    red     = "#ff4560",
    yellow  = "#feb624",
)

BASE_LAYOUT = dict(
    paper_bgcolor = C["bg"],
    plot_bgcolor  = C["bg"],
    font          = dict(color="#94a3b8", size=10, family="Segoe UI"),
    margin        = dict(l=0, r=58, t=10, b=0),
    hovermode     = "x unified",
    hoverlabel    = dict(bgcolor="#1a1d2e", bordercolor="#2d3561", font_color="#e2e8f0"),
    legend        = dict(orientation="h", y=1.04, x=0, font_size=10, bgcolor="rgba(0,0,0,0)"),
    dragmode      = "pan",
    xaxis_rangeslider_visible = False,
)


def _axis(row=1, side="right"):
    return dict(showgrid=True, gridcolor=C["grid"], zeroline=False,
                showline=False, side=side)


def make_stock_chart(df: pd.DataFrame,
                     show_ma20=True, show_ma50=True,
                     show_ema=False, show_bb=False,
                     show_rsi=True, show_macd=True,
                     chart_type="line") -> go.Figure:

    n_extra = int(show_rsi) + int(show_macd)
    rows    = 2 + n_extra
    rh_base = [0.55, 0.13]
    rh_extra= [0.16] * n_extra
    row_heights = rh_base + rh_extra

    fig = make_subplots(
        rows=rows, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.018,
        row_heights=row_heights,
    )

    # ── PRICE ──────────────────────────────────────────────
    if chart_type == "candlestick":
        fig.add_trace(go.Candlestick(
            x=df.index,
            open=df["open"], high=df["high"],
            low=df["low"], close=df["close"],
            increasing_line_color=C["green"],
            increasing_fillcolor=C["green"],
            decreasing_line_color=C["red"],
            decreasing_fillcolor=C["red"],
            name="OHLC",
            showlegend=False,
        ), row=1, col=1)
    else:
        fig.add_trace(go.Scatter(
            x=df.index, y=df["close"],
            fill="tozeroy", fillcolor=C["area"],
            line=dict(color=C["price"], width=2),
            name="Harga",
        ), row=1, col=1)

    if show_ma20 and "ma20" in df:
        fig.add_trace(go.Scatter(x=df.index, y=df["ma20"],
            line=dict(color=C["ma20"], width=1.5), name="MA20"), row=1, col=1)
    if show_ma50 and "ma50" in df:
        fig.add_trace(go.Scatter(x=df.index, y=df["ma50"],
            line=dict(color=C["ma50"], width=1.5), name="MA50"), row=1, col=1)
    if show_ema and "ema12" in df:
        fig.add_trace(go.Scatter(x=df.index, y=df["ema12"],
            line=dict(color=C["ema12"], width=1.5, dash="dot"), name="EMA12"), row=1, col=1)
    if show_bb and "bb_up" in df:
        fig.add_trace(go.Scatter(x=df.index, y=df["bb_up"],
            line=dict(color=C["bb"], width=1, dash="dash"),
            name="BB", showlegend=True), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df["bb_lo"],
            line=dict(color=C["bb"], width=1, dash="dash"),
            fill="tonexty", fillcolor="rgba(139,92,246,.04)",
            name="BB Low", showlegend=False), row=1, col=1)

    # ── VOLUME ──────────────────────────────────────────────
    vc = [C["vol_up"] if df["close"].iloc[i] >= df["open"].iloc[i]
          else C["vol_dn"] for i in range(len(df))]
    fig.add_trace(go.Bar(x=df.index, y=df["volume"],
        marker_color=vc, name="Volume", showlegend=False), row=2, col=1)

    cur_row = 3
    # ── RSI ────────────────────────────────────────────────
    if show_rsi and "rsi" in df:
        fig.add_trace(go.Scatter(x=df.index, y=df["rsi"],
            line=dict(color=C["rsi_c"], width=1.5),
            name="RSI", showlegend=False), row=cur_row, col=1)
        for lvl, col in [(70, "rgba(255,69,96,.35)"), (50, "rgba(148,163,184,.2)"), (30, "rgba(0,211,149,.35)")]:
            fig.add_hline(y=lvl, line_dash="dot", line_color=col, row=cur_row, col=1)
        fig.update_yaxes(range=[0, 100], row=cur_row, col=1)
        cur_row += 1

    # ── MACD ───────────────────────────────────────────────
    if show_macd and "macd" in df:
        hc = [C["hp"] if v >= 0 else C["hn"] for v in df["macd_hist"].fillna(0)]
        fig.add_trace(go.Bar(x=df.index, y=df["macd_hist"],
            marker_color=hc, name="Hist", showlegend=False), row=cur_row, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df["macd"],
            line=dict(color=C["macd_c"], width=1.5),
            name="MACD", showlegend=False), row=cur_row, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df["macd_sig"],
            line=dict(color=C["sig_c"], width=1.5),
            name="Signal", showlegend=False), row=cur_row, col=1)

    # ── GLOBAL LAYOUT ──────────────────────────────────────
    fig.update_layout(**BASE_LAYOUT, height=520)
    for r in range(1, rows + 1):
        fig.update_xaxes(showgrid=True, gridcolor=C["grid"], zeroline=False, row=r, col=1)
        fig.update_yaxes(showgrid=True, gridcolor=C["grid"], zeroline=False, side="right", row=r, col=1)
    return fig


def make_compare_chart(df1: pd.DataFrame, df2: pd.DataFrame,
                        code1: str, code2: str) -> go.Figure:
    """Normalized performance comparison (base=100)."""
    fig = go.Figure()
    if not df1.empty:
        n1 = df1["close"] / df1["close"].iloc[0] * 100
        fig.add_trace(go.Scatter(x=df1.index, y=n1,
            line=dict(color="#3b82f6", width=2), name=code1,
            hovertemplate=f"<b>{code1}</b>: %{{y:.1f}}<extra></extra>"))
    if not df2.empty:
        n2 = df2["close"] / df2["close"].iloc[0] * 100
        fig.add_trace(go.Scatter(x=df2.index, y=n2,
            line=dict(color="#f59e0b", width=2), name=code2,
            hovertemplate=f"<b>{code2}</b>: %{{y:.1f}}<extra></extra>"))
    fig.add_hline(y=100, line_dash="dot", line_color="rgba(148,163,184,.3)")
    fig.update_layout(**BASE_LAYOUT, height=320)
    fig.update_xaxes(showgrid=True, gridcolor=C["grid"])
    fig.update_yaxes(showgrid=True, gridcolor=C["grid"], side="right",
                     title_text="Performa (Base=100)", title_font_size=10)
    return fig


def make_dividend_chart(df: pd.DataFrame, code: str) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df["date"], y=df["dividend"],
        marker_color="#3b82f6",
        marker_line_width=0,
        text=[f"Rp {v:,.0f}" for v in df["dividend"]],
        textposition="outside",
        textfont=dict(size=9, color="#94a3b8"),
        name="Dividen",
    ))
    fig.update_layout(**BASE_LAYOUT, height=260,
                      showlegend=False)
    fig.update_xaxes(showgrid=False, gridcolor=C["grid"])
    fig.update_yaxes(showgrid=True,  gridcolor=C["grid"], side="right")
    return fig


def make_portfolio_pie(labels, values, colors) -> go.Figure:
    fig = go.Figure(go.Pie(
        labels=labels, values=values,
        marker=dict(colors=colors, line=dict(color=C["bg"], width=2)),
        hole=0.55,
        textfont=dict(size=11),
        hovertemplate="<b>%{label}</b><br>%{percent}<extra></extra>",
    ))
    fig.update_layout(**{**BASE_LAYOUT,
                        "legend": dict(x=1.02, y=0.5, orientation="v",
                                       font_size=10, bgcolor="rgba(0,0,0,0)")},
                       height=260, showlegend=True)
    return fig
