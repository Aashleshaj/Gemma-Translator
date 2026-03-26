from cProfile import label
import re
import json
from tkinter.tix import TEXT
import streamlit as st
import requests
import ollama
import pandas as pd

# OLLAMA_MODEL="gemma3:12b"  # Updated model name for Ollama
OLLAMA_MODEL="translategemma:latest"  # Thinking Model
OLLAMA_URL = "http://localhost:11434/api/generate"  # Ollama API endpoint
OLLAMA_TAGS_URL = "http://localhost:11434/api/tags"  # Ollama tags/list endpoint

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
        # models is a list of dicts with 'name' and other fields
        models = data.get("models", [])
        print('models------------->',models)
        model_names = [m.get("name", "unknown") for m in models]
        print('model_names------------->',model_names)
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
selected_model = st.sidebar.selectbox(
    "Select Ollama Model",
    available_models,
    index=available_models.index(st.session_state.selected_model) if st.session_state.selected_model in available_models else 0,
    help="Choose the LLM model to use for analysis and Q&A generation"
)
st.session_state.selected_model = selected_model

# Fetch and prepare language data Added language and code in data.csv file took this info from https://ollama.com/library/translategemma
data = pd.read_csv("data.csv")
df = pd.DataFrame(data)
source_language = st.selectbox("Select Source Language:", df['Language'].unique())
source_code = df[df['Language'] == source_language]['Code'].values[0]
target_language = st.selectbox("Select Target Language:", df['Language'].unique())
target_code = df[df['Language'] == target_language]['Code'].values[0]
text_to_translate = st.text_area(label="Enter Text to Translate:")

if st.button("Translate"):
    print('Inside button click')
    if source_language and target_language and text_to_translate:
        print('All fields filled')
        prompt = f"""
        You are a professional {source_language} ({source_code}) to {target_language} ({target_code}) translator. Your goal is to accurately convey the meaning and nuances of the original {source_language} text while adhering to {target_language} grammar, vocabulary, and cultural sensitivities.
        Produce only the {target_language} translation, without any additional explanations or commentary. Please translate the following {source_language} text into {target_language}:
        {text_to_translate}
        """

        try:
            with st.spinner("⏳ Translating..."):
                payload = {
                    "model": st.session_state.selected_model,
                    "prompt": prompt,
                }
                print('payload------------->',payload)
                response = ollama.generate(
                    model=st.session_state.selected_model,
                    prompt=prompt,
                    stream=False,
                )
                output = response['response']

            # Show Results
            st.subheader("📌 Translation Results")
            st.markdown(output)

            # Save in session for download
            st.session_state["translation"] = output

        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

    else:
        st.warning("⚠️ Please fill in all the required fields.")