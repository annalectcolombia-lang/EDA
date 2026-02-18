# 🔭 DataLens AI — EDA · ETL · Business Insights

> Sube cualquier dataset CSV/Excel y obtén análisis exploratorio completo, pipeline ETL automatizado e insights de negocio impulsados por Claude AI.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.32+-red)
![Claude](https://img.shields.io/badge/Anthropic-Claude%20AI-purple)

---

## ✨ Funcionalidades

### 📊 EDA Automático
- Métricas generales (filas, columnas, nulos, duplicados)
- Mapa de calor de valores nulos
- Distribuciones de variables numéricas
- Matriz de correlación interactiva
- Boxplots para detección de outliers
- Análisis de variables categóricas
- Diagrama de dispersión configurable

### 🔧 Pipeline ETL
- Eliminación de duplicados
- Imputación de nulos (Mediana/Moda, Media, o eliminar filas)
- Inferencia y conversión automática de fechas
- Extracción de features temporales (año, mes, día, día semana)
- Normalización MinMax opcional

### 🤖 Insights IA (Claude)
- Dashboard del KPI seleccionado
- Análisis de correlación con el KPI
- KPI por categoría con métricas agregadas
- Generación de insights con streaming en tiempo real:
  - Análisis completo
  - Oportunidades de negocio
  - Riesgos y anomalías
  - Plan de acción 30-60-90 días
- Consultas personalizadas en lenguaje natural

### 📥 Exportar
- Descarga el dataset limpio en CSV o Excel

---

## 🚀 Despliegue Local

```bash
# 1. Clonar el repositorio
git clone https://github.com/TU_USUARIO/datalens-ai.git
cd datalens-ai

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Ejecutar
streamlit run app.py
```

---

## ☁️ Despliegue en Streamlit Cloud

1. Haz fork o sube este repo a tu GitHub
2. Ve a [share.streamlit.io](https://share.streamlit.io) y conecta tu repositorio
3. En **Advanced settings → Secrets**, agrega (opcional, también puedes ingresarla en la UI):
   ```
   ANTHROPIC_API_KEY = "sk-ant-..."
   ```
4. ¡Deploy! 🎉

---

## 🗂️ Estructura del Proyecto

```
datalens-ai/
│
├── app.py                   # App principal Streamlit
├── requirements.txt         # Dependencias
├── .streamlit/
│   └── config.toml          # Tema oscuro
│
└── modules/
    ├── __init__.py
    ├── eda.py               # Módulo EDA
    ├── etl.py               # Módulo ETL
    └── insights.py          # Módulo Insights IA
```

---

## 🔑 API Key de Anthropic

Necesitas una API Key de [console.anthropic.com](https://console.anthropic.com) para usar los Insights IA.  
Puedes ingresarla directamente en el sidebar de la app (campo seguro) o configurarla como secreto en Streamlit Cloud.

---

## 📄 Licencia

MIT — libre para usar y modificar.
