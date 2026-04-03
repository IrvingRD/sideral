from anthropic import Anthropic
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()  # Carga las variables de entorno desde el archivo .env



ANTROPIC_API_KEY = os.getenv('ANTROPIC_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')


os.environ["ANTHROPIC_API_KEY"] = ANTROPIC_API_KEY
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
os.environ["GEMINI_API_KEY"] = GEMINI_API_KEY
os.environ["DEEPSEEK_API_KEY"] = DEEPSEEK_API_KEY


# client = OpenAI()
client = Anthropic()

CLASS_DESCRIPTIONS = {
    "elliptical": "galaxia elíptica — forma esferoidal suave sin estructura de disco ni brazos espirales",
    "spiral":     "galaxia espiral — disco con brazos espirales claramente definidos",
    "edge_on":    "galaxia de disco vista de canto — el plano del disco apunta hacia el observador",
    "merger":     "galaxia en fusión — interacción gravitacional entre dos o más galaxias"
}


def get_galaxy_explanation(
    galaxy_name: str,
    predicted_class: str,
    probabilities: dict,
    knowledge_level: str = "general"
) -> str:
    """
    Genera una explicación contextual de la clasificación usando Claude.
    """
    probs_str = "\n".join([
        f"  - {cls}: {prob*100:.1f}%"
        for cls, prob in sorted(probabilities.items(), key=lambda x: -x[1])
    ])

    nivel_instruccion = {
        "general":    "Explica de forma accesible para alguien sin conocimientos de astronomía. Usa analogías cotidianas.",
        "estudiante": "Explica para un estudiante universitario de ciencias. Puedes usar terminología básica de astronomía.",
        "experto":    "Explica con terminología técnica de astrofísica. Asume conocimiento de morfología galáctica."
    }[knowledge_level]

    prompt = f"""Se clasificó la galaxia '{galaxy_name}' usando un modelo de visión por computadora 
entrenado en Galaxy Zoo 2.

Resultado de la clasificación:
- Clase predicha: {predicted_class} ({CLASS_DESCRIPTIONS[predicted_class]})
- Probabilidades por clase:
{probs_str}

{nivel_instruccion}

Por favor explica en español:
1. Qué significa morfológicamente que esta galaxia sea clasificada como '{predicted_class}'
2. Qué características visuales llevaron probablemente a esta clasificación
3. Qué nos dice esta morfología sobre la historia y evolución de la galaxia
4. Por qué el modelo asignó esa probabilidad a la segunda clase más probable

Sé conciso — máximo 250 palabras. No uses markdown ni bullet points, solo párrafos."""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        # model="gpt-5.4-mini",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.content[0].text


def get_gallery_description(galaxy_data: dict) -> str:
    """
    Genera una descripción narrativa enriquecida para una galaxia de la galería.
    """
    prompt = f"""Genera una descripción narrativa en español para la siguiente galaxia,
para mostrar en una aplicación educativa de astronomía:

Nombre: {galaxy_data['name']} ({galaxy_data['designation']})
Tipo morfológico: {galaxy_data['class']}
Distancia: {galaxy_data['distance_ly']} años luz
Constelación: {galaxy_data['constellation']}
Descripción base: {galaxy_data['description']}

Escribe 3 párrafos cortos y atractivos que:
1. Describan la apariencia visual y características morfológicas
2. Expliquen qué hace única o interesante a esta galaxia
3. Den contexto sobre su importancia en la astronomía moderna

Tono: divulgativo y apasionante. Máximo 200 palabras. Sin markdown."""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        # model="gpt-5.4-mini",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}]
    )