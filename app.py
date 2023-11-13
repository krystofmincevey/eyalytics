import streamlit as st

from src.gui.data import (
    display_dataset, create_dataset_selection_buttons,
    create_upload_buttons,
    init_data_states, ADMIN_USERS, RAG_USERS,
    ADMIN_DATASETS, GUEST_DATASETS,
    DATASET_KEY
)
from src.gui.chat import (
    init_chatbot_session_state,
)
from src.gui.image import (
    set_background_image, get_image_base64,
    set_logo,
)


st.markdown("""
<style>
/* Global font color */
body {
    color: white;
}

/* Headers, descriptions, text inside expanders */
h1, h2, h3, h4, h5, h6, .stMarkdown {
    color: white !important;
}

/* For text input and selectbox values */
.stTextInput input, .stSelectbox select {
    color: black !important;
}

/* Selectbox label color - adjust this class as needed */
.stSelectbox label, .stTextInput label {
    color: white !important;
}

/* Text inside an expander */
.stExpander .stMarkdown p {
    color: white !important;
}

/* You may need to add further selectors for other widgets/parts of the UI where the color is not as expected */
</style>
""", unsafe_allow_html=True)

# BACKGROUND --------------------------------------------------
# Set the background image
background_image_path = './img/belfius_equal.jpg'
set_background_image(get_image_base64(background_image_path))

# SIDEBAR -----------------------------------------------------
# Set the logo in the sidebar
# Function to set the logo in the sidebar
logo_path = './img/belfius_logo.jpg'
set_logo(logo_path)

# Sidebar username input and handling
with st.sidebar.form(key='user_form'):
    username = st.text_input(
        label="Username", label_visibility="collapsed",
        placeholder="Enter username..."
    )
    submit = st.form_submit_button(label='Submit')


# TODO: Refactor
if submit:
    # Initialize session state variables
    init_data_states()
    init_chatbot_session_state()

    if username.lower() in ADMIN_USERS:
        st.session_state['allowed_datasets'] = ADMIN_DATASETS
    elif username.lower() in RAG_USERS:
        st.session_state['allowed_datasets'] = []
    else:
        st.session_state['allowed_datasets'] = GUEST_DATASETS

if 'allowed_datasets' in st.session_state:
    if st.session_state['allowed_datasets']:  # code interpreter
        create_dataset_selection_buttons(st.session_state['allowed_datasets'])
    else:  # RAG
        create_upload_buttons()

# DATA PREVIEW INTERFACE --------------------------------------
# Define the custom style
custom_title = """
<div style="
    font-size: 60px;
    font-weight: bold;
    color: white; /* Belfius red */
    text-shadow: 
        2px 2px 2px #555; /* subtle shadow for depth */
    font-family: 'Open Sans', sans-serif; /* sleek, modern font */
    text-align: center; /* Center aligns the text */
">
    Belfius Analytics
</div>
"""

# Load the Google Fonts stylesheet for 'Open Sans'
st.markdown(
    '<style>@import url("https://fonts.googleapis.com/css2?family=Open+Sans:wght@700&display=swap");</style>',
    unsafe_allow_html=True
)

# Display the custom title
st.markdown(custom_title, unsafe_allow_html=True)

if DATASET_KEY in st.session_state:
    if not st.session_state[DATASET_KEY].empty:
        display_dataset()

# CHATBOT INTERFACE ------------------------------------------
# user_question = chat_interface()
# if user_question:
#     ai_response = conversational_chat(user_question, st.session_state['chat_chain'])
#     st.session_state['chat_log'].append((user_question, ai_response))
#
# # Display the chat log
# display_chat_log()


