import functools
import json
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


def extract_value(text: str, key: str):
    if (key in text):
        try:
            j = json.loads(text)
            return j[key]
        except:
            print("Failed to extract key:", key, 'from', text)
    return text
