import streamlit as st
import numpy as np
from PIL import Image

from utils.model_loader import load_model_and_metadata, predict_galaxy
from utils.llm import MODEL_REGISTRY, chat_universal, generate_text_universal

st.set_page_config(page_title="Sideral — Observatorio", layout="wide")

# CUSTOM TAB STYLING
st.markdown("""
<style>
    button[data-baseweb="tab"] {
        font-size: 1.3rem !important;
        font-weight: 600 !important;
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
        color: #94A3B8 !important;
    }

    button[data-baseweb="tab"][aria-selected="true"] {
        color: #3B82F6 !important;
        border-bottom-color: #3B82F6 !important;
    }

    button[data-baseweb="tab"]:hover {
        color: #E2E8F0 !important;
    }
</style>
""", unsafe_allow_html=True)

# SESSION STATE
if "clf_chat_messages" not in st.session_state:
    st.session_state.clf_chat_messages = []
if "last_uploaded_file" not in st.session_state:
    st.session_state.last_uploaded_file = None
if "chat_active" not in st.session_state:
    st.session_state.chat_active = False

MODELO_FIJO = "claude-opus-4-6"

# SIDEBAR


with st.sidebar:
    st.image("logo.png", use_container_width=True)
    
    if st.button("🗑️ Limpiar historial de análisis"):
        st.session_state.clf_chat_messages = []
        st.session_state.chat_active = False
        st.rerun()

    st.markdown("---")
    st.markdown("Sideral © 2026")

model, model_metadata = load_model_and_metadata()

# MAIN INTERFACE
st.title("🔭 Observatorio Inteligente")
st.markdown("Sube una imagen del universo. Nuestro sistema visual analizará su forma, y luego podrás platicar con Sideral para descubrir los secretos de tu fotografía.")

uploaded = st.file_uploader("Sube la fotografía de una galaxia. Para un resultado óptimo, usa imágenes de alta resolución y donde la galaxia esté cerca del centro (JPG, PNG).", type=["jpg", "jpeg", "png"])

if uploaded:
    # Reset state on new upload
    if st.session_state.last_uploaded_file != uploaded.name:
        st.session_state.clf_chat_messages = []
        st.session_state.chat_active = False
        st.session_state.last_uploaded_file = uploaded.name

    st.divider()
    c1, c2, c3 = st.columns([1, 2, 1])

    with c2:
        img = Image.open(uploaded).convert("RGB")
        st.image(img, caption="Imagen recibida desde tu dispositivo", use_container_width=True)

        img_array = np.array(img)
        with st.spinner("Nuestra lente inteligente está analizando tu imagen..."):
            predicted_class, probabilities = predict_galaxy(model, model_metadata, img_array)

        CLASE_LABELS = {"elliptical": "🔴 Elíptica", "spiral": "🌀 Espiral", "edge_on": "💫 Disco de Canto", "merger": "💥 Galaxias en Fusión"}

        st.success(f"### Nuestro análisis sugiere: {CLASE_LABELS.get(predicted_class, predicted_class)}")
        st.markdown("**Nivel de certeza visual:**")

        probs_str = ""
        for cls, prob in sorted(probabilities.items(), key=lambda x: -x[1]):
            st.progress(prob, text=f"{CLASE_LABELS.get(cls, cls)}: {prob*100:.1f}%")
            probs_str += f"- {cls}: {prob*100:.1f}%\n"

        if not st.session_state.chat_active:
            if st.button("💬 Platicar con Sideral sobre tu imagen", use_container_width=True):
                st.session_state.chat_active = True
                from utils.prompt_engineering import stronger_prompt
                sys_prompt = f"[CONTEXTO]\nEl usuario ha subido una fotografía. Nuestro sistema visual predice que es: {predicted_class}\nCerteza del sistema:\n{probs_str}\n\n[REGLAS FUNDAMENTALES]\n{stronger_prompt}\nIMPORTANTE: Habla siempre en términos astronómicos o divulgativos. NUNCA menciones palabras como 'CNN', 'Machine Learning', 'Tensores' o 'Red Neuronal'. Si hablas de las probabilidades, refiérete a ellas como 'lo que sugiere nuestra observación visual'."
                st.session_state.clf_chat_messages = [{"role": "system", "content": sys_prompt}]
                st.rerun()

# CHAT INTERFACE
if st.session_state.chat_active and uploaded:
    st.divider()
    col_chat1, col_chat2, col_chat3 = st.columns([1, 10, 1])

    with col_chat2:
        st.markdown("### 💬 Conversación con Sideral")
        chat_container = st.container(height=500)

        with chat_container:
            # Generate initial greeting
            if len(st.session_state.clf_chat_messages) == 1:
                with st.spinner("Sideral está preparando su explicación..."):
                    primer_msg = "Hola. Explícame de forma divulgativa, apasionante y muy accesible qué tipo de galaxia crees que te he mostrado, basándote en el análisis visual. Recuerda no usar términos técnicos de IA."
                    saludo = chat_universal(
                        st.session_state.clf_chat_messages + [{"role": "user", "content": primer_msg}],
                        MODELO_FIJO
                    )
                    st.session_state.clf_chat_messages.append({"role": "assistant", "content": saludo})
                    st.rerun()

            for msg in st.session_state.clf_chat_messages:
                if msg["role"] != "system":
                    with st.chat_message(msg["role"]):
                        st.markdown(msg["content"])

        if prompt := st.chat_input("Escribe aquí tu duda sobre el universo..."):
            with chat_container:
                with st.chat_message("user"):
                    st.markdown(prompt)
            st.session_state.clf_chat_messages.append({"role": "user", "content": prompt})

            with chat_container:
                with st.chat_message("assistant"):
                    with st.spinner("Explorando el cosmos para responderte..."):
                        respuesta = chat_universal(st.session_state.clf_chat_messages, MODELO_FIJO)
                        st.markdown(respuesta)
            st.session_state.clf_chat_messages.append({"role": "assistant", "content": respuesta})