import streamlit as st
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler

PLOTLY_THEME = dict(
    template="plotly_dark",
    paper_bgcolor="#0A0A0F",
    plot_bgcolor="#12121A",
    font_color="#E8E8F0",
)


def run_etl(df: pd.DataFrame, drop_duplicates: bool = True,
            fill_strategy: str = "Mediana/Moda",
            normalize: bool = False) -> pd.DataFrame:

    st.markdown('<p class="section-title">🔧 Pipeline ETL – Limpieza y Transformación</p>',
                unsafe_allow_html=True)

    df_clean = df.copy()
    log = []

    # ── 1. Duplicados
    st.markdown("#### 1️⃣ Manejo de Duplicados")
    dup_before = df_clean.duplicated().sum()
    if drop_duplicates and dup_before > 0:
        df_clean = df_clean.drop_duplicates()
        log.append(f"🗑️ Eliminadas **{dup_before}** filas duplicadas")
        st.success(f"Eliminadas {dup_before} filas duplicadas")
    elif dup_before == 0:
        st.info("✅ No se encontraron duplicados")
    else:
        st.info(f"ℹ️ Se mantienen {dup_before} duplicados (desactivado)")

    # ── 2. Nulos
    st.markdown("#### 2️⃣ Imputación de Nulos")
    null_counts = df_clean.isnull().sum()
    null_cols = null_counts[null_counts > 0]

    if len(null_cols) == 0:
        st.success("✅ No hay valores nulos")
    else:
        st.dataframe(pd.DataFrame({
            "Columna": null_cols.index,
            "Nulos": null_cols.values,
            "% Nulos": (null_cols.values / len(df_clean) * 100).round(2)
        }), use_container_width=True)

        numeric_cols = df_clean.select_dtypes(include=np.number).columns
        cat_cols = df_clean.select_dtypes(include=["object", "category"]).columns

        if fill_strategy == "Mediana/Moda":
            for c in numeric_cols:
                if df_clean[c].isnull().any():
                    df_clean[c].fillna(df_clean[c].median(), inplace=True)
            for c in cat_cols:
                if df_clean[c].isnull().any():
                    df_clean[c].fillna(df_clean[c].mode()[0] if len(df_clean[c].mode()) > 0 else "Unknown", inplace=True)
            log.append("🔧 Nulos imputados con **Mediana/Moda**")
            st.success("Nulos imputados con Mediana (numéricos) y Moda (categóricos)")

        elif fill_strategy == "Media":
            for c in numeric_cols:
                if df_clean[c].isnull().any():
                    df_clean[c].fillna(df_clean[c].mean(), inplace=True)
            for c in cat_cols:
                if df_clean[c].isnull().any():
                    df_clean[c].fillna("Unknown", inplace=True)
            log.append("🔧 Nulos imputados con **Media**")
            st.success("Nulos imputados con Media (numéricos)")

        elif fill_strategy == "Eliminar filas":
            before = len(df_clean)
            df_clean = df_clean.dropna()
            removed = before - len(df_clean)
            log.append(f"🗑️ Eliminadas **{removed}** filas con nulos")
            st.warning(f"Eliminadas {removed} filas con al menos un nulo")

        else:
            st.info("ℹ️ Nulos mantenidos sin cambios")

    # ── 3. Tipos de datos
    st.markdown("#### 3️⃣ Inferencia de Tipos")
    date_candidates = [c for c in df_clean.select_dtypes("object").columns
                       if any(kw in c.lower() for kw in ["date", "fecha", "time", "dia", "mes", "año"])]
    converted = []
    for c in date_candidates:
        try:
            df_clean[c] = pd.to_datetime(df_clean[c], infer_datetime_format=True, errors="coerce")
            converted.append(c)
        except Exception:
            pass
    if converted:
        st.success(f"📅 Columnas convertidas a fecha: {', '.join(converted)}")
        log.append(f"📅 Fechas detectadas y convertidas: {converted}")
    else:
        st.info("ℹ️ No se detectaron columnas de fecha por nombre")

    # ── 4. Normalización
    st.markdown("#### 4️⃣ Normalización")
    numeric_cols = df_clean.select_dtypes(include=np.number).columns.tolist()
    if normalize and len(numeric_cols) > 0:
        scaler = MinMaxScaler()
        df_clean[numeric_cols] = scaler.fit_transform(df_clean[numeric_cols])
        log.append(f"📐 Variables numéricas normalizadas (MinMax): {numeric_cols}")
        st.success(f"Variables normalizadas (0-1): {', '.join(numeric_cols)}")
    else:
        st.info("ℹ️ Normalización desactivada")

    # ── 5. Columnas derivadas de fecha
    date_cols = df_clean.select_dtypes(include=["datetime64"]).columns.tolist()
    if date_cols:
        st.markdown("#### 5️⃣ Features de Fecha Derivadas")
        for dc in date_cols:
            df_clean[f"{dc}_year"] = df_clean[dc].dt.year
            df_clean[f"{dc}_month"] = df_clean[dc].dt.month
            df_clean[f"{dc}_day"] = df_clean[dc].dt.day
            df_clean[f"{dc}_weekday"] = df_clean[dc].dt.day_name()
        st.success(f"✅ Derivadas: año, mes, día, día semana para {date_cols}")
        log.append("📅 Features de fecha extraídas automáticamente")

    # ── Log summary
    st.markdown("#### 📋 Resumen del Pipeline")
    if log:
        for entry in log:
            st.markdown(f"- {entry}")
    else:
        st.info("No se realizaron transformaciones")

    col1, col2 = st.columns(2)
    col1.metric("Filas originales", f"{len(df):,}")
    col2.metric("Filas resultantes", f"{len(df_clean):,}", delta=f"{len(df_clean)-len(df):,}")

    st.markdown("#### 👀 Preview del Dataset Limpio")
    st.dataframe(df_clean.head(30), use_container_width=True)

    return df_clean
