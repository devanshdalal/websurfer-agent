import base64
import os

import requests
from playwright.sync_api import sync_playwright

import web_controller
from utils import extract_json

SCROLL_JSON_EXPR = """{"scroll": "down"}"""

SEARCH_JSON_EXPR = """{"placeholder": "text visible in input box", "text": "text to type in input box"}"""

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
    # work_dir = working_dir()

    # prompt = "Tell me a name of any 6 Gb smartphone under Rs 25000 from the https://www.smartprix.com?" # lgtm
    # prompt = "Tell me the name of a Vivo smartphone under Rs 10000 from the https://www.smartprix.com?" # lgtm
    # prompt = "Find me a biryani restaurant in Karnal city from the https://www.zomato.com/?"  # lgtm, unsatisfactory
    # prompt = "Find me a highest rated restaurant of Karnal city from the https://www.swiggy.com/?"  # Fails
    # prompt = "Tell the name of a derma roller with 192 needles & 1 mm size from the https://www.amazon.in/?"  # lgtm
    # prompt = "Tell the name of a derma roller with 192 needles & 1 mm size from the www.flipkart.com?"  # lgtm
    prompt = "Tell me the latest order from my amazon account(https://www.amazon.in/)?"  # fails?
    # prompt = "Tell me which is the most trending open source repository on https://github.com?"  # scary
    # prompt = "Tell me what is current share price of IRFC using yahoo finance?"  # lgtm
    # prompt = "Tell me when is the lok sabha 2024 polls in Haryana?"  # not good

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
            
            If required, you should scroll down a page on current website by answering with the following JSON format:
            %s

            Once you are on a URL and you have found the answer to the user's question, you can answer with a regular message.
                   
            Use google search by set a sub-page like 'https://google.com/search?q=search' if applicable. Prefer to use Google for simple queries.
            If the user provides a direct URL, go to that one. Do not make up links. 
            Always scroll to the end of the page before compiling your final result. 
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
        if j is None:
            print("Failed to extract json out of", res_text)
            break

        if 'url' in j:
            controller.goto(j['url'])
        elif 'click' in j:
            link_text = j['click']
            controller.click(link_text=link_text)
        elif 'scroll' in j:
            controller.down()
        elif 'placeholder' in j:
            success = controller.type_input(j['placeholder'], j['text'])
            if not success:
                controller.try_click_by_text(j['placeholder'])
        user_input = input("Press Enter to continue...  or type 'q' to quit..")
        if user_input == 'q':
            break
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
    controller.close()
    print("Done")
