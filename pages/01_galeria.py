import streamlit as st
import json
from PIL import Image
import numpy as np
import requests
from io import BytesIO
import random
import os

from utils.llm import get_galaxy_explanation, MODEL_REGISTRY, chat_universal
from utils.model_loader import load_model_and_metadata, predict_galaxy
from utils.prompt_engineering import stronger_prompt

st.set_page_config(page_title="Galería — Sideral", layout="wide")

# ==========================================
# 0. EXTRACCIÓN Y LIMPIEZA DE DATOS (ETL) APOD
# ==========================================
@st.cache_data(ttl=300, show_spinner=False) 
def fetch_curated_apod(category="galaxy", count=6):
    """
    Descarga un lote grande de APODs y aplica filtros semánticos estrictos
    para asegurar imágenes 100% espaciales y del tema correcto.
    """
    nasa_key = os.getenv("NASA_API_KEY", "DEMO_KEY")
    # Pedimos 50 imágenes de golpe para tener suficiente margen de filtrado
    url = f"https://api.nasa.gov/planetary/apod?api_key={nasa_key}&count=50"
    
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            data = response.json()
            valid_items = []
            
            for item in data:
                # 1. Filtro base: Solo imágenes (nada de videos de YouTube)
                if item.get("media_type") != "image":
                    continue
                    
                title = item.get("title", "").lower()
                desc = item.get("explanation", "").lower()
                text_corpus = title + " " + desc
                
                # 2. Blacklist (Evitamos Tierra, arte, virus o paisajes)
                blacklist = ["artist", "illustration", "concept", "coronavirus", "virus", 
                             "landscape", "skyline", "earth from", "aurora", "comet", "meteor", "eclipse"]
                if any(bad in text_corpus for bad in blacklist):
                    continue
                
                # 3. Whitelist por categoría
                if category == "galaxy":
                    # Solo galaxias
                    if "galaxy" in title or "andromeda" in title or "sombrero" in title or "galaxies" in desc:
                        valid_items.append(item)
                else:
                    # Fenómenos (Nebulosas, Supernovas, etc.), excluyendo galaxias para no repetir
                    whitelist = ["nebula", "supernova", "pulsar", "quasar", "black hole", "cluster", "dust", "remnant"]
                    if any(good in title for good in whitelist) and "galaxy" not in title:
                        valid_items.append(item)
                        
                # Si ya llenamos el cupo que queríamos, nos detenemos
                if len(valid_items) >= count:
                    break
                    
            return valid_items
    except Exception as e:
        st.error(f"Error conectando con APOD: {e}")
    return []

def load_image_from_url(url):
    try:
        response = requests.get(url, timeout=5)
        img = Image.open(BytesIO(response.content)).convert("RGB")
        return img, np.array(img)
    except:
        return None, None

# ==========================================
# 1. ESTADO DE LA SESIÓN
# ==========================================
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []
if "active_chat_item" not in st.session_state:
    st.session_state.active_chat_item = None

# ==========================================
# 2. CONFIGURACIÓN GLOBAL EN SIDEBAR
# ==========================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3254/3254054.png", width=50)
    st.markdown("### Configuración de IA")
    modelo_elegido = st.selectbox("🧠 Modelo de Lenguaje (LLM):", options=list(MODEL_REGISTRY.keys()), index=0)
    
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
st.markdown("Imágenes de altísima calidad obtenidas de curaciones manuales (Sideral) y astronómicas profesionales (NASA APOD).")

tab_galaxias, tab_nasa = st.tabs(["🔭 Galaxias (Clasificador CNN)", "🚀 Fenómenos del Universo"])

model, model_metadata = load_model_and_metadata()
CLASE_LABELS = {"elliptical": "🔴 Elíptica", "spiral": "🌀 Espiral", "edge_on": "💫 Edge-on", "merger": "💥 Merger"}

