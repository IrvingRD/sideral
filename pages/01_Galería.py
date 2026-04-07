import streamlit as st
import json
from PIL import Image
import numpy as np
import requests
from io import BytesIO
import random
import os

from utils.llm import MODEL_REGISTRY, chat_universal
from utils.model_loader import load_model_and_metadata, predict_galaxy
from utils.prompt_engineering import stronger_prompt

st.set_page_config(page_title="Galería — Sideral", layout="wide")

# ==========================================
# 0. EXTRACCIÓN Y LIMPIEZA DE DATOS (APOD)
# ==========================================
@st.cache_data(ttl=300, show_spinner=False) 
def fetch_curated_apod(category="galaxy", count=6):
    nasa_key = os.getenv("NASA_API_KEY", "DEMO_KEY")
    url = f"https://api.nasa.gov/planetary/apod?api_key={nasa_key}&count=50"
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            data = response.json()
            valid_items = []
            for item in data:
                if item.get("media_type") != "image": continue
                title = item.get("title", "").lower()
                desc = item.get("explanation", "").lower()
                text_corpus = title + " " + desc
                
                blacklist = ["artist", "illustration", "concept", "coronavirus", "virus", "landscape", "skyline", "earth from", "aurora", "comet", "meteor", "eclipse"]
                if any(bad in text_corpus for bad in blacklist): continue
                
                if category == "galaxy":
                    if "galaxy" in title or "andromeda" in title or "sombrero" in title or "galaxies" in desc:
                        valid_items.append(item)
                else:
                    whitelist = ["nebula", "supernova", "pulsar", "quasar", "black hole", "cluster", "dust", "remnant"]
                    if any(good in title for good in whitelist) and "galaxy" not in title:
                        valid_items.append(item)
                if len(valid_items) >= count: break
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
if "chat_messages" not in st.session_state: st.session_state.chat_messages = []
if "active_chat_item" not in st.session_state: st.session_state.active_chat_item = None
# NUEVO: Estado para almacenar la imagen enfocada y ocultar la galería
if "focus_data" not in st.session_state: st.session_state.focus_data = None

# Fijamos el LLM por regla de negocio
MODELO_FIJO = "claude-opus-4-6"

# ==========================================
# 2. CONFIGURACIÓN GLOBAL EN SIDEBAR
# ==========================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3254/3254054.png", width=50)
    st.markdown("### Configuración del Sistema")
    st.info(f"🧠 Motor Analítico Activo:\n**{MODELO_FIJO.upper()}**")
    
    if st.button("🗑️ Limpiar historial de chat"):
        st.session_state.chat_messages = []
        st.session_state.active_chat_item = None
        st.session_state.focus_data = None
        st.rerun()
    st.markdown("---")
    st.markdown("Sideral © 2026")

# ==========================================
# 3. VISTA MAESTRA (SI NO HAY IMAGEN ENFOCADA)
# ==========================================
if st.session_state.focus_data is None:
    st.title("🌌 Galería del Universo")
    st.markdown("Imágenes de altísima calidad obtenidas de curaciones manuales (Sideral) y astronómicas profesionales (NASA APOD).")

    tab_galaxias, tab_nasa = st.tabs(["🔭 Clasificación de Galaxias", "🚀 Fenómenos del Universo"])

    model, model_metadata = load_model_and_metadata()
    CLASE_LABELS = {"elliptical": "🔴 Elíptica", "spiral": "🌀 Espiral", "edge_on": "💫 Edge-on", "merger": "💥 Merger"}

    # --- PESTAÑA GALAXIAS ---
    with tab_galaxias:
        origen_datos = st.radio("Fuente de datos:", ["Datos Curados Sideral (Alta Precisión)", "Streaming NASA APOD"], horizontal=True)
        
        if "Sideral" in origen_datos:
            with open("data/gallery_metadata.json") as f:
                galaxias_filtradas = json.load(f)["galaxies"]
            
            cols = st.columns(3)
            for i, galaxy in enumerate(galaxias_filtradas):
                with cols[i % 3]:
                    img_path = f"data/images/{galaxy['image_file']}"
                    st.image(img_path, use_container_width=True)
                    st.markdown(f"**{galaxy['name']}**")
                    
                    if st.button("🔍 Analizar y Explorar", key=f"btn_loc_{galaxy['name']}"):
                        # Calculamos probabilidades al instante para guardarlas
                        img = Image.open(img_path)
                        img_array = np.array(img.convert("RGB"))
                        predicted_class, probabilities = predict_galaxy(model, model_metadata, img_array)
                        
                        # Guardamos en estado para la vista de enfoque
                        st.session_state.focus_data = {
                            "image_src": img_path,
                            "title": galaxy['name'],
                            "predicted_class": predicted_class,
                            "probabilities": probabilities,
                            "is_nasa": False
                        }
                        st.session_state.active_chat_item = f"Galaxia: {galaxy['name']}"
                        ctx = f"[CONTEXTO]\nEl usuario ve: {galaxy['name']}. Clase real: {galaxy['class']}. Predicción CNN: {predicted_class}."
                        st.session_state.chat_messages = [{"role": "system", "content": ctx + "\n\n" + stronger_prompt}]
                        st.rerun()

        else:
            if st.button("🔄 Cargar otras galaxias"): fetch_curated_apod.clear()
            with st.spinner("Descargando fotos de APOD..."):
                nasa_galaxies = fetch_curated_apod(category="galaxy", count=6)
                
            if nasa_galaxies:
                cols = st.columns(3)
                for i, item in enumerate(nasa_galaxies):
                    with cols[i % 3]:
                        st.image(item["url"], use_container_width=True)
                        st.markdown(f"**{item['title']}**")
                        
                        if st.button("🔍 Analizar y Explorar", key=f"btn_dyn_{i}"):
                            img_pil, img_array = load_image_from_url(item["url"])
                            if img_array is not None:
                                predicted_class, probabilities = predict_galaxy(model, model_metadata, img_array)
                                st.session_state.focus_data = {
                                    "image_src": item["url"],
                                    "title": item['title'],
                                    "predicted_class": predicted_class,
                                    "probabilities": probabilities,
                                    "is_nasa": True
                                }
                                st.session_state.active_chat_item = f"NASA Galaxia: {item['title']}"
                                ctx = f"[CONTEXTO]\nEl usuario ve la galaxia: {item['title']}. Explicación: {item['explanation']}. Predicción CNN: {predicted_class}."
                                st.session_state.chat_messages = [{"role": "system", "content": ctx + "\n\n" + stronger_prompt}]
                                st.rerun()

    # --- PESTAÑA FENÓMENOS ---
    with tab_nasa:
        if st.button("🔄 Buscar nuevos fenómenos"): fetch_curated_apod.clear()
        with st.spinner("Filtrando el cosmos..."):
            nasa_items = fetch_curated_apod(category="phenomenon", count=6)
        if nasa_items:
            cols_nasa = st.columns(3)
            for i, item in enumerate(nasa_items):
                with cols_nasa[i % 3]:
                    st.image(item['url'], use_container_width=True)
                    st.markdown(f"**{item['title']}**")
                    if st.button("💬 Explorar fenómeno", key=f"btn_nasa_{i}"):
                        st.session_state.focus_data = {
                            "image_src": item["url"],
                            "title": item['title'],
                            "predicted_class": None, # No aplica CNN
                            "probabilities": None,
                            "is_nasa": True
                        }
                        st.session_state.active_chat_item = f"NASA Cosmos: {item['title']}"
                        ctx = f"[CONTEXTO]\nEl usuario ve: {item['title']}. Explicación oficial: {item['explanation']}. NO usar clasificación."
                        st.session_state.chat_messages = [{"role": "system", "content": ctx + "\n\n" + stronger_prompt}]
                        st.rerun()

