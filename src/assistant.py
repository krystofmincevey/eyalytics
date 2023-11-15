"""
USEFUL LINKS:
https://www.youtube.com/watch?v=XvIgEY0I-Xg
https://mer.vin/2023/11/openai-assistants-api-code-interpreter/
https://mer.vin/2023/11/openai-assistants-api-function-calling/
https://medium.com/@odhitom09/communicate-with-your-csv-a-guide-to-data-visualization-with-langchain-and-streamlit-fca271a8591c
https://medium.com/prompt-engineering/unleashing-the-power-of-openais-new-gpt-assistants-with-streamlit-83779294629f
"""
import os

from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv


load_dotenv()
if not os.getenv("OPENAI_API_KEY"):
    raise KeyError(
        "You will need an OPENAI_API_KEY to use the LLM models in this notebook."
    )
KEY = os.getenv("OPENAI_API_KEY")

STATUS_COMPLETED = "completed"

client = OpenAI(api_key=KEY)

root_path = Path(__file__).parent.parent
stock_prices = client.files.create(
  file=open(root_path / "data/cwyod/equities/stock_prices.csv", "rb"),
  purpose='assistants'
)
mifid = client.files.create(
  file=open(root_path / "data/cwyod/mifid/mifid_sample.csv", "rb"),
  purpose='assistants'
)

assistant = client.beta.assistants.create(
    name="Belfius Analytics Chatbot",
    instructions="""
        Belfius Analytics Chatbot, an OpenAI Assistant, is tailored to facilitate advanced CSV data analysis and 
        visualization within a Streamlit environment. It generates Python code for data manipulation and visualization 
        tasks, responding to user queries with precision. The assistant interacts through Streamlit components, offering 
        a dynamic and responsive user experience. It upholds a friendly and patient demeanor, actively seeks to clarify 
        ambiguous user requests, and is equipped to incrementally learn from each interaction to improve its 
        performance.
    """,
    tools=[{"type": "code_interpreter"}],
    model="gpt-4-1106-preview",
    # file_ids=[stock_prices.id, mifid.id],
)

thread = client.beta.threads.create(
    messages=[
        {
          "role": "user",
          "content": """
          This table contains historical stock data for US listed companies, detailing:

            Date: Trading day (DD/MM/YYYY).
            Open: Opening stock price in USD.
            High: Highest price of the stock for the day in USD.
            Low: Lowest price of the stock for the day in USD.
            Close: Closing price, adjusted for splits, in USD.
            Adj Close: Adjusted closing price, accounting for splits and dividends, in USD.
            Volume: Total shares traded during the day.
            Ticker: Company's stock ticker symbol (e.g., TSLA, JPM, META).
        
          This compact dataset is ideal for stock performance analysis and investment decision-making.
          """,
          "file_ids": [stock_prices.id]
        }
    ]
)
print(f"Your thread id is - {thread.id}")

run_instructions = f"Please use data from the provided .cvs to answer the users queries."
run = client.beta.threads.runs.create(
    thread_id=thread.id,
    assistant_id=assistant.id,
    instructions=run_instructions,
)
print(f"Your run id is - {run.id}\n")

while True:
    text = input("Input question:\n")

    message = client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=text,
    )

    new_run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant.id,
        instructions=run_instructions,
    )
    print(f"Your new run id is - {new_run.id}")

    status = None
    while status != STATUS_COMPLETED:
        run_list = client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=new_run.id
        )
        print(f"{run_list.status}\r", end="")
        status = run_list.status

    messages = client.beta.threads.messages.list(
        thread_id=thread.id
    )

    print(messages)
    # content = client.files.retrieve_content(file.id)

    print(
        f"{'assistant' if messages.data[0].role == 'assistant' else 'user'} : "
        f"{messages.data[0].content[0].text.value}\n"
    )
