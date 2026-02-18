import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import io
import anthropic
from modules.eda import run_eda
from modules.etl import run_etl
from modules.insights import run_insights

# ─── PAGE CONFIG ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="DataLens AI",
    page_icon="🔭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── CUSTOM CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;700;800&family=DM+Sans:wght@300;400;500&display=swap');

:root {
    --bg: #0A0A0F;
    --surface: #12121A;
    --border: #1E1E2E;
    --accent: #6C63FF;
    --accent2: #FF6584;
    --text: #E8E8F0;
    --muted: #6B6B80;
}

html, body, [data-testid="stApp"] {
    background-color: var(--bg);
    color: var(--text);
    font-family: 'DM Sans', sans-serif;
}

h1, h2, h3 { font-family: 'Syne', sans-serif; }

[data-testid="stSidebar"] {
    background-color: var(--surface) !important;
    border-right: 1px solid var(--border);
}

.metric-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px;
    margin: 8px 0;
    transition: border-color 0.2s;
}
.metric-card:hover { border-color: var(--accent); }

.section-title {
    font-family: 'Syne', sans-serif;
    font-size: 1.4rem;
    font-weight: 700;
    color: var(--accent);
    border-bottom: 1px solid var(--border);
    padding-bottom: 8px;
    margin: 24px 0 16px 0;
}

.insight-card {
    background: linear-gradient(135deg, #12121A 0%, #1A1A2E 100%);
    border: 1px solid var(--accent);
    border-radius: 12px;
    padding: 20px;
    margin: 12px 0;
}

.badge {
    display: inline-block;
    background: var(--accent);
    color: white;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
    margin-right: 6px;
}

[data-testid="stButton"] > button {
    background: var(--accent) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    padding: 0.5rem 1.5rem !important;
    transition: opacity 0.2s !important;
}
[data-testid="stButton"] > button:hover { opacity: 0.85 !important; }

.stTabs [data-baseweb="tab"] {
    font-family: 'Syne', sans-serif !important;
    color: var(--muted) !important;
}
.stTabs [aria-selected="true"] {
    color: var(--accent) !important;
    border-bottom-color: var(--accent) !important;
}
</style>
""", unsafe_allow_html=True)

# ─── HEADER ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center; padding: 2rem 0 1rem 0;">
    <h1 style="font-family:'Syne',sans-serif; font-size:3rem; font-weight:800; 
               background: linear-gradient(90deg,#6C63FF,#FF6584); 
               -webkit-background-clip:text; -webkit-text-fill-color:transparent; margin:0;">
        🔭 DataLens AI
    </h1>
    <p style="color:#6B6B80; font-size:1.1rem; margin-top:8px;">
        EDA · ETL · Insights de Negocio con Inteligencia Artificial
    </p>
</div>
""", unsafe_allow_html=True)

# ─── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Configuración")
    st.markdown("---")

    api_key = st.text_input("🔑 Anthropic API Key", type="password",
                             help="Obtén tu key en console.anthropic.com")

    st.markdown("---")
    uploaded_file = st.file_uploader("📁 Sube tu dataset",
                                      type=["csv", "xlsx", "xls"],
                                      help="Soporta CSV y Excel")

    if uploaded_file:
        st.success(f"✅ **{uploaded_file.name}** cargado")

    st.markdown("---")
    st.markdown("### 🎯 KPI Principal")
    kpi_col = st.selectbox("Variable KPI", options=[], key="kpi_selector_placeholder")
    kpi_context = st.text_area("Contexto del negocio",
                                placeholder="Ej: Somos una empresa de retail. El KPI mide las ventas mensuales...",
                                height=100)

    st.markdown("---")
    st.markdown("### 🔧 Opciones ETL")
    drop_duplicates = st.checkbox("Eliminar duplicados", value=True)
    fill_nulls = st.selectbox("Manejo de nulos", ["Mediana/Moda", "Media", "Eliminar filas", "Dejar como están"])
    normalize = st.checkbox("Normalizar columnas numéricas", value=False)

    st.markdown("---")
    run_btn = st.button("🚀 Analizar Dataset", use_container_width=True)

# ─── LOAD DATA ─────────────────────────────────────────────────────────────────
df_raw = None
df_clean = None

if uploaded_file:
    try:
        if uploaded_file.name.endswith(".csv"):
            df_raw = pd.read_csv(uploaded_file)
        else:
            df_raw = pd.read_excel(uploaded_file)

        # Update KPI selector with real columns
        with st.sidebar:
            kpi_col = st.selectbox("Variable KPI", options=df_raw.columns.tolist(), key="kpi_selector")

    except Exception as e:
        st.error(f"Error al cargar el archivo: {e}")

# ─── MAIN TABS ─────────────────────────────────────────────────────────────────
if df_raw is not None:
    tab1, tab2, tab3, tab4 = st.tabs(["📊 EDA", "🔧 ETL", "🤖 Insights IA", "📥 Exportar"])

    with tab1:
        run_eda(df_raw)

    with tab2:
        df_clean = run_etl(df_raw, drop_duplicates=drop_duplicates,
                           fill_strategy=fill_nulls, normalize=normalize)

    with tab3:
        if not api_key:
            st.warning("⚠️ Ingresa tu Anthropic API Key en el sidebar para activar los Insights IA.")
        else:
            selected_kpi = kpi_col if "kpi_selector" in st.session_state else (df_raw.columns[0] if len(df_raw.columns) > 0 else None)
            run_insights(
                df=df_clean if df_clean is not None else df_raw,
                kpi_col=selected_kpi,
                context=kpi_context,
                api_key=api_key
            )

    with tab4:
        st.markdown('<p class="section-title">📥 Exportar Dataset Limpio</p>', unsafe_allow_html=True)
        df_export = df_clean if df_clean is not None else df_raw

        col1, col2 = st.columns(2)
        with col1:
            csv_bytes = df_export.to_csv(index=False).encode()
            st.download_button("⬇️ Descargar CSV", csv_bytes, "dataset_limpio.csv", "text/csv", use_container_width=True)
        with col2:
            excel_buf = io.BytesIO()
            df_export.to_excel(excel_buf, index=False)
            st.download_button("⬇️ Descargar Excel", excel_buf.getvalue(),
                               "dataset_limpio.xlsx",
                               "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                               use_container_width=True)

        st.markdown(f"**Filas:** {len(df_export):,} | **Columnas:** {len(df_export.columns)}")
        st.dataframe(df_export.head(20), use_container_width=True)

else:
    # Landing state
    st.markdown("""
    <div style="text-align:center; padding: 4rem 2rem; opacity:0.7;">
        <div style="font-size:5rem;">📂</div>
        <h3 style="font-family:'Syne',sans-serif; color:#6B6B80;">Sube un dataset para comenzar</h3>
        <p style="color:#4A4A5A;">Formatos soportados: CSV, XLSX, XLS</p>
    </div>
    """, unsafe_allow_html=True)
