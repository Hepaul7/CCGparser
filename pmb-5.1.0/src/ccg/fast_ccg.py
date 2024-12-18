from ccg import Item
from typing import Self, Optional, Union, List, Dict
import re


class KuhlmannItem(Item):
    """
    The type of item introduced in Kuhlmann and Satta 2014 algorithm to avoid exponential runtime.
    [/Y, β, i, i', j', j]: for any category X, if we can build a derivation tree t' with yield w[i', j'] and type
    X/Y, then we can also build the derivation tree t' with yield w[i, j] and type Xβ.

    Similarly, [\\Y, β, i, i', j', j]: for any category X, if we can build a derivation tree t' with yield w[i, j']
    and type Y\\X, then we can build a derivation tree t' with yield w[i, j] and type βX.
    """

    def __init__(self, category: str, β: str, i: int, i_prime: int, j_prime: int, j: int):
        super().__init__(category, i, j)
        self.β = β
        self.i_prime = i_prime
        self.j_prime = j_prime

    def __repr__(self):
        return f"KuhlmannItem({self.category}, {self.β}, {self.i}, {self.i_prime}, {self.j_prime}, {self.j})"

def split_category(category: str) -> List[str]:
    parts = []
    stack = []
    i = 0
    while i < len(category):
        if category[i] == '(':
            stack.append(i)
        elif category[i] == ')':
            start = stack.pop()
            if not stack:  # Top-level parentheses
                parts.append(category[start + 1:i])
        elif category[i] in '/\\' and not stack:  # Split at / or \ only at top level
            parts.append(category[:i])
            category = category[i + 1:]
            i = 0
            continue
        i += 1
    if category:
        parts.append(category)  # Remaining part if no split happens
    return parts


def ccg_extend(left: Item, right: Item, c_G: int) -> Union[None, Item, KuhlmannItem]:
    """
    Applies the CKY style forward/backward rule if possible, except this checks if the arity
    of the result is greater than some pre-defined arity
    :param left: left item in the form [X|Y, i, j]
    :param right: right item in the form [Yβ, j, k]
    :param c_G: arity bound for the grammar G
    :return: new item in the form [Xβ, i, j] or [|Y, β, i, i, j, k]
    """
    category = left.category
    # We need to get all possible parts, for example: A/B\C/D\F/G then
    # B\C/D\F/G, D\F/G, G are all possible arguments we can expect with different return types.
    parts = {category[:x.span()[0]]: category[x.span()[0] + 1:] for x in re.finditer(r'/([^/\\]+)', category)}
    bwd_parts = {category[:x.span()[0]]: category[x.span()[0] + 1:] for x in re.finditer(r'\\([^/\\]+)', category)}
    # print(category)
    # parts = split_category(category)
    # print(parts)
    # bwd_parts = {category[:x.span()[0]]: category[x.span()[0] + 1:] for x in re.finditer(r'\\([^/\\]+)', category)}

    parts.update(bwd_parts)
    for func_type, expected_arg in parts.items():
        right_category = right.category
        if right_category.startswith(expected_arg):
            β = right_category[len(expected_arg):]
            new_category = f"{func_type}{β}" if β else func_type
            new_item = Item(new_category, left.i, right.j)  # this is Xβ
            # count the occurence of / \\ in Xβ
            # should be [Y, β, i, i', j', j]
            ar_xβ = new_item.category.count('/') + new_item.category.count('\\')
            if ar_xβ > c_G:
                new_item = KuhlmannItem(category[len(func_type)] + expected_arg, β, left.i, left.i, right.i, right.j)
            return new_item

    return None


# TODO: ccg_backward crossing
def ccg_backward_crossing(left: Item, right: Union[Item, KuhlmannItem]) -> Union[None, Item, KuhlmannItem]:
    """
    Applies the CKY style backward crossing rule if possible.
    :param left: left item in the form [Yβ, i, j]
    :param right: right item in the form [X/Y, j, k] OR [/F, X/Y, j, i', j', k]
    :return: new item in the form [Xβ, i, k] or None if not applicable OR [/F, X, i, i', j', k]
    """
    category = right.β if isinstance(right, KuhlmannItem) else right.category
    # Extract backward-slash components
    parts = {category[:x.span()[0]]: category[x.span()[0] + 1:] for x in re.finditer(r'\\([^/\\]+)', category)}
    for func_type, expected_arg in parts.items():
        right_category = left.category
        # Check if the left category matches the expected argument
        if right_category.startswith(expected_arg):
            β = right_category[len(expected_arg):]
            new_category = f"{func_type}" if β == "" else f"{func_type}{β}"
            if isinstance(right, KuhlmannItem):
                new_item = KuhlmannItem(right.category, new_category, left.i, right.i_prime, right.j_prime, right.j)
            else:
                new_item = Item(new_category, left.i, right.j)
            return new_item
    return None


