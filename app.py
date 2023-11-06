import pandas as pd
import streamlit as st

from src.gui.ui_elements import render_dataset_buttons, display_dataset
from src.gui.chat import (
    init_chatbot_session_state, chat_interface,
    conversational_chat, display_chat_log, setup_sidebar
)
from src.gui.background import set_background_image, get_image_base64

# Initialize session state variables
if 'chat_log' not in st.session_state:
    st.session_state['chat_log'] = []
if 'dataset' not in st.session_state:
    st.session_state['dataset'] = pd.DataFrame()

# Initialize session state for chatbot and datasets
init_chatbot_session_state()
if 'chat_log' not in st.session_state:
    st.session_state['chat_log'] = []
if 'dataset' not in st.session_state:
    st.session_state['dataset'] = pd.DataFrame()

# Set the background image
background_image_path = './img/belfius_equal.jpg'
set_background_image(get_image_base64(background_image_path))

# Paths to datasets
DATA_URL_1 = "./data/cwyod/titanic.csv"
DATA_URL_2 = "./data/cwyod/titanic.csv"

st.title("Chat with Data App")

col1, col2 = st.columns([1, 3])

with col1:
    render_dataset_buttons(DATA_URL_1, DATA_URL_2)

with col2:
    if 'dataset' in st.session_state and not st.session_state['dataset'].empty:
        display_dataset('dataset')  # Pass the key here

# Setup sidebar for chatbot (API key input and CSV upload)
setup_sidebar()

# Chat interface and logic
user_question = chat_interface()
if user_question:
    ai_response = conversational_chat(user_question, st.session_state['chat_chain'])
    st.session_state['chat_log'].append((user_question, ai_response))

# Display the chat log
display_chat_log()

