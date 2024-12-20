import re
from fast_ccg import fast_ccg
from ccg import cky_parse 
import os
import string
import matplotlib.pyplot as plt
from collections import defaultdict
import time
import numpy as np


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



all_paths = ["/Users/paulhe/Desktop/CCG Parsing/pmb-5.1.0/src/ccg/standard", 
             "/Users/paulhe/Desktop/CCG Parsing/pmb-5.1.0/src/ccg/de_ccg",
             "/Users/paulhe/Desktop/CCG Parsing/pmb-5.1.0/src/ccg/it_ccg"]


count = 0
total = 0
kulhmann_count = 0
mapping_language = {0: 'en', 1: 'de', 2:'it'}
lx_rules = {'en': 0, 'de': 0, 'it': 0}
total_per_lan = {'en': 0, 'de': 0, 'it': 0}
kulhmann_per_lan = {'en': 0, 'de': 0, 'it': 0}

total_edges_per_lan = {'en': 0, 'de': 0, 'it': 0}
kulhmann_edges_per_lan = {'en': 0, 'de': 0, 'it': 0}

derivation_length_en = defaultdict(int)
derivation_length_de = defaultdict(int)
derivation_length_it = defaultdict(int)
derivation_length_time = defaultdict(list)
naive_derivation_time = defaultdict(list)


total_edges, kulhmann_edges = 0, 0
derivation_length_time = defaultdict(int)
naive_derivation_time = defaultdict(int)

mismatched_parses = 0
mismatched_km = 0

for idx in range(len(all_paths)):
    directory_path = all_paths[idx]
    for root, dirs, files in os.walk(directory_path):
        # print(files)
        for file in files:
            # print(file)
            if file.endswith(".ccg"):
                # print(file)
                total += 1
                total_per_lan[mapping_language[idx]] += 1
                
                # print('ok', all_function_types)
                file_path = os.path.join(root, file)
                with open(file_path, "r") as f:
                    prolog_code = f.read()
                    match = re.search(r'ccg\(.*', prolog_code, re.DOTALL)
                    if match and 'lx' not in prolog_code:
                        # if file == 'p74_d1790.ccg':
                        #     print(prolog_code)
                        #     print(match.group(0))
                        count += 1
                        result = match.group(0)
                        ccg_entries_simple = parse_ccg_structure(result)
                        lexicon = {x:y for x, y in ccg_entries_simple}
                        input_tokens = [x[0] for x in ccg_entries_simple if x[0] not in string.punctuation]

                        start_time = time.time()
                        num_parses, chart, num_edges, num_km_edges = fast_ccg(lexicon, input_tokens)
                        end_time = time.time()
                        total_edges += num_edges
                        kulhmann_edges += num_km_edges
                        
                        elapsed_time = end_time - start_time
                        # derivation_length_time[len(lexicon)].append(elapsed_time)
                        derivation_length_time[file] = elapsed_time

                        # print(num_parses)
                        
                        start_naive_time = time.time()
                        naive_parses, chart_naive = cky_parse(lexicon, input_tokens)
                        end_naive_time = time.time()
                        elapsed_time = end_naive_time - start_naive_time
                        # naive_derivation_time[len(lexicon)].append(elapsed_time)
                        naive_derivation_time[file] = elapsed_time

                        print(f'FAST PARSES {num_parses}, NAIVE PARSES {naive_parses}')
                        if num_parses != naive_parses:
                            print(file)
                            mismatched_parses += 1
                            if int('KuhlmannItem' in str(chart)) >= 1:
                                mismatched_km += 1
                        if idx == 0:
                            derivation_length_en[num_parses] += 1
                            kulhmann_edges_per_lan['en'] += num_km_edges
                            total_edges_per_lan['en'] += num_edges
                        elif idx == 1:
                            derivation_length_de[num_parses] += 1
                            kulhmann_edges_per_lan['de'] += num_km_edges
                            total_edges_per_lan['de'] += num_edges
                        elif idx == 2:
                            derivation_length_it[num_parses] += 1
                            kulhmann_edges_per_lan['it'] += num_km_edges
                            total_edges_per_lan['it'] += num_edges


                        kulhmann_count += int('KuhlmannItem' in str(chart))
                        kulhmann_per_lan[mapping_language[idx]] += int('KuhlmannItem' in str(chart))
                        # if int('KuhlmannItem' in str(chart)):
                        #     print(str(chart))   
                        #     for item in chart[0][len(input_tokens) - 1]:
                        #         if item.category == "S":
                        #             print('nice')
                        # print('KULMANN COUNT',kulhmann_count, 'TOTAL', total)
                    else:
                        lx_rules[mapping_language[idx]] += 1




