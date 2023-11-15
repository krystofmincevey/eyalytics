import io
import os
import time
import json
import streamlit as st

from dotenv import load_dotenv
from openai import OpenAI
from typing import List
from PIL import Image

from .image import USER_LOGO, ASSISTANT_LOGO


CHAT_KEY = 'start_chat'
CLIENT_KEY = 'client'
MESSAGES_KEY = 'messages'
ASSISTANT_KEY = 'assistant_id'
THREAD_KEY = 'thread_id'
FILE_IDS_KEY = 'file_id_list'

RAG_ASSISTANT_FILE = './data/cwyod/rag_assistant_id.txt'
CODE_ASSISTANT_FILE = './data/cwyod/code_assistant_id.txt'
ACTIONS_FILE = './data/cwyod/required_actions.json'
MESSAGES_FILE = './data/cwyod/messages/messages_{0}.json'
IMAGE_FILE = './data/cwyod/img/image_{0}_{1}.png'
RUN_FILE = './data/cwyod/run_steps/run_steps_{0}.json'
MODEL = 'gpt-4-1106-preview'


load_dotenv()
if not os.getenv("OPENAI_API_KEY"):
    raise KeyError(
        "You will need an OPENAI_API_KEY to use the LLM models in this notebook."
    )


def init_chatbot_session_state():
    st.session_state[CHAT_KEY] = False
    st.session_state[MESSAGES_KEY] = None
    st.session_state[ASSISTANT_KEY] = None
    st.session_state[THREAD_KEY] = None
    st.session_state[FILE_IDS_KEY] = []
    st.session_state[CLIENT_KEY] = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY")
    )


