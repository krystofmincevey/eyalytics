import pandas as pd
import streamlit as st


# TODO: For industrialised version make sure these are stored securely!
# Dataset URLs and their headers
SALYTICS_KEY = 'ESG'
MIFID_KEY = 'MIFID'
EMISSIONS_KEY = 'Emissions'

ADMIN_DATASETS = [
    SALYTICS_KEY, MIFID_KEY, EMISSIONS_KEY
]  # Admin sees all datasets
GUEST_DATASETS = [EMISSIONS_KEY, MIFID_KEY]  # Guests see only these datasets

PATHS = {
    SALYTICS_KEY: "./data/cwyod/titanic.csv",
    MIFID_KEY: "./data/cwyod/titanic.csv",
    EMISSIONS_KEY: "./data/cwyod/titanic.csv",
}
INFO = {
    SALYTICS_KEY: "ESG Corporate KPIs: Key Performance Indicators from Sustainalytics for corporate environmental, social, and governance metrics.",
    MIFID_KEY: "MiFID Sustainability Data: Corporate sustainability insights as per the Markets in Financial Instruments Directive.",
    EMISSIONS_KEY: "Client Emissions Data: Measures of Belfius clients' financed emissions.",
}

# Define which datasets are allowed for each type of user
ADMIN_USERS = ['admin']


def init_data_states():
    if 'dataset' not in st.session_state:
        st.session_state['dataset'] = pd.DataFrame()
        st.session_state['dataset_info'] = ""


# Now update the dataset_selection_buttons function to check the session state
def dataset_selection_buttons(allowed_datasets):
    for name in allowed_datasets:
        button_key = f'button_{name}'
        if st.sidebar.button(
                name, key=button_key,
                use_container_width=True,
                type='primary',
        ):
            url, info = PATHS[name], INFO[name]
            dataset = load_data(url)
            st.session_state['dataset_info'] = info
            st.session_state['dataset'] = dataset
            st.session_state['chat_log'] = []
            st.experimental_rerun()


@st.cache_data
def load_data(url):
    data = pd.read_csv(url)
    return data


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
