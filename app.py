import streamlit as st
from utils.secrets import bootstrap_env
bootstrap_env()

st.set_page_config(
    page_title="Sideral",
    page_icon="🔭",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🔭 Sideral")
st.subheader("Exploración y clasificación morfológica de galaxias")

st.markdown("""
Sideral es una aplicación interactiva que combina visión por computadora 
y modelos de lenguaje para explorar la morfología de galaxias.

**¿Qué puedes hacer aquí?**
- 🌌 **Galería** — Explora galaxias clasificadas por tipo morfológico
- 🤖 **Clasificador** — Sube una imagen y obtén una clasificación automática

El clasificador usa **EfficientNet-B0** entrenado sobre Galaxy Zoo 2 
con ~5,000 imágenes etiquetadas por consenso ciudadano científico.
""")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Clases morfológicas", "4")
with col2:
    st.metric("Imágenes de entrenamiento", "5,060")
with col3:
    st.metric("Accuracy en test", "90.1%")
with col4:
    st.metric("Arquitectura", "EfficientNet-B0")