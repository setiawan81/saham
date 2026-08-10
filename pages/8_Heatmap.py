import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
import pandas as pd
import plotly.express as px
from utils.analysis import ALL_STOCKS, PREMIUM, MAHASISWA, fetch_ohlcv
from utils.ui import inject_css

st.set_page_config(page_title="Heatmap", page_icon="🗺️", layout="wide")
inject_css()

st.markdown("# 🗺️ Heatmap Saham IDX")
st.markdown("Visualisasi performa harian semua saham dalam satu tampilan.")

# ── FETCH ALL DATA ────────────────────────────────────────────────────────────
rows = []
prog = st.progress(0, text="Memuat data saham...")
total = len(ALL_STOCKS)

for i, (code, meta) in enumerate(ALL_STOCKS.items()):
    df = fetch_ohlcv(code, "5d")
    if not df.empty and len(df) >= 2:
        last = float(df["close"].iloc[-1])
        prev = float(df["close"].iloc[-2])
        chg  = (last - prev) / prev * 100
        vol  = float(df["volume"].iloc[-1])
        kategori = "Premium" if code in PREMIUM else "Mahasiswa"
        rows.append({
            "Kode":     code,
            "Nama":     meta["name"],
            "Sektor":   meta["sector"],
            "Kategori": kategori,
            "Harga":    last,
            "Change":   round(chg, 2),
            "AbsChg":   abs(round(chg, 2)),
            "Volume":   vol,
            "Label":    f"{code}\n{chg:+.2f}%",
        })
    prog.progress((i + 1) / total, text=f"Memuat {code}...")

prog.empty()

if not rows:
    st.error("Tidak bisa mengambil data saham. Coba lagi nanti.")
    st.stop()

df_hm = pd.DataFrame(rows)

# ── SUMMARY METRICS ───────────────────────────────────────────────────────────
st.markdown("---")
naik  = len(df_hm[df_hm["Change"] > 0])
turun = len(df_hm[df_hm["Change"] < 0])
flat  = len(df_hm[df_hm["Change"] == 0])
avg   = df_hm["Change"].mean()

c1, c2, c3, c4 = st.columns(4)
c1.metric("🟢 Naik",  f"{naik} saham")
c2.metric("🔴 Turun", f"{turun} saham")
c3.metric("⚪ Flat",  f"{flat} saham")
c4.metric("📊 Rata-rata", f"{avg:+.2f}%")

# ── HEATMAP TREEMAP ───────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### 🗺️ Heatmap Performa Harian")

# Custom color scale: red -> dark -> green
color_scale = [
    [0.0,  "#b91c1c"],  # deep red (-5%+)
    [0.25, "#ef4444"],  # red
    [0.45, "#374151"],  # dark gray (near zero neg)
    [0.5,  "#1f2937"],  # neutral
    [0.55, "#374151"],  # dark gray (near zero pos)
    [0.75, "#10b981"],  # green
    [1.0,  "#047857"],  # deep green (+5%+)
]

fig = px.treemap(
    df_hm,
    path=["Sektor", "Kode"],
    values="AbsChg" if df_hm["AbsChg"].sum() > 0 else None,
    color="Change",
    color_continuous_scale=color_scale,
    color_continuous_midpoint=0,
    range_color=[-5, 5],
    custom_data=["Nama", "Harga", "Change"],
    hover_data={"Label": False, "AbsChg": False},
)

fig.update_traces(
    texttemplate="<b>%{label}</b><br>%{customdata[2]:+.2f}%",
    textfont=dict(size=13, color="white"),
    hovertemplate=(
        "<b>%{label}</b><br>"
        "%{customdata[0]}<br>"
        "Harga: Rp %{customdata[1]:,.0f}<br>"
        "Change: %{customdata[2]:+.2f}%"
        "<extra></extra>"
    ),
)

fig.update_layout(
    paper_bgcolor="#0f1117",
    plot_bgcolor="#0f1117",
    font=dict(color="#94a3b8", size=11, family="Segoe UI"),
    margin=dict(l=0, r=0, t=30, b=0),
    height=500,
    coloraxis_colorbar=dict(
        title="Change %",
        ticksuffix="%",
        len=0.6,
        thickness=12,
        bgcolor="rgba(0,0,0,0)",
    ),
)

st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# ── DETAIL TABLE ──────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### 📋 Detail Performa Harian")

col_f1, col_f2 = st.columns(2)
with col_f1:
    filter_kat = st.selectbox("Kategori", ["Semua", "Premium", "Mahasiswa"])
with col_f2:
    sort_opt = st.selectbox("Urutkan", ["Change ↓ (Terbaik)", "Change ↑ (Terburuk)", "Nama A-Z"])

df_table = df_hm.copy()
if filter_kat != "Semua":
    df_table = df_table[df_table["Kategori"] == filter_kat]

if sort_opt == "Change ↓ (Terbaik)":
    df_table = df_table.sort_values("Change", ascending=False)
elif sort_opt == "Change ↑ (Terburuk)":
    df_table = df_table.sort_values("Change", ascending=True)
else:
    df_table = df_table.sort_values("Kode")

display = df_table[["Kode", "Nama", "Sektor", "Kategori", "Harga", "Change"]].copy()
display["Harga"]  = display["Harga"].apply(lambda x: f"Rp {x:,.0f}")
display["Change"] = display["Change"].apply(lambda x: f"{x:+.2f}%")

st.dataframe(display, use_container_width=True, hide_index=True)

# ── SECTOR SUMMARY ────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### 🏭 Performa per Sektor")

sector_avg = df_hm.groupby("Sektor")["Change"].mean().sort_values(ascending=False).reset_index()
sector_avg.columns = ["Sektor", "Rata-rata Change"]

for _, row in sector_avg.iterrows():
    chg = row["Rata-rata Change"]
    col = "#00d395" if chg > 0 else ("#ff4560" if chg < 0 else "#64748b")
    icon = "🟢" if chg > 0 else ("🔴" if chg < 0 else "⚪")
    st.markdown(f"""<div class="card" style="padding:10px 16px;margin-bottom:6px;display:flex;justify-content:space-between;align-items:center">
      <span style="font-weight:700;font-size:.85rem">{icon} {row['Sektor']}</span>
      <span style="color:{col};font-weight:800;font-size:.85rem">{chg:+.2f}%</span>
    </div>""", unsafe_allow_html=True)
