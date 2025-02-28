from typing import List, Union, Generator, Iterator
from schemas import OpenAIChatMessage
import subprocess

# Import relevant functionality
from langchain_ollama import ChatOllama
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.messages import HumanMessage, trim_messages
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import StructuredTool

import os
from typing import Annotated
# from rich.console import Console
# from rich.markdown import Markdown


import os
import requests
import json


SPOTIFY_TOOL_URL = "http://tools_api:8000/spotify/"

SPOTIFY_URL_API = "https://api.spotify.com/v1/"

access_token = "BQB1XbiT_BxRsBn3wt29Q4lIxKB9KO-Fl3_17fVXOrmyMaB2HR7E9SRtMDT_sw2hGuo3VIPSrV_kIU5MedBOYatZNlwA2WqYduOeuD3Dd0qChlQgQ_WRJ2v9DQ-0vgi613FOmH_Aspuxhci4gknrBwXUJFlUeixh4nBdPldqzHAK3ZyL3h1PgdJyCHR5-RDGAbD6atsqRycLkKaljfdRyn1H7x7lbDntfjWDoLQj0G52tzk"

def get_auth_url():
    return requests.get(SPOTIFY_TOOL_URL + "login_url").json()["login_url"]

def get_access_token():
    response = requests.get(SPOTIFY_TOOL_URL + "token").json()
    if "error" in response:
        raise Exception(f'Error: {response["error"]}')
    access_token = response["access_token"]
    return access_token

def search_tracks(query:str) -> list[str]:
    """Search for tracks on Spotify with the given query.

    Args:
        query (str): The search query to use.

    Raises:
        Exception: If the Spotify API returns an error, this function raises an exception with the error message.

    Returns:
        str: A JSON string containing the search results. 
    """
    params = {"q": query, "type": "track", "market" : "US", "limit" : 5}
    response = requests.get(SPOTIFY_URL_API + "search", headers={'Authorization': f'Bearer {access_token}'}, params = params).json()
    if "error" in response:
        raise Exception(f'Error: {response["error"]}')
    
    result = []
    for item in response["tracks"]["items"]:
        artist = []
        for a in item["artists"]:
            artist.append(a["name"])
        result.append({"title" : item["name"], "artist" : str.join(", ", artist), "album" : item["album"]["name"], "uri" : item["uri"]})
    return result

def queue_track(uri: str) -> str:
    """Queue a track for playback on Spotify.

    Args:
        uri (str): The Spotify URI for the track to queue.
    
    Raises:
        Exception: If the Spotify API returns an error, this function raises an exception with the error message.

    Returns:
        str: A success message if the track was queued successfully.
    """
    response = requests.post(SPOTIFY_URL_API + "me/player/queue", headers={'Authorization': f'Bearer  {access_token}'}, params = {"uri": uri})
    if response.status_code != 200:
        raise Exception(f'Error: {response.status_code}')
    return "Track queued successfully."


def spotify_tools():
    search_tool = StructuredTool.from_function(search_tracks, name="search_tracks", parse_docstring=True)
    queue_tool = StructuredTool.from_function(queue_track, name="queue_track", parse_docstring=True)
    return [search_tool, queue_tool]

class Pipeline:
    def __init__(self):
        # Optionally, you can set the id and name of the pipeline.
        # Best practice is to not specify the id so that it can be automatically inferred from the filename, so that users can install multiple versions of the same pipeline.
        # The identifier must be unique across all pipelines.
        # The identifier must be an alphanumeric string that can include underscores or hyphens. It cannot contain spaces, special characters, slashes, or backslashes.
        # self.id = "python_code_pipeline"
        self.name = "Tool User Pipeline"
        pass

    async def on_startup(self):
        # This function is called when the server is started.
        os.environ["TAVILY_API_KEY"] = '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'

        memory = MemorySaver()
        model = ChatOllama(base_url="http://ollama:11434", model="mistral-nemo")
        trimmer = trim_messages(max_tokens=25,strategy="last",token_counter=model,include_system=True,allow_partial=False,start_on="human",)
        search = TavilySearchResults(max_results=2)

        tools = [search] + spotify_tools()

        self.agent_executor = create_react_agent(model, tools, checkpointer=memory, messages_modifier=trimmer)
        # Use the agent
        self.config = {"configurable": {"thread_id": "abc123"}}
        print("Agent Started.")
        print(f"on_startup:{__name__}")
        pass

    async def on_shutdown(self):
        # This function is called when the server is stopped.
        print(f"on_shutdown:{__name__}")
        pass

    def pipe(
        self, user_message: str, model_id: str, messages: List[dict], body: dict
    ) -> Union[str, Generator, Iterator]:
        # This is where you can add your custom pipelines like RAG.
        try:
            get_access_token()
        except:
            yield "Access token not found.\n"
            yield "Login to continue.\n"
            yield get_auth_url() + "\n"
            get_access_token()
             
        if body.get("title", False):
            print("Title Generation")
            return "Python Code Pipeline"
        else:
            for chunk in self.agent_executor.stream({"messages": [HumanMessage(content=messages[-1]["content"])]}, self.config):
                if 'agent' in chunk:
                    for message in chunk['agent']['messages']:
                        if message.content:
                            yield message.content
                        if message.tool_calls:
                            for tool in message.tool_calls:
                                yield f"tool -> {tool['name']} {tool['args']}\n"