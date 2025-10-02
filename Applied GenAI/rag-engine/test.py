import inspect
from rank_bm25 import BM25Okapi

print("--- Diagnostic Report ---")

# 1. Self-contained data from your example
corpus = [
    "Hello there good man!",
    "It is quite windy in London",
    "How is the weather today?"
]
tokenized_corpus = [doc.split(" ") for doc in corpus]

# 2. Model instantiation
bm25 = BM25Okapi(tokenized_corpus)
attribute_to_test = bm25.doc_freqs

# 3. Run diagnostic tests on the attribute
print(f"Type of bm25.doc_freqs: {type(attribute_to_test)}")
print(f"Length of bm25.doc_freqs: {len(attribute_to_test)}")

# 4. Show the contents based on its type
if isinstance(attribute_to_test, dict):
    print("Contents (as a dictionary):")
    # Show the first 5 items if it's a dict
    print(list(attribute_to_test.items())[:5])
elif isinstance(attribute_to_test, list):
    print("Contents (as a list):")
    # Show the first item if it's a list
    print(attribute_to_test[0])
else:
    print(f"Contents (other type): {attribute_to_test}")

# 5. Find out EXACTLY where the library is installed (The most important test)
try:
    file_path = inspect.getfile(BM25Okapi)
    print(f"\nThe BM25Okapi class is being loaded from this file:\n{file_path}")
except TypeError:
    print("\nCould not determine the file path (this can happen in some interactive environments).")

print("\n--- End of Report ---")