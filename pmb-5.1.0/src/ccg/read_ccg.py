import re
FUNCTION_TYPES = {'rp', 'conj', 'lx', 'fa', 'gbc', 'gbxc', 'fc', 'op', 'bc', 'lp', 'ba', 'ccg', 't', 'bxc', 'fxc'}


# def remove_parentheses(text):
#     # Remove ')' if followed by ')' or ',' or '/' or '\'
#     text = re.sub(r'\)(?=[),/\\])', '', text)
    
#     # Remove '(' if preceded by '(' or ',' or '/' or '\'
#     text = re.sub(r'(?<=[(,/\\])\(', '', text)
    
#     return text


# def remove_features(string):
#     return re.sub(r':[^,/\\]*', '', string)



def tokenize(expr):
    """Convert input string into a list of tokens."""
    tokens = []
    current_token = []
    i = 0
    prev = ''
    sq = False
    while i < len(expr):
        char = expr[i]
        if char == '[':
            sq = True
        if char == ']':
            sq = False

        if char.isspace():
            i += 1
            continue

        if char == ':' and not sq:
            print('OK')
            while char not in '/\\(),':
                print(char)
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
        elif char == "'":
            current_token.append(char)
            i += 1
            while i < len(expr) and expr[i] != "'":
                assert expr[i] != "/"
                current_token.append(expr[i])
                i += 1
                char = expr[i]
            assert expr[i] == "'"
            current_token.append("'")  
            char = expr[i]
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
    
    # Add any remaining token
    if current_token:
        tokens.append(''.join(current_token))
    # print('TOKENS', tokens)
    # print('END TOKENS')
    return tokens


def parse_tokens(tokens):
    """ Recursively parse tokens into a nested dictionary, correctly handling nested structures. """
    if not tokens:
        return None
    token = tokens.pop(0)
    
    if token in FUNCTION_TYPES:  
        func_name = token
        tokens.pop(0)  # this pops (
        args = []
        while tokens[0] != ')':
            if tokens[0] == '(':
                ignore = True
            if tokens[0] == ')':
                ignore = False
            # if func_name not in {'t', 'lx'}:
            #     print(func_name, len(args), args)
            arg = parse_tokens(tokens)
            if arg is not None:
                args.append(arg)
        tokens.pop(0)
        # if func_name == 'ba': 
        #     print({func_name: len(args)})
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
        # print(token)
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

input_str = r"""
 ccg(1,
 ba(s:dcl,
  fa(np,
   t(np/n, 'A', [lemma:'a', from:0, to:1, pos:'DT', sem:'DIS', wordnet:'O']),
   fa(n,
    t(n/n, 'big', [lemma:'big', from:2, to:5, pos:'JJ', sem:'DEG', wordnet:'big.a.01', verbnet:['Attribute']]),
    t(n, 'typhoon', [lemma:'typhoon', from:6, to:13, pos:'NN', sem:'CON', wordnet:'typhoon.n.01']))),
  fa(s:dcl\np,
   t((s:dcl\np)/(s:ng\np), 'is', [lemma:'be', from:14, to:16, pos:'VBZ', sem:'NOW', wordnet:'O']),
   rp(s:ng\np,
    t(s:ng\np, 'approaching', [lemma:'approach', from:17, to:28, pos:'VBG', sem:'EXG', wordnet:'approach.v.04', verbnet:['Theme']]),
    t(., '.', [lemma:'.', from:28, to:29, pos:'.', sem:'NIL', wordnet:'O']))))).
"""


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
# Parse the input string
parsed_result = parse_prolog_to_dict(input_str)
# print(parsed_result)
print_recursive(parsed_result)
# print_rules(parsed_result)
# print(extract_derivation_tree(parsed_result))
# print_recursive(extract_derivation_tree(parsed_result))

inference_tree, r = extract_inference_tree(parsed_result)
print(inference_tree, r)

