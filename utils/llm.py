import os
import streamlit as st
from dotenv import load_dotenv
from anthropic import Anthropic
from openai import OpenAI

load_dotenv()  # Carga variables desde .env en local

# ==========================================
# 1. GESTIÓN DE CREDENCIALES
# ==========================================

def get_secret(key_name: str, required: bool = True):
    """Busca una secret primero en .env y luego en st.secrets."""
    value = os.getenv(key_name)
    if value and str(value).strip() != "":
        return str(value).strip()

    try:
        if key_name in st.secrets:
            value = st.secrets[key_name]
            if value and str(value).strip() != "":
                return str(value).strip()
    except Exception:
        pass

    if required:
        raise ValueError(f"No se encontró la secret '{key_name}'.")
    return None


def bootstrap_env():
    """
    Copia secrets a os.environ solo si no existen aún.
    Esto permite que código legado con os.getenv(...) siga funcionando.
    """
    for key in [
        "ANTHROPIC_API_KEY",
        "OPENAI_API_KEY",
        "GEMINI_API_KEY",
        "DEEPSEEK_API_KEY",
    ]:
        value = get_secret(key, required=False)
        if value and os.getenv(key) is None:
            os.environ[key] = value

bootstrap_env()

# ==========================================
# 2. ENDPOINTS Y REGISTRO DE MODELOS
# ==========================================
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1" # Agregamos /v1 por convención de compatibilidad

# Este diccionario es nuestro "Enrutador". Mapea el nombre del modelo a su proveedor.
# Si en el futuro agregas más modelos, solo los anotas aquí.
MODEL_REGISTRY = {
    # OpenAI
    "gpt-5.4": "openai",
    "gpt-5.4-mini": "openai",
    "gpt-5.4-nano": "openai",
    # DeepSeek
    "deepseek-chat": "deepseek",
    "deepseek-reasoner": "deepseek",
    # Gemini
    "gemini-2.5-pro": "gemini",
    "gemini-2.5-flash-image": "gemini",
    "gemini-2.5-flash": "gemini",
    # Anthropic
    "claude-opus-4-6": "anthropic",
    "claude-sonnet-4-6": "anthropic",
    "claude-haiku-4-5": "anthropic",
}


# ==========================================
# 3. INSTANCIACIÓN DE CLIENTES (SINGLETONS)
# ==========================================
# Nota de Mentor: Cambié @lru_cache por @st.cache_resource. 
# En Streamlit, @cache_resource está diseñado específicamente para conexiones a bases 
# de datos y clientes de APIs, evitando fugas de memoria entre recargas de la app.

@st.cache_resource
def get_anthropic_client():
    return Anthropic(api_key=get_secret("ANTHROPIC_API_KEY"))

@st.cache_resource
def get_openai_client():
    return OpenAI(api_key=get_secret("OPENAI_API_KEY"))

@st.cache_resource
def get_deepseek_client():
    return OpenAI(
        api_key=get_secret("DEEPSEEK_API_KEY"),
        base_url=DEEPSEEK_BASE_URL
    )

@st.cache_resource
def get_gemini_client():
    return OpenAI(
        api_key=get_secret("GEMINI_API_KEY"),
        base_url=GEMINI_BASE_URL
    )


