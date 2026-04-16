# 🌌 Sideral

> *Tu ventana inteligente al cosmos*

Sideral es una herramienta interactiva de divulgación científica que te acerca al universo, permitiéndote explorar galaxias reales capturadas por los telescopios más poderosos de la humanidad y analizar sus características con la ayuda de inteligencia artificial.

## ¿Qué es Sideral?

Imagina tener a un astrónomo amigable a tu lado que puede observar una fotografía del espacio profundo y contarte, con palabras sencillas y emocionantes, los secretos que esconden las galaxias. Eso es Sideral.

La aplicación combina:
- **Fotografías reales del universo**: Imágenes curadas del catálogo Galaxy Zoo 2 (SDSS) y descargas en vivo desde NASA APOD
- **Inteligencia visual avanzada**: Modelo EfficientNetB0 entrenado para reconocer 4 clases morfológicas de galaxias
- **Explicaciones accesibles**: Asistente de IA que traduce conceptos astronómicos a lenguaje conversacional

No necesitas ser astrónomo ni tener conocimientos técnicos para usar Sideral. Solo tu curiosidad.

## 🚀 ¿Qué puedes hacer?

### 1. **Explorar Galería** 🌌
Navega por una colección curada de 100 imágenes reales del universo:
- Galaxias elípticas suaves sin estructura de disco
- Galaxias espirales con brazos majestuosos
- Discos de canto vistos de lado (edge-on)
- Pares de galaxias en fusión (mergers)

Cada imagen incluye:
- Nombre del catálogo (NGC, IC, M, etc.)
- Distancia estimada en años luz
- Clasificación automática por tipo morfológico
- Explicación generada por IA

### 2. **Analizar Galaxia** 🔭
¿Tienes una fotografía de una galaxia y quieres saber más?

1. Sube la imagen desde tu dispositivo (224×224 px)
2. El modelo visual de Sideral la analiza automáticamente
3. Clasifica la galaxia en una de 4 categorías con nivel de confianza
4. Abre una conversación con Sideral para que te explique en detalle

## 📋 Requisitos

