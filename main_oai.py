import base64
import os

import requests
from playwright.sync_api import sync_playwright

import web_controller
from utils import extract_json, working_dir

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
    wd = working_dir()
    controller = web_controller.WebController(p, wd)

    # prompt = "Tell me a name of any 6 Gb smartphone under Rs 25000 from the https://www.smartprix.com?" # lgtm
    # prompt = "Tell me the name of a Vivo smartphone under Rs 10000 from the https://www.smartprix.com?"  # lgtm
    # prompt = "Find me a biryani restaurant in Karnal city from the https://www.zomato.com/?"  # lgtm, unsatisfactory
    # prompt = "Find me a highest rated restaurant of Karnal city from the https://www.swiggy.com/?"  # Fails
    # prompt = "Tell the name of a derma roller with 192 needles & 1 mm size from the https://www.amazon.in/?"  # lgtm
    # prompt = "Tell the name of a derma roller with 192 needles & 1 mm size from the www.flipkart.com?"  # lgtm
    # prompt = "Tell me the latest order from my amazon account(https://www.amazon.in/)?"  # partial-success
    # prompt = "Tell me which is the most trending open source repository on https://github.com?"  # very good
    # prompt = "Tell me what is lowest share price of IRFC in past 6 months?"  # lgtm
    # prompt = "Tell me when is the lok sabha 2024 polls in Haryana?"  # lgtm
    # prompt = "Ask chatgpt about names of top 5 most influential applied ai authors of 2024 in Bangalore. website: https://chatgpt.com"  # lgtm
    # prompt = "what is the iqoo z9x price on amazon.in?"  # lgtm, it solves captcha
    prompt = "Buy me Philips All-in-One Trimmer for Men Phillips Trimmer from amazon.in"

    messages = [{
        "role": "system",
        "content": """
            You are a website crawler connected to a web browser. Your task is to follow the provided instructions by 
            browsing the web iteratively. You will receive screenshots of the websites you visit, with links highlighted
            in red and search boxes highlighted in green.
            
            **Instructions:** 
            
            1. **Reading Screenshots**: Always start by carefully examining the content of the screenshot provided to
            you. Do not make assumptions about the links or content; rely only on what you see. 

            
            2. **Clicking Links**: 
            Identify links/buttons bounded by red boxes. 
            To click a link, respond in the following JSON format: 
            ```json 
            { "action": "click", "text": "Link Text" }
            ``` 
            Be precise and do not guess link names. 


            3. **Navigating to Specific URLs**: 
            - To go directly to a specific URL, respond with this JSON format: 
            ```json 
            { "action": "navigate", "url": "https://example.com" } 
            ``` 
            
            4. **Typing in Search Boxes**: 
            - To type in a search box bounded by a green box, respond with this JSON format: 
            ```json 
            { "action": "type_input", “placeholder”: “text in input box”, "text": "Search Query" } 
            ``` 
            
            5. **Scrolling Down a Page**: 
            - If you need to scroll down the current webpage, use this JSON format: 
            ```json 
            { "action": "scroll" }
            ``` 
            
            6. **Compiling Results**: 
            - Continue browsing iteratively until you find the answer to the user's question. 
            - Always scroll to the end of the page before compiling your final result. 
            - Once you have found the required information, respond with a regular message containing the answer. 

            O7. **Using Google Search**: 
            - For simple queries, you can set a sub-page like 'https://google.com/search?q=search'. Prefer using Google for such queries. 
            
            8. **Direct URLs**: 
            - If the user provides a direct URL, navigate to it without making up any links. 
            
            **Important Guidelines**: 
            - Always be precise in your actions. 
            - Never guess the link names or content; rely only on provided screenshots. 
            - Ensure to scroll to the end of a webpage before summarizing your findings.

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

        j = extract_json(res_text)
        if j is None:
            print("The final response from llm:", res_text)
            break

        action = j['action']
        if action == 'navigate':
            controller.goto(j['url'])
        elif action == 'click':
            link_text = j['text']
            controller.click(link_text=link_text)
        elif action == 'scroll':
            controller.down()
        elif action == 'type_input':
            success = controller.type_input(j['placeholder'], j['text'])
            if not success:
                controller.try_click_by_text(j['placeholder'])
        # user_input = input("Press Enter to continue...  or type 'q' to quit..")
        # if user_input == 'q':
        #     break
        img = encode_image(os.path.join(wd, "screenshot.jpeg"))
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
                            If you find the answer to the user's question, you can respond normally. Do not make up link/placeholder names."""
                    }
                ]
            }
        ]
    # controller.close()
    print("Done")
