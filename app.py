import streamlit as st

from src.gui.data import (
    display_dataset, dataset_selection_buttons,
    init_data_states, ADMIN_USERS,
    ADMIN_DATASETS, GUEST_DATASETS
)
from src.gui.chat import (
    init_chatbot_session_state, chat_interface,
    conversational_chat, display_chat_log
)
from src.gui.image import (
    set_background_image, get_image_base64,
    set_logo,
)


# Initialize session state variables
init_data_states()
init_chatbot_session_state()

# BACKGROUND --------------------------------------------------
# Set the background image
background_image_path = './img/belfius_equal.jpg'
set_background_image(get_image_base64(background_image_path))

# SIDEBAR -----------------------------------------------------
# Set the logo in the sidebar
# Function to set the logo in the sidebar
logo_path = './img/belfius_gpt.jpg'
set_logo(logo_path)

# Sidebar username input and handling
with st.sidebar.form(key='user_form'):
    username = st.text_input(
        label="Username", label_visibility="collapsed",
        placeholder="Enter username..."
    )
    submit = st.form_submit_button(label='Submit')

if submit:
    if username.lower() in ADMIN_USERS:
        st.session_state['allowed_datasets'] = ADMIN_DATASETS
    else:
        st.session_state['allowed_datasets'] = GUEST_DATASETS

if 'allowed_datasets' not in st.session_state:
    st.session_state['allowed_datasets'] = []

dataset_selection_buttons(st.session_state['allowed_datasets'])

# DATA PREVIEW INTERFACE --------------------------------------
# Define the custom style
custom_title = """
<div style="
    font-size: 60px;
    font-weight: bold;
    color: white;
    text-shadow: 
        -2px -2px 0px red, 
         2px -2px 0px red, 
        -2px  2px 0px black, 
         2px  2px 0px black;
    font-family: 'Permanent Marker', cursive;
">
    Belfius Analytics
</div>
"""

# Load the Google Fonts stylesheet for 'Permanent Marker'
st.markdown(
    '<style>@import url("https://fonts.googleapis.com/css2?family=Permanent+Marker&display=swap");</style>',
    unsafe_allow_html=True
)

# Display the custom title
st.markdown(custom_title, unsafe_allow_html=True)

if 'dataset' in st.session_state and not st.session_state['dataset'].empty:
    display_dataset('dataset')

# CHATBOT INTERFACE ------------------------------------------
# user_question = chat_interface()
# if user_question:
#     ai_response = conversational_chat(user_question, st.session_state['chat_chain'])
#     st.session_state['chat_log'].append((user_question, ai_response))
#
# # Display the chat log
# display_chat_log()


