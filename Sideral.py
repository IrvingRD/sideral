import streamlit as st

# 0. PAGE CONFIGURATION
st.set_page_config(
    page_title="Sideral — Inicio",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 1. CUSTOM STYLES FOR PAGE LINKS
st.markdown("""
<style>
    div[data-testid="stPageLink-NavLink"] {
        background-color: #1E293B;
        border: 1px solid #3B82F6;
        border-radius: 12px;
        transition: all 0.3s ease-in-out;
    }

    div[data-testid="stPageLink-NavLink"] > a {
        padding: 1.5rem !important;
        font-size: 1.3rem !important;
        font-weight: 700 !important;
        justify-content: center !important;
    }

    div[data-testid="stPageLink-NavLink"]:hover {
        background-color: #2563EB !important;
        box-shadow: 0 0 20px rgba(59, 130, 246, 0.4);
        transform: translateY(-3px);
    }
</style>
""", unsafe_allow_html=True)

# 2. MAIN CONTAINER WITH SIDE MARGINS
margen_izq, main_col, margen_der = st.columns([1, 4, 1])

with main_col:
    # 3. HEADER AND CENTERED LOGO
    col_vacia1, col_logo, col_vacia2 = st.columns([2, 5, 2])
    with col_logo:
        # Image must be named "logo.png"
        st.image("logo.png", use_container_width=True)

    st.markdown("<h3 style='text-align: center; color: #A0AEC0; font-weight: 500;'>Tu ventana inteligente al cosmos </h3>", unsafe_allow_html=True)

    st.divider()

    # 4. MAIN VALUE PROPOSITION
    st.markdown("""
    ### Bienvenido a bordo, explorador. 🚀

    El universo está lleno de misterios: desde majestuosas galaxias espirales donde nacen miles de estrellas, hasta colisiones cósmicas que desafían nuestra imaginación. **Sideral** es tu asistente astronómico personal, diseñado para acercarte a las estrellas sin necesidad de ser un científico experto.

    Hemos entrenado a un sistema de Inteligencia Artificial capaz de observar fotografías del espacio profundo y clasificar las galaxias según su forma. Imagina tener a un astrónomo amigable a tu lado: tú le muestras una imagen del universo, y él te cuenta con palabras sencillas y emocionantes la increíble historia que esconden sus estrellas.

    **¿Qué te gustaría hacer hoy?**
    """)

    # 5. NAVIGATION CARDS
    c1, c2 = st.columns(2, gap="large")

    with c1:
        with st.container(border=True):
            st.markdown("<h2 style='text-align: center;'>🌌 Explorar Galería</h2>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; color: #94A3B8; font-size: 1.1rem; height: 100px;'>Navega por nuestra colección de imágenes curadas o descubre <b>fotografías en vivo</b> descargadas directamente desde los archivos de la NASA.</p>", unsafe_allow_html=True)

            st.page_link("pages/01_Galería.py", label="Entrar a la Galería", icon="🚀", use_container_width=True)

    with c2:
        with st.container(border=True):
            st.markdown("<h2 style='text-align: center;'>🌀 Analizar Galaxia</h2>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; color: #94A3B8; font-size: 1.1rem; height: 100px;'>¿Tienes la foto de una galaxia y quieres saber más sobre ella? Súbela y deja que nuestra lente inteligente descubra sus secretos en tiempo real.</p>", unsafe_allow_html=True)

            st.page_link("pages/02_Clasificador.py", label="Abrir Observatorio", icon="🔭", use_container_width=True)

    # 6. FOOTER
    st.divider()
    st.markdown("<p style='text-align: center; color: gray; font-size: 0.9rem;'>Sideral © 2026 | Desarrollado para conectar a la humanidad con el universo.</p>", unsafe_allow_html=True)