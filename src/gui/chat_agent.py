import tempfile
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from streamlit_chat import message
from langchain.llms.openai import OpenAI
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent


def init_agent_session_state():
    if 'pandas_agent' not in st.session_state:
        st.session_state['pandas_agent'] = None
    if 'chat_log' not in st.session_state:
        st.session_state['chat_log'] = None


def init_pandas_agent(csv_file_path, api_key):
    df = pd.read_csv(csv_file_path)
    pandas_agent = create_pandas_dataframe_agent(
        llm=OpenAI(temperature=0.0, model_name='gpt-3.5-turbo', openai_api_key=api_key),
        df = df,
        verbose=True
    )
    return pandas_agent


def run_agent(query, agent):
    result = agent.run(query)
    return result["answer"]


def chat_interface():
    user_input = st.text_input("You:", key="user_input")
    if user_input and 'pandas_agent' in st.session_state and st.session_state['pandas_agent']:
        return user_input
    return None


def display_chat_log():
    if st.session_state['chat_log']:
        for user_text, bot_response in st.session_state['chat_log']:
            message(user_text, is_user=True)
            message(bot_response)



def setup_sidebar():
    user_api_key = st.sidebar.text_input("Your OpenAI API key", type="password")
    uploaded_file = st.sidebar.file_uploader("Upload CSV", type="csv")

    if uploaded_file and user_api_key:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_file_path = tmp_file.name
        st.session_state['pandas_agent'] = init_pandas_agent(tmp_file_path, user_api_key)
