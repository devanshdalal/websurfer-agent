import re
from typing import Annotated

import autogen
from autogen import ConversableAgent, AssistantAgent
from playwright.sync_api import sync_playwright

import web_controller

config_list_gpt_4v = autogen.config_list_from_json(
    "OAI_CONFIG_LIST",
    filter_dict={
        "model": ["gpt-4-vision-preview"],
    },
)

config_list_gpt = autogen.config_list_from_json(
    "OAI_CONFIG_LIST",
    filter_dict={
        "model": ["gpt-4", "gpt-4-0314", "gpt-3.5-turbo", "gpt-4-32k", "gpt-4-32k-0314", "gpt-4-32k-v0314"],
    },
)

gpt4_llm_config = {"config_list": config_list_gpt_4v, "cache_seed": 42}

instructions = """You are a website crawler. You will be given instructions on what to do by browsing. You are 
connected to a web browser and you will be given the screenshot of the website you are on. The links on the website 
will be highlighted in red in the screenshot. Always read what is in the screenshot. Don't guess link names. 

You can go to a specific URL by answering with the following JSON format: {"url": "url goes here"}
        
You can click links on the website by referencing the text inside of the link/button, by answering with only the link 
text to click.
            
Once you are on a URL and you have found the answer to the user's question, you can answer with a regular message.
         
Please be PRECISE and DO not make up link texts. Only click on the links that are visible on the image provided.
    """

image_agent = AssistantAgent(
    name="Webpage Navigator",
    max_consecutive_auto_reply=5,
    llm_config={"config_list": config_list_gpt_4v, "temperature": 0, "max_tokens": 1000},
    system_message=instructions
)

user_proxy = ConversableAgent(
    "UserProxy",
    llm_config=False,  # No LLM for this agent.
    human_input_mode="ALWAYS",
    code_execution_config=False,  # No code execution for this agent.
    is_termination_msg=lambda x: x.get("content", "") is not None and "terminate" in x["content"].lower(),
    default_auto_reply="Please continue if not finished, otherwise return 'TERMINATE'.",
)
screenshot = "<img screenshot.jpeg>"

# Main execution block.
with sync_playwright() as p:
    browser = web_controller.WebController(p)


    # browser.navigate("https://www.smartprix.com")
    # browser.click("Mobiles")

    @user_proxy.register_for_execution()
    @image_agent.register_for_llm(description="Perform the cmd requested by llm and return the screenshot.")
    def perform(cmd: Annotated[str, "The response from the model"]) -> str:
        print("cmd from llm", cmd)
        urls = re.findall('https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+', cmd)
        if len(urls) > 0:
            browser.goto(urls[0])
            return "Continue to find the answer to user's question for the screenshot " + screenshot
        elif len(cmd) < 50:
            browser.click(matching_link_text=cmd)
            return "Continue to find the answer to user's question for the screenshot " + screenshot
        return "Please be precise and answer according to:\n" + instructions + screenshot


    user_proxy.initiate_chat(
        image_agent,
        message="""Tell me the name of any smartphone under Rs 25000 from the https://www.smartprix.com?"""
    )
