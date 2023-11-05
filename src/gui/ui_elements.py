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

    if not dataset.empty:
        # Check if the filters state exists; if not, initialize it
        if 'filters' not in st.session_state:
            st.session_state['filters'] = {}

        # Reset filters if a new dataset is loaded
        if 'last_dataset' not in st.session_state or st.session_state['last_dataset'] != dataset_key:
            st.session_state['last_dataset'] = dataset_key
            st.session_state['filters'] = {}

        # Dynamically create filters based on dataset columns
        for col in dataset.columns:
            # Skip if the column has too many unique values
            if len(dataset[col].unique()) > 50:
                continue

            # Create a unique key for the multiselect widget
            filter_key = f"{dataset_key}_filter_{col}"

            # Check if a filter already exists in the session state
            default_value = st.session_state['filters'].get(filter_key, [])

            # Define the multiselect filter
            selected = st.multiselect(
                f"Filter by {col}",
                options=dataset[col].unique(),
                default=default_value,
                key=filter_key
            )

            # Save the selected filter values to the session state
            st.session_state['filters'][filter_key] = selected

        # Filter the dataset based on selected filter values
        filtered_data = dataset.copy()
        for col in dataset.columns:
            filter_key = f"{dataset_key}_filter_{col}"
            if filter_key in st.session_state['filters']:
                selected_values = st.session_state['filters'][filter_key]
                if selected_values:
                    filtered_data = filtered_data[filtered_data[col].isin(selected_values)]

        # Display the filtered dataset
        st.dataframe(filtered_data)


def chat_interface():
    st.header("Chat Interface")
    user_question = st.text_input("Ask a question about the data:")
    return user_question


def display_chat_log(chat_log):
    for question, answer in chat_log:
        st.text_area("Q:", value=question, height=50, disabled=True)
        st.text_area("A:", value=answer, height=100, disabled=True)
