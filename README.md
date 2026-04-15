# 🌌 Sideral

> *Tu ventana inteligente al cosmos*

Sideral es una herramienta interactiva de divulgación científica que te acerca al universo, permitiéndote explorar galaxias reales capturadas por los telescopios más poderosos de la humanidad y analizar sus características con la ayuda de inteligencia artificial.

## ¿Qué es Sideral?

Imagina tener a un astrónomo amigable a tu lado que puede observar una fotografía del espacio profundo y contarte, con palabras sencillas y emocionantes, los secretos que esconden las galaxias. Eso es Sideral.

La aplicación combina:
- **Fotografías reales del universo**: Imágenes en vivo descargadas desde los archivos de la NASA (NASA APOD)
- **Inteligencia visual**: Un sistema entrenado para reconocer la forma y estructura de las galaxias
- **Explicaciones accesibles**: Un asistente de IA que traduce los conceptos astronómicos a un lenguaje conversacional y emocionante

No necesitas ser astrónomo ni tener conocimientos técnicos para usar Sideral. Solo tu curiosidad.

## 🚀 ¿Qué puedes hacer?

### 1. **Explorar Galería** 🌌
Navega por una colección curada de imágenes del universo. Descubre:
- Galaxias espirales majestuosas donde nacen nuevas estrellas
- Estructuras lejanas capturadas por el telescopio Hubble
- Fenómenos cósmicos que desafían la imaginación

Cada imagen viene con una historia traducida al español y explicaciones sobre lo que estás viendo.

### 2. **Analizar Galaxia** 🔭
¿Tienes una fotografía de una galaxia y quieres saber más sobre ella?

1. Sube la imagen desde tu dispositivo
2. El sistema visual de Sideral la analiza automáticamente
3. Identifica si se trata de una galaxia elíptica, espiral, disco de canto o si está fusionándose con otra
4. Abre una conversación con Sideral para que te explique en detalle qué estás viendo

## 📋 Requisitos

Para ejecutar Sideral necesitas:
- **Python 3.11 o superior**
- Las bibliotecas listadas en `requirements.txt`
- Una conexión a internet (para descargar imágenes de la NASA)
- Claves API (opcional) para obtener imágenes en vivo:
  - `NASA_API_KEY`: Obtén una gratis en [api.nasa.gov](https://api.nasa.gov)
  - Claves para modelos de IA: Anthropic o OpenAI (si deseas usar esos modelos)

## 🛠️ Instalación y Uso

### Paso 1: Clonar el repositorio
```bash
git clone https://github.com/yourusername/sideral.git
cd sideral
```

### Paso 2: Instalar dependencias
```bash
pip install -r requirements.txt
```

O usando `uv` (más rápido):
```bash
uv sync
```

### Paso 3: Configurar variables de entorno
Crea un archivo `.env` en la raíz del proyecto:
```
NASA_API_KEY=tu_clave_aqui
ANTHROPIC_API_KEY=tu_clave_aqui  # Si usas Claude
OPENAI_API_KEY=tu_clave_aqui     # Si usas OpenAI
```

### Paso 4: Ejecutar la aplicación
```bash
streamlit run Sideral.py
```

La aplicación se abrirá en tu navegador (típicamente en `http://localhost:8501`)

## 📂 Estructura del Proyecto

```
sideral/
├── Sideral.py                  # Página de inicio principal
├── pages/
│   ├── 01_Galería.py           # Explorador de imágenes y galería
│   └── 02_Clasificador.py      # Analizador de galaxias
├── utils/
│   ├── llm.py                  # Integración con modelos de IA
│   ├── model_loader.py         # Carga del modelo visual de galaxias
│   ├── prompt_engineering.py   # Prompts especializados
│   └── secrets.py              # Gestión de claves API
├── data/
│   └── gallery_metadata.json   # Metadatos de la galería
├── requirements.txt            # Dependencias del proyecto
└── README.md                   # Este archivo
```

## 🎨 Características Principales

### Diseño Responsivo
Sideral funciona en computadoras, tablets y dispositivos móviles.

### Interfaz Intuitiva
Navegación clara con explicaciones en cada paso. No hay jerga técnica innecesaria.

### Análisis Visual en Tiempo Real
Sube una imagen y obtén un análisis instantáneo de:
- **Tipo de galaxia**: Elíptica, espiral, disco de canto o en fusión
- **Nivel de certeza**: Visualización clara de qué tan seguro es el análisis
- **Explicación personalizada**: Conversación con Sideral sobre tu galaxia

### Educativo y Entretenido
El objetivo es conectar a las personas con la maravilla del universo, no con la complejidad de la tecnología.

## 🧠 Tecnologías Utilizadas

- **[Streamlit](https://streamlit.io/)**: Framework web para crear aplicaciones de datos interactivas
- **[TensorFlow](https://www.tensorflow.org/)**: Red neuronal convolucional para clasificación de galaxias
- **[Anthropic Claude](https://www.anthropic.com/)** / **[OpenAI GPT](https://openai.com/)**: Modelos de lenguaje para explicaciones
- **[NASA APOD API](https://api.nasa.gov/)**: Acceso a fotografías del espacio
- **[Hugging Face Hub](https://huggingface.co/)**: Hosting de modelos pre-entrenados

## 📝 Cómo Funciona el Análisis

1. **Carga de imagen**: Subes una fotografía de una galaxia
2. **Preprocesamiento**: La imagen se redimensiona y normaliza
3. **Clasificación**: Un modelo entrenado con TensorFlow predice la forma de la galaxia
4. **Contexto**: Se calcula el nivel de certeza en cada categoría
5. **Narración**: Claude o GPT generan una explicación accesible basada en la predicción

## 🌐 Desplegar en Línea

Sideral puede desplegarse en servicios como:
- **[Streamlit Cloud](https://streamlit.io/cloud)**: Gratuito y simple
- **[Hugging Face Spaces](https://huggingface.co/spaces)**: Excelente para modelos
- **[Heroku](https://www.heroku.com/)** o **[Railway](https://railway.app/)**: Con contenedores Docker

Consulta la documentación de cada plataforma para instrucciones específicas.

## 🤝 Contribuciones

¿Tienes ideas para mejorar Sideral? Las contribuciones son bienvenidas.

Para contribuir:
1. Fork el repositorio
2. Crea una rama para tu característica (`git checkout -b feature/nueva-caracteristica`)
3. Confirma tus cambios (`git commit -m 'Añade nueva característica'`)
4. Empuja a la rama (`git push origin feature/nueva-caracteristica`)
5. Abre un Pull Request

## 📜 Licencia

Este proyecto está bajo la licencia [especificada en LICENSE](LICENSE).

## 🙌 Créditos

- **Desarrollo**: Iván Irving Rosas Domínguez
- **Fotografías**: [NASA APOD](https://apod.nasa.gov/) (Astronomy Picture of the Day)
- **Modelos de IA**: Entrenados con datos públicos de galaxias

## 💬 Contacto y Soporte

¿Preguntas o comentarios? Abre un issue en el repositorio o contacta con el desarrollador.

---

**Sideral © 2026** | Desarrollado para conectar a la humanidad con el universo.

*"El universo está lleno de misterios. Sideral te ayuda a explorarlos."* 🌌✨
