import pandas as pd
import streamlit as st


# Function to load data
@st.experimental_memo
def load_data(url):
    data = pd.read_csv(url)
    return data
