import streamlit as st
import json
from PIL import Image
from utils.llm import get_gallery_description
from utils.model_loader import load_model_and_metadata, predict_galaxy
import numpy as np

st.set_page_config(page_title="Galería — Sideral", layout="wide")

with open("data/gallery_metadata.json") as f:
    gallery_data = json.load(f)["galaxies"]

model, model_metadata = load_model_and_metadata()

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
            img_array = np.array(img.convert("RGB"))
            predicted_class, probabilities = predict_galaxy(
                model, model_metadata, img_array
            )

            st.markdown("**Clasificación del modelo:**")
            for cls, prob in sorted(probabilities.items(), key=lambda x: -x[1]):
                st.progress(prob, text=f"{cls}: {prob*100:.1f}%")

            nivel = st.selectbox(
                "Nivel de explicación:",
                ["general", "estudiante", "experto"],
                key=f"nivel_{galaxy['id']}"
            )

            if st.button("Generar explicación", key=f"btn_{galaxy['id']}"):
                with st.spinner("Consultando al modelo de lenguaje..."):
                    explanation = get_gallery_description(galaxy)
                    st.markdown(explanation)

        st.divider()