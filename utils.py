import datetime
import functools
import json
import os
import time
from functools import reduce

import spacy

nlp = spacy.load('en_core_web_sm')


def similar(text, list_of_texts):
    text_doc = nlp(text)
    text_with_scores = list(map(
        lambda x: {"score": text_doc.similarity(nlp(x)), "text": x}, list_of_texts));
    match = reduce(lambda x, y: x if x['score'] > y['score'] else y, text_with_scores,
                   {"score": 0, "text": ""})
    print("Similar Match:", match, "text:", text, "list:", list_of_texts)
    return match['text']


def timer(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        value = func(*args, **kwargs)
        end_time = time.perf_counter()
        run_time = end_time - start_time
        print("Finished {} in {} secs".format(repr(func.__name__), round(run_time, 3)))
        return value

    return wrapper


def working_dir():
    # Get the current date and time
    now = datetime.datetime.now()

    # Create a string representing the current date and time
    date_time_string = now.strftime("%Y-%m-%d_%H-%M-%S")

    # Create a folder with the current date and time string as the name
    os.mkdir(date_time_string)

    # Print the name of the new folder
    print("Created folder:", date_time_string)

    return date_time_string


def extract_json(text: str) -> dict:
    json_str = text[text.find("{"):text.find("}") + 1]
    try:
        return json.loads(json_str)
    except:
        print("Failed to extract json out of", text)
        return None
