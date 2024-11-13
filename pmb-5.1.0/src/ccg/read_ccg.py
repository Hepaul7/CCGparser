import os
import re
FUNCTION_TYPES = {'rp', 'conj', 'lx', 'fa', 'gbc', 'gbxc', 'fc', 'op', 'bc', 'lp', 'ba', 'ccg', 't', 'bxc', 'fxc'}


def tokenize(expr):
    """Convert input string into a list of tokens."""
    tokens = []
    current_token = []
    i = 0
    prev = ''
    sq = False
    stack_count = 0
    while i < len(expr):
        char = expr[i]
        if char == '[':
            sq = True
            stack_count += 1
        if char == ']' and stack_count == 1:
            sq = False
            stack_count -= 1
        elif char == ']':
            stack_count -= 1

        if char.isspace():
            i += 1
            continue

        if char == ':' and not sq:
        
            while char not in '/\\(),':
                i += 1
                char = expr[i]

        # if prev == '/':
        #     print(f'prev: {prev} curr: {char}')
        if (prev == '/' or prev == '\\' or prev == '(') and char == '(':
            # i += 1
            # prev = char
            # continue
            char = '<'
        elif prev.isalpha() and char == ')':
            # i += 1
            # prev = char
            # continue
            char = '>'

        # if char == '/':
        #     print(char, prev)

        if char in '(),':
            if current_token:
                tokens.append(''.join(current_token))
                current_token = []
            tokens.append(char)
        # elif char == "'" and prev != "'":
        #     current_token.append(char)
        #     i += 1
        #     while i < len(expr) and expr[i] != "'":
        #         assert expr[i] != "/"
        #         current_token.append(expr[i])
        #         i += 1
        #         char = expr[i]
        #     assert expr[i] == "'"
        #     current_token.append("'")  
        #     char = expr[i]
        #     tokens.append(''.join(current_token))
        #     current_token = []
        elif char == "'" and prev != "'":
            current_token.append(char)
            i += 1
            while i < len(expr):
                if expr[i] == "'" and expr[i-1] != "\\":
                    break
                elif expr[i] == "\\" and i + 1 < len(expr) and expr[i + 1] == "'":
                    current_token.append("'")
                    i += 2 
                else:
                    current_token.append(expr[i])
                    i += 1
            assert i < len(expr) and expr[i] == "'", f'Got {i}/{len(expr)} and {expr[i]}'
            current_token.append("'")
            tokens.append(''.join(current_token))
            current_token = []
        else:
            current_token.append(char)
        
        if char not in '<>':
            prev = char
        elif char == '<':
            prev = '('
        else:
            prev = ')'
        
        i += 1
    
    if current_token:
        tokens.append(''.join(current_token))
    return tokens


def parse_tokens(tokens):
    """ Recursively parse tokens into a nested dictionary, correctly handling nested structures. """
    if not tokens:
        return None
    
    token = tokens.pop(0)
    
    if token in FUNCTION_TYPES:
        func_name = token
        tokens.pop(0)  # Assume this pops the opening '('
        args = []
        nesting_level = 1  

        while tokens:
            current_token = tokens[0]
            
            if current_token == '(':
                nesting_level += 1
            elif current_token == ')':
                nesting_level -= 1
                if nesting_level == 0:
                    tokens.pop(0)  # Pop closing ')'
                    break
            
            # Skip commas that are within nested structures
            if current_token == ',' and nesting_level > 1:
                tokens.pop(0)  
                continue
            
            arg = parse_tokens(tokens)
            if arg is not None:
                args.append(arg)
        
        return {func_name: args}

    if token == ')':  
        return None
    
    if token == ',':  
        return parse_tokens(tokens)
    
    if token.isalnum() or token[0] == "'" or ":" in token:  
        return token.strip("'")
    
    elif '/' in token or '\\' in token: 
        return token

    return None



def parse_prolog_to_dict(expr):
    tokens = tokenize(expr)
    # for token in tokens:
    #     print(token)
    return parse_tokens(tokens)


