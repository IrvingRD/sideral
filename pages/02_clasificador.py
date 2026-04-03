import streamlit as st
import numpy as np
from PIL import Image
from utils.model_loader import load_model_and_metadata, predict_galaxy
from utils.llm import get_galaxy_explanation

st.set_page_config(page_title="Clasificador — Sideral", layout="wide")

model, model_metadata = load_model_and_metadata()

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
        "Nivel de explicación:",
        ["general", "estudiante", "experto"],
        help="Ajusta el nivel técnico de la explicación generada por el modelo de lenguaje."
    )

    if uploaded:
        img = Image.open(uploaded).convert("RGB")
        st.image(img, caption="Imagen cargada", use_container_width=True)

with col_result:
    if uploaded:
        img_array = np.array(img)

        with st.spinner("Clasificando..."):
            predicted_class, probabilities = predict_galaxy(
                model, model_metadata, img_array
            )

        CLASE_LABELS = {
            "elliptical": "🔴 Elíptica",
            "spiral":     "🌀 Espiral",
            "edge_on":    "💫 Edge-on (disco de canto)",
            "merger":     "💥 Merger (galaxias en fusión)"
        }

        st.success(f"### Clasificación: {CLASE_LABELS[predicted_class]}")

        st.markdown("**Probabilidades por clase:**")
        for cls, prob in sorted(probabilities.items(), key=lambda x: -x[1]):
            st.progress(
                prob,
                text=f"{CLASE_LABELS[cls]}: {prob*100:.1f}%"
            )

        max_prob = max(probabilities.values())
        if max_prob < 0.6:
            st.warning(
                "⚠️ La confianza del modelo es baja. "
                "La imagen puede no corresponder a una galaxia clara "
                "o puede ser un caso morfológicamente ambiguo."
            )

        st.divider()
        if st.button("🔍 Generar explicación astronómica", use_container_width=True):
            with st.spinner("Consultando al modelo de lenguaje..."):
                explanation = get_galaxy_explanation(
                    galaxy_name="imagen subida",
                    predicted_class=predicted_class,
                    probabilities=probabilities,
                    knowledge_level=nivel
                )
            st.markdown("**Explicación:**")
            st.markdown(explanation)
    else:
        st.info("👈 Sube una imagen para comenzar la clasificación.")