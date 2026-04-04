import streamlit as st
import numpy as np
from PIL import Image

# Importamos el registro de modelos además de la función
from utils.model_loader import load_model_and_metadata, predict_galaxy
from utils.llm import get_galaxy_explanation, MODEL_REGISTRY

st.set_page_config(page_title="Clasificador — Sideral", layout="wide")

# ==========================================
# 1. CONFIGURACIÓN GLOBAL EN SIDEBAR
# ==========================================
# Mantenemos la consistencia visual con la galería
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3254/3254054.png", width=50) # Logo Sideral
    st.markdown("### Configuración de IA")
    modelo_elegido = st.selectbox(
        "🧠 Modelo de Lenguaje (LLM):",
        options=list(MODEL_REGISTRY.keys()),
        index=0,
        help="Selecciona qué inteligencia artificial interpretará los resultados."
    )
    
    st.markdown("---")
    st.markdown("Sideral © 2025")

# ==========================================
# 2. CARGA DE MODELO (CNN)
# ==========================================
model, model_metadata = load_model_and_metadata()

# ==========================================
# 3. INTERFAZ PRINCIPAL
# ==========================================
st.title("🤖 Clasificador de Galaxias")
st.markdown("""
Sube una imagen de una galaxia y el modelo determinará su tipo morfológico.
Funciona mejor con imágenes del SDSS u otros surveys ópticos en bandas g, r, i.
""")

col_upload, col_result = st.columns([1, 1], gap="large")

with col_upload:
    uploaded = st.file_uploader(
        "Sube tu imagen de galaxia",
        type=["jpg", "jpeg", "png"],
        help="Formatos soportados: JPG, PNG. Resolución recomendada: mínimo 224×224 px."
    )

    nivel = st.selectbox(
        "Nivel de explicación astronómica:",
        ["General", "Estudiante", "Experto"],
        help="Ajusta el nivel técnico de la explicación generada por el modelo de lenguaje."
    )

    if uploaded:
        # Programación defensiva por si la imagen tiene canal Alpha (RGBA)
        img = Image.open(uploaded).convert("RGB")
        st.image(img, caption="Imagen cargada", use_container_width=True)

with col_result:
    if uploaded:
        img_array = np.array(img)

        with st.spinner("Clasificando con EfficientNet..."):
            predicted_class, probabilities = predict_galaxy(
                model, model_metadata, img_array
            )

        CLASE_LABELS = {
            "elliptical": "🔴 Elíptica",
            "spiral":     "🌀 Espiral",
            "edge_on":    "💫 Edge-on (disco de canto)",
            "merger":     "💥 Merger (galaxias en fusión)"
        }

        st.success(f"### Clasificación: {CLASE_LABELS.get(predicted_class, predicted_class)}")

        st.markdown("**Probabilidades (Distribución Softmax):**")
        for cls, prob in sorted(probabilities.items(), key=lambda x: -x[1]):
            st.progress(
                prob,
                text=f"{CLASE_LABELS.get(cls, cls)}: {prob*100:.1f}%"
            )

        # Análisis de entropía/incertidumbre
        max_prob = max(probabilities.values())
        if max_prob < 0.6:
            st.warning(
                "⚠️ La confianza del modelo es baja. "
                "La imagen puede no corresponder a una galaxia clara, "
                "tener ruido atmosférico, o ser un caso morfológicamente ambiguo."
            )

        st.divider()
        if st.button("🔍 Generar explicación astronómica", use_container_width=True):
            with st.spinner(f"Consultando a {modelo_elegido}..."):
                # Agregamos el parámetro model_name que creamos en llm.py
                explanation = get_galaxy_explanation(
                    galaxy_name="imagen subida por el usuario",
                    predicted_class=predicted_class,
                    probabilities=probabilities,
                    model_name=modelo_elegido,  # <--- Integración Multi-LLM
                    knowledge_level=nivel
                )
            st.markdown(f"**Análisis de la IA ({modelo_elegido}):**")
            st.markdown(explanation)
    else:
        st.info("👈 Sube una imagen para comenzar la clasificación.")