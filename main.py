import os                               # for accessing environment variables
import chainlit as cl                   # Web UI framework for chat applicatio
from dotenv import load_dotenv          # for loading environment variables
from typing import Optional, Dict       # type hints for better code readability
from agents import Agent, Runner, AsyncOpenAI, OpenAIChatCompletionsModel
from agents.tool import function_tool
import requests

# load environment variables from .env file
load_dotenv()

gemini_api_key = os.getenv("GEMINI_API_KEY")

# Initialize OpenAI provider with Gemini API setting
provider = AsyncOpenAI(
    api_key=gemini_api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai",
)

# configure the language model
model = OpenAIChatCompletionsModel(
    model="gemini-2.0-flash",
    openai_client=provider
)

@function_tool("get_weather")
def get_weather(Location: str, unit: str = "C") -> str:
    """
    Get the weather for a given location, return the weather
    """
    return f"The weather is {Location} is 22 degrees {unit}"

agent = Agent(
    name="Greeting Agent",
    instructions="""You are a Greeting Agent designed to provide friendly interactions and information about weather.
    Your task is to greet the user with a friendly message, when someone says Hi you have to reply back with Salam 
    from Mahnoor Khalid, if someone says Bye then reply Allah Hafiz from Mahnoor Khalid, and if someone asks about 
    weather then use the get_weather tool to get weather. When someone asks other than greeting and weather then say 
    I'm only able to provide greetings. I can't answer other questions at this time, sorry.

    Always maintain a friendly, professional tone and ensure responses are helpful within your defined scope.""",
    model=model,
    tools=[get_weather],
)

# decorator to handle OAuth callback from GitHub
@cl.oauth_callback
def oauth_callback(
    provider_id: str,               # ID of thhe OAuth provider (GitHub)
    token: str,                     # OAuth token   
    raw_user_data: Dict[str, str],  # default user object from chainlit
    default_user: cl.User,          # return User object or None
)-> Optional[cl.User]:
    """
    Handle the OAuth callback from GitHub
    Return the user object if authentication is successful, None otherwise
    """
    print(f"Provider: {provider_id}")        # print the provider ID for debugging
    print(f"User data: {raw_user_data}")    # print the user data for debugging

    return default_user                     # return the default user object

# Handler for when a new chat session starts
@cl.on_chat_start
async def handle_chat_start():

    cl.user_session.set("history", [])    # initialize the chat history as an empty list
    await cl.Message(
        content="Hello! How can I help you today?"
    ).send()

# Handler for incoming chat messages
@cl.on_message
async def handle_message(message: cl.Message):

    history = cl.user_session.get("history")            # get the chat history from the user session
    history.append(
        {"role": "user", "content": message.content}
    )                                                   # add user message to history
    
    result = await cl.make_async(Runner.run_sync)(agent, input=history)

    response_text = result.final_output
    await cl.Message(content=response_text).send()

    history.append(
        {"role": "assistant", "content": response_text}
        )
    cl.user_session.set("history", history)