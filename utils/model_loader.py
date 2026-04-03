import streamlit as st
import tensorflow as tf
import numpy as np
import json
from huggingface_hub import hf_hub_download

REPO_ID = "IrvingRD/Sideral"

@st.cache_resource(show_spinner="Cargando modelo de clasificación...")
def load_model_and_metadata():
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


def predict_galaxy(model, metadata, img_array):
    """
    Recibe un numpy array (H, W, 3) uint8,
    aplica el preprocesamiento de EfficientNet,
    y devuelve clase predicha + probabilidades.
    """
    img_size = metadata['img_size']
    classes  = metadata['classes']

    img = tf.image.resize(img_array, [img_size, img_size])
    img = tf.keras.applications.efficientnet.preprocess_input(img)
    img = tf.expand_dims(img, axis=0)

    preds = model.predict(img, verbose=0)[0]

    predicted_class = classes[np.argmax(preds)]
    probabilities   = {cls: float(prob) for cls, prob in zip(classes, preds)}

    return predicted_class, probabilities