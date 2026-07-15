# import re
# import json
import streamlit as st
import requests
import pandas as pd
from ollama import Client
import httpx

# Configuration
OLLAMA_MODEL = "translategemma:latest"
OLLAMA_HOST_URL = "http://localhost:11434"
OLLAMA_TAGS_URL = f"{OLLAMA_HOST_URL}/api/tags"

system = """You are an expert translator. Translate the user's text from {source_language} to {target_language}.
Follow these rules strictly:
1. Output ONLY the translated text.
2. Do not add any conversational filler, greetings, or explanations.
3. Maintain the original tone and formatting."""

@st.cache_data(ttl=60)
def fetch_available_models(tags_url: str = OLLAMA_TAGS_URL):
    """Fetch list of available Ollama models from the /api/tags endpoint."""
    try:
        response = requests.get(tags_url, timeout=5)
        response.raise_for_status()
        data = response.json()
        models = data.get("models", [])
        model_names = [m.get("name", "unknown") for m in models]
        return sorted(model_names) if model_names else [OLLAMA_MODEL]
    except Exception as e:
        st.warning(f"⚠️ Could not fetch Ollama models: {e}. Using default: {OLLAMA_MODEL}")
        return [OLLAMA_MODEL]
    
st.set_page_config(page_title="Gemma Translator", layout="centered")
st.title("Ollama Gemma Translator 🌐")

# Initialize session state for selected model
if "selected_model" not in st.session_state:
    st.session_state.selected_model = OLLAMA_MODEL

# Add model selector in sidebar
st.sidebar.subheader("⚙️ Model Settings")
available_models = fetch_available_models()

# Safely set the dropdown index based on session state
try:
    default_index = available_models.index(st.session_state.selected_model)
except ValueError:
    default_index = 0

selected_model = st.sidebar.selectbox(
    "Select Ollama Model",
    available_models,
    index=default_index,
    help="Choose the LLM model to use for translation"
)
st.session_state.selected_model = selected_model

# Fetch and prepare language data
try:
    df = pd.read_csv("data.csv")
except FileNotFoundError:
    st.error("⚠️ data.csv not found. Please ensure the file is in the same directory.")
    st.stop()

source_language = st.selectbox("Select Source Language:", df['Language'].unique())
source_code = df[df['Language'] == source_language]['Code'].values[0]
target_language = st.selectbox("Select Target Language:", df['Language'].unique())
target_code = df[df['Language'] == target_language]['Code'].values[0]

text_to_translate = st.text_area(label="Enter Text to Translate:")

if st.button("Translate"):
    if source_language and target_language and text_to_translate:
        prompt = f"""
        You are a professional {source_language} ({source_code}) to {target_language} ({target_code}) translator. Your goal is to accurately convey the meaning and nuances of the original {source_language} text while adhering to {target_language} grammar, vocabulary, and cultural sensitivities.
        Produce only the {target_language} translation, without any additional explanations or commentary. Please translate the following {source_language} text into {target_language}:
        {text_to_translate}
        """

        try:
            with st.spinner("⏳ Translating... (This may take a moment)"):
                
                # Use httpx to set a 2-minute timeout so Ollama has time to load large models into memory
                client = Client(
                    host=OLLAMA_HOST_URL,
                    timeout=120.0
                )
                
                response = client.generate(
                    model=st.session_state.selected_model,
                    prompt=prompt,
                    # stream=False,
                )
                output = response['response']

            # Show Results
            st.subheader("📌 Translation Results")
            st.markdown(output)

            # Save in session for download
            st.session_state["translation"] = output

        except Exception as e:
            # Replaced the hardcoded network error with the actual Python exception
            st.error(f"❌ Translation Failed: {type(e).__name__} - {str(e)}")

    else:
        st.warning("⚠️ Please fill in all the required fields.")