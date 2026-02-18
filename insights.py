import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import anthropic
import json

PLOTLY_THEME = dict(
    template="plotly_dark",
    paper_bgcolor="#0A0A0F",
    plot_bgcolor="#12121A",
    font_color="#E8E8F0",
)
COLOR_SEQ = px.colors.qualitative.Bold


def _build_dataset_summary(df: pd.DataFrame, kpi_col: str) -> str:
    numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()

    summary = {
        "shape": {"rows": len(df), "columns": len(df.columns)},
        "columns": df.columns.tolist(),
        "numeric_stats": df[numeric_cols].describe().round(4).to_dict() if numeric_cols else {},
        "categorical_top": {c: df[c].value_counts().nlargest(5).to_dict() for c in cat_cols[:5]},
        "null_counts": df.isnull().sum().to_dict(),
        "kpi_column": kpi_col,
        "kpi_stats": df[kpi_col].describe().round(4).to_dict() if kpi_col and kpi_col in df.columns and pd.api.types.is_numeric_dtype(df[kpi_col]) else "No numérico",
        "correlation_with_kpi": df[numeric_cols].corrwith(df[kpi_col]).round(4).to_dict() if kpi_col and kpi_col in numeric_cols and len(numeric_cols) > 1 else {},
    }
    return json.dumps(summary, ensure_ascii=False, default=str)