# ------------------------------------------
# PESTAÑA 1: GALAXIAS
# ------------------------------------------
with tab_galaxias:
    origen_datos = st.radio("Fuente de datos de Galaxias:", ["Datos Curados Sideral (Alta Precisión)", "Streaming de Galaxias NASA APOD"], horizontal=True)
    
    if "Sideral" in origen_datos:
        with open("data/gallery_metadata.json") as f:
            galaxias_filtradas = json.load(f)["galaxies"]
        
        cols = st.columns(3)
        for i, galaxy in enumerate(galaxias_filtradas):
            with cols[i % 3]:
                img = Image.open(f"data/images/{galaxy['image_file']}")
                st.image(img, width='stretch')
                st.markdown(f"**{galaxy['name']}**")
                
                with st.expander("Ver análisis de Red Neuronal"):
                    img_array = np.array(img.convert("RGB"))
                    predicted_class, probabilities = predict_galaxy(model, model_metadata, img_array)
                    
                    st.markdown("**Clasificación CNN:**")
                    for cls, prob in sorted(probabilities.items(), key=lambda x: -x[1]):
                        st.progress(prob, text=f"{cls}: {prob*100:.1f}%")

                    if st.button("💬 Analizar galaxia con IA", key=f"btn_loc_{galaxy['name']}"):
                        st.session_state.active_chat_item = f"Galaxia: {galaxy['name']}"
                        ctx = f"[CONTEXTO]\nEl usuario ve: {galaxy['name']}. Clase real: {galaxy['class']}. Predicción CNN: {predicted_class}."
                        st.session_state.chat_messages = [{"role": "system", "content": ctx + "\n\n" + stronger_prompt}]
                        st.rerun()

    else:
        st.info("💡 Descargando fotos espectaculares de galaxias curadas por astrónomos de la NASA.")
        if st.button("🔄 Cargar otras galaxias de APOD"):
            fetch_curated_apod.clear()
            
        with st.spinner("Procesando datos del espacio profundo..."):
            nasa_galaxies = fetch_curated_apod(category="galaxy", count=6)
            
        if nasa_galaxies:
            cols = st.columns(3)
            for i, item in enumerate(nasa_galaxies):
                with cols[i % 3]:
                    st.image(item["url"], width='stretch')
                    st.markdown(f"**{item['title']}**")
                    
                    with st.expander("Inferencia CNN en Tiempo Real"):
                        img_pil, img_array = load_image_from_url(item["url"])
                        
                        if img_array is not None:
                            predicted_class, probabilities = predict_galaxy(model, model_metadata, img_array)
                            
                            st.markdown("**Distribución Softmax:**")
                            for cls, prob in sorted(probabilities.items(), key=lambda x: -x[1]):
                                st.progress(prob, text=f"{CLASE_LABELS.get(cls, cls)}: {prob*100:.1f}%")
                                
                            if max(probabilities.values()) < 0.5:
                                st.warning("Entropía alta. Posible imagen Out-Of-Distribution.")

                            if st.button("💬 Interrogar a la IA", key=f"btn_dyn_{i}"):
                                st.session_state.active_chat_item = f"NASA Galaxia: {item['title']}"
                                ctx = f"[CONTEXTO]\nEl usuario ve la galaxia: {item['title']}. Explicación: {item['explanation']}. Predicción CNN: {predicted_class}."
                                st.session_state.chat_messages = [{"role": "system", "content": ctx + "\n\n" + stronger_prompt}]
                                st.rerun()
                        else:
                            st.error("Error procesando imagen.")
        else:
            st.warning("No se encontraron galaxias en este lote. Intenta recargar.")

# ------------------------------------------
# PESTAÑA 2: EXPLORACIÓN FENÓMENOS (Nebulosas, Cúmulos, etc.)
# ------------------------------------------
with tab_nasa:
    st.markdown("### Maravillas del Cosmos")
    st.markdown("Descubre nebulosas, remanentes de supernovas y regiones de formación estelar, curadas por la APOD.")
    
    if st.button("🔄 Buscar nuevos fenómenos"):
        fetch_curated_apod.clear()
        
    with st.spinner("Filtrando fenómenos astronómicos impactantes..."):
        nasa_items = fetch_curated_apod(category="phenomenon", count=6)
    
    if nasa_items:
        cols_nasa = st.columns(3)
        for i, item in enumerate(nasa_items):
            with cols_nasa[i % 3]:
                st.image(item['url'], width='stretch')
                st.markdown(f"**{item['title']}**")
                
                with st.expander("Información e Interacción"):
                    st.info("ℹ️ Imagen general del universo. El análisis morfológico CNN no aplica aquí.")
                    if st.button("💬 Explorar imagen con IA", key=f"btn_nasa_{i}"):
                        st.session_state.active_chat_item = f"NASA Cosmos: {item['title']}"
                        ctx = f"[CONTEXTO]\nEl usuario ve: {item['title']}. Explicación oficial: {item['explanation']}. NO usar clasificación."
                        st.session_state.chat_messages = [{"role": "system", "content": ctx + "\n\n" + stronger_prompt}]
                        st.rerun()
    else:
        st.warning("No se encontraron fenómenos en este lote. Intenta recargar.")

st.divider()

# ==========================================
# 4. INTERFAZ DE CHAT UNIFICADA
# ==========================================
if st.session_state.active_chat_item:
    st.markdown(f"### 💬 Panel de Discusión: {st.session_state.active_chat_item}")
    chat_container = st.container(height=400)
    
    with chat_container:
        if len(st.session_state.chat_messages) == 1:
            with st.spinner("La IA está preparando su introducción astronómica..."):
                if "Cosmos" in st.session_state.active_chat_item:
                    primer_msg = "Hola. Explícame qué fenómeno asombroso se ve en esta imagen basándote en su explicación oficial, aplicando tus reglas de estilo."
                else:
                    primer_msg = "Hola. Preséntame brevemente esta galaxia y si la CNN tuvo problemas clasificándola, aplicando tus reglas de estilo."
                    
                saludo = chat_universal(st.session_state.chat_messages + [{"role": "user", "content": primer_msg}], modelo_elegido)
                st.session_state.chat_messages.append({"role": "assistant", "content": saludo})
                st.rerun()

        for msg in st.session_state.chat_messages:
            if msg["role"] != "system":
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

    if prompt := st.chat_input("Escribe tu duda sobre el universo aquí..."):
        with chat_container:
            with st.chat_message("user"): st.markdown(prompt)
        st.session_state.chat_messages.append({"role": "user", "content": prompt})

        with chat_container:
            with st.chat_message("assistant"):
                with st.spinner(f"Analizando con {modelo_elegido}..."):
                    respuesta = chat_universal(st.session_state.chat_messages, modelo_elegido)
                    st.markdown(respuesta)
        st.session_state.chat_messages.append({"role": "assistant", "content": respuesta})