def create_rag_assistant(client):
    if os.path.exists(RAG_ASSISTANT_FILE):
        with open(RAG_ASSISTANT_FILE, 'r') as file:
            assistant_id = file.read().strip()
    else:
        assistant = client.beta.assistants.create(
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

    return assistant_id


# TODO: Create functionality for RAG.
def create_rag_thread(client, file_ids: List[str]):
    thread = client.beta.threads.create(
        messages=[
            {
                "role": "user",
                "content": "Use the provided files to answer user queries.",
                "file_ids": file_ids,
            }
        ]
    )
    return thread.id


def create_analyst_assistant(client):  # TODO add info as input in the future
    if os.path.exists(CODE_ASSISTANT_FILE):
        with open(CODE_ASSISTANT_FILE, 'r') as file:
            assistant_id = file.read().strip()
    else:
        assistant = client.beta.assistants.create(
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

    return assistant_id


def create_analyst_thread(client, file_ids: List[str], info: str):
    thread = client.beta.threads.create(
        messages=[
            {
                "role": "user",
                "content": info[:2000],  # TODO: Improve content fetching
                "file_ids": file_ids,
            }
        ]
    )
    return thread.id


def send_message_and_run_assistant(
        client, thread_id: str, assistant_id: str, user_message: str,
):
    client.beta.threads.messages.create(
        thread_id=thread_id,
        role='user',
        content=user_message,
    )
    run = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assistant_id,
    )
    return run


# Poll the Run status and handle function calls
def poll_run_status(client, thread_id: str, run):
    while True:
        client = st.session_state[CLIENT_KEY]
        run = client.beta.threads.runs.retrieve(
            thread_id=thread_id,
            run_id=run.id
        )
        if run.status in ['completed', 'failed', 'cancelled']:
            break
        elif run.status == 'required_action':
            handle_required_actions(client, thread_id, run)
        else:
            time.sleep(5)
    return run


def handle_required_actions(client, thread_id: str, run):
    required_actions = run.required_action.submit_tool_outputs
    with open(ACTIONS_FILE, 'w') as f:
        required_actions_json = required_actions.model_dump()
        json.dump(required_actions_json, f, indent=4)

    tool_outputs = []
    for action in required_actions.tool_calls:
        func_name = action.function.name
        arguments = json.loads(action.function.arguments)

        # TODO: if you add functions to Analytics assistant remember to add them here!!!
        #  Below we have a placeholder for a sample function.
        if func_name == "do_nothing":
            output = lambda x: arguments['x']
        else:
            raise ValueError(f'Unknown function: {func_name}')

        tool_outputs.append({
            "tool_call_id": action.id,
            "output": output,
        })

    # Submit function call outputs back to the assistant!
    client.beta.threads.runs.sumbit_tool_outputs(
        thread_id=thread_id,
        run_id=run.id,
    )


def process_response(client, thread_id: str, run):
    messages = client.beta.threads.messages.list(
        thread_id=thread_id
    )
    # save messages
    with open(MESSAGES_FILE.format(thread_id), 'w') as f:
        messages_json = messages.model_dump()
        json.dump(messages_json, f, indent=4)

    run_steps = client.beta.threads.runs.steps.list(
        thread_id=thread_id,
        run_id=run.id,
    )
    # save run steps
    with open(RUN_FILE.format(thread_id), 'w') as f:
        run_steps_json = run_steps.model_dump()
        json.dump(run_steps_json, f, indent=4)

    # process message
    image_counter = 0
    updated_messages = []
    assistant_messages_for_run = [
        message for message in messages
        if message.run_id == run.id and message.role == "assistant"
    ]
    for message in reversed(assistant_messages_for_run):
        if message.content:
            citations = []

            for content_part in message.content:
                if content_part.type == 'text':
                    annotations = content_part.text.annotations
                    text_value = content_part.text.value

                    for index, annotation in enumerate(annotations):
                        text_value = text_value.replace(annotations.text, f' [{index}]')
                        if file_citation := getattr(annotation, 'file_citation', None):
                            cited_file = client.files.retrieve(file_citation.file_id)
                            citations.append(f'[{index}] {file_citation.quote} from {cited_file.filename}')

                        elif file_path := getattr(annotation, 'file_path', None):
                            cited_file = client.files.retrieve(file_path.file_id)
                            citations.append(f'[{index}] Click <here> to download {cited_file.filename}')
                            image_file_id = cited_file.id
                            image_data: bytes = client.files.with_raw_response.retrieve_content(image_file_id).content
                            image = Image.open(io.BytesIO(image_data))
                            updated_messages.append({"role": "assistant", "type": "image", "content": image})

                            image.save(IMAGE_FILE.format(image_counter, thread_id))
                            image_counter += 1

                    text_value += '\n' + '\n'.join(citations)
                    updated_messages.append({"role": "assistant", "type": "text", "content": text_value})

                    content_part.text.value = text_value
                elif content_part.type == 'image_file':
                    image_file_id = content_part.image_file.file_id
                    image_data: bytes = client.files.with_raw_response.retrieve_content(image_file_id).content
                    image = Image.open(io.BytesIO(image_data))
                    updated_messages.append({"role": "assistant", "type": "image", "content": image})

                    image.save(IMAGE_FILE.format(image_counter, thread_id))
                    image_counter += 1

    return updated_messages


def display_message(col, message):
    if message["type"] == "text":
        col.markdown(message["content"], unsafe_allow_html=True)  # Using markdown for more flexibility
    elif message["type"] == "image":
        col.image(message["content"])


def chat():
    client = st.session_state[CLIENT_KEY]
    assistant_id = st.session_state[ASSISTANT_KEY]
    thread_id = st.session_state[THREAD_KEY]

    # Display existing messages in the chat
    # Group messages by consecutive roles
    grouped_messages = []
    for message in st.session_state.messages:
        if not grouped_messages or message["role"] != grouped_messages[-1][0]["role"]:
            grouped_messages.append([message])
        else:
            grouped_messages[-1].append(message)

    # Display grouped messages
    for group in grouped_messages:
        with st.container():
            col1, col2 = st.columns([1, 5])  # Adjust the ratio as needed

            # Display the logo for the first message in the group
            if group[0]["role"] == "assistant":
                col1.image(ASSISTANT_LOGO, width=30)
            elif group[0]["role"] == "user":
                col1.image(USER_LOGO, width=30)

            # Display all messages in the group
            for message in group:
                display_message(col2, message)

    # Chat input for the user
    if prompt := st.chat_input("Message BelfiusGPT..."):
        # Add user message to the state and display it
        message = {"role": "user", "type": "text", "content": prompt}
        st.session_state[MESSAGES_KEY].append(
            message
        )
        with st.container():
            col1, col2 = st.columns([1, 5])  # Adjust the ratio as needed
            col1.image(USER_LOGO, width=30)  # Smaller width for icons
            display_message(col2, message)

        run = send_message_and_run_assistant(
            client, thread_id=thread_id,
            assistant_id=assistant_id, user_message=prompt
        )
        run = poll_run_status(client, thread_id=thread_id, run=run)
        messages = process_response(client, thread_id=thread_id, run=run)
        st.session_state[MESSAGES_KEY].extend(messages)

        with st.container():
            col1, col2 = st.columns([1, 5])  # Adjust the ratio as needed
            col1.image(ASSISTANT_LOGO, width=30)  # Smaller width for icons
            for message in messages:
                display_message(col2, message)

# SUDO CODE:
# get_client()
# create_assistant()
# create_thread()
# while True:
#     user_message = input("Enter message:")
#     if user_message.lower() == quit():
#         breakpoint()
#
#     run = send_message_and_run_assistant(user_message)
#     run = poll_run_status(run)
#     display_final_response(run)