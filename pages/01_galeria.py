import streamlit as st
import json
from PIL import Image
import numpy as np

# Importamos el registro de modelos y ambas funciones de nuestro nuevo llm.py
from utils.llm import get_gallery_description, get_galaxy_explanation, MODEL_REGISTRY
from utils.model_loader import load_model_and_metadata, predict_galaxy

st.set_page_config(page_title="Galería — Sideral", layout="wide")

# ==========================================
# 1. CONFIGURACIÓN GLOBAL EN SIDEBAR
# ==========================================
# Colocamos el selector de IA en el sidebar. 
# Esto mejora el UX porque es una decisión "global" para toda la página.
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3254/3254054.png", width=50) # Un loguito temporal para Sideral
    st.markdown("### Configuración de IA")
    modelo_elegido = st.selectbox(
        "🧠 Modelo de Lenguaje (LLM):",
        options=list(MODEL_REGISTRY.keys()),
        index=0,
        help="Selecciona qué inteligencia artificial generará las narrativas."
    )
    
    st.markdown("---")
    st.markdown("Sideral © 2025")

# ==========================================
# 2. CARGA DE DATOS Y MODELOS
# ==========================================
with open("data/gallery_metadata.json") as f:
    gallery_data = json.load(f)["galaxies"]

# Asumo que esta función ya tiene su propio @st.cache_resource en model_loader.py
model, model_metadata = load_model_and_metadata()

# ==========================================
# 3. INTERFAZ PRINCIPAL
# ==========================================
st.title("🌌 Galería de Galaxias")
st.markdown("Explora ejemplos representativos de cada tipo morfológico.")

CLASE_LABELS = {
    "elliptical": "🔴 Elípticas",
    "spiral":     "🌀 Espirales",
    "edge_on":    "💫 Edge-on",
    "merger":     "💥 Mergers"
}

clase_sel = st.radio(
    "Filtrar por tipo:",
    options=["todas"] + list(CLASE_LABELS.keys()),
    format_func=lambda x: "🔭 Todas" if x == "todas" else CLASE_LABELS[x],
    horizontal=True
)

galaxias_filtradas = (
    gallery_data if clase_sel == "todas"
    else [g for g in gallery_data if g["class"] == clase_sel]
)

cols = st.columns(3)

# ==========================================
# 4. RENDERIZADO DE LA GALERÍA
# ==========================================
for i, galaxy in enumerate(galaxias_filtradas):
    with cols[i % 3]:
        img = Image.open(f"data/images/{galaxy['image_file']}")
        st.image(img, use_container_width=True)
        st.markdown(f"**{galaxy['name']}** — {galaxy['designation']}")
        st.caption(
            f"{CLASE_LABELS[galaxy['class']]} · "
            f"{galaxy['distance_ly']} al · "
            f"{galaxy['constellation']}"
        )

        with st.expander("Ver clasificación y explicación"):
            # Predicción con la CNN (EfficientNet B0)
            img_array = np.array(img.convert("RGB"))
            predicted_class, probabilities = predict_galaxy(
                model, model_metadata, img_array
            )

            st.markdown("**Clasificación del modelo:**")
            # Mostramos la distribución Softmax
            for cls, prob in sorted(probabilities.items(), key=lambda x: -x[1]):
                st.progress(prob, text=f"{cls}: {prob*100:.1f}%")

            nivel = st.selectbox(
                "Nivel de explicación:",
                ["general", "estudiante", "experto"],
                key=f"nivel_{galaxy['name']}" # Cambié ID por nombre por si tu JSON no tiene 'id'
            )

            # Generación de la narrativa con el LLM elegido
            if st.button("Generar explicación", key=f"btn_{galaxy['name']}"):
                with st.spinner(f"Consultando a {modelo_elegido}..."):
                    # NOTA DE MENTOR: 
                    # Decidí usar get_galaxy_explanation en lugar de get_gallery_description
                    # porque aquí YA tienes las predicciones de tu red neuronal, y vale la pena
                    # que el LLM explique por qué la EfficientNet falló o acertó.
                    explanation = get_galaxy_explanation(
                        galaxy_name=galaxy['name'],
                        predicted_class=predicted_class,
                        probabilities=probabilities,
                        model_name=modelo_elegido,  # Pasamos el modelo del sidebar
                        knowledge_level=nivel       # Pasamos el nivel elegido
                    )
                    st.success("Explicación generada")
                    st.markdown(explanation)

        st.divider()