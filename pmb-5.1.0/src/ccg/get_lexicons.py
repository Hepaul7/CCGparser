import re
from fast_ccg import fast_ccg
import os
import string


def remove_features(input_str):
    result = []
    i = 0
    while i < len(input_str):
        if input_str[i:i+2] == "s:":
            # Add just "s" and skip over the feature part until we hit a '/' or ')'
            result.append("s")
            i += 2  # Skip over "s:"
            while i < len(input_str) and input_str[i] not in ['/','(',')', '\\']:
                i += 1
        else:
            result.append(input_str[i])
            i += 1
    return ''.join(result)

def parse_ccg_structure(ccg_text):
    ccg_entries = []
    pattern_token = r"t\((.*?), '(.*?)', \[(.*?)\]\)"
    lines = ccg_text.splitlines()
    for line in lines:
        token_match = re.search(pattern_token, line)
        if token_match:
            category, word, features = token_match.groups()
            cat_no_feature = remove_features(re.sub(r'[()]', '', category))
            ccg_entries.append((word, cat_no_feature.upper()))
    return ccg_entries

def human_readable_format_simple(ccg_entries):
    output = []
    for word, category in ccg_entries:

        cat_no_feature = re.sub(r's:[^/()]+', 's', category)
        output.append(f"{word} := {cat_no_feature.upper()}")
    return "\n".join(output)

def human_readable_format_tree(ccg_entries):
    tree_output = []
    stack = []
    for entry in ccg_entries:
        if entry['type'] == 'token':
            stack.append(entry['word'])
            tree_output.append(f"Token: '{entry['word']}', CCG Category: {entry['category']}")
        elif entry['type'] == 'combinator':
            if len(stack) >= 2:
                right_child = stack.pop()
                left_child = stack.pop()
                combined_category = entry['category']
                tree_output.append(f"Combining: {left_child} and {right_child} -> {combined_category}")
                stack.append(combined_category)
    return "\n".join(tree_output)

# ccg_text = r"""
# #  ccg(1,
# #  ba(s:dcl,
# #   fa(np,
# #    t(np/n, 'A', [lemma:'a', from:0, to:1, pos:'DT', sem:'DIS', wordnet:'O']),
# #    t(n, 'boy', [lemma:'boy', from:2, to:5, pos:'NN', sem:'CON', wordnet:'boy.n.01'])),
# #   fa(s:dcl\np,
# #    t((s:dcl\np)/(s:ng\np), 'is', [lemma:'be', from:6, to:8, pos:'VBZ', sem:'NOW', wordnet:'O']),
# #    fa(s:ng\np,
# #     t((s:ng\np)/np, 'styling', [lemma:'style', from:9, to:16, pos:'VBG', sem:'EXG', wordnet:'style.v.02', verbnet:['Patient','Agent']]),
# #     fa(np,
# #      t(np/n, 'his', [lemma:'male', from:17, to:20, pos:'PRP$', sem:'HAS', wordnet:'male.n.02', verbnet:['PartOf'], antecedent:'2,5']),
# #      t(n, 'hair', [lemma:'hair', from:21, to:25, pos:'NN', sem:'CON', wordnet:'hair.n.01'])))))).
# # """
# ccg_entries_simple = parse_ccg_structure(ccg_text)
# lexicon = {x:y for x, y in ccg_entries_simple}
# # lexicon = {word: category.replace('(', '').replace(')', '') for word, category in lexicon.items()}
# input_tokens = [x[0] for x in ccg_entries_simple]
# print(lexicon)
# print(input_tokens)

# print(fast_ccg(lexicon, input_tokens))

# # human_readable_output_simple = human_readable_format_simple(ccg_entries_simple)
# # print(ccg_entries_simple)

directory_path = "/Users/paulhe/Desktop/CCG Parsing/pmb-5.1.0/src/ccg/standard"
count = 0
total = 0
kulhmann_count = 0
for root, dirs, files in os.walk(directory_path):
    # print(files)
    for file in files:
        # print(file)
        if file.endswith(".ccg"):
            print(file)
            total += 1
            kulhmann_count += 1
            # print('ok', all_function_types)
            file_path = os.path.join(root, file)
            with open(file_path, "r") as f:
                prolog_code = f.read()
                match = re.search(r'ccg\(.*', prolog_code, re.DOTALL)
                if match and 'lx' not in match.group(0):
                    count += 1
                    result = match.group(0)
                    ccg_entries_simple = parse_ccg_structure(result)
                    lexicon = {x:y for x, y in ccg_entries_simple}
                    input_tokens = [x[0] for x in ccg_entries_simple if x[0] not in string.punctuation]
                    print(fast_ccg(lexicon, input_tokens))
                    print('KULMANN COUNT', kulhmann_count)
