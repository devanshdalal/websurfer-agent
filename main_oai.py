import base64
import os
import re

import requests
from playwright.sync_api import sync_playwright

import web_controller
from utils import extract_value

# API request headers
api_key = os.environ['OPENAI_API_KEY']
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {api_key}"
}


def request_body(messages):
    # Construct the payload
    return {
        'model': 'gpt-4-vision-preview',
        'messages': messages,
        'temperature': 0,
        'max_tokens': 2000
    }


# Function to encode the image to base64
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


# Main execution block.
with sync_playwright() as p:
    controller = web_controller.WebController(p)

    # browser.navigate("https://www.smartprix.com")
    # browser.click("Mobiles")

    prompt = "Tell me the name of a smartphone under Rs 25000 from the https://www.smartprix.com?"

    messages = [{
        "role": "system",
        "content": """
            You are a website crawler. You will be given instructions on what to do by browsing. You are connected to a web browser and you will be given the screenshot of the website you are on. The links on the website will be highlighted in red in the screenshot. Always read what is in the screenshot. Be precise and Don't guess link names.

            You can go to a specific URL by answering with the following JSON format:
            {"url": "url goes here"}

            You can click links on the website by referencing the text inside of the link/button, by answering in the following JSON format:
            {"click": "Text in link"}

            Once you are on a URL and you have found the answer to the user's question, you can answer with a regular message.

            Use google search by set a sub-page like 'https://google.com/search?q=search' if applicable. Prefer to use Google for simple queries. If the user provides a direct URL, go to that one. Do not make up links
            """
    }, {
        "role": "user",
        "content": prompt,
    }]

    step_messages = []

    while True:

        print("Sending request...")

        # Make the API request
        payload = request_body(messages + step_messages)
        response = requests.post(url='https://api.openai.com/v1/chat/completions',
                                 headers=headers,
                                 json=payload)

        print("Response from server...")

        # Print the response
        res_text = None
        if response.status_code == 200:
            res_text = response.json()['choices'][0]['message']['content']
            print(res_text)
        else:
            print(f"Error: {response.status_code}, {response.text}")
            break

        urls = re.findall('https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+', res_text)
        if len(urls) > 0:
            controller.navigate(urls[0])
        else:
            link_text = extract_value(res_text, 'click')
            controller.click(link_text=link_text)
        input("Press Enter to continue...")
        img = encode_image("screenshot.jpeg")
        step_messages = [
            {
                "role": "assistant",
                "content": res_text,
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {'url': f'data:image/jpeg;base64,{img}', 'detail': 'low'},
                    },
                    {
                        "type": "text",
                        "text": "Here's the screenshot of the website you are on right now. You can click on links with {\"click\": \"Link text\"} or you can crawl to another URL if this one is incorrect. If you find the answer to the user's question, you can respond normally. Do not make up link names."
                    }
                ]
            }
        ]
