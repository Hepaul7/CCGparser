import re
import os


def extract_function_types(prolog_code: str):
    """
    Extracts all function types from the Prolog code such as `lx`, `rp`, `ba`, etc.

    :param prolog_code: A string containing Prolog code.
    :return: A set of function types (e.g., 'lx', 'rp', 'ba').
    """
    pattern = r'\b([a-z]+)\('
    function_types = re.findall(pattern, prolog_code)

    return set(function_types)


def traverse_directory_for_function_types(directory_path: str):
    """
    Traverses a directory and extracts function types from all `.ccg` files.

    :param directory_path: Path to the directory containing `.ccg` files.
    :return: A set of all unique function types found across all `.ccg` files.
    """
    all_function_types = set()
    sample_files = {}

    # print(directory_path)
    for root, dirs, files in os.walk(directory_path):
        # print(files)
        for file in files:
            # print(file)
            if file.endswith(".ccg"):
                # print('ok', all_function_types)
                file_path = os.path.join(root, file)
                with open(file_path, "r") as f:
                    prolog_code = f.read()
                    function_types = extract_function_types(prolog_code)
                    if len(all_function_types.difference(function_types)) > 0:
                        difference = [x for x in function_types.difference(all_function_types)]
                        # print(all_function_types)
                        # print(function_types)
                        # print(difference)
                        for diff in difference:
                            sample_files[diff] = file
                    all_function_types.update(function_types)

    return all_function_types, sample_files


directory_path = "/Users/paulhe/Desktop/CCG Parsing/pmb-5.1.0/src/ccg/standard"
function_types, difference_dict = traverse_directory_for_function_types(directory_path)
print("Function types found:", function_types)
print("Example of each rule:", difference_dict)