def print_recursive(data, level=0):
    """Recursively prints each function and its arguments in a readable format."""
    indent = '  ' * level  

    if isinstance(data, dict):
        for func, args in data.items():
            print(f"{indent}{func}:")
            print_recursive(args, level + 1)
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, (dict, list)):
                print_recursive(item, level + 1)
            else:
                print(f"{indent}- {item}")
    else:
        print(f"{indent}- {data}")


def extract_inference_tree(ccg_dict):
    """
    we can derive this to an item list and compare.
    """
    for key in ccg_dict.keys():
        # each KEY should correspond to one of the function types
        assert key in FUNCTION_TYPES
        arguments = ccg_dict[key]  # arguments :: List

        # The first index is always string, this is a category
        category = arguments[0]
        if len(arguments) == 1:
            # we have an axiom
            return {category: arguments[0]}
        elif len(arguments) == 2:
            # these are puncts
            return {category: arguments[1]}, None
        
        # In the case of binary inference rules, both arg[1], arg[2] are dicts
        if isinstance(arguments[1], dict) and isinstance(arguments[2], dict):
            binary_rule = True
        else:
            binary_rule = False
            assert isinstance(arguments[2], str)

        if binary_rule:
            # only do it if the rule isnt an axiom.
            l_args = extract_inference_tree(arguments[1])
            r_args = extract_inference_tree(arguments[2])
            return {category: [l_args, r_args]}, None
        else:
            if not isinstance(arguments[1], dict):
                return arguments[1]
            assert type(arguments[1]) == dict, f"expected dict got {type(arguments[1])}"
            l_args = extract_inference_tree(arguments[1])
            return {category: [l_args]}, None
        



# Input string
# input_str = """
# ccg(1,
#  ba(s:dcl,
#   lx(np, n,
#    t(n, 'Maria', [lemma:'maria', from:0, to:5, pos:'NNP', sem:'PER', wordnet:'female.n.02'])),
#   fa(s:dcl\\np,
#    t((s:dcl\\np)/np, 'has', [lemma:'have', from:6, to:9, pos:'VBZ', sem:'ENS', wordnet:'have.v.02', verbnet:['Theme','Pivot']]),
#    rp(np,
#     lx(np, n,
#      fa(n,
#       t(n/n, 'long', [lemma:'long', from:10, to:14, pos:'JJ', sem:'DEG', wordnet:'long.a.02', verbnet:['Attribute']]),
#       t(n, 'hair', [lemma:'hair', from:15, to:19, pos:'NN', sem:'CON', wordnet:'hair.n.01']))),
#     t(., '.', [lemma:'.', from:19, to:20, pos:'.', sem:'NIL', wordnet:'O'])))))
# """

# input_str = r"""
#  ccg(1,
#  ba(s:dcl,
#   fa(np,
#    t(np/n, 'A', [lemma:'a', from:0, to:1, pos:'DT', sem:'DIS', wordnet:'O']),
#    fa(n,
#     t(n/n, 'big', [lemma:'big', from:2, to:5, pos:'JJ', sem:'DEG', wordnet:'big.a.01', verbnet:['Attribute']]),
#     t(n, 'typhoon', [lemma:'typhoon', from:6, to:13, pos:'NN', sem:'CON', wordnet:'typhoon.n.01']))),
#   fa(s:dcl\np,
#    t((s:dcl\np)/(s:ng\np), 'is', [lemma:'be', from:14, to:16, pos:'VBZ', sem:'NOW', wordnet:'O']),
#    rp(s:ng\np,
#     t(s:ng\np, 'approaching', [lemma:'approach', from:17, to:28, pos:'VBG', sem:'EXG', wordnet:'approach.v.04', verbnet:['Theme']]),
#     t(., '.', [lemma:'.', from:28, to:29, pos:'.', sem:'NIL', wordnet:'O']))))).
# """


