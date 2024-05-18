import base64
import os

import requests
from playwright.sync_api import sync_playwright

import web_controller
from utils import extract_json

SCROLL_JSON_EXPR = """{"scroll": "down"}"""

SEARCH_JSON_EXPR = """{"placeholder": "text visible in the search box", "text": "text to type in the search box"}"""

CLICK_JSON_EXPR = """{"click": "Text in link"}"""

GOTO_JSON_EXPR = """{"url": "url goes here"}"""

api_key = os.environ['OPENAI_API_KEY']
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {api_key}"
}


def request_body(messages):
    # Construct the payload
    return {
        'model': 'gpt-4o',
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

    prompt = "Tell me a name of a 6 Gb smartphone under Rs 25000 from the https://www.smartprix.com?"
    # prompt = "Tell me the name of a Vivo smartphone under Rs 10000 from the https://www.smartprix.com?"
    # prompt = "Find me a biryani restaurant in Karnal city from the https://www.zomato.com/?"

    messages = [{
        "role": "system",
        "content": """
            You are a website crawler. You will be given instructions on what to do by browsing. You are connected to a web browser and you will be given the screenshot of the website you are on. The links on the website will be highlighted in red in the screenshot. Always read what is in the screenshot. Be precise and Don't guess link names.
            
            You can click links on the website by referencing the text inside of the link/button bounded by a red box in the screenshot.
            by answering in the following JSON format:
            % s
            
            You can go to a specific URL by answering with the following JSON format:
            %s
            
            You can type in the search box bounded by a green box in the screenshot by answering with the following JSON format:
            %s
            
            You can go to a scroll down a page on current website by answering with the following JSON format:
            %s

            Once you are on a URL and you have found the answer to the user's question, you can answer with a regular message.
                   
           Use google search by set a sub-page like 'https://google.com/search?q=search' if applicable. Prefer to use Google for simple queries. If the user provides a direct URL, go to that one. Do not make up links
           """ % (CLICK_JSON_EXPR, GOTO_JSON_EXPR, SEARCH_JSON_EXPR, SCROLL_JSON_EXPR)
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

        j = extract_json(res_text)

        if 'url' in j:
            controller.goto(j['url'])
        elif 'click' in j:
            link_text = j['click']
            controller.click(link_text=link_text)
        elif 'scroll' in j:
            controller.down()
        elif 'placeholder' in j:
            controller.fill_input(j['placeholder'], j['text'])
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
                        "image_url": {'url': f'data:image/jpeg;base64,{img}', 'detail': 'auto'},
                    },
                    {
                        "type": "text",
                        "text":
                            """Here's the screenshot of the website you are on right now. 
                            Possible commands are:
                            """
                            + GOTO_JSON_EXPR + "\n"
                            + CLICK_JSON_EXPR + "\n"
                            + SEARCH_JSON_EXPR + "\n"
                            + SCROLL_JSON_EXPR + "\n" +
                            """
                            If you find the answer to the user's question, you can respond normally. Do not make up link names."""
                    }
                ]
            }
        ]
