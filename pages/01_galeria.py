import streamlit as st
import json
from PIL import Image
import numpy as np
import requests # <--- Necesario para llamar a la NASA
import os

from utils.llm import get_galaxy_explanation, MODEL_REGISTRY, chat_universal
from utils.model_loader import load_model_and_metadata, predict_galaxy
from utils.prompt_engineering import stronger_prompt

st.set_page_config(page_title="Galería — Sideral", layout="wide")

# ==========================================
# 0. CONEXIÓN A LA API DE LA NASA
# ==========================================
@st.cache_data(ttl=3600, show_spinner=False) # Cacheamos por 1 hora
def fetch_nasa_images(count=6):
    """Obtiene imágenes aleatorias del universo usando la API APOD de la NASA."""
    nasa_key = os.getenv("NASA_API_KEY", "DEMO_KEY")
    # Filtramos para asegurarnos de que la NASA nos devuelva imágenes (y no videos de YouTube)
    url = f"https://api.nasa.gov/planetary/apod?api_key={nasa_key}&count={count}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            # Devolvemos solo las que son tipo 'image'
            return [item for item in data if item.get('media_type') == 'image']
        return []
    except Exception as e:
        st.error(f"Error conectando con la NASA: {e}")
        return []

# ==========================================
# 1. ESTADO DE LA SESIÓN
# ==========================================
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []
# Cambiamos el nombre de la variable para que sirva tanto para galaxias como para NASA
if "active_chat_item" not in st.session_state:
    st.session_state.active_chat_item = None

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
    
    if st.button("🗑️ Limpiar historial de chat"):
        st.session_state.chat_messages = []
        st.session_state.active_chat_item = None
        st.rerun()

    st.markdown("---")
    st.markdown("Sideral © 2025")

# ==========================================
# 3. INTERFAZ PRINCIPAL (PESTAÑAS)
# ==========================================
st.title("🌌 Galería del Universo")
st.markdown("Explora nuestra clasificación de galaxias o sumérgete en las maravillas del cosmos capturadas por la NASA.")

# CREACIÓN DE PESTAÑAS (TABS)
tab_galaxias, tab_nasa = st.tabs(["🔭 Clasificación de Galaxias (CNN)", "🚀 Archivo NASA (Exploración)"])

# ------------------------------------------
# PESTAÑA 1: GALAXIAS (TU CÓDIGO ORIGINAL)
# ------------------------------------------
with tab_galaxias:
    with open("data/gallery_metadata.json") as f:
        gallery_data = json.load(f)["galaxies"]

    model, model_metadata = load_model_and_metadata()

    CLASE_LABELS = {
        "elliptical": "🔴 Elípticas",
        "spiral":     "🌀 Espirales",
        "edge_on":    "💫 Edge-on",
        "merger":     "💥 Mergers"
    }

    clase_sel = st.radio("Filtrar por tipo morfológico:", options=["todas"] + list(CLASE_LABELS.keys()), 
                         format_func=lambda x: "🔭 Todas" if x == "todas" else CLASE_LABELS[x], horizontal=True)

    galaxias_filtradas = gallery_data if clase_sel == "todas" else [g for g in gallery_data if g["class"] == clase_sel]
    cols = st.columns(3)

    for i, galaxy in enumerate(galaxias_filtradas):
        with cols[i % 3]:
            img = Image.open(f"data/images/{galaxy['image_file']}")
            st.image(img, use_container_width=True)
            st.markdown(f"**{galaxy['name']}** — {galaxy['designation']}")
            st.caption(f"{CLASE_LABELS[galaxy['class']]} · {galaxy['distance_ly']} al")

            with st.expander("Ver análisis de Red Neuronal"):
                img_array = np.array(img.convert("RGB"))
                predicted_class, probabilities = predict_galaxy(model, model_metadata, img_array)

                st.markdown("**Clasificación CNN:**")
                for cls, prob in sorted(probabilities.items(), key=lambda x: -x[1]):
                    st.progress(prob, text=f"{cls}: {prob*100:.1f}%")

                if st.button("💬 Analizar esta galaxia con IA", key=f"btn_chat_gx_{galaxy['name']}"):
                    st.session_state.active_chat_item = f"Galaxia: {galaxy['name']}"
                    
                    contexto_galaxia = f"""[CONTEXTO DE LA INTERFAZ]
El usuario está observando la galaxia '{galaxy['name']}'.
- Tipo morfológico real: {galaxy['class']}
- Distancia: {galaxy['distance_ly']} años luz
- Predicción de nuestra CNN local: {predicted_class}
"""
                    sys_prompt = contexto_galaxia + "\n\n[TUS REGLAS DE COMPORTAMIENTO]\n" + stronger_prompt
                    st.session_state.chat_messages = [{"role": "system", "content": sys_prompt}]
                    st.rerun()

