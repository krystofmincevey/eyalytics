import streamlit as st
from utils.csv_agent import (
    csv_tool, ask_agent, decode_response, write_answer
)

st.set_page_config(page_title="👨‍💻 Talk with your CSV")
st.title("👨‍💻 Talk with your CSV")

# st.write("Please upload your CSV file below.")

# data = st.file_uploader("Upload a CSV" , type="csv")

# query = st.text_area("Send a Message")

# if st.button("Submit Query", type="primary"):
#     # Create an agent from the CSV file.
#     agent = csv_tool(data)

#     # Query the agent.
#     response = ask_agent(agent=agent, query=query)

#     # Decode the response.
#     decoded_response = decode_response(response)

#     # Write the response to the Streamlit app.
#     write_answer(decoded_response)