# ==========================================
# 4. VISTA DE ENFOQUE (MODO DETALLE + CHAT)
# ==========================================
else:
    # Botón para regresar a la cuadrícula
    if st.button("⬅️ Volver a la Galería"):
        st.session_state.focus_data = None
        st.session_state.active_chat_item = None
        st.session_state.chat_messages = []
        st.rerun()

    st.divider()
    
    # CENTRAMOS LA IMAGEN Y LOS RESULTADOS (1/4 - 2/4 - 1/4)
    c1, c2, c3 = st.columns([1, 2, 1])
    
    with c2:
        st.markdown(f"<h2 style='text-align: center;'>{st.session_state.focus_data['title']}</h2>", unsafe_allow_html=True)
        st.image(st.session_state.focus_data["image_src"], use_container_width=True)
        
        # Si tiene clasificación CNN, la renderizamos limpia debajo de la foto
        if st.session_state.focus_data["probabilities"] is not None:
            CLASE_LABELS = {"elliptical": "🔴 Elíptica", "spiral": "🌀 Espiral", "edge_on": "💫 Edge-on", "merger": "💥 Merger"}
            st.markdown("**Resultados de la Red Neuronal (CNN):**")
            for cls, prob in sorted(st.session_state.focus_data["probabilities"].items(), key=lambda x: -x[1]):
                st.progress(prob, text=f"{CLASE_LABELS.get(cls, cls)}: {prob*100:.1f}%")
        else:
            st.info("ℹ️ Fenómeno general del universo. Clasificación morfológica deshabilitada.")

    # EL CHAT JUSTO DEBAJO DE LA IMAGEN ENFOCADA
    st.divider()
    st.markdown(f"### 💬 Conversación sobre: {st.session_state.focus_data['title']}")
    
    # Creamos un contenedor más ancho para que sea cómodo chatear
    col_chat1, col_chat2, col_chat3 = st.columns([1, 4, 1])
    with col_chat2:
        chat_container = st.container(height=500)
        
        with chat_container:
            if len(st.session_state.chat_messages) == 1:
                with st.spinner("La IA está preparando su introducción astronómica..."):
                    if st.session_state.focus_data["probabilities"] is None:
                        primer_msg = "Hola. Explícame qué fenómeno asombroso se ve en esta imagen, aplicando tus reglas de estilo."
                    else:
                        primer_msg = "Hola. Preséntame brevemente esta galaxia y los resultados de la CNN, aplicando tus reglas de estilo."
                        
                    saludo = chat_universal(st.session_state.chat_messages + [{"role": "user", "content": primer_msg}], MODELO_FIJO)
                    st.session_state.chat_messages.append({"role": "assistant", "content": saludo})
                    st.rerun()

            for msg in st.session_state.chat_messages:
                if msg["role"] != "system":
                    with st.chat_message(msg["role"]):
                        st.markdown(msg["content"])

        if prompt := st.chat_input("Escribe tu duda astronómica aquí..."):
            with chat_container:
                with st.chat_message("user"): st.markdown(prompt)
            st.session_state.chat_messages.append({"role": "user", "content": prompt})

            with chat_container:
                with st.chat_message("assistant"):
                    with st.spinner("Analizando..."):
                        respuesta = chat_universal(st.session_state.chat_messages, MODELO_FIJO)
                        st.markdown(respuesta)
            st.session_state.chat_messages.append({"role": "assistant", "content": respuesta})