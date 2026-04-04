import streamlit as st
import numpy as np
from PIL import Image

# Importamos la nueva función chat_universal
from utils.model_loader import load_model_and_metadata, predict_galaxy
from utils.llm import MODEL_REGISTRY, chat_universal

st.set_page_config(page_title="Clasificador — Sideral", layout="wide")

# ==========================================
# 1. ESTADO DE LA SESIÓN (SESSION STATE)
# ==========================================
# Usamos prefijos 'clf_' para no mezclar la memoria del clasificador con la de la galería
if "clf_chat_messages" not in st.session_state:
    st.session_state.clf_chat_messages = []
if "last_uploaded_file" not in st.session_state:
    st.session_state.last_uploaded_file = None
if "chat_active" not in st.session_state:
    st.session_state.chat_active = False

# ==========================================
# 2. CONFIGURACIÓN GLOBAL EN SIDEBAR
# ==========================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3254/3254054.png", width=50)
    st.markdown("### Configuración de IA")
    modelo_elegido = st.selectbox(
        "🧠 Modelo Conversacional (LLM):",
        options=list(MODEL_REGISTRY.keys()),
        index=0,
        help="Este modelo interpretará los resultados de la red neuronal."
    )
    
    if st.button("🗑️ Limpiar historial de análisis"):
        st.session_state.clf_chat_messages = []
        st.session_state.chat_active = False
        st.rerun()

    st.markdown("---")
    st.markdown("Sideral © 2025")

# ==========================================
# 3. CARGA DE MODELO (CNN)
# ==========================================
model, model_metadata = load_model_and_metadata()

# ==========================================
# 4. INTERFAZ PRINCIPAL Y CLASIFICACIÓN
# ==========================================
st.title("🤖 Clasificador y Analista de Galaxias")
st.markdown("""
Sube una imagen. Nuestra red neuronal (EfficientNet) extraerá las características morfológicas, 
y luego podrás discutir los resultados en tiempo real con nuestra IA analítica.
""")

col_upload, col_result = st.columns([1, 1], gap="large")

with col_upload:
    uploaded = st.file_uploader(
        "Sube tu imagen de galaxia",
        type=["jpg", "jpeg", "png"]
    )

    if uploaded:
        img = Image.open(uploaded).convert("RGB")
        st.image(img, caption="Imagen recibida por el sensor", use_container_width=True)
        
        # LOGICA DE RESETEO INTELIGENTE:
        # Si el usuario subió una imagen diferente a la anterior, borramos el chat.
        if st.session_state.last_uploaded_file != uploaded.name:
            st.session_state.clf_chat_messages = []
            st.session_state.chat_active = False
            st.session_state.last_uploaded_file = uploaded.name

with col_result:
    if uploaded:
        img_array = np.array(img)

        with st.spinner("Procesando tensores en EfficientNet..."):
            predicted_class, probabilities = predict_galaxy(
                model, model_metadata, img_array
            )

        CLASE_LABELS = {
            "elliptical": "🔴 Elíptica",
            "spiral":     "🌀 Espiral",
            "edge_on":    "💫 Edge-on (disco de canto)",
            "merger":     "💥 Merger (galaxias en fusión)"
        }

        st.success(f"### Clasificación Principal: {CLASE_LABELS.get(predicted_class, predicted_class)}")

        st.markdown("**Distribución de Confianza (Softmax):**")
        probs_str = "" # Guardaremos esto para inyectarlo al LLM
        for cls, prob in sorted(probabilities.items(), key=lambda x: -x[1]):
            st.progress(prob, text=f"{CLASE_LABELS.get(cls, cls)}: {prob*100:.1f}%")
            probs_str += f"- {cls}: {prob*100:.1f}%\n"

        max_prob = max(probabilities.values())
        if max_prob < 0.6:
            st.warning("⚠️ Alta entropía detectada: La red neuronal no está muy segura de esta clasificación.")

        st.divider()
        
        # Botón para inicializar el agente conversacional
        if not st.session_state.chat_active:
            if st.button("💬 Iniciar análisis interactivo con IA", use_container_width=True):
                st.session_state.chat_active = True
                
                # INYECCIÓN DEL SYSTEM PROMPT (El "Cerebro" del agente)
                sys_prompt = f"""Eres el Asistente Analítico de 'Sideral'. 
El usuario ha subido una imagen de una galaxia que acaba de ser procesada por nuestro modelo de visión computacional.
Resultados de la Red Neuronal:
- Clase predicha: {predicted_class}
- Distribución de probabilidades:
{probs_str}

Tu objetivo es explicarle al usuario qué significan estos resultados, por qué el modelo pudo haber asignado esas probabilidades (justificando la segunda clase más probable si es necesario), y responder cualquier duda técnica o básica sobre astronomía que el usuario tenga sobre esta imagen."""
                
                st.session_state.clf_chat_messages = [{"role": "system", "content": sys_prompt}]
                st.rerun()

    else:
        st.info("👈 Sube una imagen en el panel izquierdo para comenzar.")

# ==========================================
# 5. INTERFAZ DE CHAT DEL CLASIFICADOR
# ==========================================
if st.session_state.chat_active and uploaded:
    st.markdown("---")
    st.markdown("### 💬 Panel de Discusión Analítica")
    
    chat_container = st.container(height=400)
    
    with chat_container:
        # Si acabamos de iniciar, la IA saluda automáticamente basándose en los resultados
        if len(st.session_state.clf_chat_messages) == 1: # Solo está el system prompt
            with st.spinner("La IA está interpretando los resultados de la red neuronal..."):
                saludo_inicial = chat_universal(
                    messages=st.session_state.clf_chat_messages + [{"role": "user", "content": "Hola. Por favor hazme un resumen inicial de los resultados de clasificación y pregúntame si tengo dudas."}],
                    model_name=modelo_elegido
                )
                st.session_state.clf_chat_messages.append({"role": "assistant", "content": saludo_inicial})
                st.rerun()

        # Renderizar historial de mensajes (ocultando el system prompt)
        for msg in st.session_state.clf_chat_messages:
            if msg["role"] != "system":
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

    # Captura de input del usuario
    if prompt := st.chat_input("Escribe tu pregunta sobre esta clasificación..."):
        
        with chat_container:
            with st.chat_message("user"):
                st.markdown(prompt)
                
        st.session_state.clf_chat_messages.append({"role": "user", "content": prompt})

        with chat_container:
            with st.chat_message("assistant"):
                with st.spinner(f"Analizando con {modelo_elegido}..."):
                    respuesta = chat_universal(
                        messages=st.session_state.clf_chat_messages,
                        model_name=modelo_elegido
                    )
                    st.markdown(respuesta)
                    
        st.session_state.clf_chat_messages.append({"role": "assistant", "content": respuesta})