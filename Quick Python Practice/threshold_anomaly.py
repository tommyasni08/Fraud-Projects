# Problem. Flag claims whose amount is more than k standard deviations above user’s mean.

rows = [("u1",100),("u1",110),("u1",500),("u2",50),("u2",49)]
k = 2

from collections import defaultdict
import math

def stddev(vals):
    n = len(vals)
    if n < 2: return 0.0
    mu = sum(vals)/n
    var = sum((x-mu)**2 for x in vals)/(n-1)
    return mu, math.sqrt(var)

def high_amount_anomalies(rows, k):
    by = defaultdict(list)
    for u, amt in rows: by[u].append(amt)
    flagged = []
    for u, vals in by.items():
        mu, sd = stddev(vals)
        if sd == 0: continue
        for v in vals:
            if v > mu + k*sd: flagged.append((u, v))
    return flagged

print(high_amount_anomalies(rows, k)) # [("u1", 500)]
