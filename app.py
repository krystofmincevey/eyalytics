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
    set_background_image,
    get_image_base64,
    set_logo,
)
from src.gui.users import (
    ADMIN_USER, GUEST_USER,
    verify_user
)


st.markdown("""
    <style>
    /* Global background color */
    body, .stApp {
        background-color: black !important;
    }
    
    /* Global font color */
    body, .stMarkdown {
        color: white !important;
    }
    
    /* Headers, descriptions, text inside expanders */
    h1, h2, h3, h4, h5, h6 {
        color: white !important;
    }
    
    /* Selectbox label color - adjust this class as needed */
    .stSelectbox label, .stTextInput label {
        color: white !important;
    }
    
    /* Text inside an expander */
    .stExpander .stMarkdown p {
        color: white !important;
    }
    
    /* Adjust sidebar background color */
    [data-testid=stSidebar] {
        background-color: #333333 !important;
    }
    
    .stChat {
      background-color: transparent !important;
      box-shadow: none !important;
      padding: 0 !important;
    }
    
    .stContainer {
      background-color: transparent !important;
      margin: 0 !important;
      border: none !important;
    }
    
    .stChat input {
      background-color: transparent !important;
    }
    
    .stChat button {
      font-color: white !important;
    }
    
    .stChatInput {
        background-color: transparent !important;
    }
    
    .stChatInput input {
        background-color: transparent !important;
    }
    
    .stChatFloatingInputContainer {
        background-color: transparent !important;
    }
    
    /* You may need to add further selectors for other widgets/parts of the UI where the color is not as expected */
    </style>
    """, unsafe_allow_html=True
)

# BACKGROUND --------------------------------------------------
# Set the background image
background_image_path = './img/belfius_equal_dark.jpg'
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
    text-align: center; /* Horizontally center the content */
    width: 100%; /* Ensure the div takes up the full width */
">
    <div style="
        font-size: 60px;
        font-weight: bold;
        color: white; /* Belfius red */
        text-shadow: 2px 2px 2px #555; /* subtle shadow for depth */
        font-family: 'Open Sans', sans-serif; /* sleek, modern font */
    ">
        {0}
    </div>
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

if st.session_state.get(DATASET_KEY) is not None and not st.session_state[DATASET_KEY].empty:
    display_dataset()

if st.session_state.get(CHAT_KEY) and st.session_state[CHAT_KEY]:
    chat()
