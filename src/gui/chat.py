import tempfile
import streamlit as st
from streamlit_chat import message
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from langchain.document_loaders.csv_loader import CSVLoader
from langchain.vectorstores import FAISS


def init_chatbot_session_state():
    if 'history' not in st.session_state:
        st.session_state['history'] = []
    if 'csv_vectors' not in st.session_state:
        st.session_state['csv_vectors'] = None
    if 'chat_chain' not in st.session_state:
        st.session_state['chat_chain'] = None


def init_chat_chain(csv_file_path, api_key):
    loader = CSVLoader(file_path=csv_file_path, encoding="utf-8")
    data = loader.load()
    embeddings = OpenAIEmbeddings(openai_api_key=api_key)
    vectors = FAISS.from_documents(data, embeddings)
    return ConversationalRetrievalChain.from_llm(
        llm=ChatOpenAI(temperature=0.0, model_name='gpt-3.5-turbo', openai_api_key=api_key),
        retriever=vectors.as_retriever()
    )


def conversational_chat(query, chain):
    result = chain({"question": query, "chat_history": st.session_state['history']})
    st.session_state['history'].append((query, result["answer"]))
    return result["answer"]


def chat_interface():
    user_input = st.text_input("You:", key="user_input")
    if user_input and 'chat_chain' in st.session_state and st.session_state['chat_chain']:
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
        st.session_state['chat_chain'] = init_chat_chain(tmp_file_path, user_api_key)
