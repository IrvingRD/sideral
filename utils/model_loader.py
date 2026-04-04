import streamlit as st
import tensorflow as tf
import numpy as np
import json
from huggingface_hub import hf_hub_download

REPO_ID = "IrvingRD/Sideral"

@st.cache_resource(show_spinner="Descargando y compilando arquitectura CNN...")
def load_model_and_metadata():
    """
    Descarga los pesos y metadatos desde HuggingFace y los compila en RAM.
    Gracias a @st.cache_resource, esto solo sucede 1 vez por inicio de servidor.
    """
    try:
        model_path = hf_hub_download(
            repo_id=REPO_ID,
            filename="efficientnet_gz2_fase2_best.keras",
            repo_type="model"
        )
        metadata_path = hf_hub_download(
            repo_id=REPO_ID,
            filename="model_metadata.json",
            repo_type="model"
        )

        model = tf.keras.models.load_model(model_path)

        with open(metadata_path) as f:
            metadata = json.load(f)

        return model, metadata
        
    except Exception as e:
        # Programación defensiva en caso de que HuggingFace falle
        st.error(f"Error crítico al cargar el modelo espacial: {e}")
        return None, None


def predict_galaxy(model, metadata, img_array):
    """
    Recibe un numpy array (H, W, 3) de píxeles,
    aplica el preprocesamiento matemático y ejecuta un Forward Pass directo.
    """
    # Si el modelo no cargó, evitamos que la app colapse y devolvemos valores nulos seguros
    if model is None or metadata is None:
        return "Desconocido", {"elliptical": 0.25, "spiral": 0.25, "edge_on": 0.25, "merger": 0.25}

    img_size = metadata['img_size']
    classes  = metadata['classes']

    # 1. Cast explícito a Tensor Float32 (Evita cuellos de botella en operaciones de la CPU)
    img = tf.convert_to_tensor(img_array, dtype=tf.float32)

    # 2. Redimensionamiento bilineal espacial
    img = tf.image.resize(img, [img_size, img_size])

    # 3. Preprocesamiento (Z-score o scaling específico de la arquitectura EfficientNet)
    img = tf.keras.applications.efficientnet.preprocess_input(img)

    # 4. Expansión a Tensor de 4 dimensiones (Batch_size, Height, Width, Channels)
    # Ejemplo: pasa de (224, 224, 3) a (1, 224, 224, 3)
    img = tf.expand_dims(img, axis=0)

    # =========================================================================
    # 5. INFERENCIA OPTIMIZADA (Direct Forward Pass)
    # Reemplazamos model.predict() por model() para evitar el overhead del tf.data.Dataset
    # training=False garantiza que el Dropout y BatchNormalization actúen de forma determinista.
    # =========================================================================
    preds_tensor = model(img, training=False)
    
    # Extraemos el vector probabilístico del tensor a un array de numpy unidimensional
    preds = preds_tensor.numpy()[0] 

    predicted_class = classes[np.argmax(preds)]
    probabilities   = {cls: float(prob) for cls, prob in zip(classes, preds)}

    return predicted_class, probabilities