Para ejecutar Sideral necesitas:
- **Python 3.11 o superior**
- Las bibliotecas listadas en `requirements.txt`
- Una conexión a internet (para descargar imágenes de la NASA)
- Claves API (opcional):
  - `NASA_API_KEY`: Obtén una gratis en [api.nasa.gov](https://api.nasa.gov)
  - `ANTHROPIC_API_KEY` o `OPENAI_API_KEY`: Para explicaciones con IA

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
ANTHROPIC_API_KEY=tu_clave_aqui  # Para Claude
OPENAI_API_KEY=tu_clave_aqui     # Para GPT
```

### Paso 4: Ejecutar la aplicación
```bash
streamlit run Sideral.py
```

La aplicación se abrirá en tu navegador en `http://localhost:8501`

## Despliegue en línea

¡Existe una versión alojada en Streamlit Cloud! Accede en: https://sideral-dcdg30.streamlit.app/

---

## 🔬 Pipeline de Ciencia de Datos

Sideral no es solo una aplicación; es el resultado de un completo pipeline de análisis astronómico y aprendizaje automático. Todo el código de construcción del modelo y la galería está documentado en la carpeta `developing/`.

### Fases del Desarrollo

#### **Fase 1: Análisis Exploratorio de Datos (EDA)**
📄 **Archivo**: `developing/notebooks/Datos_EDA.ipynb`

En esta fase se realizó un análisis profundo del catálogo Galaxy Zoo 2:
- Carga y exploración de 243,500 imágenes con clasificaciones voluntarias
- Análisis de distribución de 679 categorías morfológicas granulares
- Aplicación de umbrales de confianza (scores debiased) para extraer clases puras
- Balanceo estratificado para crear un dataset de 5,060 imágenes en 4 clases

**Resultado**: Dataset etiquetado limpio (`gz2_labels_clean.csv`)

#### **Fase 2: Entrenamiento del Modelo Visual**
📓 **Archivo**: `developing/notebooks/EfficientNetSideral.ipynb`

Entrenamiento de un modelo EfficientNetB0 usando transfer learning:

**Arquitectura**:
- Backbone: EfficientNetB0 preentrenado en ImageNet
- Pooling global + Dropout(0.3)
- Cabeza clasificadora: Dense(4 clases)

**Estrategia de 2 fases**:
1. **Fase 1** (15 épocas): Backbone congelado, solo entrena la cabeza (lr=1e-3)
2. **Fase 2** (25 épocas): Fine-tuning completo del backbone (lr=1e-5)

**Hardware**: GPU Tesla T4 (Google Colab) con mixed precision (float16/float32)

**Métricas finales**:
- Accuracy en validación: **91.44%**
- Recall por clase (test set):
  - Elliptical: 91.6%
  - Edge-on: 98.4%
  - Merger: 80.0%
  - Spiral: 89.9%

**Resultado**: Modelo guardado en Hugging Face Hub (`IrvingRD/Sideral`)

#### **Fase 3: Curaduría de Galería Interactiva**
🖼️ **Archivo**: `developing/notebooks/generar_galería.py`

Pipeline ETL que:
1. Muestrea 25 galaxias de cada clase (100 total)
2. Consulta SIMBAD para obtener nombres en catálogos principales (NGC, M, IC, UGC)
3. Calcula distancia de luminosidad usando redshift (ley de Hubble)
4. Descarga imágenes de alta calidad del SDSS (512×512 px)
5. Genera metadatos JSON para la aplicación interactiva

**Datos consultados**:
- SIMBAD: Nombres de catálogo y redshifts
- SDSS SkyServer: Imágenes astronómicas recortadas
- Galaxy Zoo 2: Clasificaciones voluntarias

**Resultado**: `data/gallery_metadata.json` con 100 galaxias curadas

#### **Fase 4: Publicación en Hugging Face**
🤝 **Archivo**: `developing/notebooks/Hugging_Face.ipynb`

Subida del modelo a Hugging Face Hub para que sea accesible desde Streamlit Cloud:
- Modelo: `efficientnet_gz2_fase2_best.keras` (45.3 MB)
- Metadatos: `model_metadata.json` (clases, thresholds, métricas)
- Repositorio público: https://huggingface.co/IrvingRD/Sideral

### 📂 Estructura de `developing/`

```
developing/
├── notebooks/
│   ├── Datos_EDA.ipynb              # Análisis exploratorio (30 celdas)
│   ├── EfficientNetSideral.ipynb    # Entrenamiento (24 celdas)
│   ├── Hugging_Face.ipynb           # Publicación (6 celdas)
│   └── generar_galería.py           # Pipeline ETL de galería
│
└── data/
    ├── labels.csv                   # Galaxy Zoo 2 clasificaciones (243.5K registros)
    ├── filemapping.csv              # Mapeo ID → archivo imagen
    ├── gz2_labels_clean.csv         # Dataset etiquetado (5,060 galaxias)
    ├── Column_description_and_format.txt
    ├── results.txt / results_public.txt
    └── images_efficientnet/         # Imágenes de entrenamiento
```

### 🔑 Características Técnicas del Pipeline

- **Data Augmentation**: Flips horizontal/vertical, rotación ±45°
- **Normalización**: ImageNet preprocess_input para EfficientNet
- **Early Stopping**: Monitoreo de `val_loss` con paciencia de 5-7 épocas
- **Mixed Precision**: float16/float32 para 2× aceleración en GPU
- **Stratified Splits**: 70% train / 15% val / 15% test
- **Reproducibilidad**: Seeds fijos para resultados consistentes

### 📊 Flujo de Datos

```
Galaxy Zoo 2 (SDSS)
    ↓
[Datos_EDA.ipynb] ← Exploración y limpieza
    ↓
gz2_labels_clean.csv (5,060 imágenes, 4 clases)
    ↓
[EfficientNetSideral.ipynb] ← Entrenamiento
    ↓
efficientnet_gz2_fase2_best.keras
    ↓
[Hugging_Face.ipynb] ← Publicación
    ↓
Hugging Face Hub
    ↓
[Sideral.py] ← Aplicación web
```

---

## 📂 Estructura del Proyecto (Completa)

```
sideral/
├── Sideral.py                          # Página de inicio principal
│
├── pages/
│   ├── 01_Galería.py                   # Explorador de galería curada
│   └── 02_Clasificador.py              # Analizador de galaxias
│
├── utils/
│   ├── llm.py                          # Integración con Claude/GPT
│   ├── model_loader.py                 # Carga del modelo desde HF
│   ├── prompt_engineering.py           # Prompts especializados
│   └── secrets.py                      # Gestión de claves API
│
├── data/
│   ├── gallery_metadata.json           # Metadatos de 100 galaxias
│   └── images/                         # Galería (4 carpetas por clase)
│       ├── elliptical/
│       ├── spiral/
│       ├── edge_on/
│       └── merger/
│
├── developing/                         # Pipeline de construcción
│   ├── notebooks/                      # Análisis y entrenamiento
│   │   ├── Datos_EDA.ipynb
│   │   ├── EfficientNetSideral.ipynb
│   │   ├── Hugging_Face.ipynb
│   │   └── generar_galería.py
│   └── data/                           # Datos de Galaxy Zoo 2
│       ├── labels.csv
│       ├── filemapping.csv
│       ├── gz2_labels_clean.csv
│       └── images_efficientnet/
│
├── .gitignore
├── LICENSE
├── README.md                           # Este archivo
├── requirements.txt                    # Dependencias
├── pyproject.toml
└── tree.txt                            # Estructura del proyecto
```

---

## 🎨 Características Principales

### Diseño Responsivo
Sideral funciona en computadoras, tablets y dispositivos móviles.

### Interfaz Intuitiva
Navegación clara con explicaciones en cada paso. Sin jerga técnica innecesaria.

### Análisis Visual en Tiempo Real
Sube una imagen y obtén análisis instantáneo de:
- **Tipo de galaxia**: 4 categorías morfológicas
- **Nivel de certeza**: Confianza visual por clase
- **Explicación personalizada**: Conversación con IA

### Educativo y Entretenido
Objetivo: conectar a las personas con la maravilla del universo, no con la complejidad técnica.

---

## 🧠 Tecnologías Utilizadas

### Backend & ML
- **[TensorFlow](https://www.tensorflow.org/)**: Red neuronal convolucional (EfficientNetB0)
- **[Hugging Face Hub](https://huggingface.co/)**: Hosting de modelos preentrenados
- **[astropy](https://www.astropy.org/)**: Cálculos astronómicos (redshift, distancia)
- **[astroquery](https://astroquery.readthedocs.io/)**: Consultas a SIMBAD

### Frontend & IA
- **[Streamlit](https://streamlit.io/)**: Framework web interactivo
- **[Anthropic Claude](https://www.anthropic.com/)**: Explicaciones en lenguaje natural
- **[OpenAI GPT](https://openai.com/)**: Alternativa a Claude

### Datos
- **[NASA APOD API](https://api.nasa.gov/)**: Imágenes del espacio en vivo
- **[Galaxy Zoo 2](https://www.zooniverse.org/projects/waveney/galaxy-zoo-2/)**: Catálogo de clasificaciones voluntarias
- **[SDSS SkyServer](https://skyserver.sdss.org/)**: Imágenes astronómicas de alta resolución
- **[SIMBAD](http://simbad.u-strasbg.fr/)**: Base de datos astronómica

---

## 📝 Cómo Funciona el Análisis

### Flujo de Clasificación

1. **Carga de imagen**: Subes una fotografía de una galaxia (formato JPEG/PNG)
2. **Preprocesamiento**:
   - Redimensión a 224×224 px
   - Normalización ImageNet (escala a [-1, 1])
3. **Clasificación**: EfficientNetB0 predice probabilidades para 4 clases
4. **Contexto**:
   - Extrae clase predicha y nivel de confianza
   - Calcula certeza por cada categoría
5. **Narración**: Claude o GPT generan explicación accesible

### Ejemplo de Output

```
🔍 Tipo Detectado: Galaxia Espiral

Confianza por clase:
├── Spiral:     92.3% ████████████████████
├── Elliptical: 4.2%  ░░
├── Edge-on:    3.1%  ░░
└── Merger:     0.4%  ░

💬 Explicación:
"Estamos observando una hermosa galaxia espiral, similar a la Vía Láctea.
La estructura de brazo que ves es donde se forman nuevas estrellas..."
```

---

## 🤝 Contribuciones

¿Tienes ideas para mejorar Sideral? Las contribuciones son bienvenidas.

Para contribuir:
1. Fork el repositorio
2. Crea una rama para tu característica (`git checkout -b feature/nueva-caracteristica`)
3. Confirma tus cambios (`git commit -m 'Añade nueva característica'`)
4. Empuja a la rama (`git push origin feature/nueva-caracteristica`)
5. Abre un Pull Request

### Áreas de Mejora Sugeridas

- Ampliar galería curada con más galaxias
- Entrenar modelos especializados para subestructuras galácticas
- Integración con otras APIs (ESA, Spitzer)
- Modo offline con modelo comprimido
- Gamificación de aprendizaje (cuestionarios, retos)

---

## 📜 Licencia

Este proyecto está bajo la licencia [especificada en LICENSE](LICENSE).

---

## 🙌 Créditos

- **Desarrollo**: Iván Irving Rosas Domínguez
- **Datos**: [Galaxy Zoo 2](https://www.zooniverse.org/) (clasificaciones voluntarias) y [SDSS](https://www.sdss.org/) (imágenes)
- **Imágenes en vivo**: [NASA APOD](https://apod.nasa.gov/) (Astronomy Picture of the Day)
- **Modelos de IA**: Entrenados con datos públicos de galaxias del catálogo SDSS
- **Inspiración**: El proyecto de divulgación científica y educación astronómica

---

## 💬 Contacto y Soporte

¿Preguntas sobre el desarrollo, las matemáticas o cómo usar Sideral?
- Abre un issue en el repositorio
- Contacta al desarrollador directamente

---

**Sideral © 2026** | Desarrollado para conectar a la humanidad con el universo.

*"El universo está lleno de misterios. Sideral te ayuda a explorarlos."* 🌌✨
