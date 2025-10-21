# Problem. For each user, output the running total of claim amount ordered by time.

events = [
  ("u1", 100, 1), ("u1", 50, 2), ("u2", 500, 1), ("u1", 10, 3)
]  # (user, amount, time_rank)

from collections import defaultdict

def running_user_totals(events):
    by = defaultdict(list)
    for u, amt, t in events: by[u].append((t, amt))
    out = []
    for u, lst in by.items():
        lst.sort()
        s = 0
        for t, amt in lst:
            s += amt
            out.append((u, t, s))
    out.sort()  # optional stable presentation
    return out

print(running_user_totals(events)) # [("u1",1,100), ("u1",2,150), ("u1",3,160), ("u2",1,500)]
