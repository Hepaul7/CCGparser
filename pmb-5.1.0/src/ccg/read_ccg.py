import re


def parse_ccg_structure(ccg_text):
    ccg_entries = []

    pattern_token = r"t\((.*?), '(.*?)', \[(.*?)\]\)"

    lines = ccg_text.splitlines()

    for line in lines:
        token_match = re.search(pattern_token, line)

        if token_match:
            category, word, features = token_match.groups()
            ccg_entries.append((word, category))

    return ccg_entries


def human_readable_format_simple(ccg_entries):
    output = []
    for word, category in ccg_entries:
        output.append(f"{word} := {category.upper()}")

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


ccg_text = """
ccg(1,
 ba(s:dcl,
  lx(np, n,
   t(n, 'Maria', [lemma:'maria', from:0, to:5, pos:'NNP', sem:'PER', wordnet:'female.n.02'])),
  fa(s:dcl\\np,
   t((s:dcl\\np)/np, 'has', [lemma:'have', from:6, to:9, pos:'VBZ', sem:'ENS', wordnet:'have.v.02', verbnet:['Theme','Pivot']]),
   rp(np,
    lx(np, n,
     fa(n,
      t(n/n, 'long', [lemma:'long', from:10, to:14, pos:'JJ', sem:'DEG', wordnet:'long.a.02', verbnet:['Attribute']]),
      t(n, 'hair', [lemma:'hair', from:15, to:19, pos:'NN', sem:'CON', wordnet:'hair.n.01']))),
    t(., '.', [lemma:'.', from:19, to:20, pos:'.', sem:'NIL', wordnet:'O']))))).
"""

ccg_entries_simple = parse_ccg_structure(ccg_text)
human_readable_output_simple = human_readable_format_simple(ccg_entries_simple)
print(human_readable_output_simple)