# input_str = r"""
#  ccg(1,
#  fa(s:q,
#   fa(s:q/np,
#    t((s:q/np)/np, 'Is', [lemma:'be', from:0, to:2, pos:'VBZ', sem:'ENS', wordnet:'be.v.02', verbnet:['Theme','Co-Theme']]),
#    t(np, 'this', [lemma:'entity', from:3, to:7, pos:'DT', sem:'PRX', wordnet:'entity.n.01'])),
#   rp(np,
#    fa(np,
#     t(np/n, 'your', [lemma:'hearer', from:8, to:12, pos:'PRP$', sem:'HAS', wordnet:'O', verbnet:['User']]),
#     t(n, 'bicycle', [lemma:'bicycle', from:13, to:20, pos:'NN', sem:'CON', wordnet:'bicycle.n.01'])),
#    t(., '?', [lemma:'?', from:20, to:21, pos:'.', sem:'QUE', wordnet:'O'])))).
#  """

# input_str = """
#  ccg(1,
#  fa(s:wq,
#   t(s:wq/s:q, 'How', [lemma:'manner', from:0, to:3, pos:'WRB', sem:'QUE', wordnet:'manner.n.01', verbnet:['Manner','Equal']]),
#   fa(s:q,
#    fa(s:q/s:pss\\np,
#     t(s:q/s:pss\\np/np, 'is', [lemma:'be', from:4, to:6, pos:'VBZ', sem:'NOW', wordnet:'O']),
#     fa(np,
#      t(np/n/pp, 'your', [lemma:'hearer', from:7, to:11, pos:'PRP$', sem:'HAS', wordnet:'O', verbnet:['Bearer','Equal']]),
#      t(n/pp, 'first~name', [lemma:'first~name', from:12, to:22, pos:'NN', sem:'CON', wordnet:'first_name.n.01']))),
#    rp(s:pss\\np,
#     t(s:pss\\np, 'pronounced', [lemma:'pronounce', from:23, to:33, pos:'VBD', sem:'EXS', wordnet:'pronounce.v.01', verbnet:['Theme']]),
#     t(., '?', [lemma:'?', from:33, to:34, pos:'.', sem:'QUE', wordnet:'O']))))).
# """

# input_str = """
#  ccg(1,
#  fa(s:wq,
#   t(s:wq/s:q/np, 'Who', [lemma:'person', from:0, to:3, pos:'WP', sem:'QUE', wordnet:'person.n.01', verbnet:['Name']]),
#   rp(s:q/np,
#    fa(s:q/np,
#     t(s:q/np/np, 'is', [lemma:'be', from:4, to:6, pos:'VBZ', sem:'ENS', wordnet:'be.v.02', verbnet:['Theme','Co-Theme']]),
#     t(np, 'he', [lemma:'male', from:7, to:9, pos:'PRP', sem:'PRO', wordnet:'male.n.02'])),
#    t(., '?', [lemma:'?', from:9, to:10, pos:'.', sem:'QUE', wordnet:'O'])))).
# """

# input_str = """
#  ccg(1,
#  fa(s:wq,
#   t(s:wq/(s:q/np), 'Who', [lemma:'person', from:0, to:3, pos:'WP', sem:'QUE', wordnet:'person.n.01', verbnet:['Name']]),
#   rp(s:q/np,
#    fa(s:q/np,
#     t((s:q/np)/np, 'is', [lemma:'be', from:4, to:6, pos:'VBZ', sem:'ENS', wordnet:'be.v.02', verbnet:['Theme','Co-Theme']]),
#     t(np, 'he', [lemma:'male', from:7, to:9, pos:'PRP', sem:'PRO', wordnet:'male.n.02'])),
#    t(., '?', [lemma:'?', from:9, to:10, pos:'.', sem:'QUE', wordnet:'O'])))).
#  """


