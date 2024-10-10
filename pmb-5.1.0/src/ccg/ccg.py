import re
from typing import Self, Optional, Union, List, Dict


class Item:
    """
    The CKY-style algorithm uses a logic with items of the form [X;i,j] where X is a category
    and i,j are fencepost positions in w.  The goal of the algorithm is the construction
    of the item [S;0,n], which asserts the existence of a derivation tree for the entire input string.
    """

    def __init__(self, category: str, i: int, j: int):
        # TODO: Some way to check the arity of the category is bounded by some arity constraint
        self.category = category
        self.i = i
        self.j = j

    def __repr__(self):
        return f"Item({self.category}, {self.i}, {self.j})"


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


def is_axiom(item: Item) -> bool:
    return item.i == item.j + 1



def cky_forward(left: Item, right: Item) -> Union[None, Item]:
    """
    Applies the CKY style forward rule if possible
    :param left: left item in the form [X/Y, i, j]
    :param right: right item in the form [Yβ, j, k]
    :return: new item in the form [Xβ, i, j]

    >>> left_item = Item("S/NP/VP", 0, 1)
    >>> right_item = Item("VP", 1, 2)
    >>> cky_forward(left_item, right_item)
    Item(S/NP, 0, 2)
    """
    category = left.category
    # We need to get all possible parts, for example: A/B\C/D\F/G then
    # B\C/D\F/G, D\F/G, G are all possible arguments we can expect with different return types.
    print(left, right)
    # TODO: no brackets assumed! Loop over cat using a stack, whatever inside a bracket replace with a special char
    parts = {category[:x.span()[0]]: category[x.span()[0] + 1:] for x in re.finditer(r'/([^/\\]+)', category)}
    for func_type, expected_arg in parts.items():
        right_category = right.category
        if right_category.startswith(expected_arg):
            β = right_category[len(expected_arg):]
            print()
            new_category = f"{func_type}{β}" if β else func_type
            new_item = Item(new_category, left.i, right.j)
            return new_item

    return None


def cky_backward(left: Item, right: Item) -> Union[None, Item]:
    """
    Applies the CKY style backward rule if possible.
    :param left: left item in the form [X\\Y, i, j]
    :param right: right item in the form [Yβ, j, k]
    :return: new item in the form [Xβ, i, j] or None if not applicable.
    >>> left_item = Item("A\\B/C\\D", 0, 1)
    >>> right_item = Item("B/C\\D", 1, 2)
    >>> cky_backward(left_item, right_item)
    Item(A, 0, 2)
    """
    category = left.category
    # We need to get all possible parts, for example: A\B/C\D\F then
    # B/C\\D\\F, C\D\\F, F are all possible arguments we can expect with different return types.

    parts = {category[:x.span()[0]]: category[x.span()[0] + 1:] for x in re.finditer(r'\\([^/\\]+)', category)}
    for func_type, expected_arg in parts.items():
        right_category = right.category
        # Check if the right category matches the expected argument
        if right_category.startswith(expected_arg):
            β = right_category[len(expected_arg):]
            new_category = f"{func_type}{β}" if β else func_type
            new_item = Item(new_category, left.i, right.j)
            return new_item

    return None


def cky_backward_crossing(left: Item, right: Item) -> Union[None, Item]:
    """
    Applies the CKY style backward crossing rule if possible.
    :param left: left item in the form [Yβ, i, j]
    :param right: right item in the form [X/Y, j, k]
    :return: new item in the form [Xβ, i, k] or None if not applicable.
    """
    category = right.category
    # Extract backward-slash components
    parts = {category[:x.span()[0]]: category[x.span()[0] + 1:] for x in re.finditer(r'\\([^/\\]+)', category)}
    for func_type, expected_arg in parts.items():
        right_category = left.category
        # Check if the left category matches the expected argument
        if right_category.startswith(expected_arg):
            β = right_category[len(expected_arg):]
            new_category = f"{func_type}" if β == "" else f"{func_type}{β}"
            new_item = Item(new_category, left.i, right.j)
            return new_item

    return None


def cky_parse(lexicon: Dict[str, str], input_tokens: List[str]) -> Optional[Item]:
    """
    Parses a sentence from the given lexicon.
    This algorithm runs exponential in the input length! See section 3.2 of Kuhlmann, Satta 2014
    :param lexicon: a dictionary mapping tokens (str) to a category (str)
    :param input_tokens: the input words (tokens) to be parsed
    :return: An Item representing the parse of the entire input, or None if no parse is possible.
    """
    n = len(input_tokens)
    chart = [[[] for _ in range(n)] for _ in range(n)]

    for j in range(n):
        word = input_tokens[j]
        if word in lexicon:
            category = lexicon[word]
            chart[j][j].append(Item(category, j, j + 1))

    for length in range(2, n + 1):
        for i in range(n - length + 1):
            j = i + length - 1
            for k in range(i, j):
                for left_item in chart[i][k]:
                    for right_item in chart[k + 1][j]:
                        new_item = cky_forward(left_item, right_item)
                        print(new_item)

                        if (new_item and new_item.category[0] not in {'\\', '/'}
                                and new_item.category[-1] not in {'\\', '/'}):
                            chart[i][j].append(new_item)

                        new_item = cky_backward(left_item, right_item)
                        if (new_item and new_item.category[0] not in {'\\', '/'}
                                and new_item.category[-1] not in {'\\', '/'}):
                            chart[i][j].append(new_item)

                        new_item = cky_backward_crossing(left_item, right_item)
                        if (new_item and new_item.category[0] not in {'\\', '/'}
                                and new_item.category[-1] not in {'\\', '/'}):
                            chart[i][j].append(new_item)

    # Look for a complete parse item [S;0,n]
    print(chart)
    for item in chart[0][n - 1]:
        if item.category == "S":
            return item
    return None


lexicon = {
    "the": "NP/N",
    "dog": "N",
    "john": "NP",
    "bit": r"S\NP/NP"
}

input_tokens = ["the", "dog", "bit", "john"]

# Parse the input tokens
parsed_item = cky_parse(lexicon, input_tokens)

if parsed_item:
    print("Parsed Item:", parsed_item)
else:
    print("No valid parse found.")

lexicon = {
    "w1" : "A",
    "w2" : "B",
    "w3" : r"C\A/F",
    "w4" : r"S\E",
    "w5" : r"E/H\C",
    "w6" : r"F/G\B",
    "w7" : "G",
    "w8" : "H"
}

input_tokens = [f"w{i}" for i in range(1, 9)]
parsed_item = cky_parse(lexicon, input_tokens)

if parsed_item:
    print("Parsed Item:", parsed_item)
else:
    print("No valid parse found.")