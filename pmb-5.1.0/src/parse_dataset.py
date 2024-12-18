from ccg.read_ccg import extract_inference_tree, parse_prolog_to_dict
import os
import re

dataset_path = "/Users/paulhe/Desktop/CCG Parsing/pmb-5.1.0/src/ccg/standard"


def extract_words_and_categories(data):
    """
    Recursively extracts words and their categories from a nested structure.
    Handles lists and dictionaries with keys like 't'.

    :param data: Nested input dictionary or list.
    :return: A list of tuples (word, category) in order.
    """
    results = []

    def traverse(node):
        # If node is a dictionary, check for key 't' and recurse into values
        if isinstance(node, dict):
            if 't' in node:  # If 't' exists, extract word and category
                t_list = node['t']
                if len(t_list) > 1:  # Ensure it's valid
                    category = t_list[0]
                    word = t_list[1]
                    results.append((word, category))
            for key, value in node.items():  # Traverse all dictionary values
                traverse(value)

        # If node is a list, traverse each element
        elif isinstance(node, list):
            for item in node:
                traverse(item)

    # Start traversal
    traverse(data)
    return results



for root, dirs, files in os.walk(dataset_path):
    for file in files:
        # print(file)
        if file.endswith(".ccg"):
            file_path = os.path.join(root, file)
            with open(file_path, "r") as f:
                prolog_code = f.read()
                start_idx = prolog_code.find('ccg(')
                prolog_code = prolog_code[start_idx:]
                match = re.search(r'ccg\(.*', prolog_code, re.DOTALL)
                if match and 'lx' not in match.group(0):
                    print(prolog_code)
                    parsed_result = parse_prolog_to_dict(prolog_code)
                    lexicon = extract_words_and_categories(parsed_result)
                    print(lexicon)
                    lexicon = {word: category for word, category in lexicon}
                    print(lexicon)


