import streamlit as st
import numpy as np
from PIL import Image

from utils.model_loader import load_model_and_metadata, predict_galaxy
from utils.llm import chat_universal

st.set_page_config(page_title="Clasificador — Sideral", layout="wide")

# ==========================================
# 1. ESTADO DE LA SESIÓN
# ==========================================
if "clf_chat_messages" not in st.session_state: st.session_state.clf_chat_messages = []
if "last_uploaded_file" not in st.session_state: st.session_state.last_uploaded_file = None
if "chat_active" not in st.session_state: st.session_state.chat_active = False

MODELO_FIJO = "claude-opus-4-6"

# ==========================================
# 2. CONFIGURACIÓN GLOBAL EN SIDEBAR
# ==========================================

with st.sidebar:
    # Usamos tu nueva imagen local y dejamos que se ajuste al ancho del sidebar
    st.image("logo.png", use_container_width=True)
    
    st.markdown("### Configuración del Sistema")
    st.info(f"🧠 Motor Analítico Activo:\n**{MODELO_FIJO.upper()}**")
    
    if st.button("🗑️ Limpiar historial de análisis"):
        st.session_state.clf_chat_messages = []
        st.session_state.chat_active = False
        st.rerun()

    st.markdown("---")
    st.markdown("Sideral © 2026")

model, model_metadata = load_model_and_metadata()

# ==========================================
# 3. INTERFAZ PRINCIPAL CENTRADA
# ==========================================
st.title("🤖 Clasificador de Galaxias")
st.markdown("Sube una imagen. Nuestra Red Neuronal (EfficientNet) extraerá las características, y luego podrás discutir los resultados con la IA.")

uploaded = st.file_uploader("Sube tu imagen (JPG, PNG)", type=["jpg", "jpeg", "png"])

if uploaded:
    if st.session_state.last_uploaded_file != uploaded.name:
        st.session_state.clf_chat_messages = []
        st.session_state.chat_active = False
        st.session_state.last_uploaded_file = uploaded.name

    # CENTRAMOS LA IMAGEN (DISEÑO 1/4 - 2/4 - 1/4)
    st.divider()
    c1, c2, c3 = st.columns([1, 2, 1])
    
    with c2:
        img = Image.open(uploaded).convert("RGB")
        st.image(img, caption="Imagen recibida", use_container_width=True)

        img_array = np.array(img)
        with st.spinner("Procesando tensores..."):
            predicted_class, probabilities = predict_galaxy(model, model_metadata, img_array)

        CLASE_LABELS = {"elliptical": "🔴 Elíptica", "spiral": "🌀 Espiral", "edge_on": "💫 Edge-on", "merger": "💥 Merger"}

        st.success(f"### Clasificación Principal: {CLASE_LABELS.get(predicted_class, predicted_class)}")

        probs_str = ""
        for cls, prob in sorted(probabilities.items(), key=lambda x: -x[1]):
            st.progress(prob, text=f"{CLASE_LABELS.get(cls, cls)}: {prob*100:.1f}%")
            probs_str += f"- {cls}: {prob*100:.1f}%\n"

        if not st.session_state.chat_active:
            if st.button("💬 Iniciar análisis interactivo", use_container_width=True):
                st.session_state.chat_active = True
                from utils.prompt_engineering import stronger_prompt
                sys_prompt = f"[CONTEXTO]\nImagen subida. Clase predicha: {predicted_class}\nProbabilidades:\n{probs_str}\n\n[REGLAS]\n{stronger_prompt}"
                st.session_state.clf_chat_messages = [{"role": "system", "content": sys_prompt}]
                st.rerun()

## ==========================================
# 4. INTERFAZ DE CHAT DEBAJO DE LA IMAGEN
# ==========================================
if st.session_state.chat_active and uploaded:
    st.divider()
    # Ensanchamos la zona de interacción
    col_chat1, col_chat2, col_chat3 = st.columns([1, 10, 1])
    
    with col_chat2:
        st.markdown("### 💬 Panel de Discusión Analítica")
        chat_container = st.container(height=500)
        
        with chat_container:
            if len(st.session_state.clf_chat_messages) == 1:
                with st.spinner("La IA está interpretando los resultados..."):
                    saludo = chat_universal(st.session_state.clf_chat_messages + [{"role": "user", "content": "Hola. Resume estos resultados de la CNN y pregunta si tengo dudas."}], MODELO_FIJO)
                    st.session_state.clf_chat_messages.append({"role": "assistant", "content": saludo})
                    st.rerun()

            for msg in st.session_state.clf_chat_messages:
                if msg["role"] != "system":
                    with st.chat_message(msg["role"]):
                        st.markdown(msg["content"])

        if prompt := st.chat_input("Escribe tu pregunta sobre esta clasificación..."):
            with chat_container:
                with st.chat_message("user"): st.markdown(prompt)
            st.session_state.clf_chat_messages.append({"role": "user", "content": prompt})

            with chat_container:
                with st.chat_message("assistant"):
                    with st.spinner("Analizando..."):
                        respuesta = chat_universal(st.session_state.clf_chat_messages, MODELO_FIJO)
                        st.markdown(respuesta)
            st.session_state.clf_chat_messages.append({"role": "assistant", "content": respuesta})