def plot_runtimes():
    average_times = {
        key: times 
        for key, times in sorted(derivation_length_time.items(), key=lambda item: item[1])
    }

    # As of Python version 3.7, dictionaries are ordered.
    naive_runtimes = {key: naive_derivation_time[key] for key in average_times.keys()}
    x = list(average_times.keys())[:5200]
    y_fast = list(average_times.values())[:5200]
    y_slow = list(naive_runtimes.values())[:5200]


    def moving_average(data, window_size):
        """Compute the moving average of a list with the given window size."""
        return np.convolve(data, np.ones(window_size) / window_size, mode='valid')

    x = list(average_times.keys())[:5200]
    y_fast = list(average_times.values())[:5200]
    y_slow = list(naive_runtimes.values())[:5200]

    window_size = 50  

    y_fast_smoothed = moving_average(y_fast, window_size)
    y_slow_smoothed = moving_average(y_slow, window_size)

    x_smoothed = x[:len(y_fast_smoothed)]  

    plt.figure(figsize=(10, 6))
    # plt.plot(x, y_fast, label="FastCCG Original", alpha=0.4, marker='o', linestyle='--')
    plt.plot(x_smoothed, y_fast_smoothed, label="FastCCG", marker='o')
    # plt.plot(x, y_slow, label="NaiveCCG Original", alpha=0.4, marker='o', linestyle='--')
    plt.plot(x_smoothed, y_slow_smoothed, label="NaiveCCG", marker='o')

    plt.title("Runtime Comparison Between Fast and Naive with Moving Average")
    plt.xlabel("File")
    plt.ylabel("Runtime (ms)")
    plt.legend()
    plt.grid(True)
    plt.gca().set_xticklabels([])
    plt.show()

    plt.figure(figsize=(10, 6))
    plt.plot(x, y_fast, label="FastCCG", alpha=0.4, marker='o', linestyle='--')
    # plt.plot(x_smoothed, y_fast_smoothed, label="FastCCG Smoothed", marker='o')
    plt.plot(x, y_slow, label="NaiveCCG", alpha=0.4, marker='o', linestyle='--')
    # plt.plot(x_smoothed, y_slow_smoothed, label="NaiveCCG Smoothed", marker='o')

    plt.title("Runtime Comparison Between Fast and Naive")
    plt.xlabel("File")
    plt.ylabel("Runtime (ms)")
    plt.legend()
    plt.grid(True)
    plt.gca().set_xticklabels([])
    plt.show()

    naive_runtimes = {key: naive_derivation_time[key] for key in average_times.keys()}
    x = list(average_times.keys())[:5200]
    y_fast = list(average_times.values())[:5200]
    y_slow = list(naive_runtimes.values())[:5200]
    plt.figure(figsize=(10, 6))
    plt.plot(x, y_slow, label="NaiveCCG", marker='o')
    plt.title("Runtime Comparison Between Fast and Naive")
    plt.xlabel("File")
    plt.ylabel("Runtime (ms)")
    plt.legend()
    plt.grid(True)
    plt.gca().set_xticklabels([])
    plt.show()

# average_times_naive = {
#     key: times
#     for key, times in sorted(naive_derivation_time.items(), key=lambda item: item[1])
# }

# print(average_times_naive)

# average_times_naive = {
#     key: (sum(times) / len(times))  
#     for key, times in naive_derivation_time.items()
# }
# print(average_times_naive)

# sorted_keys = sorted(average_times.keys())[:12]
# dict1_sorted = [average_times[key] for key in sorted_keys][:12]
# dict2_sorted = [average_times_naive[key] for key in sorted_keys][:12]

# plt.figure(figsize=(10, 6))
# plt.plot(sorted_keys, dict1_sorted, label="FastCCG", marker="o")
# plt.plot(sorted_keys, dict2_sorted, label="NaiveCCG", marker="o")

