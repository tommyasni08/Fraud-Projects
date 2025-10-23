# Problem. Stream of (policy, risk_score) → keep top-K risk scores per policy.

stream = [("p1",0.7),("p1",0.9),("p2",0.6),("p1",0.85),("p2",0.95)]
K = 2

import heapq
from collections import defaultdict

def topk_per_policy(stream, K):
    heaps = defaultdict(list)  # min-heaps
    for p, s in stream:
        h = heaps[p]
        if len(h) < K:
            heapq.heappush(h, s)
        else:
            if s > h[0]:
                heapq.heapreplace(h, s)
    # sort desc for presentation
    return {p: sorted(h, reverse=True) for p, h in heaps.items()}

print(topk_per_policy(stream,K)) # {"p1":[0.9,0.85],"p2":[0.95,0.6]}
