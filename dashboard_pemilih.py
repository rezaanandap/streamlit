# ============================================================
#  DASHBOARD REKAP DATA PEMILIH — SULAWESI BARAT
#  100% DINAMIS: periode baru di data → otomatis muncul di chart
#  Jalankan : streamlit run dashboard_pemilih.py
#  Install  : pip install streamlit pandas plotly openpyxl
#
#  PASSWORD SETUP — buat file .streamlit/secrets.toml:
#    [auth]
#    upload_password = "passwordkamu"
#    admin_name      = "Nama Kamu"
# ============================================================

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import hashlib
import io

# ── Page Config ──────────────────────────────────────────────
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
.kpi { background:linear-gradient(145deg,#111827,#0f1f38); border:1px solid #1f3358;
       border-radius:14px; padding:1.1rem 1.3rem; height:100%; }
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

# ── Warna dinamis ─────────────────────────────────────────────
# Pool warna — otomatis dipakai berurutan untuk setiap periode baru
COLOR_POOL = [
    "#3b82f6","#a78bfa","#34d399","#fb923c",
    "#f472b6","#facc15","#22d3ee","#f87171",
    "#4ade80","#c084fc","#38bdf8","#fbbf24",
]
PAL_GENDER = {"P": "#f472b6", "L": "#3b82f6"}

def build_period_meta(periods: list[str]) -> dict:
    """
    Buat label & warna otomatis dari daftar kode periode di data.
    Tidak ada hardcode — semua dari data.
    """
    meta = {}
    for i, kode in enumerate(periods):
        # Label: ganti underscore → spasi, title-case
        label = kode.replace("_", " ").title()
        color = COLOR_POOL[i % len(COLOR_POOL)]
        meta[kode] = {"label": label, "color": color}
    return meta

# ── Plotly theme ──────────────────────────────────────────────
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

# ── Helpers ──────────────────────────────────────────────────
def fmt(n):
    if n >= 1_000_000: return f"{n/1_000_000:.2f}M"
    if n >= 1_000:     return f"{n/1_000:.1f}K"
    return str(int(n))

def safe_div(a, b):
    return (a - b) / b * 100 if b else 0

def delta_html(pct):
    if pct > 0:   return f'<span class="kpi-delta-pos">▲ +{pct:.2f}%</span>'
    elif pct < 0: return f'<span class="kpi-delta-neg">▼ {pct:.2f}%</span>'
    return '<span style="color:#64748b">— 0%</span>'

# ── Auth ──────────────────────────────────────────────────────
def get_credentials():
    try:
        pwd  = st.secrets["auth"]["upload_password"]
        name = st.secrets["auth"].get("admin_name", "Admin")
    except Exception:
        pwd, name = "admin123", "Admin"
    return pwd, name

def hash_pw(pw): return hashlib.sha256(pw.encode()).hexdigest()
def is_admin():  return st.session_state.get("is_admin", False)

# ── Load & clean data ─────────────────────────────────────────
def clean_df(df):
    df.columns = [c.strip().lower() for c in df.columns]
    df["kabupaten"] = df["kabupaten"].str.strip().str.title()
    return df

@st.cache_data
def load_bytes(raw_bytes, fname):
    return clean_df(pd.read_excel(io.BytesIO(raw_bytes)))

@st.cache_data
def load_default():
    return clean_df(pd.read_excel("rekap_perjalanan_data_frompemilu.xlsx"))

# ════════════════════════════════════════════════════════════
#  SIDEBAR
# ════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 🗳️ Dashboard Pemilih\n##### Sulawesi Barat")
    st.markdown("---")

    if is_admin():
        admin_name = st.session_state.get("admin_name", "Admin")
        st.markdown(f"### ✅ Login sebagai **{admin_name}**")
        if st.button("🚪 Logout", use_container_width=True):
            for k in ["is_admin","admin_name","uploaded_data","uploaded_fname"]:
                st.session_state.pop(k, None)
            st.rerun()
        st.markdown("### 📁 Upload Data")
        uploaded = st.file_uploader("File Excel", type=["xlsx","xls"],
                                    label_visibility="collapsed")
        if uploaded:
            st.session_state["uploaded_data"]  = uploaded.read()
            st.session_state["uploaded_fname"] = uploaded.name
            st.success(f"✅ **{uploaded.name}**")
    else:
        st.markdown("### 📁 Data")
        st.info("👁 Mode publik — hanya bisa melihat.")
        st.markdown("---")
        st.markdown("### 🔐 Admin Login")
        pw_input = st.text_input("Password", type="password",
                                 placeholder="Masukkan password...", key="pw_input")
        if st.button("🔑 Login", use_container_width=True):
            correct_pw, admin_name = get_credentials()
            if hash_pw(pw_input) == hash_pw(correct_pw):
                st.session_state["is_admin"]   = True
                st.session_state["admin_name"] = admin_name
                st.rerun()
            else:
                st.error("❌ Password salah!")

    st.markdown("---")

    # ── Resolve data ─────────────────────────────────────────
    if "uploaded_data" in st.session_state:
        df = load_bytes(st.session_state["uploaded_data"],
                        st.session_state["uploaded_fname"])
    else:
        try:
            df = load_default()
            if not is_admin():
                st.caption("📌 Menampilkan data bawaan")
        except Exception:
            st.warning("⚠️ Belum ada data. Login & upload file dulu.")
            st.stop()

    # ── Bangun metadata periode dari data aktual ──────────────
    # Urutan periode diambil dari urutan kemunculan di data (agar konsisten)
    all_periods_in_data = list(dict.fromkeys(df["keterangan"].tolist()))
    PM = build_period_meta(all_periods_in_data)  # PM = Period Meta

    def p_label(kode): return PM.get(kode, {}).get("label", kode)
    def p_color(kode): return PM.get(kode, {}).get("color", "#94a3b8")

    pal_period  = {k: v["color"] for k,v in PM.items()}
    label_map   = {k: v["label"] for k,v in PM.items()}

    # ── Filter ───────────────────────────────────────────────
    st.markdown("### 🔍 Filter")
    all_kab = sorted(df["kabupaten"].unique())
    sel_kab = st.multiselect("Kabupaten", all_kab, default=all_kab)

    sel_period = st.multiselect(
        "Periode",
        options=all_periods_in_data,
        default=all_periods_in_data,
        format_func=p_label
    )

    sel_jk = st.multiselect(
        "Jenis Kelamin", ["L","P"], default=["L","P"],
        format_func=lambda x: {"L":"Laki-laki","P":"Perempuan"}[x]
    )

    st.markdown("---")

    # ── Info: periode yang terdeteksi ─────────────────────────
    st.markdown("### 📋 Periode Terdeteksi")
    for kode in all_periods_in_data:
        col_dot, col_lbl = st.columns([1, 5])
        col_dot.markdown(
            f"<div style='width:12px;height:12px;border-radius:50%;"
            f"background:{p_color(kode)};margin-top:4px'></div>",
            unsafe_allow_html=True
        )
        col_lbl.caption(p_label(kode))

    st.markdown("---")
    show_table = st.checkbox("Tampilkan Tabel Data", False)

# ── Apply filter ─────────────────────────────────────────────
fdf = df[
    df["kabupaten"].isin(sel_kab) &
    df["keterangan"].isin(sel_period) &
    df["jenis_kelamin"].isin(sel_jk)
].copy()

# Periode yang aktif setelah filter (urutan tetap)
active_periods = [p for p in all_periods_in_data if p in fdf["keterangan"].unique()]

# ════════════════════════════════════════════════════════════
#  HEADER
# ════════════════════════════════════════════════════════════
st.markdown("# 🗳️ Rekap Data Pemilih — Sulawesi Barat")
tren_str = " → ".join([p_label(p) for p in all_periods_in_data])
st.caption(f"Perjalanan data: {tren_str}")
st.markdown("---")

# ════════════════════════════════════════════════════════════
#  KPI — DINAMIS: jumlah kartu = jumlah periode + 1 total
# ════════════════════════════════════════════════════════════
totals = {p: df[df["keterangan"]==p]["jumlah_pemilih"].sum()
          for p in all_periods_in_data}

total_f  = fdf["jumlah_pemilih"].sum()
total_l  = fdf[fdf["jenis_kelamin"]=="L"]["jumlah_pemilih"].sum()
total_pr = fdf[fdf["jenis_kelamin"]=="P"]["jumlah_pemilih"].sum()

# Tampilkan maks 5 kartu (4 periode + 1 total filter)
# Jika periode > 4 kartu tetap tampil semua via baris kedua
kpi_periods = all_periods_in_data
n_cols      = min(len(kpi_periods) + 1, 6)  # max 6 kolom
kpi_cols    = st.columns(n_cols)

for i, kode in enumerate(kpi_periods[:n_cols-1]):
    prev = kpi_periods[i-1] if i > 0 else None
    dlt  = delta_html(safe_div(totals[kode], totals[prev])) if prev else ""
    sub  = f"vs {p_label(prev)}" if prev else "Baseline awal"
    kpi_cols[i].markdown(f"""<div class="kpi">
        <div class="kpi-label">{p_label(kode)}</div>
        <div class="kpi-value">{fmt(totals[kode])}</div>
        <div class="kpi-sub">{sub}</div>{dlt}
    </div>""", unsafe_allow_html=True)

# Kartu terakhir = total filter
kpi_cols[-1].markdown(f"""<div class="kpi">
    <div class="kpi-label">Total (Filter Aktif)</div>
    <div class="kpi-value">{fmt(total_f)}</div>
    <div class="kpi-sub">♂ {fmt(total_l)}  ♀ {fmt(total_pr)}</div>
</div>""", unsafe_allow_html=True)

# Baris kedua jika periode > 5
extra_periods = kpi_periods[n_cols-1:]
if extra_periods:
    extra_cols = st.columns(len(extra_periods))
    for i, kode in enumerate(extra_periods):
        idx  = kpi_periods.index(kode)
        prev = kpi_periods[idx-1] if idx > 0 else None
        dlt  = delta_html(safe_div(totals[kode], totals[prev])) if prev else ""
        sub  = f"vs {p_label(prev)}" if prev else "Baseline awal"
        extra_cols[i].markdown(f"""<div class="kpi">
            <div class="kpi-label">{p_label(kode)}</div>
            <div class="kpi-value">{fmt(totals[kode])}</div>
            <div class="kpi-sub">{sub}</div>{dlt}
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

# ── TAB 1: Perbandingan Periode ──────────────────────────────
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
            text=agg["jumlah_pemilih"].apply(fmt),
            textposition="outside",
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
    agg_kab["label"] = agg_kab["keterangan"].map(label_map)
    fig3 = px.bar(agg_kab, x="kabupaten", y="jumlah_pemilih",
                  color="keterangan", barmode="group",
                  color_discrete_map=pal_period,
                  labels={"jumlah_pemilih":"Jumlah Pemilih","kabupaten":"","keterangan":"Periode"})
    for trace in fig3.data:
        trace.name = label_map.get(trace.name, trace.name)
    apply_theme(fig3, 380, xaxis_title="", yaxis_title="Jumlah Pemilih", legend_title="Periode")
    st.plotly_chart(fig3, use_container_width=True)

# ── TAB 2: Analisis Gender ───────────────────────────────────
with tab2:
    c1, c2 = st.columns(2)

    with c1:
        st.markdown("#### Total L vs P per Periode")
        agg_jk = fdf.groupby(["keterangan","jenis_kelamin"])["jumlah_pemilih"].sum().reset_index()
        agg_jk["label_p"] = agg_jk["keterangan"].map(label_map)
        fig4 = px.bar(agg_jk, x="label_p", y="jumlah_pemilih",
                      color="jenis_kelamin", barmode="group",
                      color_discrete_map=PAL_GENDER,
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
        pivot2["label"]   = pivot2["keterangan"].map(label_map)
        fig6 = px.bar(pivot2, x="kabupaten", y="selisih",
                      color="keterangan", barmode="group",
                      color_discrete_map=pal_period,
                      labels={"selisih":"Selisih (L−P)","kabupaten":""},
                      title="Positif = Laki-laki lebih banyak  |  Negatif = Perempuan lebih banyak")
        fig6.add_hline(y=0, line_color="#ffffff", line_width=1, opacity=0.3)
        for trace in fig6.data:
            trace.name = label_map.get(trace.name, trace.name)
        apply_theme(fig6, 360, xaxis_title="", legend_title="Periode")
        st.plotly_chart(fig6, use_container_width=True)

# ── TAB 3: Per Kabupaten ─────────────────────────────────────
with tab3:
    st.markdown("#### Total Pemilih per Kabupaten (Semua Periode)")
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
    # Urutkan kolom sesuai urutan periode di data
    ordered_cols = [p for p in all_periods_in_data if p in hm_pivot.columns]
    hm_pivot = hm_pivot[ordered_cols]
    hm_pivot.columns = [label_map.get(c, c) for c in hm_pivot.columns]
    fig10 = px.imshow(hm_pivot,
                      color_continuous_scale=["#0f172a","#1e3a5f","#1d4ed8","#60a5fa"],
                      text_auto=",", aspect="auto", labels={"color":"Pemilih"})
    apply_theme(fig10, 320, xaxis_title="Periode", yaxis_title="Kabupaten")
    st.plotly_chart(fig10, use_container_width=True)

# ── TAB 4: Tren Perubahan ────────────────────────────────────
with tab4:
    st.markdown("#### Tren Pertumbuhan Pemilih per Kabupaten")
    tren = fdf.groupby(["kabupaten","keterangan"])["jumlah_pemilih"].sum().reset_index()
    tren["label"] = tren["keterangan"].map(label_map)
    # Urutkan sesuai urutan periode di data
    order_map = {k: i for i, k in enumerate(all_periods_in_data)}
    tren["order"] = tren["keterangan"].map(order_map)
    tren = tren.sort_values("order")

    fig11 = px.line(tren, x="label", y="jumlah_pemilih",
                    color="kabupaten", markers=True,
                    color_discrete_sequence=COLOR_POOL,
                    labels={"label":"","jumlah_pemilih":"Jumlah Pemilih","kabupaten":"Kabupaten"})
    fig11.update_traces(line_width=2.2, marker_size=9)
    apply_theme(fig11, 380, hovermode="x unified")
    st.plotly_chart(fig11, use_container_width=True)

    # Persentase perubahan — dinamis: semua pasangan periode berurutan
    st.markdown("#### Persentase Perubahan Antar Periode")
    # Buat pasangan otomatis: (period[0]→period[1]), (period[1]→period[2]), dst
    pairs = []
    for i in range(len(active_periods) - 1):
        p1, p2 = active_periods[i], active_periods[i+1]
        lbl = f"{p_label(p1)} → {p_label(p2)}"
        pairs.append((p1, p2, lbl))

    pct_rows = []
    for kab in sorted(fdf["kabupaten"].unique()):
        for p1, p2, lbl in pairs:
            v1 = fdf[(fdf["kabupaten"]==kab)&(fdf["keterangan"]==p1)]["jumlah_pemilih"].sum()
            v2 = fdf[(fdf["kabupaten"]==kab)&(fdf["keterangan"]==p2)]["jumlah_pemilih"].sum()
            if v1 > 0:
                pct_rows.append({"Kabupaten":kab, "Perubahan":lbl, "Persen":(v2-v1)/v1*100})

    pct_df = pd.DataFrame(pct_rows)
    if not pct_df.empty:
        fig12 = px.bar(pct_df, x="Kabupaten", y="Persen", color="Perubahan",
                       barmode="group",
                       color_discrete_sequence=COLOR_POOL,
                       text=pct_df["Persen"].round(2).astype(str)+"%",
                       labels={"Persen":"Perubahan (%)"})
        fig12.add_hline(y=0, line_color="#ffffff", line_width=1, opacity=0.3)
        fig12.update_traces(textposition="outside")
        apply_theme(fig12, 380, xaxis_title="", yaxis_title="Persentase Perubahan (%)")
        st.plotly_chart(fig12, use_container_width=True)

    # Tabel ringkas — dinamis: kolom = semua periode yang ada
    st.markdown("#### Tabel Ringkas Perubahan Jumlah Pemilih")
    summary_rows = []
    for kab in sorted(df["kabupaten"].unique()):
        row = {"Kabupaten": kab}
        for kode in all_periods_in_data:
            v = df[(df["kabupaten"]==kab)&(df["keterangan"]==kode)]["jumlah_pemilih"].sum()
            row[p_label(kode)] = f"{v:,.0f}"
        # Delta: periode pertama → periode terakhir
        if len(all_periods_in_data) >= 2:
            p_first, p_last = all_periods_in_data[0], all_periods_in_data[-1]
            v_first = df[(df["kabupaten"]==kab)&(df["keterangan"]==p_first)]["jumlah_pemilih"].sum()
            v_last  = df[(df["kabupaten"]==kab)&(df["keterangan"]==p_last)]["jumlah_pemilih"].sum()
            if v_first > 0:
                d = (v_last - v_first) / v_first * 100
                lbl_delta = f"Δ {p_label(p_first)}→{p_label(p_last)} (%)"
                row[lbl_delta] = f"+{d:.2f}%" if d >= 0 else f"{d:.2f}%"
        summary_rows.append(row)

    st.dataframe(pd.DataFrame(summary_rows), use_container_width=True, hide_index=True)

# ── TABEL DATA ────────────────────────────────────────────────
if show_table:
    st.markdown("---")
    st.markdown(f"### 📋 Data Lengkap ({len(fdf)} baris)")
    disp = fdf.copy()
    disp["jumlah_pemilih"] = disp["jumlah_pemilih"].apply(lambda x: f"{x:,.0f}")
    disp["keterangan"]    = disp["keterangan"].map(label_map)
    disp["jenis_kelamin"] = disp["jenis_kelamin"].map({"L":"Laki-laki","P":"Perempuan"})
    st.dataframe(
        disp[["kabupaten","jumlah_kec","jumlah_kel_desa","jenis_kelamin","keterangan","jumlah_pemilih"]]
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
n_p = len(all_periods_in_data)
st.markdown(f"""<div style='text-align:center;color:#334155;font-size:.78rem'>
    🗳️ Dashboard Rekap Data Pemilih Sulawesi Barat &nbsp;·&nbsp;
    {n_p} periode terdeteksi &nbsp;·&nbsp; {tren_str}
</div>""", unsafe_allow_html=True)
