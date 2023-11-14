"""
Cost reduction ideas:
    - Keep track of previous queries, and answers and offer these up
        as answers prior to using the LLM. The user will have a chance to
        proceed to or view the previous answer.
"""
import streamlit as st

from src.gui.data import (
    display_dataset, create_dataset_selection_buttons,
    create_upload_buttons,
    init_data_states,
    ADMIN_DATASETS, GUEST_DATASETS,
    DATASET_KEY
)
from src.gui.chat import (
    init_chatbot_session_state, CHAT_KEY, chat
)
from src.gui.image import (
    set_background_image, get_image_base64,
    set_logo,
)
from src.gui.users import (
    ADMIN_USER, GUEST_USER,
    verify_user
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

# Login Form
with st.sidebar:
    with st.form(key='login_form'):
        username = st.text_input(
            "Username", placeholder="Enter username..."
        )
        password = st.text_input(
            "Password", type='password', placeholder="Enter password..."
        )
        submit = st.form_submit_button("Sign In")

# Authentication and State Management
if submit:
    if verify_user(username, password):
        # Initialize session state variables
        init_data_states()
        init_chatbot_session_state()

        if username.lower() == ADMIN_USER:
            st.session_state['allowed_datasets'] = ADMIN_DATASETS
        elif username.lower() == GUEST_USER:
            st.session_state['allowed_datasets'] = GUEST_DATASETS
        else:
            st.session_state['allowed_datasets'] = []

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
    {0}
</div>
"""

# Load the Google Fonts stylesheet for 'Open Sans'
st.markdown(
    '<style>@import url("https://fonts.googleapis.com/css2?family=Open+Sans:wght@700&display=swap");</style>',
    unsafe_allow_html=True
)

# Dataset Selection or Upload Buttons
if 'allowed_datasets' in st.session_state:
    if st.session_state['allowed_datasets']:  # code interpreter to be used with CSVs
        st.markdown(custom_title.format('Belfius Analytics'), unsafe_allow_html=True)
        create_dataset_selection_buttons(st.session_state['allowed_datasets'])
    else:  # RAG - no CSVs shared
        st.markdown(custom_title.format('BelfiusGPT+'), unsafe_allow_html=True)
        create_upload_buttons()

if st.session_state.get(DATASET_KEY) and not st.session_state[DATASET_KEY].empty:
    display_dataset()

if st.session_state.get(CHAT_KEY) and st.session_state[CHAT_KEY]:
    chat()

# CHATBOT INTERFACE ------------------------------------------
# user_question = chat_interface()
# if user_question:
#     ai_response = conversational_chat(user_question, st.session_state['chat_chain'])
#     st.session_state['chat_log'].append((user_question, ai_response))
#
# # Display the chat log
# display_chat_log()


