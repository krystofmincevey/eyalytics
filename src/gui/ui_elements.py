import streamlit as st
from .data_loader import load_data


def render_dataset_buttons(data_url_1, data_url_2):
    st.header("Datasets")
    if st.button('Load Dataset 1'):
        dataset = load_data(data_url_1)
        st.session_state['dataset'] = dataset
        st.session_state['chat_log'] = []

    if st.button('Load Dataset 2'):
        dataset = load_data(data_url_2)
        st.session_state['dataset'] = dataset
        st.session_state['chat_log'] = []


def display_dataset(dataset_key):
    if dataset_key not in st.session_state or st.session_state[dataset_key].empty:
        # If the dataset isn't in the session state or is empty, don't proceed
        st.warning("No dataset loaded or dataset is empty.")
        return

    st.header("Dataset Preview")
    dataset = st.session_state[dataset_key]

    # Check if the filters state exists; if not, initialize it
    if 'filter_column' not in st.session_state:
        st.session_state['filter_column'] = None
    if 'filter_value' not in st.session_state:
        st.session_state['filter_value'] = None

    # Reset filters if a new dataset is loaded
    if 'last_dataset' not in st.session_state or st.session_state['last_dataset'] != dataset_key:
        st.session_state['last_dataset'] = dataset_key
        st.session_state['filter_column'] = None
        st.session_state['filter_value'] = None

    # Dropdown to select a column
    col_options = [''] + list(dataset.columns)
    selected_column = st.selectbox("Select a column to filter by:", col_options, index=0, key=f"{dataset_key}_select_column")

    # Save the selected column to the session state
    st.session_state['filter_column'] = selected_column

    if selected_column:
        # Dropdown to select unique values from the column
        unique_values = [''] + list(dataset[selected_column].dropna().unique())
        selected_value = st.selectbox(f"Select a value from {selected_column}:", unique_values, index=0, key=f"{dataset_key}_select_value")

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


def chat_interface():
    st.header("Chat Interface")
    user_question = st.text_input("Ask a question about the data:")
    return user_question


def display_chat_log(chat_log):
    for question, answer in chat_log:
        st.text_area("Q:", value=question, height=50, disabled=True)
        st.text_area("A:", value=answer, height=100, disabled=True)
