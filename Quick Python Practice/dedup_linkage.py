# Problem. Find pairs of users that share the same bank_account (potential mule links).
rows = [
  {"user":"u1","bank":"bA"},
  {"user":"u2","bank":"bA"},
  {"user":"u3","bank":"bB"},
  {"user":"u4","bank":"bA"},
]

from collections import defaultdict
from itertools import combinations

def shared_bank_pairs(rows):
    by = defaultdict(list)
    for r in rows: by[r["bank"]].append(r["user"])
    pairs = set()
    for users in by.values():
        users = sorted(set(users))
        for a, b in combinations(users, 2):
            pairs.add((a, b))
    return pairs

print(shared_bank_pairs(rows)) # {("u1","u2"), ("u1","u4"), ("u2","u4")}