def ccg_recombine(left: Item, right: KuhlmannItem, c_G: int) -> Union[None, Item]:
    """
    Recombines the original derivation that triggered a KuhlmannItem. (3)
    :param left: [X|Y, i', j']
    :param right: [|Y, β, i, i', j', j]
    :param c_G: arity bound for the grammar G
    :return: [Xβ, i, j]
    """
    # TODO: Requires a check that ar(Xβ) < c_G (solved?)
    category = left.category
    # this rule is a bit different, so we include the directions
    parts = {category[:x.span()[0]]: category[x.span()[0]:] for x in re.finditer(r'/([^/\\]+)', category)}
    bwd_parts = {category[:x.span()[0]]: category[x.span()[0]:] for x in re.finditer(r'\\([^/\\]+)', category)}
    parts.update(bwd_parts)
    for func_type, expected_arg in parts.items():
        right_category = right.category
        if right_category.startswith(expected_arg):
            β = right_category[len(expected_arg):]
            new_category = f"{func_type}{β}" if β else func_type
            new_item = Item(new_category, right.i, right.j)
            ar_xβ = new_item.category.count('/') + new_item.category.count('\\')
            if ar_xβ < c_G:
                return new_item
    return None  # should never hit this case if checks done properly in algorithm


def ccg_derivation_ctxt_extend(left: KuhlmannItem, right: Item, c_G: int) -> Union[None, Item]:
    """
    Extends derivation contexts similarly to derivation trees if:
    - X/Y Zγ -> Xγ
    :param left: [|Y, β/Z, i, i', j', j]
    :param right: [Zγ, j, k]
    :param c_G: arity bound for the grammar G
    :param X: untouched part of derivation contex, see equation (4)
    :return: [|Y, βγ, i, i', j', k] OR [/Z, γ, i, i, j, k]
    """
    category = left.β
    parts = {category[:x.span()[0]]: category[x.span()[0] + 1:] for x in re.finditer(r'/([^/\\]+)', category)}
    for func_type, expected_arg in parts.items():
        # we should have something in the form of β and expected arg Z
        right_category = right.category
        if right_category.startswith(expected_arg):
            γ = right_category[len(expected_arg):]
            new_category = f"{func_type}{γ}" if γ else func_type
            new_item = KuhlmannItem(left.category, new_category, left.i, left.i_prime, left.j_prime, right.j)
            ar_Yβγ = left.category.count('/') + left.category.count('\\') + new_item.category.count('/') + new_item.category.count('\\')
            if ar_Yβγ > c_G:
                new_item = KuhlmannItem(f"/{expected_arg}", γ, left.i, left.i, right.j, right.k)
            return new_item
    return None


def ccg_derivation_ctxt_recombine(left: KuhlmannItem, right: KuhlmannItem, c_G):
    """
    Recombine a derivation context with the context that originally triggered it.
    :param left: [|_1 Y, β|_2 Z, i'', i', j', j'']
    :param right: [|_2 Z, ε, i, i'', j'', j]
    :param c_G: arity bound for the grammar G
    :return: [|_1, Y, β, i, i', j', j]
    """
    slash_2 = right.category[0]
    assert slash_2 in left.β
    start_idx = left.β.find(slash_2)
    return KuhlmannItem(left.category, left.β[:start_idx], right.i, left.i_prime, left.j_prime, right.j)


def compute_artiy_bound(lexicon: Dict[str, str]) -> int:
    """
    Computes the arity bound c_G given a lexicon
    As defined in section 5.2 of the paper: c_G >= max{l, a + d}
    where l is the maximum arity of a lexicon entry,
    a is the maximum arity
    d is the maximum degree of a composition
    :param lexicon: a dictionary mapping tokens (str) to a category (str)
    :return: The arity bound
    """
    raise NotImplementedError