# plt.title("Runtime Comparison Between Fast and Naive")
# plt.xlabel("Input Length")
# plt.ylabel("Runtime (ms)")
# plt.legend()
# plt.grid(True)

# plt.show()


all_lang = ['EN', 'DE', 'IT']
total_count = [total_per_lan['en'], total_per_lan['de'], total_per_lan['it']]
lx_count = list(lx_rules.values())
non_lx_count = [total_count[lang] - lx_count[lang] for lang in range(len(total_count))]

x = np.arange(len(total_count))

# print(total_edges_per_lan)
# print(kulhmann_edges_per_lan)

kulhmann_edges = list(kulhmann_edges_per_lan.values())
non_kulhmann_edges = [total_edges_per_lan[lang] - kulhmann_edges_per_lan[lang] for lang in ['en', 'de', 'it']]

# # Plot stacked bars
# plt.figure(figsize=(10, 6))
# plt.bar(x, lx_count, label="Magic Counts", color="skyblue")
# plt.bar(x, non_lx_count, bottom=lx_count, label="Non-Magic Count", color="orange")

# plt.title("'Magic' and 'Non-Magic 'Counts")
# plt.xlabel("Languages")
# plt.ylabel("Counts")
# plt.xticks(x, all_lang)
# plt.legend()
# plt.grid(axis="y", linestyle="--", alpha=0.7)

# plt.tight_layout()
# plt.show()

kulhmann_edges = list(kulhmann_edges_per_lan.values())
non_kulhmann_edges = [total_edges_per_lan[lang] - kulhmann_edges_per_lan[lang] for lang in ['en', 'de', 'it']]
kulhmann_count = list(kulhmann_per_lan.values())
non_km_count = [total_count[lang] - kulhmann_count[lang] for lang in range(len(total_count))]
bar_width = 0.4  

# plt.figure(figsize=(10, 6))
# plt.bar(x - bar_width / 2, kulhmann_count, width=bar_width, label="Kulhmann Count", color="skyblue")
# plt.bar(x - bar_width / 2, non_km_count, width=bar_width, bottom=kulhmann_count, label="Non-Kulhmann Count", color="orange")
# plt.bar(x + bar_width / 2, kulhmann_edges, width=bar_width, label="Kulhmann Edges", color="lightgreen")
# plt.bar(x + bar_width / 2, non_kulhmann_edges, width=bar_width, bottom=kulhmann_edges, label="Non-Kulhmann Edges", color="salmon")

# # Adding titles and labels
# plt.title("Ratio of Kuhlmann Rules Applied")
# plt.xlabel("Languages")
# plt.ylabel("Counts")
# plt.xticks(x, all_lang)  # Add language names as x-axis labels
# plt.legend()
# plt.grid(axis="y", linestyle="--", alpha=0.7)

# plt.tight_layout()
# plt.show()


# Bar width
bar_width = 0.4

# Plot 1: Counts
plt.figure(figsize=(10, 6))
plt.bar(x, kulhmann_count, width=bar_width, label="Kulhmann Count", color="skyblue")
plt.bar(x, non_km_count, width=bar_width, bottom=kulhmann_count, label="Non-Kulhmann Count", color="orange")
plt.title("Ratio of Kuhlmann Rules Applied: Per Sentence")
plt.xlabel("Languages")
plt.ylabel("Counts")
plt.xticks(x, all_lang)  
plt.legend()
plt.grid(axis="y", linestyle="--", alpha=0.7)
plt.tight_layout()
plt.show()

# Plot 2: Edges
plt.figure(figsize=(10, 6))
plt.bar(x, kulhmann_edges, width=bar_width, label="Kulhmann Edges", color="lightgreen")
plt.bar(x, non_kulhmann_edges, width=bar_width, bottom=kulhmann_edges, label="Non-Kulhmann Edges", color="salmon")
plt.title("Ratio of Kuhlmann Rules Applied: Per Edge")
plt.xlabel("Languages")
plt.ylabel("Edges")
plt.xticks(x, all_lang)  
plt.legend()
plt.grid(axis="y", linestyle="--", alpha=0.7)
plt.tight_layout()
plt.show()


# plt.bar(x, total_count)
# plt.show()

# plt.bar(x, lx_count)
# plt.show()

# plt.bar(x, kulhmann_count)
# plt.show()

