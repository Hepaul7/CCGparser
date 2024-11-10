import time
from ccg import cky_parse
from fast_ccg import fast_ccg

# Lexicon and input tokens
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

# Timing CKY parse
start_time = time.time()
naive_item = cky_parse(lexicon, input_tokens)
cky_duration = time.time() - start_time
print(f"CKY Parse time: {cky_duration:.6f} seconds")

# Timing Fast CCG parse
start_time = time.time()
parsed_item = fast_ccg(lexicon, input_tokens)
fast_ccg_duration = time.time() - start_time
print(f"Fast CCG Parse time: {fast_ccg_duration:.6f} seconds")

# Output result for fast_ccg
if parsed_item:
    print("Parsed Item:", parsed_item)
else:
    print("No valid parse found.")
