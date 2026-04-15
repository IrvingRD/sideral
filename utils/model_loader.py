import streamlit as st
import tensorflow as tf
import numpy as np
import json
from huggingface_hub import hf_hub_download

REPO_ID = "IrvingRD/Sideral"

@st.cache_resource(show_spinner="Descargando y compilando arquitectura CNN...")
def load_model_and_metadata():
    """
    Downloads model weights and metadata from HuggingFace.
    Cached with @st.cache_resource — runs once per server start.
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
        st.error(f"Error crítico al cargar el modelo espacial: {e}")
        return None, None


def predict_galaxy(model, metadata, img_array):
    """
    Accepts numpy array (H, W, 3) and returns predicted galaxy class with probabilities.
    Uses EfficientNet preprocessing and optimized forward pass.
    """
    if model is None or metadata is None:
        return "Desconocido", {"elliptical": 0.25, "spiral": 0.25, "edge_on": 0.25, "merger": 0.25}

    img_size = metadata['img_size']
    classes = metadata['classes']

    # Convert to tensor and resize
    img = tf.convert_to_tensor(img_array, dtype=tf.float32)
    img = tf.image.resize(img, [img_size, img_size])

    # Apply EfficientNet preprocessing
    img = tf.keras.applications.efficientnet.preprocess_input(img)

    # Expand dimensions for batch inference: (H, W, C) → (1, H, W, C)
    img = tf.expand_dims(img, axis=0)

    # Direct forward pass (avoids tf.data.Dataset overhead)
    preds_tensor = model(img, training=False)
    preds = preds_tensor.numpy()[0]

    predicted_class = classes[np.argmax(preds)]
    probabilities = {cls: float(prob) for cls, prob in zip(classes, preds)}

    return predicted_class, probabilities