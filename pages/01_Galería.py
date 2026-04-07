import streamlit as st
import json
from PIL import Image
import numpy as np
import requests
from io import BytesIO
import random
import os

from utils.llm import MODEL_REGISTRY, chat_universal, generate_text_universal
from utils.model_loader import load_model_and_metadata, predict_galaxy
from utils.prompt_engineering import stronger_prompt

st.set_page_config(page_title="Galería — Sideral", layout="wide")

# ==========================================
# 0. INYECCIÓN DE CSS (HACER PESTAÑAS MÁS GRANDES)
# ==========================================
st.markdown("""
<style>
    /* Hacemos que las pestañas (Tabs) de Streamlit sean mucho más grandes */
    button[data-baseweb="tab"] {
        font-size: 1.3rem !important; /* Texto más grande */
        font-weight: 600 !important; /* Texto en negrita */
        padding-top: 1rem !important; /* Más espacio arriba */
        padding-bottom: 1rem !important; /* Más espacio abajo */
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 0.1 EXTRACCIÓN Y LIMPIEZA DE DATOS (APOD)
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
# 0.2 TRADUCTOR INTELIGENTE
# ==========================================
@st.cache_data(ttl=3600, show_spinner=False)
def traducir_titulo_con_ia(titulo_ingles: str) -> str:
    """Usa el LLM para traducir dinámicamente los títulos de la NASA al español."""
    try:
        # Usamos generate_text_universal para un solo disparo rápido (One-Shot)
        # Importamos la función correcta
        from utils.llm import generate_text_universal
        
        prompt_traduccion = f"Traduce este título astronómico de la NASA al español de forma natural y sin comillas. Solo dame el título traducido, nada más: {titulo_ingles}"
        
        # Usamos un modelo rápido (en este caso el que tengas por defecto)
        titulo_espanol = generate_text_universal(prompt=prompt_traduccion, model_name=MODELO_FIJO)
        return titulo_espanol.strip()
    except:
        return titulo_ingles # Si la IA falla, devolvemos el original para que no crashee
# ==========================================
# 1. ESTADO DE LA SESIÓN
# ==========================================
if "chat_messages" not in st.session_state: st.session_state.chat_messages = []
if "active_chat_item" not in st.session_state: st.session_state.active_chat_item = None
if "focus_data" not in st.session_state: st.session_state.focus_data = None

MODELO_FIJO = "claude-opus-4-6"

# ==========================================
# 2. CONFIGURACIÓN GLOBAL EN SIDEBAR
# ==========================================
with st.sidebar:
    st.image("logo.png", use_container_width=True)
    
    if st.button("🗑️ Limpiar historial de análisis"):
        st.session_state.clf_chat_messages = []
        st.session_state.chat_active = False
        st.rerun()

    st.markdown("---")
    st.markdown("Sideral © 2026")

# ==========================================
# 3. INTERFAZ PRINCIPAL (CUADRÍCULA)
# ==========================================
if st.session_state.focus_data is None:

    st.title("🌌 Galería del Universo")
    
    # NUEVO: TEXTO GUÍA GENERAL PARA EL USUARIO
    st.markdown("""
    **Explora las fascinantes imágenes de galaxias**, donde puedes descubrir y estudiar su forma, o bien, 
    **sumérgete en otros impactantes fenómenos del universo**. En todo momento estarás acompañado de **Sideral**, 
    tu asistente inteligente, listo para responder todas tus dudas.
    """)

    tab_galaxias, tab_nasa = st.tabs(["🔭 Clasificación de Galaxias", "🚀 Fenómenos del Universo"])

    model, model_metadata = load_model_and_metadata()
    CLASE_LABELS = {"elliptical": "🔴 Elíptica", "spiral": "🌀 Espiral", "edge_on": "💫 Disco de Canto", "merger": "💥 Galaxias en Fusión"}

    # ------------------------------------------
    # PESTAÑA 1: GALAXIAS
    # ------------------------------------------
    with tab_galaxias:
        # NUEVO: Explicación amigable del modelo y las probabilidades
        st.info("💡 **¿Cómo funciona nuestro observatorio?** Nuestra lente inteligente analiza la estructura de cada galaxia y nos da un *nivel de certeza visual* en porcentajes. Es decir, nos cuenta qué tan segura está de su forma. ¡Entra a cualquier galaxia y pregúntale a Sideral el porqué de estos resultados!")
        
        st.write("")

        if "fuente_galaxias" not in st.session_state:
            st.session_state.fuente_galaxias = "Sideral"

        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            if st.button("🌌 Nuestro Archivo (Galaxias Clásicas)", use_container_width=True, type="primary" if st.session_state.fuente_galaxias == "Sideral" else "secondary"):
                st.session_state.fuente_galaxias = "Sideral"
                st.rerun()
                
        with col_btn2:
            if st.button("🛰️ Conexión NASA (Imágenes en vivo)", use_container_width=True, type="primary" if st.session_state.fuente_galaxias == "NASA" else "secondary"):
                st.session_state.fuente_galaxias = "NASA"
                st.rerun()

        st.write("") 

        # --- LÓGICA DE DIBUJADO DE GALAXIAS SIDERAL ---
        if st.session_state.fuente_galaxias == "Sideral":
            with open("data/gallery_metadata.json") as f:
                galaxias_filtradas = json.load(f)["galaxies"]

            cols = st.columns(3)
            for i, galaxy in enumerate(galaxias_filtradas):
                with cols[i % 3]:
                    img = Image.open(f"data/images/{galaxy['image_file']}")
                    st.image(img, use_container_width=True)
                    st.markdown(f"**{galaxy['name']}**")
                    
                    if st.button("🔍 Analizar y Explorar", key=f"btn_loc_{galaxy['name']}"):
                        img_array = np.array(img.convert("RGB"))
                        predicted_class, probabilities = predict_galaxy(model, model_metadata, img_array)
                        
                        st.session_state.focus_data = {
                            "image_src": img, 
                            "title": galaxy['name'],
                            "predicted_class": predicted_class,
                            "probabilities": probabilities,
                            "is_nasa": False
                        }
                        st.session_state.active_chat_item = f"Galaxia: {galaxy['name']}"
                        ctx = f"[CONTEXTO]\nEl usuario ve: {galaxy['name']}. Clase real: {galaxy['class']}. Predicción visual: {predicted_class}."
                        st.session_state.chat_messages = [{"role": "system", "content": ctx + "\n\n" + stronger_prompt}]
                        st.rerun()

        # --- LÓGICA DE DIBUJADO DE GALAXIAS NASA ---
        else: 
            st.info("💡 Conectando con los archivos de la NASA... Buscando las fotografías de galaxias más espectaculares del día.")
            
            if st.button("🔄 Buscar otras galaxias en el archivo"):
                fetch_curated_apod.clear()
            
            with st.spinner("Descargando fotos de APOD..."):
                nasa_galaxies = fetch_curated_apod(category="galaxy", count=6)
                
            if nasa_galaxies:
                cols = st.columns(3)
                for i, item in enumerate(nasa_galaxies):
                    with cols[i % 3]:
                        st.image(item["url"], use_container_width=True)
                        
                        # TRADUCCIÓN DEL TÍTULO EN VIVO
                        titulo_espanol = traducir_titulo_con_ia(item['title'])
                        st.markdown(f"**{titulo_espanol}**")
                        
                        if st.button("🔍 Analizar y Explorar", key=f"btn_dyn_{i}"):
                            img_pil, img_array = load_image_from_url(item["url"])
                            if img_array is not None:
                                predicted_class, probabilities = predict_galaxy(model, model_metadata, img_array)
                                st.session_state.focus_data = {
                                    "image_src": item["url"],
                                    "title": titulo_espanol, # Pasamos el título en español al modo enfoque
                                    "predicted_class": predicted_class,
                                    "probabilities": probabilities,
                                    "is_nasa": True
                                }
                                st.session_state.active_chat_item = f"NASA Galaxia: {titulo_espanol}"
                                ctx = f"[CONTEXTO]\nEl usuario ve la galaxia: {titulo_espanol}. Explicación de la NASA: {item['explanation']}. Predicción visual: {predicted_class}."
                                st.session_state.chat_messages = [{"role": "system", "content": ctx + "\n\n" + stronger_prompt}]
                                st.rerun()

    ## ------------------------------------------
    # PESTAÑA 2: FENÓMENOS DEL UNIVERSO
    # ------------------------------------------
    with tab_nasa:
        st.info("💡 **Exploración Libre:** A diferencia de las galaxias, estos fenómenos (nebulosas, supernovas, etc.) tienen formas caóticas. Nuestro sistema de análisis de formas está descansando aquí, pero Sideral ha estudiado los archivos de la NASA para contarte la asombrosa historia detrás de cada imagen.")
        
        st.write("")

        if st.button("🔄 Buscar nuevos fenómenos"): fetch_curated_apod.clear()
        with st.spinner("Filtrando el cosmos..."):
            nasa_items = fetch_curated_apod(category="phenomenon", count=6)
        if nasa_items:
            cols_nasa = st.columns(3)
            for i, item in enumerate(nasa_items):
                with cols_nasa[i % 3]:
                    st.image(item['url'], use_container_width=True)
                    
                    # TRADUCCIÓN DEL TÍTULO EN VIVO
                    titulo_espanol = traducir_titulo_con_ia(item['title'])
                    st.markdown(f"**{titulo_espanol}**")
                    
                    if st.button("💬 Explorar fenómeno", key=f"btn_nasa_{i}"):
                        st.session_state.focus_data = {
                            "image_src": item["url"],
                            "title": titulo_espanol, # Pasamos el título en español al modo enfoque
                            "predicted_class": None, 
                            "probabilities": None,
                            "is_nasa": True
                        }
                        st.session_state.active_chat_item = f"NASA Cosmos: {titulo_espanol}"
                        ctx = f"[CONTEXTO]\nEl usuario ve: {titulo_espanol}. Explicación oficial: {item['explanation']}. NO usar clasificación de formas."
                        st.session_state.chat_messages = [{"role": "system", "content": ctx + "\n\n" + stronger_prompt}]
                        st.rerun()

# ==========================================
# 4. VISTA DE ENFOQUE (MODO DETALLE + CHAT)
# ==========================================
else:
    if st.button("⬅️ Volver a la Galería"):
        st.session_state.focus_data = None
        st.session_state.active_chat_item = None
        st.session_state.chat_messages = []
        st.rerun()

    st.divider()
    
    c1, c2, c3 = st.columns([1, 2, 1])
    
    with c2:
        st.markdown(f"<h2 style='text-align: center;'>{st.session_state.focus_data['title']}</h2>", unsafe_allow_html=True)
        st.image(st.session_state.focus_data["image_src"], use_container_width=True)
        
        # Modo Divulgativo para la Red Neuronal (Sin jerga técnica)
        if st.session_state.focus_data["probabilities"] is not None:
            CLASE_LABELS = {"elliptical": "🔴 Elíptica", "spiral": "🌀 Espiral", "edge_on": "💫 Disco de canto", "merger": "💥 Galaxias en Fusión"}
            st.markdown("**🔍 Nuestro análisis visual sugiere:**")
            for cls, prob in sorted(st.session_state.focus_data["probabilities"].items(), key=lambda x: -x[1]):
                st.progress(prob, text=f"{CLASE_LABELS.get(cls, cls)}: {prob*100:.1f}%")

    st.divider()
    
    col_chat1, col_chat2, col_chat3 = st.columns([1, 10, 1])
    with col_chat2:
        st.markdown(f"### 💬 Conversación sobre: {st.session_state.focus_data['title']}")
        chat_container = st.container(height=500)
        
        with chat_container:
            if len(st.session_state.chat_messages) == 1:
                with st.spinner("Preparando tu guía astronómica personal..."):
                    if st.session_state.focus_data["probabilities"] is None:
                        primer_msg = "Hola. Explícame qué fenómeno asombroso se ve en esta imagen de forma muy accesible, emocionante y sin tecnicismos, aplicando tus reglas de estilo."
                    else:
                        primer_msg = "Hola. Preséntame esta galaxia de forma divulgativa. Háblame de nuestro análisis de forma (las probabilidades de que sea espiral, elíptica, etc.) y qué significa eso visualmente, pero explícalo como un guía de museo, SIN usar términos de programación o IA."
                        
                    saludo = chat_universal(
                        st.session_state.chat_messages + [{"role": "user", "content": primer_msg}], 
                        MODELO_FIJO
                    )
                    st.session_state.chat_messages.append({"role": "assistant", "content": saludo})
                    st.rerun()

            for msg in st.session_state.chat_messages:
                if msg["role"] != "system":
                    with st.chat_message(msg["role"]):
                        st.markdown(msg["content"])

        if prompt := st.chat_input("Pregúntale a Sideral sobre este rincón del universo..."):
            with chat_container:
                with st.chat_message("user"): 
                    st.markdown(prompt)
            st.session_state.chat_messages.append({"role": "user", "content": prompt})

            with chat_container:
                with st.chat_message("assistant"):
                    with st.spinner("Explorando el cosmos para responderte..."):
                        respuesta = chat_universal(st.session_state.chat_messages, MODELO_FIJO)
                        st.markdown(respuesta)
            st.session_state.chat_messages.append({"role": "assistant", "content": respuesta})