# ------------------------------------------
# PESTAÑA 2: EXPLORACIÓN NASA
# ------------------------------------------
with tab_nasa:
    st.markdown("### Archivo Astronómico de la NASA")
    st.markdown("Descubre maravillas cósmicas aleatorias capturadas por los mejores telescopios de la humanidad.")
    
    # Botón para refrescar y traer nuevas imágenes de la API
    if st.button("🔄 Cargar nuevas imágenes aleatorias"):
        fetch_nasa_images.clear() # Limpiamos el caché temporalmente
    
    # Traemos las imágenes (se ejecuta rápido si está en caché)
    with st.spinner("Conectando con servidores de la NASA..."):
        nasa_items = fetch_nasa_images(count=6)
    
    if nasa_items:
        cols_nasa = st.columns(3)
        for i, item in enumerate(nasa_items):
            with cols_nasa[i % 3]:
                # Mostramos la imagen directo de la URL de la NASA
                st.image(item['url'], use_container_width=True)
                st.markdown(f"**{item['title']}**")
                st.caption(f"📅 Fecha: {item.get('date', 'Desconocida')}")
                
                with st.expander("Información e Interacción"):
                    # Aquí NO pasamos la imagen por la CNN porque la confundiríamos
                    st.info("ℹ️ Imagen obtenida del repositorio global de la NASA. El análisis morfológico de Sideral no aplica aquí.")
                    
                    if st.button("💬 Explorar esta imagen con IA", key=f"btn_chat_nasa_{i}"):
                        st.session_state.active_chat_item = f"NASA: {item['title']}"
                        
                        contexto_nasa = f"""[CONTEXTO DE LA INTERFAZ]
El usuario está observando una imagen astronómica general proveniente de la base de datos APOD de la NASA.
- Título de la imagen: {item['title']}
- Explicación oficial de la NASA: {item.get('explanation', 'Sin explicación disponible.')}

NOTA IMPORTANTE PARA EL ASISTENTE: Esto NO fue analizado por nuestra red neuronal de galaxias. Es una imagen general del universo. Utiliza la explicación oficial de la NASA como base de conocimiento para responder las dudas del usuario.
"""
                        sys_prompt = contexto_nasa + "\n\n[TUS REGLAS DE COMPORTAMIENTO]\n" + stronger_prompt
                        st.session_state.chat_messages = [{"role": "system", "content": sys_prompt}]
                        st.rerun()

st.divider()

# ==========================================
# 4. INTERFAZ DE CHAT (ZONA INFERIOR UNIFICADA)
# ==========================================
if st.session_state.active_chat_item:
    st.markdown(f"### 💬 Panel de Discusión: {st.session_state.active_chat_item}")
    st.caption(f"Asistente Analítico: **{modelo_elegido}**")

    chat_container = st.container(height=400)
    
    with chat_container:
        # Generación Proactiva (Rompehielos)
        if len(st.session_state.chat_messages) == 1:
            with st.spinner("La IA está preparando su introducción astronómica..."):
                # Pregunta dinámica:
                if "NASA" in st.session_state.active_chat_item:
                    primer_mensaje = "Hola. Explícame brevemente qué fenómeno asombroso se ve en esta imagen de la NASA, aplicando tus reglas de estilo y terminando con una pregunta."
                else:
                    primer_mensaje = "Hola. Preséntame brevemente esta galaxia y los resultados de clasificación de la CNN, aplicando tus reglas de estilo."
                    
                saludo_inicial = chat_universal(
                    messages=st.session_state.chat_messages + [{"role": "user", "content": primer_mensaje}],
                    model_name=modelo_elegido
                )
                st.session_state.chat_messages.append({"role": "assistant", "content": saludo_inicial})
                st.rerun()

        for msg in st.session_state.chat_messages:
            if msg["role"] != "system":
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

    if prompt := st.chat_input("Escribe tu duda sobre el universo aquí..."):
        
        with chat_container:
            with st.chat_message("user"):
                st.markdown(prompt)
        
        st.session_state.chat_messages.append({"role": "user", "content": prompt})

        with chat_container:
            with st.chat_message("assistant"):
                with st.spinner(f"Analizando con {modelo_elegido}..."):
                    respuesta = chat_universal(
                        messages=st.session_state.chat_messages,
                        model_name=modelo_elegido
                    )
                    st.markdown(respuesta)
        
        st.session_state.chat_messages.append({"role": "assistant", "content": respuesta})