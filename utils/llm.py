import os
import streamlit as st
from dotenv import load_dotenv
from anthropic import Anthropic
from openai import OpenAI
import utils.prompt_engineering

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
    # "gpt-5.4-nano": "openai",
    # DeepSeek
    "deepseek-chat": "deepseek",
    "deepseek-reasoner": "deepseek",
    # Gemini
    "gemini-2.5-pro": "gemini",
    # "gemini-2.5-flash-image": "gemini",
    "gemini-2.5-flash": "gemini",
    # Anthropic
    "claude-opus-4-6": "anthropic",
    "claude-sonnet-4-6": "anthropic",
    # "claude-haiku-4-5": "anthropic",
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
# 4. FUNCIÓN CORE: GENERADOR UNIVERSAL (ONE-SHOT)
# ==========================================
def generate_text_universal(prompt: str, model_name: str, system_prompt: str = None) -> str:
    """
    Ahora acepta un system_prompt para inyectar reglas duras.
    """
    if model_name not in MODEL_REGISTRY:
        raise ValueError(f"El modelo '{model_name}' no está registrado.")
    
    provider = MODEL_REGISTRY[model_name]
    
    try:
        if provider == "anthropic":
            client = get_anthropic_client()
            kwargs = {
                "model": model_name,
                "max_tokens": 500,
                "messages": [{"role": "user", "content": prompt}]
            }
            if system_prompt:
                kwargs["system"] = system_prompt # Anthropic lo recibe como parámetro separado
                
            response = client.messages.create(**kwargs)
            return response.content[0].text
            
        else:
            if provider == "openai": client = get_openai_client()
            elif provider == "deepseek": client = get_deepseek_client()
            elif provider == "gemini": client = get_gemini_client()
            
            # Construimos la lista de mensajes correctamente
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            api_kwargs = {
                "model": model_name,
                "messages": messages
            }
            
            if provider == "openai":
                api_kwargs["max_completion_tokens"] = 500
            else:
                api_kwargs["max_tokens"] = 500
                
            response = client.chat.completions.create(**api_kwargs)
            return response.choices[0].message.content

    except Exception as e:
        st.error(f"Error de comunicación con {provider} ({model_name}): {str(e)}")
        return "No se pudo generar la explicación debido a un error de conexión."


# ==========================================
# 5. FUNCIONES DE NEGOCIO (UI)
# ==========================================
CLASS_DESCRIPTIONS = {
    "elliptical": "Galaxia elíptica — forma esferoidal suave sin estructura de disco ni brazos espirales",
    "spiral": "Galaxia espiral — disco con brazos espirales claramente definidos",
    "edge_on": "Galaxia de disco vista de canto — el plano del disco apunta hacia el observador",
    "merger": "Galaxia en fusión — interacción gravitacional entre dos o más galaxias"
}

def get_galaxy_explanation(galaxy_name: str,
                           predicted_class: str,
                           probabilities: dict,
                           model_name: str,
                           knowledge_level: str = "General") -> str:
    
    probs_str = "\n".join([f"  - {cls}: {prob*100:.1f}%" for cls, prob in sorted(probabilities.items(), key=lambda x: -x[1])])

    # El User Prompt AHORA SOLO TIENE DATOS. Es limpio y objetivo.
    prompt = f"""Datos del análisis de la galaxia '{galaxy_name}':
- Nivel del usuario: {knowledge_level}
- Clase predicha por la CNN: {predicted_class} ({CLASS_DESCRIPTIONS.get(predicted_class, '')})
- Distribución Softmax (Confianza):
{probs_str}

Por favor, analiza estos datos y explícaselos al usuario siguiendo estrictamente tu estructura de sistema (Contexto, Detalles sutiles y CTA). Justifica la segunda probabilidad más alta si es relevante."""

    # Pasamos tu súper prompt como el cerebro (system_prompt)
    return generate_text_universal(
        prompt=prompt, 
        model_name=model_name, 
        system_prompt=utils.prompt_engineering.stronger_prompt
    )


def get_gallery_description(galaxy_data: dict, model_name: str) -> str:
    prompt = f"""El usuario está observando la siguiente galaxia en la galería:
Nombre: {galaxy_data['name']} ({galaxy_data.get('designation', '')})
Tipo morfológico: {galaxy_data.get('class', '')}
Distancia: {galaxy_data.get('distance_ly', '')} años luz
Descripción base: {galaxy_data.get('description', '')}

Genera tu explicación siguiendo tus directrices de sistema."""

    return generate_text_universal(
        prompt=prompt, 
        model_name=model_name, 
        system_prompt=utils.prompt_engineering.stronger_prompt
    )
# =============================================
# PARA TENER CHAT EN LA APP
# ==============================================

def chat_universal(messages: list, model_name: str) -> str:
    """
    Función puente para chats multi-turno.
    Recibe una lista de diccionarios en formato OpenAI: 
    [{"role": "system"|"user"|"assistant", "content": "..."}]
    y la adapta según el proveedor.
    """
    if model_name not in MODEL_REGISTRY:
        raise ValueError(f"El modelo '{model_name}' no está registrado.")
    
    provider = MODEL_REGISTRY[model_name]
    
    try:
        if provider == "anthropic":
            client = get_anthropic_client()
            
            # Anthropic no acepta "system" dentro de la lista de mensajes.
            # Lo extraemos si existe y lo pasamos como parámetro independiente.
            system_msg = next((m["content"] for m in messages if m["role"] == "system"), None)
            
            # Filtramos solo los mensajes de usuario y asistente para la lista
            anthropic_msgs = [{"role": m["role"], "content": m["content"]} 
                              for m in messages if m["role"] in ["user", "assistant"]]
            
            kwargs = {
                "model": model_name,
                "max_tokens": 1000, # Un poco más largo para chats
                "messages": anthropic_msgs
            }
            if system_msg:
                kwargs["system"] = system_msg # Inyectamos el system prompt a la manera de Anthropic
                
            response = client.messages.create(**kwargs)
            return response.content[0].text
            
        else:
            # Para OpenAI, DeepSeek y Gemini
            if provider == "openai":
                client = get_openai_client()
            elif provider == "deepseek":
                client = get_deepseek_client()
            elif provider == "gemini":
                client = get_gemini_client()
            
            api_kwargs = {
                "model": model_name,
                "messages": messages # Estos proveedores aceptan la lista intacta (incluyendo "system")
            }
            
            if provider == "openai":
                api_kwargs["max_completion_tokens"] = 1000
            else:
                api_kwargs["max_tokens"] = 1000
                
            response = client.chat.completions.create(**api_kwargs)
            return response.choices[0].message.content

    except Exception as e:
        st.error(f"Error de comunicación con {provider} ({model_name}): {str(e)}")
        return "Hubo un error al procesar tu mensaje."