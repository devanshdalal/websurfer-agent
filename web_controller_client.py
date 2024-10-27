import json
import os
from time import sleep

import requests
from playwright.sync_api import sync_playwright

import web_controller
from utils import working_dir

API_SERVER = 'http://127.0.0.1:7878'
INSTRUCTIONS_ENDPOINT = f'{API_SERVER}/v2/instructions'

# Main execution block.
with sync_playwright() as p:
    wd = working_dir()
    controller = web_controller.WebController(playwright=p, wd=wd, storage_state='s4.json')

    # prompt = "Tell me a name of any 6 Gb smartphone under Rs 25000 from the https://www.smartprix.com?" # lgtm
    # prompt = "Tell me the name of a Vivo smartphone under Rs 10000 from the https://www.smartprix.com?"  # lgtm
    # prompt = "Find me a biryani restaurant in Karnal city from the https://www.zomato.com/?"  # lgtm, unsatisfactory
    # prompt = "Find me a highest rated restaurant of Karnal city from the https://www.swiggy.com/?"  # Fails
    # prompt = "Tell the name of a derma roller with 192 needles & 1 mm size from the https://www.amazon.in/?"  # lgtm
    # prompt = "Tell the name of a derma roller with 192 needles & 1 mm size from the www.flipkart.com?"  # lgtm
    # prompt = "Tell me the latest order from my amazon account(https://www.amazon.in/)?"  # partial-success
    # prompt = "Tell me which is the most trending open source repository on https://github.com?"
    # prompt = "Tell me what is lowest share price of IRFC in past 6 months?"
    # prompt = "Tell me when is the vidhan sabha 2024 polls in Haryana?"
    # prompt = "Ask chatgpt about names of top 5 most influential applied ai authors of 2024 in Bangalore. website: https://chatgpt.com"  # lgtm
    # prompt = "what is the iqoo z9x price on amazon.in?"  # lgtm, it solves captcha
    # prompt = "Buy me Philips All-in-One Trimmer for Men Phillips Trimmer from amazon.in"
    # prompt = "From https://www.smartprix.com, tell me name of any bike brand name under 100k"
    # prompt = "From https://www.hindustantimes.com, give me top story on 'Games'"
    prompt = """"Create a jira ticket on https://devanshdalal2jira.atlassian.net/jira/servicedesk/projects/ST/queues/custom/1 with the following details:
    summary: Test Customer Service Ticket\n
    description: This is a test ticket for customer service\n
    """

    while True:

        print("Sending request...")

        # Make the API request
        form_data = {}
        if not os.path.isfile(controller.screenshot_path):  # Fist instruction, where only prompt is available
            form_data['prompt'] = (None, prompt)
        else:  # Subsequent instructions with just webpage data
            form_data['screenshot'] = open(controller.screenshot_path, 'rb')
            summary = controller.elements_summaries()
            form_data['element_summaries'] = (None, json.dumps(summary))
        response = requests.post(INSTRUCTIONS_ENDPOINT, files=form_data)

        print("Response from server...")
        # Print the response
        instruction = None
        if response.status_code == 200:
            instruction = response.json()['instructions'][0]
            print(instruction)
        else:
            print(f"Error: {response.status_code}, {response.text}")
            break

        action = instruction['action']
        if action == 'answer':
            print("Answer:", instruction['description'])
            break
        elif action == 'navigate':
            controller.goto(instruction['url'])
        elif action == 'click' or action == 'press':
            link_index = instruction['index']
            controller.click(link_index=link_index)
        elif action == 'scroll':
            controller.down()
        elif action == 'type_input':
            success = controller.type_input(instruction['placeholder'], instruction['text'])

        # controller.__quick_capture()

    # controller.close()
    sleep(20)
    print("Done")
