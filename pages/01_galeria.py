import streamlit as st
import json
from PIL import Image
import numpy as np

# Importamos el nuevo chat_universal
from utils.llm import get_galaxy_explanation, MODEL_REGISTRY, chat_universal
from utils.model_loader import load_model_and_metadata, predict_galaxy

st.set_page_config(page_title="Galería — Sideral", layout="wide")

# ==========================================
# 1. ESTADO DE LA SESIÓN (SESSION STATE)
# ==========================================
# Aquí guardamos la memoria del chat y la galaxia activa
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []
if "active_chat_galaxy" not in st.session_state:
    st.session_state.active_chat_galaxy = None

# ==========================================
# 2. CONFIGURACIÓN GLOBAL EN SIDEBAR
# ==========================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3254/3254054.png", width=50)
    st.markdown("### Configuración de IA")
    modelo_elegido = st.selectbox(
        "🧠 Modelo de Lenguaje (LLM):",
        options=list(MODEL_REGISTRY.keys()),
        index=0
    )
    
    # Un botón para limpiar la memoria del chat
    if st.button("🗑️ Limpiar historial de chat"):
        st.session_state.chat_messages = []
        st.session_state.active_chat_galaxy = None
        st.rerun()

    st.markdown("---")
    st.markdown("Sideral © 2025")

# ==========================================
# 3. CARGA DE DATOS Y MODELOS
# ==========================================
with open("data/gallery_metadata.json") as f:
    gallery_data = json.load(f)["galaxies"]

model, model_metadata = load_model_and_metadata()

st.title("🌌 Galería de Galaxias")
st.markdown("Explora ejemplos representativos. Si te da curiosidad una, ¡inicia un chat con la IA!")

CLASE_LABELS = {
    "elliptical": "🔴 Elípticas",
    "spiral":     "🌀 Espirales",
    "edge_on":    "💫 Edge-on",
    "merger":     "💥 Mergers"
}

clase_sel = st.radio("Filtrar por tipo:", options=["todas"] + list(CLASE_LABELS.keys()), 
                     format_func=lambda x: "🔭 Todas" if x == "todas" else CLASE_LABELS[x], horizontal=True)

galaxias_filtradas = gallery_data if clase_sel == "todas" else [g for g in gallery_data if g["class"] == clase_sel]

cols = st.columns(3)

# ==========================================
# 4. RENDERIZADO DE LA GALERÍA
# ==========================================
for i, galaxy in enumerate(galaxias_filtradas):
    with cols[i % 3]:
        img = Image.open(f"data/images/{galaxy['image_file']}")
        st.image(img, use_container_width=True)
        st.markdown(f"**{galaxy['name']}** — {galaxy['designation']}")
        st.caption(f"{CLASE_LABELS[galaxy['class']]} · {galaxy['distance_ly']} al")

        with st.expander("Ver análisis e interactuar"):
            img_array = np.array(img.convert("RGB"))
            predicted_class, probabilities = predict_galaxy(model, model_metadata, img_array)

            st.markdown("**Clasificación CNN:**")
            for cls, prob in sorted(probabilities.items(), key=lambda x: -x[1]):
                st.progress(prob, text=f"{cls}: {prob*100:.1f}%")

            # Botón para activar el chat sobre esta galaxia
            if st.button("💬 Iniciar chat sobre esta galaxia", key=f"btn_chat_{galaxy['name']}"):
                # 1. Definimos la galaxia activa
                st.session_state.active_chat_galaxy = galaxy['name']
                # 2. Reiniciamos la memoria
                # Inyectamos el contexto de Sideral como "system prompt" base temporal
                sys_prompt = f"Eres el asistente astronómico de la app Sideral. El usuario está observando la galaxia {galaxy['name']} (Tipo: {galaxy['class']}, Distancia: {galaxy['distance_ly']} al). Responde sus dudas de forma concisa y amigable."
                st.session_state.chat_messages = [{"role": "system", "content": sys_prompt}]
                # 3. Forzamos recarga de la página para que aparezca la interfaz de chat abajo
                st.rerun()

st.divider()

# ==========================================
# 5. INTERFAZ DE CHAT (ZONA INFERIOR)
# ==========================================
# Solo mostramos esta zona si el usuario seleccionó una galaxia para chatear
if st.session_state.active_chat_galaxy:
    st.markdown(f"### 💬 Chat Interactivo: {st.session_state.active_chat_galaxy}")
    st.caption(f"Pregúntale a **{modelo_elegido}** lo que quieras saber sobre esta galaxia.")

    # Contenedor para el historial de mensajes
    chat_container = st.container(height=400)
    
    with chat_container:
        # Dibujamos todos los mensajes (ignoramos el de 'system' para no aburrir al usuario)
        for msg in st.session_state.chat_messages:
            if msg["role"] != "system":
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

    # Input del usuario (la barrita para escribir)
    if prompt := st.chat_input("Escribe tu pregunta astronómica aquí..."):
        
        # 1. Mostramos la pregunta del usuario inmediatamente en la UI
        with chat_container:
            with st.chat_message("user"):
                st.markdown(prompt)
        
        # 2. La guardamos en la memoria
        st.session_state.chat_messages.append({"role": "user", "content": prompt})

        # 3. Llamamos al LLM con toda la memoria usando nuestro puente universal
        with chat_container:
            with st.chat_message("assistant"):
                with st.spinner("Analizando datos..."):
                    respuesta = chat_universal(
                        messages=st.session_state.chat_messages,
                        model_name=modelo_elegido
                    )
                    st.markdown(respuesta)
        
        # 4. Guardamos la respuesta en la memoria
        st.session_state.chat_messages.append({"role": "assistant", "content": respuesta})