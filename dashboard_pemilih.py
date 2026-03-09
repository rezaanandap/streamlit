# ============================================================
#  DASHBOARD REKAP DATA PEMILIH — SULAWESI BARAT
#  Cara update data: ganti file Excel di repo → git push
#  Jalankan : streamlit run dashboard_pemilih.py
#  Install  : pip install streamlit pandas plotly openpyxl
# ============================================================

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import io
from pathlib import Path

st.set_page_config(
    page_title="Dashboard Pemilih Sulbar",
    page_icon="🗳️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', sans-serif; }
.main { background-color: #0a0f1e; }
.block-container { padding: 1.2rem 2rem 2rem; }
.kpi { background:linear-gradient(145deg,#111827,#0f1f38);
       border:1px solid #1f3358; border-radius:14px;
       padding:1.1rem 1.3rem; height:100%; }
.kpi-label { font-size:.72rem; color:#64748b; text-transform:uppercase; letter-spacing:.08em; }
.kpi-value { font-size:1.55rem; font-weight:800; color:#f0f4ff; margin:.2rem 0 .1rem; line-height:1.1; }
.kpi-sub   { font-size:.74rem; color:#475569; }
.kpi-delta-pos { color:#34d399; font-size:.78rem; font-weight:700; }
.kpi-delta-neg { color:#f87171; font-size:.78rem; font-weight:700; }
[data-testid="stSidebar"] { background-color:#060c18; border-right:1px solid #111827; }
hr { border-color:#1e293b !important; }
.stTabs [data-baseweb="tab-list"] { background:#111827; border-radius:10px; padding:4px; }
.stTabs [data-baseweb="tab"] { border-radius:8px; color:#64748b; }
.stTabs [aria-selected="true"] { background:#1e40af !important; color:#fff !important; }
</style>
""", unsafe_allow_html=True)

# ── Warna & Helpers ───────────────────────────────────────────
COLOR_POOL = [
    "#3b82f6","#a78bfa","#34d399","#fb923c",
    "#f472b6","#facc15","#22d3ee","#f87171",
    "#4ade80","#c084fc","#38bdf8","#fbbf24",
]
PAL_GENDER = {"P": "#f472b6", "L": "#3b82f6"}

def build_period_meta(periods):
    return {k: {"label": k.replace("_"," ").title(),
                "color": COLOR_POOL[i % len(COLOR_POOL)]}
            for i, k in enumerate(periods)}

T_BASE = dict(
    paper_bgcolor="#111827", plot_bgcolor="#111827",
    font=dict(family="Plus Jakarta Sans", color="#94a3b8", size=11),
    margin=dict(t=40, b=36, l=36, r=16),
    legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor="#1f2d45"),
)

def apply_theme(fig, height=360, **kwargs):
    fig.update_layout(**T_BASE, height=height, **kwargs)
    fig.update_xaxes(gridcolor="#1f2d45", linecolor="#1f2d45", zeroline=False)
    fig.update_yaxes(gridcolor="#1f2d45", linecolor="#1f2d45", zeroline=False)
    return fig

def fmt(n):
    if n >= 1_000_000: return f"{n/1_000_000:.2f}M"
    if n >= 1_000:     return f"{n/1_000:.1f}K"
    return str(int(n))

def safe_div(a, b): return (a - b) / b * 100 if b else 0

def delta_html(pct):
    if pct > 0:   return f'<span class="kpi-delta-pos">▲ +{pct:.2f}%</span>'
    elif pct < 0: return f'<span class="kpi-delta-neg">▼ {pct:.2f}%</span>'
    return '<span style="color:#64748b">— 0%</span>'

# ── Load Data ─────────────────────────────────────────────────
DATA_FILE = Path(__file__).parent / "rekap_perjalanan_data_frompemilu.xlsx"

@st.cache_data
def load_data():
    df = pd.read_excel(DATA_FILE)
    df.columns = [c.strip().lower() for c in df.columns]
    df["kabupaten"] = df["kabupaten"].str.strip().str.title()
    return df

if not DATA_FILE.exists():
    st.error(
        "⚠️ File data tidak ditemukan!\n\n"
        f"Pastikan file **{DATA_FILE.name}** ada di folder yang sama "
        "dengan `dashboard_pemilih.py` di repository GitHub."
    )
    st.stop()

df = load_data()

# ── Bangun metadata periode dari data ─────────────────────────
all_periods = list(dict.fromkeys(df["keterangan"].tolist()))
PM          = build_period_meta(all_periods)
p_label     = lambda k: PM.get(k, {}).get("label", k)
p_color     = lambda k: PM.get(k, {}).get("color", "#94a3b8")
pal_period  = {k: v["color"] for k, v in PM.items()}
label_map   = {k: v["label"] for k, v in PM.items()}

# ════════════════════════════════════════════════════════════
#  SIDEBAR — hanya filter, tanpa login/upload
# ════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 🗳️ Dashboard Pemilih\n##### Sulawesi Barat")
    st.markdown("---")
    st.markdown("### 🔍 Filter")

    all_kab = sorted(df["kabupaten"].unique())
    sel_kab = st.multiselect("Kabupaten", all_kab, default=all_kab)

    sel_period = st.multiselect(
        "Periode", options=all_periods, default=all_periods,
        format_func=p_label
    )

    sel_jk = st.multiselect(
        "Jenis Kelamin", ["L","P"], default=["L","P"],
        format_func=lambda x: {"L":"Laki-laki","P":"Perempuan"}[x]
    )

    st.markdown("---")
    st.markdown("### 📋 Periode Terdeteksi")
    for kode in all_periods:
        c1, c2 = st.columns([1, 5])
        c1.markdown(
            f"<div style='width:12px;height:12px;border-radius:50%;"
            f"background:{p_color(kode)};margin-top:4px'></div>",
            unsafe_allow_html=True
        )
        c2.caption(p_label(kode))

    st.markdown("---")
    show_table = st.checkbox("Tampilkan Tabel Data", False)

# ── Filter ────────────────────────────────────────────────────
fdf = df[
    df["kabupaten"].isin(sel_kab) &
    df["keterangan"].isin(sel_period) &
    df["jenis_kelamin"].isin(sel_jk)
].copy()

active_periods = [p for p in all_periods if p in fdf["keterangan"].unique()]

# ════════════════════════════════════════════════════════════
#  HEADER
# ════════════════════════════════════════════════════════════
st.markdown("# 🗳️ Rekap Data Pemilih — Sulawesi Barat")
tren_str = " → ".join([p_label(p) for p in all_periods])
st.caption(f"Perjalanan data: {tren_str}")
st.markdown("---")

# ── KPI ───────────────────────────────────────────────────────
totals  = {p: df[df["keterangan"]==p]["jumlah_pemilih"].sum() for p in all_periods}
total_f = fdf["jumlah_pemilih"].sum()
total_l = fdf[fdf["jenis_kelamin"]=="L"]["jumlah_pemilih"].sum()
total_p = fdf[fdf["jenis_kelamin"]=="P"]["jumlah_pemilih"].sum()

n_cols   = min(len(all_periods) + 1, 6)
kpi_cols = st.columns(n_cols)

for i, kode in enumerate(all_periods[:n_cols-1]):
    prev = all_periods[i-1] if i > 0 else None
    dlt  = delta_html(safe_div(totals[kode], totals[prev])) if prev else ""
    sub  = f"vs {p_label(prev)}" if prev else "Baseline awal"
    kpi_cols[i].markdown(f"""<div class="kpi">
        <div class="kpi-label">{p_label(kode)}</div>
        <div class="kpi-value">{fmt(totals[kode])}</div>
        <div class="kpi-sub">{sub}</div>{dlt}
    </div>""", unsafe_allow_html=True)

kpi_cols[-1].markdown(f"""<div class="kpi">
    <div class="kpi-label">Total (Filter Aktif)</div>
    <div class="kpi-value">{fmt(total_f)}</div>
    <div class="kpi-sub">♂ {fmt(total_l)}  ♀ {fmt(total_p)}</div>
</div>""", unsafe_allow_html=True)

# Baris kedua jika periode > 5
extra = all_periods[n_cols-1:]
if extra:
    for i, kode in zip(st.columns(len(extra)), extra):
        idx  = all_periods.index(kode)
        prev = all_periods[idx-1] if idx > 0 else None
        dlt  = delta_html(safe_div(totals[kode], totals[prev])) if prev else ""
        i.markdown(f"""<div class="kpi">
            <div class="kpi-label">{p_label(kode)}</div>
            <div class="kpi-value">{fmt(totals[kode])}</div>
            <div class="kpi-sub">vs {p_label(prev) if prev else '-'}</div>{dlt}
        </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
#  TABS
# ════════════════════════════════════════════════════════════
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Perbandingan Periode",
    "👥 Analisis Gender",
    "🏙️ Per Kabupaten",
    "📈 Tren Perubahan",
])

# ── TAB 1 ────────────────────────────────────────────────────
with tab1:
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### Total Pemilih per Periode")
        agg = (fdf.groupby("keterangan")["jumlah_pemilih"].sum()
               .reindex(active_periods).reset_index())
        agg["label"] = agg["keterangan"].map(label_map)
        fig = go.Figure(go.Bar(
            x=agg["label"], y=agg["jumlah_pemilih"],
            marker_color=[p_color(k) for k in agg["keterangan"]],
            text=agg["jumlah_pemilih"].apply(fmt), textposition="outside",
            hovertemplate="%{x}<br>%{y:,.0f} pemilih<extra></extra>",
        ))
        apply_theme(fig, 340, yaxis_title="Jumlah Pemilih", xaxis_title="")
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.markdown("#### Proporsi per Periode")
        fig2 = px.pie(agg, names="label", values="jumlah_pemilih", hole=0.45,
                      color="keterangan", color_discrete_map=pal_period)
        fig2.update_traces(textinfo="percent+label",
                           hovertemplate="%{label}<br>%{value:,.0f}<extra></extra>")
        apply_theme(fig2, 340, showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("#### Perbandingan Antar Periode per Kabupaten")
    agg_kab = fdf.groupby(["kabupaten","keterangan"])["jumlah_pemilih"].sum().reset_index()
    fig3 = px.bar(agg_kab, x="kabupaten", y="jumlah_pemilih",
                  color="keterangan", barmode="group", color_discrete_map=pal_period,
                  labels={"jumlah_pemilih":"Jumlah Pemilih","kabupaten":"","keterangan":"Periode"})
    for trace in fig3.data:
        trace.name = label_map.get(trace.name, trace.name)
    apply_theme(fig3, 380, xaxis_title="", yaxis_title="Jumlah Pemilih", legend_title="Periode")
    st.plotly_chart(fig3, use_container_width=True)

# ── TAB 2 ────────────────────────────────────────────────────
with tab2:
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### Total L vs P per Periode")
        agg_jk = fdf.groupby(["keterangan","jenis_kelamin"])["jumlah_pemilih"].sum().reset_index()
        agg_jk["label_p"] = agg_jk["keterangan"].map(label_map)
        fig4 = px.bar(agg_jk, x="label_p", y="jumlah_pemilih",
                      color="jenis_kelamin", barmode="group", color_discrete_map=PAL_GENDER,
                      text=agg_jk["jumlah_pemilih"].apply(fmt),
                      labels={"label_p":"","jumlah_pemilih":"Jumlah","jenis_kelamin":"Gender"})
        fig4.update_traces(textposition="outside")
        for trace in fig4.data:
            trace.name = {"L":"Laki-laki","P":"Perempuan"}.get(trace.name, trace.name)
        apply_theme(fig4, 340, yaxis_title="Jumlah Pemilih", legend_title="Gender")
        st.plotly_chart(fig4, use_container_width=True)

    with c2:
        st.markdown("#### Rasio Gender per Kabupaten")
        agg_kj = fdf.groupby(["kabupaten","jenis_kelamin"])["jumlah_pemilih"].sum().reset_index()
        pivot = agg_kj.pivot(index="kabupaten", columns="jenis_kelamin",
                             values="jumlah_pemilih").fillna(0).reset_index()
        pivot["total"] = pivot.get("L", 0) + pivot.get("P", 0)
        pivot["pct_L"] = pivot.get("L", 0) / pivot["total"] * 100
        pivot["pct_P"] = pivot.get("P", 0) / pivot["total"] * 100
        pivot = pivot.sort_values("total", ascending=True)
        fig5 = go.Figure()
        fig5.add_trace(go.Bar(
            y=pivot["kabupaten"], x=pivot["pct_L"], name="Laki-laki",
            orientation="h", marker_color="#3b82f6", opacity=0.85,
            text=pivot["pct_L"].round(1).astype(str)+"%", textposition="inside",
            hovertemplate="%{y}<br>Laki-laki: %{x:.2f}%<extra></extra>",
        ))
        fig5.add_trace(go.Bar(
            y=pivot["kabupaten"], x=pivot["pct_P"], name="Perempuan",
            orientation="h", marker_color="#f472b6", opacity=0.85,
            text=pivot["pct_P"].round(1).astype(str)+"%", textposition="inside",
            hovertemplate="%{y}<br>Perempuan: %{x:.2f}%<extra></extra>",
        ))
        apply_theme(fig5, 340, barmode="stack", yaxis_title="", legend_title="Gender")
        fig5.update_xaxes(range=[0, 100], title_text="Persentase (%)")
        st.plotly_chart(fig5, use_container_width=True)

    st.markdown("#### Selisih L−P per Kabupaten & Periode")
    agg3 = fdf.groupby(["kabupaten","keterangan","jenis_kelamin"])["jumlah_pemilih"].sum().reset_index()
    pivot2 = agg3.pivot_table(index=["kabupaten","keterangan"], columns="jenis_kelamin",
                               values="jumlah_pemilih", fill_value=0).reset_index()
    if "L" in pivot2.columns and "P" in pivot2.columns:
        pivot2["selisih"] = pivot2["L"] - pivot2["P"]
        fig6 = px.bar(pivot2, x="kabupaten", y="selisih",
                      color="keterangan", barmode="group", color_discrete_map=pal_period,
                      labels={"selisih":"Selisih (L−P)","kabupaten":""},
                      title="Positif = Laki-laki lebih banyak  |  Negatif = Perempuan lebih banyak")
        fig6.add_hline(y=0, line_color="#ffffff", line_width=1, opacity=0.3)
        for trace in fig6.data:
            trace.name = label_map.get(trace.name, trace.name)
        apply_theme(fig6, 360, xaxis_title="", legend_title="Periode")
        st.plotly_chart(fig6, use_container_width=True)

# ── TAB 3 ────────────────────────────────────────────────────
with tab3:
    st.markdown("#### Total Pemilih per Kabupaten")
    agg_k = (fdf.groupby("kabupaten")["jumlah_pemilih"].sum()
             .reset_index().sort_values("jumlah_pemilih", ascending=True))
    fig7 = go.Figure(go.Bar(
        y=agg_k["kabupaten"], x=agg_k["jumlah_pemilih"], orientation="h",
        marker=dict(color=agg_k["jumlah_pemilih"],
                    colorscale=[[0,"#0f2137"],[0.5,"#1d4ed8"],[1,"#60a5fa"]]),
        text=agg_k["jumlah_pemilih"].apply(fmt), textposition="outside",
        hovertemplate="%{y}<br>%{x:,.0f} pemilih<extra></extra>",
    ))
    apply_theme(fig7, 320, xaxis_title="Jumlah Pemilih", yaxis_title="")
    st.plotly_chart(fig7, use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### Jumlah Kecamatan")
        kec = df[["kabupaten","jumlah_kec"]].drop_duplicates().sort_values("jumlah_kec", ascending=True)
        fig8 = px.bar(kec, x="jumlah_kec", y="kabupaten", orientation="h",
                      color="jumlah_kec",
                      color_continuous_scale=["#0f2137","#7c3aed","#c4b5fd"],
                      text="jumlah_kec",
                      labels={"jumlah_kec":"Jumlah Kecamatan","kabupaten":""})
        fig8.update_traces(textposition="outside")
        apply_theme(fig8, 300, coloraxis_showscale=False)
        st.plotly_chart(fig8, use_container_width=True)

    with c2:
        st.markdown("#### Jumlah Kelurahan/Desa")
        kel = df[["kabupaten","jumlah_kel_desa"]].drop_duplicates().sort_values("jumlah_kel_desa", ascending=True)
        fig9 = px.bar(kel, x="jumlah_kel_desa", y="kabupaten", orientation="h",
                      color="jumlah_kel_desa",
                      color_continuous_scale=["#0f2137","#0e7490","#67e8f9"],
                      text="jumlah_kel_desa",
                      labels={"jumlah_kel_desa":"Jumlah Kel/Desa","kabupaten":""})
        fig9.update_traces(textposition="outside")
        apply_theme(fig9, 300, coloraxis_showscale=False)
        st.plotly_chart(fig9, use_container_width=True)

    st.markdown("#### Heatmap Pemilih: Kabupaten × Periode")
    hm = fdf.groupby(["kabupaten","keterangan"])["jumlah_pemilih"].sum().reset_index()
    hm_pivot = hm.pivot(index="kabupaten", columns="keterangan",
                        values="jumlah_pemilih").fillna(0)
    ordered_cols = [p for p in all_periods if p in hm_pivot.columns]
    hm_pivot = hm_pivot[ordered_cols]
    hm_pivot.columns = [label_map.get(c, c) for c in hm_pivot.columns]
    fig10 = px.imshow(hm_pivot,
                      color_continuous_scale=["#0f172a","#1e3a5f","#1d4ed8","#60a5fa"],
                      text_auto=",", aspect="auto", labels={"color":"Pemilih"})
    apply_theme(fig10, 320, xaxis_title="Periode", yaxis_title="Kabupaten")
    st.plotly_chart(fig10, use_container_width=True)

# ── TAB 4 ────────────────────────────────────────────────────
with tab4:
    st.markdown("#### Tren Pertumbuhan Pemilih per Kabupaten")
    tren = fdf.groupby(["kabupaten","keterangan"])["jumlah_pemilih"].sum().reset_index()
    tren["label"] = tren["keterangan"].map(label_map)
    tren["order"] = tren["keterangan"].map({k:i for i,k in enumerate(all_periods)})
    tren = tren.sort_values("order")
    fig11 = px.line(tren, x="label", y="jumlah_pemilih", color="kabupaten",
                    markers=True, color_discrete_sequence=COLOR_POOL,
                    labels={"label":"","jumlah_pemilih":"Jumlah Pemilih","kabupaten":"Kabupaten"})
    fig11.update_traces(line_width=2.2, marker_size=9)
    apply_theme(fig11, 380, hovermode="x unified")
    st.plotly_chart(fig11, use_container_width=True)

    st.markdown("#### Persentase Perubahan Antar Periode")
    pairs = [(active_periods[i], active_periods[i+1],
              f"{p_label(active_periods[i])} → {p_label(active_periods[i+1])}")
             for i in range(len(active_periods)-1)]
    pct_rows = []
    for kab in sorted(fdf["kabupaten"].unique()):
        for p1, p2, lbl in pairs:
            v1 = fdf[(fdf["kabupaten"]==kab)&(fdf["keterangan"]==p1)]["jumlah_pemilih"].sum()
            v2 = fdf[(fdf["kabupaten"]==kab)&(fdf["keterangan"]==p2)]["jumlah_pemilih"].sum()
            if v1 > 0:
                pct_rows.append({"Kabupaten":kab,"Perubahan":lbl,"Persen":(v2-v1)/v1*100})
    if pct_rows:
        pct_df = pd.DataFrame(pct_rows)
        fig12 = px.bar(pct_df, x="Kabupaten", y="Persen", color="Perubahan",
                       barmode="group", color_discrete_sequence=COLOR_POOL,
                       text=pct_df["Persen"].round(2).astype(str)+"%",
                       labels={"Persen":"Perubahan (%)"})
        fig12.add_hline(y=0, line_color="#ffffff", line_width=1, opacity=0.3)
        fig12.update_traces(textposition="outside")
        apply_theme(fig12, 380, xaxis_title="", yaxis_title="Persentase Perubahan (%)")
        st.plotly_chart(fig12, use_container_width=True)

    st.markdown("#### Tabel Ringkas")
    rows = []
    for kab in sorted(df["kabupaten"].unique()):
        row = {"Kabupaten": kab}
        for kode in all_periods:
            v = df[(df["kabupaten"]==kab)&(df["keterangan"]==kode)]["jumlah_pemilih"].sum()
            row[p_label(kode)] = f"{v:,.0f}"
        if len(all_periods) >= 2:
            p0, pN = all_periods[0], all_periods[-1]
            v0 = df[(df["kabupaten"]==kab)&(df["keterangan"]==p0)]["jumlah_pemilih"].sum()
            vN = df[(df["kabupaten"]==kab)&(df["keterangan"]==pN)]["jumlah_pemilih"].sum()
            if v0 > 0:
                d = (vN-v0)/v0*100
                row[f"Δ {p_label(p0)}→{p_label(pN)} (%)"] = f"+{d:.2f}%" if d>=0 else f"{d:.2f}%"
        rows.append(row)
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

# ── TABEL DATA ────────────────────────────────────────────────
if show_table:
    st.markdown("---")
    st.markdown(f"### 📋 Data ({len(fdf)} baris)")
    disp = fdf.copy()
    disp["jumlah_pemilih"] = disp["jumlah_pemilih"].apply(lambda x: f"{x:,.0f}")
    disp["keterangan"]    = disp["keterangan"].map(label_map)
    disp["jenis_kelamin"] = disp["jenis_kelamin"].map({"L":"Laki-laki","P":"Perempuan"})
    st.dataframe(
        disp[["kabupaten","jumlah_kec","jumlah_kel_desa",
              "jenis_kelamin","keterangan","jumlah_pemilih"]]
        .rename(columns={"kabupaten":"Kabupaten","jumlah_kec":"Kecamatan",
                         "jumlah_kel_desa":"Kel/Desa","jenis_kelamin":"Gender",
                         "keterangan":"Periode","jumlah_pemilih":"Jumlah Pemilih"}),
        use_container_width=True, hide_index=True
    )
    c1, c2 = st.columns(2)
    with c1:
        st.download_button("⬇️ Download CSV", fdf.to_csv(index=False).encode(),
                           "data_pemilih_filtered.csv", "text/csv")
    with c2:
        buf = io.BytesIO()
        fdf.to_excel(buf, index=False)
        st.download_button("⬇️ Download Excel", buf.getvalue(),
                           "data_pemilih_filtered.xlsx",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# ── FOOTER ────────────────────────────────────────────────────
st.markdown("---")
st.markdown(f"""<div style='text-align:center;color:#334155;font-size:.78rem'>
    🗳️ Dashboard Rekap Data Pemilih Sulawesi Barat &nbsp;·&nbsp;
    {len(all_periods)} periode &nbsp;·&nbsp; {tren_str}
</div>""", unsafe_allow_html=True)
