import pandas as pd
import streamlit as st

from src.gui.ui_elements import render_dataset_buttons, display_dataset, chat_interface, display_chat_log
from src.gui.chat import get_ai_response
from src.gui.background import set_background_image, get_image_base64

# Initialize session state variables
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

user_question = chat_interface()

if user_question:
    ai_response = get_ai_response(user_question)
    st.session_state['chat_log'].append((user_question, ai_response))

display_chat_log(st.session_state['chat_log'])
