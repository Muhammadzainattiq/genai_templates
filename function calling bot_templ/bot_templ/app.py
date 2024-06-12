import json
import streamlit as st
from streamlit_chat import message
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from itertools import zip_longest
from IPython.display import display
from IPython.display import Markdown
import textwrap
def to_markdown(text):
  text = text.replace('•', '  *')
  return Markdown(textwrap.indent(text, '> ', predicate=lambda _: True))


openapi_key = st.secrets["OPENAI_API_KEY"]

# Set streamlit page configuration
st.set_page_config(page_title="Weather Teller")
st.markdown(
    """
    <style>
    .custom-title {
        color: white; /* Text color */
        font-size: 50px;
        font-weight: bold;
        text-align: center;
        background-color: purple; /* Background color */
        padding: 1px; /* Padding around the text */
        border-radius: 10px; /* Rounded corners (optional) */
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Use the custom CSS class for the title
st.markdown('<p class="custom-title">Weather Teller</p>', unsafe_allow_html=True)

# Initialize session state variables
if 'entered_prompt' not in st.session_state:
    st.session_state['entered_prompt'] = ""  # Store the latest user input

if 'generated' not in st.session_state:
    st.session_state['generated'] = []  # Store AI generated responses

if 'past' not in st.session_state:
    st.session_state['past'] = []  # Store past user inputs

# Define function to submit user input
def submit():
    # Set entered_prompt to the current value of prompt_input
    st.session_state.entered_prompt = st.session_state.prompt_input
    # Clear prompt_input
    st.session_state.prompt_input = ""

# Example dummy function hard coded to return the same weather
# In production, this could be your backend API or an external API
@tool
def get_current_weather(location:str, unit:str="fahrenheit")->str:
    """Get the current weather in a given location"""
    if "tokyo" in location.lower():
        return json.dumps({"location": "Tokyo", "temperature": "10", "unit": "celsius"})
    elif "san francisco" in location.lower():
        return json.dumps({"location": "San Francisco", "temperature": "72", "unit": "fahrenheit"})
    elif "paris" in location.lower():
        return json.dumps({"location": "Paris", "temperature": "22", "unit": "celsius"})
    else:
        return json.dumps({"location": location, "temperature": "unknown"})

# Initialize the ChatOpenAI model with tools
tools = [get_current_weather]
chat = ChatOpenAI(
    temperature=0.5,
    model_name="gpt-3.5-turbo-0125",
    openai_api_key=openapi_key,
    max_tokens=100
)

chat_with_tools = chat.bind_tools(tools)

# chat_with_tools_always = chat.bind_tools(tools, tool_choice="get_current_weather")this is if you want to make it compulsory to use a tool for the llm
def build_message_list():
    """
    Build a list of messages including system, human and AI messages.
    """
    # Start zipped_messages with the SystemMessage
    zipped_messages = [SystemMessage(
        content = """you're a helpful assistant."""
    )]

    # Zip together the past and generated messages
    for human_msg, ai_msg in zip_longest(st.session_state['past'], st.session_state['generated']):
        if human_msg is not None:
            zipped_messages.append(HumanMessage(
                content=human_msg))  # Add user messages
        if ai_msg is not None:
            zipped_messages.append(
                AIMessage(content=ai_msg))  # Add AI messages

    return zipped_messages

def generate_response():
    """
    Generate AI response using the ChatOpenAI model.
    """
    # Build the list of messages
    messages = build_message_list()

    # Generate response using the chat model
    ai_response = chat_with_tools.invoke(messages)
    messages.append(ai_response)
    # Handle tool calls if any
    for tool_call in ai_response.tool_calls:
        selected_tool = {"get_current_weather": get_current_weather}[tool_call["name"].lower()]
        tool_output = selected_tool.invoke(tool_call["args"])
        messages.append(ToolMessage(tool_output, tool_call_id=tool_call["id"]))

    response = chat_with_tools.invoke(messages)
    response = response.content
    return response

# Create a text input for user
st.text_input('YOU: ', key='prompt_input', on_change=submit)

if st.session_state.entered_prompt != "":
    # Get user query
    user_query = st.session_state.entered_prompt

    # Append user query to past queries
    st.session_state.past.append(user_query)

    # Generate response
    output = generate_response()

    # Append AI response to generated responses
    st.session_state.generated.append(output)

# Display the chat history
if st.session_state['generated']:
    for i in range(len(st.session_state['generated'])-1, -1, -1):
        # Display AI response
        message(st.session_state["generated"][i], key=str(i))
        # Display user message
        message(st.session_state['past'][i],
                is_user=True, key=str(i) + '_user')