def fast_ccg(lexicon: Dict[str, str], input_tokens: List[str]) -> Optional[Item]:
    """
    Parses a sentence from the given lexicon.
    This algorithm runs in O(N^6), where N is the input length. See section 4.4 of Kuhlmann, Satta 2014
    :param lexicon: a dictionary mapping tokens (str) to a category (str)
    :param input_tokens: the input words (tokens) to be parsed
    :return: An Item representing the parse of the entire input, or None if no parse is possible.
    """
    n = len(input_tokens)
    chart = [[[] for _ in range(n)] for _ in range(n)]

    # TODO: compute arity bound, for now, hard code arity bound
    # c_G = compute_arity_bound(lexicon)
    c_G = 3

    # Parse axioms CKY style
    for j in range(n):
        word = input_tokens[j]
        if word in lexicon:
            category = lexicon[word]
            chart[j][j].append(Item(category, j, j + 1))

    derivation_contexts = {}
    for length in range(2, n + 1):
        for i in range(n - length + 1):
            j = i + length - 1
            for k in range(i, j):
                for left_item in chart[i][k]:
                    for right_item in chart[k + 1][j]:
                        new_derivation_ctxt = None      
                        # Check if you can apply the rules
                        new_item = ccg_extend(left_item, right_item, c_G)
                        if (new_item and new_item.category[0] not in {'\\', '/'}
                                and new_item.category[-1] not in {'\\', '/'}):
                            chart[i][j].append(new_item)

                        # check if derivation ctxt
                        if isinstance(new_item, KuhlmannItem):
                            derivation_contexts.setdefault(new_item.category, left_item)
                            chart[i][j].append(new_item)
                            new_derivation_ctxt = new_item

                        # check if you can apply backward crossing
                        new_item = ccg_backward_crossing(left_item, right_item)
                        if (new_item and new_item.category[0] not in {'\\', '/'}
                                and new_item.category[-1] not in {'\\', '/'}):
                            chart[i][j].append(new_item)
                        elif isinstance(new_item, KuhlmannItem):
                            chart[i][j].append(new_item)
                            new_derivation_ctxt = new_item

                        # check if you can extend a derivation context:
                        if isinstance(left_item, KuhlmannItem) and isinstance(right_item, Item):
                            new_item = ccg_derivation_ctxt_extend(left_item, right_item, c_G)
                            if isinstance(new_item, KuhlmannItem):
                                chart[i][j].append(new_item)
                                new_derivation_ctxt = new_item

                        # naively check if derivation ctxt can be recombined
                        # TODO, rule 6
                        if new_derivation_ctxt and new_derivation_ctxt.β == '':
                            if new_derivation_ctxt.category in derivation_contexts:
                                left_ctxt = derivation_contexts[new_derivation_ctxt.category]
                                new_item = ccg_recombine(left_ctxt, new_derivation_ctxt, c_G)
                                if new_item:
                                    chart[i][j].append(new_item)

    # Look for a complete parse item [S;0,n]
    print(chart)
    for item in chart[0][n - 1]:
        if item.category == "S":
            return item
    return None


# left_item = KuhlmannItem('/Y', 'β/Z', 1, 1, 2, 2)
# right_item = Item('Zγ', 2, 3)
# ccg_derivation_ctxt_extend(left_item, right_item, 5)
#
#
# lexicon = {
#     "the": "NP/N",
#     "dog": "N",
#     "john": "NP",
#     "bit": r"S\NP/NP"
# }
#
# input_tokens = ["the", "dog", "bit", "john"]
#
# # Parse the input tokens
# parsed_item = fast_ccg(lexicon, input_tokens)
#
# if parsed_item:
#     print("Parsed Item:", parsed_item)
# else:
#     print("No valid parse found.")


#
lexicon = {
    "w1": "A",
    "w2": "B",
    "w3": r"C\A/F",
    "w4": r"S/E",
    "w5": r"E/H\C",
    "w6": r"F/G\B",
    "w7": "G",
    "w8": "H"
}

input_tokens = [f"w{i}" for i in range(1, 9)]
parsed_item = fast_ccg(lexicon, input_tokens)

if parsed_item:
    print("Parsed Item:", parsed_item)
else:
    print("No valid parse found.")

#
# lexicon = {
#     'Is': "S/NP/NP",
#     'this': "NP",
#     'your': "NP/N",
#     'bicycle': "N/Q",
#     '?': "Q"
# }
#
# input_tokens = ['Is', 'this', 'your', 'bicycle', '?']
# parsed_item = fast_ccg(lexicon, input_tokens)
#
# if parsed_item:
#     print("Parsed Item:", parsed_item)
# else:
#     print("No valid parse found.")
#
#
# lexicon = {
#     'Who': "S/(S/NP)",
#     'is': "(S/NP)/NP",
#     'he?': "NP",
# }
#
# input_tokens = ['Who', 'is', 'he?']
# parsed_item = fast_ccg(lexicon, input_tokens)
#
# if parsed_item:
#     print("Parsed Item:", parsed_item)
# else:
#     print("No valid parse found.")