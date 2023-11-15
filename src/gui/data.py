import os
import pandas as pd
import streamlit as st

from pathlib import Path

from src.utils.loader import read_txt
from .chat import (
    CHAT_KEY, ASSISTANT_KEY, THREAD_KEY,
    MESSAGES_KEY, RAG_ASSISTANT_FILE,
    CODE_ASSISTANT_FILE,
    FILE_IDS_KEY,
    CLIENT_KEY,
    create_rag_assistant,
    create_analyst_assistant,
    create_analyst_thread,
    create_rag_thread,
)

# TODO: For industrialised version make sure these are stored securely!
# Dataset URLs and their headers
SALYTICS_KEY = 'ESG'
MIFID_KEY = 'MIFID'
EQUITIES_KEY = 'Equities'
EMISSIONS_KEY = 'Emissions'
UPLOAD_KEY = 'Upload'

DATASET_KEY = 'dataset'
INFO_KEY = 'dataset_info'

_root_path = Path(__file__).parent.parent.parent
PATHS = {
    SALYTICS_KEY: _root_path / "data" / "cwyod" / "salytics" / "salytics_sample.csv",
    MIFID_KEY: _root_path / "data" / "cwyod" / "mifid" / "mifid_sample.csv",
    EQUITIES_KEY: _root_path / "data" / "cwyod" / "equities" / "stock_prices.csv",
    EMISSIONS_KEY: _root_path / "data" / "cwyod" / "emissions" / "general_purpose.csv",
}
INFO_PATH = {
    SALYTICS_KEY: _root_path / "data" / "cwyod" / "salytics" / "salytics_info.txt",
    MIFID_KEY: _root_path / "data" / "cwyod" / "mifid" / "mifid_info.txt",
    EQUITIES_KEY: _root_path / "data" / "cwyod" / "equities" / "stock_price_info.txt",
    EMISSIONS_KEY: _root_path / "data" / "cwyod" / "emissions" / "general_purpose_info.txt",
}

ADMIN_DATASETS = [
    SALYTICS_KEY, MIFID_KEY, EQUITIES_KEY,  EMISSIONS_KEY
]  # Admin sees all datasets
GUEST_DATASETS = [EQUITIES_KEY]  # Guests see only these datasets


def init_data_states():
    st.session_state[DATASET_KEY] = pd.DataFrame()
    st.session_state[INFO_KEY] = ""


# TODO: add message reset once pressed.
def create_dataset_selection_buttons(allowed_datasets):
    for name in allowed_datasets:
        button_key = f'button_{name}'
        if st.sidebar.button(
                name, key=button_key,
                use_container_width=True,
                type='primary',
        ):
            # Load data:
            file_path, info = PATHS[name], read_txt(INFO_PATH[name])
            st.session_state[INFO_KEY] = info
            st.session_state[DATASET_KEY] = load_data(file_path)

            # Prepare chat interface:
            st.session_state[CHAT_KEY] = True
            st.session_state[MESSAGES_KEY] = []  # empty messages

            client = st.session_state[CLIENT_KEY]
            file = client.files.create(
                file=open(file_path, "rb"),
                purpose='assistants'
            )

            st.session_state[FILE_IDS_KEY] = [file.id]
            st.session_state[ASSISTANT_KEY] = create_analyst_assistant(client)
            st.session_state[THREAD_KEY] = create_analyst_thread(
                client, file_ids=[file.id], info=info,
            )
            # st.experimental_rerun()  # maybe not needed - test


# TODO: Add file removal: openai.File.delete(sid=file_id). Below
#  may fail when the total number of uploaded files > 20. To be seen!
def create_upload_buttons():
    client = st.session_state[CLIENT_KEY]

    # Sidebar option for users to upload their own files
    uploaded_file = st.sidebar.file_uploader(
        "Upload a file to OpenAI:", key="file_uploader"
    )

    uploaded_files = st.file_uploader(
        "Upload a file to OpenAI:", key="file_uploader",
        accept_multiple_files=True
    )
    for uploaded_file in uploaded_files:
        with open(f"{uploaded_file.name}", "wb") as f:
            f.write(uploaded_file.getbuffer())

        file = client.files.create(
            file=open(f"{uploaded_file.name}", "rb"),
            purpose='assistants'
        )
        st.session_state[FILE_IDS_KEY].append(file.id)
        st.sidebar.write(f"{uploaded_file.name}")

    # Button to start the chat session
    if st.sidebar.button("Start Chat"):
        # Prepare chat interface:
        st.session_state[CHAT_KEY] = True
        st.session_state[MESSAGES_KEY] = []  # empty messages
        st.session_state[ASSISTANT_KEY] = create_rag_assistant(client)
        st.session_state[THREAD_KEY] = create_rag_thread(
            client,
            file_ids=st.session_state[FILE_IDS_KEY],
        )


@st.cache_data
def load_data(url):
    data = pd.read_csv(url)
    return data


def display_dataset():  # why are we passing the "dataset" to the function when the key doesn't change.
    if DATASET_KEY not in st.session_state or st.session_state[DATASET_KEY].empty:
        # If the dataset isn't in the session state or is empty, don't proceed
        return

    st.header("Dataset Preview")
    dataset = st.session_state["dataset"]

    # Check if the filters state exists; if not, initialize it
    if 'filter_column' not in st.session_state:
        st.session_state['filter_column'] = None
    if 'filter_value' not in st.session_state:
        st.session_state['filter_value'] = None

    # Reset filters if a new dataset is loaded
    if 'last_dataset' not in st.session_state or st.session_state['last_dataset'] != "dataset":
        st.session_state['last_dataset'] = "dataset"
        st.session_state['filter_column'] = None
        st.session_state['filter_value'] = None

    # Dropdown to select a column
    col_options = [''] + list(dataset.columns)
    selected_column = st.selectbox(
        "Select a column to filter by:",
        col_options,
        index=0,
        key=f"dataset_select_column"
    )

    # Save the selected column to the session state
    st.session_state['filter_column'] = selected_column

    if selected_column:
        # Dropdown to select unique values from the column
        unique_values = [''] + list(dataset[selected_column].dropna().unique())
        selected_value = st.selectbox(
            f"Select a value from {selected_column}:",
            unique_values, index=0,
            key=f"dataset_select_value"
        )

        # Save the selected value to the session state
        st.session_state['filter_value'] = selected_value

        if selected_value:
            # Filter the dataset based on selected value
            filtered_data = dataset[dataset[selected_column] == selected_value]
        else:
            # If no value is selected, display unfiltered data
            filtered_data = dataset
    else:
        # If no column is selected, display unfiltered data
        filtered_data = dataset

    # Display the filtered dataset
    st.dataframe(filtered_data, height=300)

    with st.expander("Dataset Information"):
        st.markdown(
            f'<p class="big-font">{st.session_state.get("dataset_info", "No additional information available.")}</p>',
            unsafe_allow_html=True
        )