def run_insights(df: pd.DataFrame, kpi_col: str, context: str, api_key: str):
    st.markdown('<p class="section-title">🤖 Insights de Negocio con IA</p>', unsafe_allow_html=True)

    if not kpi_col:
        st.warning("⚠️ Selecciona el KPI principal en el sidebar.")
        return

    # ── KPI Dashboard
    st.markdown("#### 🎯 Dashboard del KPI")
    if kpi_col in df.columns and pd.api.types.is_numeric_dtype(df[kpi_col]):
        m1, m2, m3, m4 = st.columns(4)
        stats = [
            ("Media", f"{df[kpi_col].mean():,.2f}"),
            ("Mediana", f"{df[kpi_col].median():,.2f}"),
            ("Desv. Std.", f"{df[kpi_col].std():,.2f}"),
            ("Total", f"{df[kpi_col].sum():,.0f}"),
        ]
        for col, (label, val) in zip([m1, m2, m3, m4], stats):
            col.markdown(f"""
            <div class="metric-card">
                <div style="color:#6B6B80;font-size:0.8rem;">{label}</div>
                <div style="font-size:1.5rem;font-weight:700;font-family:'Syne',sans-serif;color:#6C63FF;">{val}</div>
            </div>""", unsafe_allow_html=True)

        # KPI distribution
        c1, c2 = st.columns(2)
        with c1:
            fig_kpi = px.histogram(df, x=kpi_col, title=f"Distribución de {kpi_col}",
                                   nbins=40, color_discrete_sequence=["#6C63FF"], **PLOTLY_THEME)
            fig_kpi.update_layout(height=350, margin=dict(t=50))
            st.plotly_chart(fig_kpi, use_container_width=True)
        with c2:
            numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
            if len(numeric_cols) > 1:
                corr = df[numeric_cols].corrwith(df[kpi_col]).drop(kpi_col, errors="ignore").sort_values()
                fig_corr = px.bar(x=corr.values, y=corr.index, orientation="h",
                                  title=f"Correlación con {kpi_col}",
                                  color=corr.values, color_continuous_scale="RdBu",
                                  **PLOTLY_THEME)
                fig_corr.update_layout(height=350, margin=dict(t=50))
                st.plotly_chart(fig_corr, use_container_width=True)

        # KPI by category
        cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
        if cat_cols:
            st.markdown("#### 📊 KPI por Categoría")
            sel_cat = st.selectbox("Analizar KPI por", cat_cols, key="kpi_cat")
            top_cats = df[sel_cat].value_counts().nlargest(15).index
            df_agg = df[df[sel_cat].isin(top_cats)].groupby(sel_cat)[kpi_col].agg(["mean", "sum", "count"]).reset_index()
            df_agg.columns = [sel_cat, "Media", "Total", "Registros"]

            agg_metric = st.radio("Métrica", ["Media", "Total", "Registros"], horizontal=True)
            fig_cat = px.bar(df_agg.sort_values(agg_metric, ascending=False),
                             x=sel_cat, y=agg_metric,
                             title=f"{kpi_col} ({agg_metric}) por {sel_cat}",
                             color=agg_metric, color_continuous_scale="Bluyl",
                             **PLOTLY_THEME)
            fig_cat.update_layout(height=420, margin=dict(t=50))
            st.plotly_chart(fig_cat, use_container_width=True)

    st.markdown("---")

    # ── AI Insights
    st.markdown("#### 🧠 Análisis con Claude AI")

    prompt_options = {
        "📊 Análisis Completo": "completo",
        "💡 Oportunidades de Negocio": "oportunidades",
        "⚠️ Riesgos y Anomalías": "riesgos",
        "📈 Recomendaciones de Acción": "acciones",
    }
    selected_prompts = st.multiselect(
        "¿Qué análisis deseas?",
        list(prompt_options.keys()),
        default=["📊 Análisis Completo"]
    )

    if st.button("🔮 Generar Insights con IA", use_container_width=True):
        if not selected_prompts:
            st.warning("Selecciona al menos un tipo de análisis")
            return

        dataset_summary = _build_dataset_summary(df, kpi_col)

        prompt_map = {
            "completo": f"""Eres un analista de datos senior. Analiza este dataset y proporciona:
1. Resumen ejecutivo del dataset (2-3 párrafos)
2. Hallazgos clave sobre el KPI '{kpi_col}'
3. Patrones y tendencias identificadas
4. Correlaciones más importantes
5. Segmentos de alto y bajo rendimiento

Contexto del negocio: {context if context else 'No proporcionado'}
Datos del dataset: {dataset_summary}

Responde en español, de forma clara y estructurada con bullets y secciones.""",

            "oportunidades": f"""Como consultor de negocio, identifica oportunidades basadas en el KPI '{kpi_col}':
1. Top 3-5 oportunidades de mejora
2. Segmentos de mayor potencial
3. Variables que más impactan positivamente el KPI
4. Acciones de quick-win (alto impacto, baja complejidad)

Contexto del negocio: {context if context else 'No proporcionado'}
Datos: {dataset_summary}""",

            "riesgos": f"""Como analista de riesgos, evalúa los riesgos en el KPI '{kpi_col}':
1. Anomalías y valores atípicos detectados
2. Variables de riesgo que impactan negativamente el KPI
3. Segmentos problemáticos
4. Alertas tempranas recomendadas

Datos: {dataset_summary}""",

            "acciones": f"""Como director de estrategia, proporciona un plan de acción para mejorar '{kpi_col}':
1. Priorización de acciones (Alta/Media/Baja urgencia)
2. KPIs secundarios a monitorear
3. Métricas de éxito para cada acción
4. Roadmap sugerido (30-60-90 días)

Contexto: {context if context else 'No proporcionado'}
Datos: {dataset_summary}""",
        }

        client = anthropic.Anthropic(api_key=api_key)

        for prompt_label in selected_prompts:
            prompt_key = prompt_options[prompt_label]
            st.markdown(f"""
            <div class="insight-card">
                <div style="font-family:'Syne',sans-serif;font-size:1.1rem;font-weight:700;margin-bottom:12px;">
                    {prompt_label}
                </div>
            """, unsafe_allow_html=True)

            with st.spinner(f"Analizando {prompt_label}..."):
                try:
                    result_placeholder = st.empty()
                    full_response = ""

                    with client.messages.stream(
                        model="claude-sonnet-4-20250514",
                        max_tokens=2000,
                        messages=[{"role": "user", "content": prompt_map[prompt_key]}]
                    ) as stream:
                        for text in stream.text_stream:
                            full_response += text
                            result_placeholder.markdown(full_response)

                except Exception as e:
                    st.error(f"Error al consultar Claude AI: {e}")

            st.markdown("</div>", unsafe_allow_html=True)
            st.markdown("")

    # ── Custom question
    st.markdown("---")
    st.markdown("#### 💬 Pregunta Personalizada al Analista IA")
    user_question = st.text_area("Escribe tu pregunta sobre los datos",
                                  placeholder="Ej: ¿Cuáles son los 3 factores que más afectan mis ventas? ¿Qué segmento tiene mayor potencial?",
                                  height=80)
    if st.button("🔍 Consultar", use_container_width=True):
        if not user_question.strip():
            st.warning("Escribe una pregunta primero")
            return

        dataset_summary = _build_dataset_summary(df, kpi_col)
        full_prompt = f"""Eres un analista de datos experto. El usuario tiene este dataset:
{dataset_summary}

KPI principal: {kpi_col}
Contexto del negocio: {context if context else 'No proporcionado'}

Pregunta del usuario: {user_question}

Responde de forma clara, concisa y accionable en español."""

        with st.spinner("Consultando a Claude AI..."):
            try:
                client = anthropic.Anthropic(api_key=api_key)
                result_ph = st.empty()
                full_response = ""

                with client.messages.stream(
                    model="claude-sonnet-4-20250514",
                    max_tokens=1500,
                    messages=[{"role": "user", "content": full_prompt}]
                ) as stream:
                    for text in stream.text_stream:
                        full_response += text
                        result_ph.markdown(f"""
                        <div class="insight-card">{full_response}</div>
                        """, unsafe_allow_html=True)

            except Exception as e:
                st.error(f"Error: {e}")
