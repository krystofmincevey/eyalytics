import io
import os
import time
import json
import streamlit as st

from dotenv import load_dotenv
from openai import OpenAI
from typing import List
from PIL import Image, ImageOps, ImageDraw


CHAT_KEY = 'start_chat'
CLIENT_KEY = 'client'
MESSAGES_KEY = 'messages'
ASSISTANT_KEY = 'assistant_id'
THREAD_KEY = 'thread_id'
FILE_IDS_KEY = 'file_id_list'

RAG_ASSISTANT_FILE = './data/rag_assistant_id.txt'
CODE_ASSISTANT_FILE = './data/code_assistant_id.txt'
ACTIONS_FILE = './data/required_actions.json'
MESSAGES_FILE = './data/messages.jsom'
RUN_FILE = './data/run_steps.json'
MODEL = 'gpt-4-1106-preview'


load_dotenv()
if not os.getenv("OPENAI_API_KEY"):
    raise KeyError(
        "You will need an OPENAI_API_KEY to use the LLM models in this notebook."
    )


# Function to create rounded icons
def create_rounded_icon(path, size=(50, 50)):
    img = Image.open(path).resize(size, Image.ANTIALIAS)
    mask = Image.new('L', img.size, 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse((0, 0) + img.size, fill=255)
    img_rounded = ImageOps.fit(img, mask.size, centering=(0.5, 0.5))
    img_rounded.putalpha(mask)
    return img_rounded


# Load and process logos
user_logo = create_rounded_icon('./img/user_logo.png')
assistant_logo = create_rounded_icon('./img/ai_logo_2.png')


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
        json.sump(required_actions_json, f, indent=4)

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
    with open('messages.json', 'w') as f:
        messages_json = messages.model_dump()
        json.dump(messages_json, f, indent=4)

    run_steps = client.beta.threads.runs.steps.list(
        thread_id=thread_id,
        run_id=run.id,
    )
    # save run steps
    with open(RUN_FILE, 'w') as f:
        run_steps_json = run_steps.model_dump()
        json.dump(run_steps_json, f, indent=4)

    # process message
    image_counter = 0
    updated_messages = []
    for message in messages.data:
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
                            image.save(f'./data/cwyod/img/image_{image_counter}.png')
                            image_counter += 1

                    text_value += '\n' + '\n'.join(citations)
                    content_part.text.value = text_value
                elif content_part.type == 'image_file':
                    image_file_id = content_part.image_file.file_id
                    image_data: bytes = client.files.with_raw_response.retrieve_content(image_file_id).content
                    image = Image.open(io.BytesIO(image_data))
                    image.save(f'./data/cwyod/img/image_{image_counter}.png')
                    image_counter += 1
            updated_messages.append(message)

    return updated_messages


def display_message(message):
    st.write(message["role"].capitalize())
    if message["type"] == "text":
        st.markdown(message["content"])  # Using markdown for more flexibility
    elif message["type"] == "image":
        st.image(message["content"])


def chat():
    # Display existing messages in the chat
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Display chat messages
    for message in st.session_state.messages:
        with st.container():
            st.write(message["role"].capitalize())
            if message["type"] == "text":
                st.text(message["content"])
            elif message["type"] == "image":
                st.image(message["content"])

    # Chat input for the user
    if prompt := st.chat_input("What is up?"):
        # Add user message to the state and display it
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Add the user's message to the existing thread
        client.beta.threads.messages.create(
            thread_id=st.session_state.thread_id,
            role="user",
            content=prompt
        )

        # Create a run with additional instructions
        run = client.beta.threads.runs.create(
            thread_id=st.session_state.thread_id,
            assistant_id=assistant_id,
            instructions="Please answer the queries using the knowledge provided in the files.When adding other information mark it clearly as such.with a different color"
        )

        # Poll for the run to complete and retrieve the assistant's messages
        while run.status != 'completed':
            time.sleep(1)
            run = client.beta.threads.runs.retrieve(
                thread_id=st.session_state.thread_id,
                run_id=run.id
            )

        # Retrieve messages added by the assistant
        messages = client.beta.threads.messages.list(
            thread_id=st.session_state.thread_id
        )

        # Process and display assistant messages
        assistant_messages_for_run = [
            message for message in messages
            if message.run_id == run.id and message.role == "assistant"
        ]
        for message in assistant_messages_for_run:
            full_response = process_message_with_citations(message)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            with st.chat_message("assistant"):
                st.markdown(full_response, unsafe_allow_html=True)


def process_message_with_citations(message):
    """Extract content and annotations from the message and format citations as footnotes."""
    message_content = message.content[0].text
    annotations = message_content.annotations if hasattr(message_content, 'annotations') else []
    citations = []

    # Iterate over the annotations and add footnotes
    for index, annotation in enumerate(annotations):
        # Replace the text with a footnote
        message_content.value = message_content.value.replace(annotation.text, f' [{index + 1}]')

        # Gather citations based on annotation attributes
        if (file_citation := getattr(annotation, 'file_citation', None)):
            # Retrieve the cited file details (dummy response here since we can't call OpenAI)
            cited_file = {'filename': 'cited_document.pdf'}  # This should be replaced with actual file retrieval
            citations.append(f'[{index + 1}] {file_citation.quote} from {cited_file["filename"]}')
        elif (file_path := getattr(annotation, 'file_path', None)):
            # Placeholder for file download citation
            cited_file = {'filename': 'downloaded_document.pdf'}  # This should be replaced with actual file retrieval
            citations.append(f'[{index + 1}] Click [here](#) to download {cited_file["filename"]}')  # The download link should be replaced with the actual download path

    # Add footnotes to the end of the message content
    full_response = message_content.value + '\n\n' + '\n'.join(citations)
    return full_response


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
