import datetime
import functools
import json
import os
import re
import time

ALPHANUMERIC_REGEXP = '[^a-zA-Z0-9 ]'


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


def return_on_failure(value):
    def decorate(f):
        def applicator(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except:
                print('Error')
                return value

        return applicator

    return decorate


def equals(text1: str, text2: str, match_till=20) -> bool:
    if (text1 is None or text2 is None):
        return False

    # Remove all non-alphanumeric characters
    text1 = re.sub('[^a-zA-Z0-9 ]', '', text1)
    text2 = re.sub('[^a-zA-Z0-9 ]', '', text2)

    # Convert both strings to lowercase
    text1 = text1.lower()
    text2 = text2.lower()

    # Truncate the strings to the `matchTill` length.
    text1 = text1[:match_till]
    text2 = text2[:match_till]

    # Perform the exact match comparison if the strings are shorter than 5 characters.
    smaller_length = min(len(text1), len(text2))
    if smaller_length <= 5:
        return text1 == text2

    # Perform a fuzzy comparison based on edit distance.
    return levenshtein_distance(text1, text2) <= 0.1 * smaller_length


def levenshtein_distance(s1, s2):
    """
    Compute the Levenshtein Distance between two strings.

    Parameters:
    s1 (str): The first string.
    s2 (str): The second string.

    Returns:
    int: The Levenshtein Distance between s1 and s2.
    """
    len_s1 = len(s1)  # Length of the first string
    len_s2 = len(s2)  # Length of the second string

    # Initialize a matrix of size (len_s1 + 1) x (len_s2 + 1)
    dp = [[0 for _ in range(len_s2 + 1)] for _ in range(len_s1 + 1)]

    # Initialize the first column and first row of the matrix
    for i in range(len_s1 + 1):
        dp[i][0] = i

    for j in range(len_s2 + 1):
        dp[0][j] = j

    # Compute the Levenshtein distance
    for i in range(1, len_s1 + 1):
        for j in range(1, len_s2 + 1):
            if s1[i - 1] == s2[j - 1]:
                cost = 0
            else:
                cost = 1

            dp[i][j] = min(dp[i - 1][j] + 1,  # Deletion
                           dp[i][j - 1] + 1,  # Insertion
                           dp[i - 1][j - 1] + cost)  # Substitution

    # The Levenshtein distance is found at the bottom-right corner of the matrix
    return dp[len_s1][len_s2]


def working_dir():
    # Get the current date and time
    now = datetime.datetime.now()

    # Create a string representing the current date and time
    date_time_string = now.strftime("%Y-%m-%d_%H-%M-%S")

    wd = 'images/' + date_time_string
    # Create a folder with the current date and time string as the name
    os.mkdir(wd)

    # Print the name of the new folder
    print("Created folder:", wd)

    return wd


def extract_json(text: str) -> dict:
    json_str = text[text.find("{"):text.find("}") + 1]
    try:
        return json.loads(json_str)
    except:
        print("Failed to extract json out of", text)
        return None


def alpha_numeric(text):
    return re.sub(ALPHANUMERIC_REGEXP, '', text)
