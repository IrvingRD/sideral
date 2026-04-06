import streamlit as st
import json
from PIL import Image
import numpy as np
import requests
from io import BytesIO
import random

from utils.llm import get_galaxy_explanation, MODEL_REGISTRY, chat_universal
from utils.model_loader import load_model_and_metadata, predict_galaxy
from utils.prompt_engineering import stronger_prompt

st.set_page_config(page_title="Galería — Sideral", layout="wide")

# ==========================================
# 0. CONEXIÓN A LA BIBLIOTECA DE LA NASA (NIVL)
# ==========================================
@st.cache_data(ttl=300, show_spinner=False) 
def fetch_nasa_library(query="galaxy", count=6):
    """
    Usa la API de búsqueda de la NASA para traer imágenes específicas.
    No requiere API Key y asegura que el contenido sea estrictamente astronómico.
    """
    url = f"https://images-api.nasa.gov/search?q={query}&media_type=image"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            items = response.json()["collection"]["items"]
            # Tomamos una muestra aleatoria de los primeros 100 resultados para variedad
            valid_items = [item for item in items if "links" in item]
            sample = random.sample(valid_items, min(count, len(valid_items)))
            
            parsed_data = []
            for item in sample:
                parsed_data.append({
                    "title": item["data"][0]["title"],
                    "description": item["data"][0].get("description", "Sin descripción."),
                    # La NASA suele entregar el link 0 como la imagen previsualizable (ideal para evitar OOM)
                    "image_url": item["links"][0]["href"] 
                })
            return parsed_data
    except Exception as e:
        st.error(f"Error conectando con la Biblioteca NASA: {e}")
    return []

# Función matemática auxiliar para procesar URLs a Tensores
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
st.title("🌌 Galería del Universo Dinámica")
st.markdown("Elige entre nuestro set de datos controlado o descarga imágenes en vivo desde los servidores de la NASA para poner a prueba nuestra Red Neuronal.")

tab_galaxias, tab_nasa = st.tabs(["🔭 Galaxias (Clasificador CNN)", "🚀 Fenómenos del Universo (Exploración)"])

model, model_metadata = load_model_and_metadata()
CLASE_LABELS = {"elliptical": "🔴 Elíptica", "spiral": "🌀 Espiral", "edge_on": "💫 Edge-on", "merger": "💥 Merger"}

# ------------------------------------------
# PESTAÑA 1: GALAXIAS (CON TOGGLE LOCAL/NASA)
# ------------------------------------------
with tab_galaxias:
    origen_datos = st.radio("Fuente de datos:", ["Datos Curados Sideral (Alta Precisión)", "Streaming desde la NASA (Inferencia en vivo)"], horizontal=True)
    
    if "Sideral" in origen_datos:
        # Lógica original con JSON local
        with open("data/gallery_metadata.json") as f:
            galaxias_filtradas = json.load(f)["galaxies"]
        
        cols = st.columns(3)
        for i, galaxy in enumerate(galaxias_filtradas):
            with cols[i % 3]:
                img = Image.open(f"data/images/{galaxy['image_file']}")
                st.image(img, width="stretch")
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
        # LÓGICA DINÁMICA: Traemos imágenes de galaxias desde la NASA al vuelo
        st.info("💡 **Aviso Científico:** Las imágenes de la NASA pueden diferir (Data Drift) de las imágenes de entrenamiento (Galaxy Zoo). Observa cómo reacciona la confianza del modelo matemático.")
        if st.button("🔄 Descargar nuevas galaxias de la NASA"):
            fetch_nasa_library.clear()
            
        with st.spinner("Conectando con la API de la NASA..."):
            nasa_galaxies = fetch_nasa_library(query="galaxy", count=6)
            
        cols = st.columns(3)
        for i, item in enumerate(nasa_galaxies):
            with cols[i % 3]:
                st.image(item["image_url"], width="stretch")
                st.markdown(f"**{item['title']}**")
                
                with st.expander("Inferencia CNN en Tiempo Real"):
                    # Descarga y conversión de la imagen on-the-fly
                    img_pil, img_array = load_image_from_url(item["image_url"])
                    
                    if img_array is not None:
                        predicted_class, probabilities = predict_galaxy(model, model_metadata, img_array)
                        
                        st.markdown("**Distribución Softmax:**")
                        for cls, prob in sorted(probabilities.items(), key=lambda x: -x[1]):
                            st.progress(prob, text=f"{CLASE_LABELS.get(cls, cls)}: {prob*100:.1f}%")
                            
                        if max(probabilities.values()) < 0.5:
                            st.warning("Entropía alta. Posible imagen Out-Of-Distribution.")

                        if st.button("💬 Interrogar a la IA", key=f"btn_dyn_{i}"):
                            st.session_state.active_chat_item = f"NASA Galaxia: {item['title']}"
                            ctx = f"[CONTEXTO]\nEl usuario ve una galaxia de la NASA: {item['title']}. Descripción oficial: {item['description']}. Predicción CNN: {predicted_class}."
                            st.session_state.chat_messages = [{"role": "system", "content": ctx + "\n\n" + stronger_prompt}]
                            st.rerun()
                    else:
                        st.error("Error procesando los tensores de esta imagen.")

# ------------------------------------------
# PESTAÑA 2: EXPLORACIÓN NASA GENERAL (Filtro Astronómico Fuerte)
# ------------------------------------------
with tab_nasa:
    st.markdown("### Maravillas del Cosmos")
    st.markdown("Imágenes extraídas de la biblioteca central de la NASA enfocadas en nebulosas, cúmulos estelares y fenómenos exóticos.")
    
    if st.button("🔄 Buscar nuevos fenómenos cósmicos"):
        fetch_nasa_library.clear()
        
    with st.spinner("Rastreando el universo..."):
        # Elegimos un fenómeno astronómico al azar en cada recarga
        import random
        fenomenos = ["nebula", "supernova", "pulsar", "quasar", "black hole", "star cluster", "exoplanet"]
        fenomeno_elegido = random.choice(fenomenos)
        
        # Le pasamos una sola palabra clave limpia a la API
        nasa_items = fetch_nasa_library(query=fenomeno_elegido, count=6)
    
    if nasa_items:
        st.success(f"🔭 Mostrando resultados para la categoría: **{fenomeno_elegido.title()}**")
        cols_nasa = st.columns(3)
        for i, item in enumerate(nasa_items):
            with cols_nasa[i % 3]:
                st.image(item['image_url'], width='stretch')
                st.markdown(f"**{item['title']}**")
                
                with st.expander("Información e Interacción"):
                    st.info("ℹ️ Imagen general del universo. El análisis morfológico CNN no aplica aquí.")
                    if st.button("💬 Explorar imagen con IA", key=f"btn_nasa_{i}_{fenomeno_elegido}"):
                        st.session_state.active_chat_item = f"NASA Cosmos: {item['title']}"
                        ctx = f"[CONTEXTO]\nEl usuario ve: {item['title']}. Explicación oficial: {item['description']}. NO usar clasificación de galaxias."
                        st.session_state.chat_messages = [{"role": "system", "content": ctx + "\n\n" + stronger_prompt}]
                        st.rerun()
    else:
        st.warning(f"No se pudieron recuperar imágenes para '{fenomeno_elegido}'. Intenta buscar de nuevo.")

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
                    primer_msg = "Hola. Explícame qué fenómeno asombroso se ve en esta imagen, aplicando tus reglas de estilo."
                else:
                    primer_msg = "Hola. Preséntame brevemente esta galaxia y si la CNN tuvo problemas clasificándola (alta o baja entropía), aplicando tus reglas de estilo."
                    
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