# input_str = r"""
#  ccg(1,
#  ba(s:dcl,
#   ba(s:dcl,
#    t(np, 'I', [lemma:'speaker', from:0, to:1, pos:'PRP', sem:'PRO', wordnet:'O', verbnet:['Equal']]),
#    fa(s:dcl\np,
#     t((s:dcl\np)/(s:adj\np), '\'m', [lemma:'be', from:1, to:3, pos:'VBP', sem:'NOW', wordnet:'O']),
#     t(s:adj\np, 'sorry', [lemma:'sorry', from:4, to:9, pos:'JJ', sem:'IST', wordnet:'sorry.a.01', verbnet:['Theme']]))),
#   conj(s:dcl\s:dcl,
#    t(conj, ',', [lemma:',', from:9, to:10, pos:',', sem:'NIL', wordnet:'O']),
#    ba(s:dcl,
#     ba(s:dcl,
#      t(np, 'I', [lemma:'speaker', from:11, to:12, pos:'PRP', sem:'PRO', wordnet:'O', verbnet:['Equal']]),
#      fa(s:dcl\np,
#       t((s:dcl\np)/pr, 'fucked', [lemma:'fuck~up', from:13, to:19, pos:'VBD', sem:'EPS', wordnet:'fuck_up.v.01', verbnet:['Agent']]),
#       t(pr, 'up', [lemma:'up', from:20, to:22, pos:'RP', sem:'REL', wordnet:'O']))),
#     t(s:dcl\s:dcl, '.', [lemma:'.', from:22, to:23, pos:'.', sem:'NIL', wordnet:'O'])))))."""

input_str = r"""
 ccg(1,
 ba(s:dcl,
  fa(np,
   t(np/n, 'A', [lemma:'a', from:0, to:1, pos:'DT', sem:'DIS', wordnet:'O']),
   t(n, 'boy', [lemma:'boy', from:2, to:5, pos:'NN', sem:'CON', wordnet:'boy.n.01'])),
  fa(s:dcl\np,
   t((s:dcl\np)/(s:ng\np), 'is', [lemma:'be', from:6, to:8, pos:'VBZ', sem:'NOW', wordnet:'O']),
   fa(s:ng\np,
    t((s:ng\np)/np, 'styling', [lemma:'style', from:9, to:16, pos:'VBG', sem:'EXG', wordnet:'style.v.02', verbnet:['Patient','Agent']]),
    fa(np,
     t(np/n, 'his', [lemma:'male', from:17, to:20, pos:'PRP$', sem:'HAS', wordnet:'male.n.02', verbnet:['PartOf'], antecedent:'2,5']),
     t(n, 'hair', [lemma:'hair', from:21, to:25, pos:'NN', sem:'CON', wordnet:'hair.n.01'])))))).
"""
parsed_result = parse_prolog_to_dict(input_str)
# print(parsed_result)
print_recursive(parsed_result)
# print_rules(parsed_result)
# print(extract_derivation_tree(parsed_result))
# print_recursive(extract_derivation_tree(parsed_result))
inference_tree, r = extract_inference_tree(parsed_result)
# print(inference_tree, r)






def traverse_directory_for_parse_items(directory_path: str):
    """
    Traverses a directory and extracts function types from all `.ccg` files.

    :param directory_path: Path to the directory containing `.ccg` files.
    :return: A set of all unique function types found across all `.ccg` files.
    """
    count = 0
    total = 0
    for root, dirs, files in os.walk(directory_path):
        # print(files)
        for file in files:
            # print(file)
            if file.endswith(".ccg"):
                print(file)
                total += 1
                # print('ok', all_function_types)
                file_path = os.path.join(root, file)
                with open(file_path, "r") as f:
                    prolog_code = f.read()
                    match = re.search(r'ccg\(.*', prolog_code, re.DOTALL)
                    if match and 'lx' not in match.group(0):
                        count += 1
                        result = match.group(0)
                        print(result)
                        parsed_result = parse_prolog_to_dict(result)
                        print_recursive(parsed_result)
                        inference_tree, r = extract_inference_tree(parsed_result)
        print(f'NO LX: {count}; TOTAL: {total}')


directory_path = "/Users/paulhe/Desktop/CCG Parsing/pmb-5.1.0/src/ccg/standard"
traverse_directory_for_parse_items(directory_path)

        