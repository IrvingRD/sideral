1import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

def bootstrap_env():
    for key, value in st.secrets.items():
        if os.getenv(key) is None and value is not None:
            os.environ[key] = str(value)