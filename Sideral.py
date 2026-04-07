import streamlit as st

# Configuración de la página como "Landing Page"
st.set_page_config(
    page_title="Sideral — Inicio", 
    layout="centered", 
    initial_sidebar_state="collapsed" # Ocultamos el menú lateral para mayor inmersión
)

# ==========================================
# 1. CABECERA Y LOGO CENTRADO
# ==========================================
# Dividimos en 3 columnas para forzar el logo al centro
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    # Asegúrate de que tu imagen se llame "logo.jpg" y esté en la misma carpeta que este script
    st.image("logo.jpg", use_container_width=True)

st.markdown("<h1 style='text-align: center; font-size: 3.5rem;'>SIDERAL</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center; color: #A0AEC0; font-weight: 300;'>Tu ventana inteligente al cosmos ✨</h3>", unsafe_allow_html=True)

st.write("") # Espacio en blanco
st.divider()

# ==========================================
# 2. EL "SPEECH" DE NEGOCIO (DIVULGATIVO)
# ==========================================
st.markdown("""
### Bienvenido a bordo, explorador. 🚀

El universo está lleno de misterios: desde majestuosas galaxias espirales donde nacen miles de estrellas, hasta colisiones cósmicas que desafían nuestra imaginación. **Sideral** es tu asistente astronómico personal, diseñado para acercarte a las estrellas sin necesidad de ser un científico experto.

Hemos entrenado a un sistema de Inteligencia Artificial capaz de observar fotografías del espacio profundo y clasificar las galaxias según su forma. Imagina tener a un astrónomo amigable a tu lado: tú le muestras una imagen del universo, y él te cuenta con palabras sencillas y emocionantes la increíble historia que esconden sus estrellas.

**¿Qué te gustaría hacer hoy?**
""")

st.write("")
st.write("")

# ==========================================
# 3. BOTONES DE NAVEGACIÓN (TARJETAS)
# ==========================================
# Usamos columnas para crear dos grandes "tarjetas" de opciones
c1, c2 = st.columns(2, gap="large")

with c1:
    st.success("#### 🌌 Galería y Exploración")
    st.markdown("""
    Navega por nuestra colección de imágenes curadas o descubre **fotografías en vivo** 
    descargadas directamente desde los archivos de la NASA.
    """)
    st.write("")
    # st.page_link crea un botón nativo que te redirige a otro archivo de tu repo
    # Asegúrate de que el nombre coincida exactamente con tu archivo en la carpeta 'pages'
    st.page_link("pages/01_Galería.py", label="Entrar a la Galería", icon="🔭", use_container_width=True)

with c2:
    st.info("#### 🤖 Analizar mi propia Galaxia")
    st.markdown("""
    ¿Tienes la foto de una galaxia y quieres saber más sobre ella? Súbela y deja 
    que nuestra IA descubra todos sus secretos en tiempo real.
    """)
    st.write("")
    # Igual aquí, verifica el nombre exacto del archivo
    st.page_link("pages/02_Clasificador.py", label="Abrir el Clasificador", icon="🛰️", use_container_width=True)

# ==========================================
# 4. PIE DE PÁGINA
# ==========================================
st.write("")
st.write("")
st.divider()
st.markdown("<p style='text-align: center; color: gray; font-size: 0.9rem;'>Sideral © 2026 | Desarrollado para conectar a la humanidad con las estrellas.</p>", unsafe_allow_html=True)