# ==========================================
# 4. FUNCIÓN CORE: GENERADOR UNIVERSAL
# ==========================================
def generate_text_universal(prompt: str, model_name: str) -> str:
    """
    Función puente. Recibe el prompt y el modelo, deduce el proveedor,
    hace la llamada a la API correcta y estandariza la respuesta.
    """
    if model_name not in MODEL_REGISTRY:
        raise ValueError(f"El modelo '{model_name}' no está registrado en MODEL_REGISTRY.")
    
    provider = MODEL_REGISTRY[model_name]
    
    try:
        if provider == "anthropic":
            client = get_anthropic_client()
            response = client.messages.create(
                model=model_name,
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
            
        else:
            # Seleccionamos el cliente correcto
            if provider == "openai":
                client = get_openai_client()
            elif provider == "deepseek":
                client = get_deepseek_client()
            elif provider == "gemini":
                client = get_gemini_client()
            
            # Preparamos los argumentos base (comunes para todos)
            api_kwargs = {
                "model": model_name,
                "messages": [{"role": "user", "content": prompt}]
            }
            
            # Ajuste dinámico de parámetros según la evolución de la API
            if provider == "openai":
                # OpenAI ahora exige este parámetro para sus modelos más recientes
                api_kwargs["max_completion_tokens"] = 500
            else:
                # DeepSeek y Gemini (en su capa de compatibilidad) siguen usando el clásico
                api_kwargs["max_tokens"] = 500
                
            # Desempaquetamos el diccionario con **api_kwargs
            response = client.chat.completions.create(**api_kwargs)
            return response.choices[0].message.content

    except Exception as e:
        # Programación defensiva: Si un proveedor falla, que no colapse la app.
        st.error(f"Error de comunicación con {provider} ({model_name}): {str(e)}")
        return "No se pudo generar la explicación debido a un error de conexión."


# ==========================================
# 5. FUNCIONES DE NEGOCIO (UI)
# ==========================================
CLASS_DESCRIPTIONS = {
    "elliptical": "galaxia elíptica — forma esferoidal suave sin estructura de disco ni brazos espirales",
    "spiral": "galaxia espiral — disco con brazos espirales claramente definidos",
    "edge_on": "galaxia de disco vista de canto — el plano del disco apunta hacia el observador",
    "merger": "galaxia en fusión — interacción gravitacional entre dos o más galaxias"
}

def get_galaxy_explanation(galaxy_name: str,
                           predicted_class: str,
                           probabilities: dict,
                           model_name: str, # <-- Nuevo parámetro
                           knowledge_level: str = "eneral") -> str:
    
    probs_str = "\n".join([
        f"  - {cls}: {prob*100:.1f}%"
        for cls, prob in sorted(probabilities.items(), key=lambda x: -x[1])
    ])

    nivel_instruccion = {
        "General": "Explica de forma accesible para alguien sin conocimientos de astronomía.",
        "Estudiante": "Explica para un estudiante universitario de ciencias.",
        "Experto": "Explica con terminología técnica de astrofísica."
    }[knowledge_level]

    prompt = f"""Se clasificó la galaxia '{galaxy_name}' usando un modelo de visión por computadora entrenado en Galaxy Zoo 2.
Resultado de la clasificación:
- Clase predicha: {predicted_class} ({CLASS_DESCRIPTIONS.get(predicted_class, '')})
- Probabilidades por clase:
{probs_str}

{nivel_instruccion}

Por favor explica en español:
1. Qué significa morfológicamente que esta galaxia sea clasificada como '{predicted_class}'
2. Qué características visuales llevaron probablemente a esta clasificación
3. Qué nos dice esta morfología sobre la historia y evolución de la galaxia
4. Por qué el modelo asignó esa probabilidad a la segunda clase más probable

Sé conciso — máximo 250 palabras. No uses markdown ni bullet points, solo párrafos."""

    # Llamamos al enrutador universal
    return generate_text_universal(prompt, model_name)


def get_gallery_description(galaxy_data: dict, model_name: str) -> str:
    prompt = f"""Genera una descripción narrativa en español para la siguiente galaxia:
Nombre: {galaxy_data['name']} ({galaxy_data.get('designation', '')})
Tipo morfológico: {galaxy_data.get('class', '')}
Distancia: {galaxy_data.get('distance_ly', '')} años luz
Constelación: {galaxy_data.get('constellation', '')}
Descripción base: {galaxy_data.get('description', '')}

Escribe 3 párrafos cortos y atractivos que:
1. Describan la apariencia visual y características morfológicas
2. Expliquen qué hace única o interesante a esta galaxia
3. Den contexto sobre su importancia en la astronomía moderna

Tono: divulgativo y apasionante. Máximo 200 palabras. Sin markdown."""

    # Llamamos al enrutador universal
    return generate_text_universal(prompt, model_name)