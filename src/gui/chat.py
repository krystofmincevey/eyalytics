import os
import streamlit as st

from dotenv import load_dotenv
from openai import OpenAI


CHAT_KEY = 'start_chat'
CLIENT_KEY = 'client'
MESSAGES_KEY = 'messages'
ASSISTANT_KEY = 'assistant_id'
THREAD_KEY = 'thread_id'
FILE_IDS_KEY = 'file_id_list'

RAG_ASSISTANT_FILE = './data/rag_assistant_id.txt'
CODE_ASSISTANT_FILE = './data/code_assistant_id.txt'
MODEL = 'gpt-4-1106-preview'


load_dotenv()
if not os.getenv("OPENAI_API_KEY"):
    raise KeyError(
        "You will need an OPENAI_API_KEY to use the LLM models in this notebook."
    )


def init_chatbot_session_state():
    # if CHAT_KEY not in st.session_state:
    st.session_state[CHAT_KEY] = False
    st.session_state[MESSAGES_KEY] = []
    st.session_state[ASSISTANT_KEY] = None
    st.session_state[THREAD_KEY] = None
    st.session_state[FILE_IDS_KEY] = []
    st.session_state[CLIENT_KEY] = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY")
    )


def create_rag_assistant():
    client = st.session_state[CLIENT_KEY]
    if os.path.exists(RAG_ASSISTANT_FILE):
        with open(RAG_ASSISTANT_FILE, 'r') as file:
            assistant_id = file.read().strip()
    else:
        assistant = client.beta.assistant.create(
            name="RAG Assistant",
            description="Information retriever agent",
            instructions="""
            You are tailored to facilitate precise and accurate question answering.
            First use the retriever function to search for
            relevant information to answer user requests. If information 
            is found, cite it with the appropriate source from the document.
            Second, if information is not found in the document, try to think through the question and provide 
            an answer based on knowledge you posses. If you are unable to accurately answer, clearly state 
            that information is not in the document and that are unable to answer with sufficient accuracy.
            Communicate clearly with the user about whether relevant information was found, an answer was 
            provided based on your own knowledge, or if you cannot answer with high accuracy.
            Keep track of the queries that have been asked and the information that was extracted to better
            meet the needs of the user. 
            """,
            tools=[{"type": "retrieval"}],
            model=MODEL,
        )
        assistant_id = assistant.id

        with open(RAG_ASSISTANT_FILE, 'w') as file:
            file.write(assistant_id)

    st.session_state[ASSISTANT_KEY] = assistant_id


# TODO: Create functionality for RAG.
def create_rag_thread():
    client = st.session_state[CLIENT_KEY]
    file_ids = st.session_state[FILE_IDS_KEY]
    thread = client.beta.threads.create(
        messages=[
            {
                "role": "user",
                "content": "Use the provided files to answer user queries.",
                "file_ids": file_ids,
            }
        ]
    )
    st.session_state[THREAD_KEY] = thread.id


def create_analyst_assistant():  # TODO add info as input in the future
    client = st.session_state[CLIENT_KEY]
    if os.path.exists(CODE_ASSISTANT_FILE):
        with open(CODE_ASSISTANT_FILE, 'r') as file:
            assistant_id = file.read().strip()
    else:
        assistant = client.beta.assistant.create(
            name="Analytics Chatbot",
            instructions="""
            You are tailored to facilitate advanced CSV data analysis and 
            visualization within a Streamlit environment. You are to generate Python code 
            for data manipulation and visualization tasks, responding to user queries with precision. 
            You will interact through Streamlit components, offering 
            a dynamic and responsive user experience. You are to uphold a friendly and patient demeanor, 
            actively seeking clarification of ambiguous user requests. You are 
            equipped to incrementally learn from each interaction to improve 
            your ability to satisfy user requests.
            """,
            tools=[{"type": "code_interpreter"}],  # TODO; add custom functions for information retrieval
            model=MODEL,
        )
        assistant_id = assistant.id

        with open(CODE_ASSISTANT_FILE, 'w') as file:
            file.write(assistant_id)

    st.session_state[ASSISTANT_KEY] = assistant_id


def create_analyst_thread(file_path: str, info: str):
    client = st.session_state[CLIENT_KEY]

    file = client.files.create(
        file=open(file_path, "rb"),
        purpose='assistants'
    )
    thread = client.beta.threads.create(
        messages=[
            {
                "role": "user",
                "content": info[:250],  # TODO: Improve content fetching
                "file_ids": [file.id],
            }
        ]
    )
    st.session_state[THREAD_KEY] = thread.id
