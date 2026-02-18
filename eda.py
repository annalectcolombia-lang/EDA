import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

PLOTLY_THEME = dict(
    template="plotly_dark",
    paper_bgcolor="#0A0A0F",
    plot_bgcolor="#12121A",
    font_color="#E8E8F0",
)

COLOR_SEQ = px.colors.qualitative.Bold


def run_eda(df: pd.DataFrame):
    st.markdown('<p class="section-title">📊 Análisis Exploratorio de Datos</p>', unsafe_allow_html=True)

    # ── Overview metrics
    col1, col2, col3, col4 = st.columns(4)
    numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
    null_pct = (df.isnull().sum().sum() / (df.shape[0] * df.shape[1]) * 100)
    dup_count = df.duplicated().sum()

    metrics = [
        ("🗃️ Filas", f"{len(df):,}"),
        ("📐 Columnas", str(len(df.columns))),
        ("🕳️ Nulos", f"{null_pct:.1f}%"),
        ("📋 Duplicados", str(dup_count)),
    ]
    for col, (label, val) in zip([col1, col2, col3, col4], metrics):
        col.markdown(f"""
        <div class="metric-card">
            <div style="color:#6B6B80;font-size:0.85rem;">{label}</div>
            <div style="font-size:1.8rem;font-weight:700;font-family:'Syne',sans-serif;">{val}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # ── Data types overview
    st.markdown("#### 🗂️ Tipos de Datos")
    dtype_df = pd.DataFrame({
        "Columna": df.columns,
        "Tipo": df.dtypes.astype(str),
        "Nulos": df.isnull().sum().values,
        "% Nulos": (df.isnull().sum().values / len(df) * 100).round(2),
        "Únicos": df.nunique().values,
    })
    st.dataframe(
        dtype_df.style.background_gradient(subset=["% Nulos"], cmap="RdYlGn_r"),
        use_container_width=True, height=250
    )

    # ── Null heatmap
    if df.isnull().any().any():
        st.markdown("#### 🕳️ Mapa de Nulos")
        null_matrix = df.isnull().astype(int)
        fig_null = px.imshow(
            null_matrix.T,
            color_continuous_scale=["#12121A", "#6C63FF"],
            labels=dict(color="Nulo"),
            title="Mapa de valores nulos (1=nulo, 0=ok)",
            **PLOTLY_THEME,
        )
        fig_null.update_layout(height=300, margin=dict(t=40, b=20))
        st.plotly_chart(fig_null, use_container_width=True)

    # ── Numeric distributions
    if numeric_cols:
        st.markdown("#### 📈 Distribuciones Numéricas")
        selected_num = st.multiselect("Selecciona variables numéricas", numeric_cols,
                                       default=numeric_cols[:min(4, len(numeric_cols))])
        if selected_num:
            n = len(selected_num)
            cols_grid = min(2, n)
            rows_grid = (n + cols_grid - 1) // cols_grid

            fig_dist = make_subplots(rows=rows_grid, cols=cols_grid,
                                     subplot_titles=selected_num)
            for i, col_name in enumerate(selected_num):
                r, c = divmod(i, cols_grid)
                fig_dist.add_trace(
                    go.Histogram(x=df[col_name].dropna(), name=col_name,
                                 marker_color=COLOR_SEQ[i % len(COLOR_SEQ)],
                                 showlegend=False, nbinsx=30),
                    row=r + 1, col=c + 1
                )
            fig_dist.update_layout(
                height=350 * rows_grid,
                **PLOTLY_THEME,
                margin=dict(t=50, b=20)
            )
            st.plotly_chart(fig_dist, use_container_width=True)

        # Correlation matrix
        if len(numeric_cols) > 1:
            st.markdown("#### 🔗 Matriz de Correlación")
            corr = df[numeric_cols].corr()
            fig_corr = px.imshow(
                corr,
                color_continuous_scale="RdBu_r",
                zmin=-1, zmax=1,
                title="Correlación de Pearson",
                text_auto=".2f",
                **PLOTLY_THEME,
            )
            fig_corr.update_layout(height=500, margin=dict(t=50))
            st.plotly_chart(fig_corr, use_container_width=True)

        # Stats summary
        st.markdown("#### 📋 Estadísticas Descriptivas")
        st.dataframe(df[numeric_cols].describe().T.style.background_gradient(cmap="Blues"),
                     use_container_width=True)

        # Boxplots
        st.markdown("#### 📦 Boxplots (detección de outliers)")
        selected_box = st.selectbox("Variable para boxplot", numeric_cols)
        group_options = ["Sin agrupación"] + cat_cols
        group_by = st.selectbox("Agrupar por", group_options)

        if group_by == "Sin agrupación":
            fig_box = px.box(df, y=selected_box, title=f"Boxplot: {selected_box}",
                             color_discrete_sequence=COLOR_SEQ, **PLOTLY_THEME)
        else:
            top_cats = df[group_by].value_counts().nlargest(10).index
            df_filtered = df[df[group_by].isin(top_cats)]
            fig_box = px.box(df_filtered, x=group_by, y=selected_box,
                             title=f"Boxplot: {selected_box} por {group_by}",
                             color=group_by, color_discrete_sequence=COLOR_SEQ, **PLOTLY_THEME)
        fig_box.update_layout(height=420, margin=dict(t=50))
        st.plotly_chart(fig_box, use_container_width=True)

    # ── Categorical
    if cat_cols:
        st.markdown("#### 🏷️ Variables Categóricas")
        selected_cat = st.selectbox("Variable categórica", cat_cols)
        top_n = st.slider("Top N categorías", 5, 30, 10)

        vc = df[selected_cat].value_counts().nlargest(top_n).reset_index()
        vc.columns = [selected_cat, "count"]

        fig_bar = px.bar(
            vc, x="count", y=selected_cat, orientation="h",
            title=f"Top {top_n}: {selected_cat}",
            color="count", color_continuous_scale="Bluyl",
            **PLOTLY_THEME
        )
        fig_bar.update_layout(height=420, margin=dict(t=50),
                               yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig_bar, use_container_width=True)

    # ── Scatter plot
    if len(numeric_cols) >= 2:
        st.markdown("#### 🔵 Diagrama de Dispersión")
        c1, c2, c3 = st.columns(3)
        x_col = c1.selectbox("Eje X", numeric_cols, index=0)
        y_col = c2.selectbox("Eje Y", numeric_cols, index=min(1, len(numeric_cols)-1))
        color_col = c3.selectbox("Color (opcional)", ["Ninguno"] + cat_cols)

        fig_sc = px.scatter(
            df, x=x_col, y=y_col,
            color=None if color_col == "Ninguno" else color_col,
            trendline="ols",
            title=f"{y_col} vs {x_col}",
            opacity=0.7,
            color_discrete_sequence=COLOR_SEQ,
            **PLOTLY_THEME
        )
        fig_sc.update_layout(height=450, margin=dict(t=50))
        st.plotly_chart(fig_sc, use_container_width=True)
