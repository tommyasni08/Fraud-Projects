# Problem. Flag users with > k claims in any T-minute window.

events = [
 ("u1","2025-10-16T09:00:00Z"),
 ("u2","2025-10-16T09:00:10Z"),
 ("u1","2025-10-16T09:01:00Z"),
 ("u1","2025-10-16T09:02:00Z"),
 ("u1","2025-10-16T09:05:00Z"),
]
k, T = 3, 5

from collections import defaultdict, deque
from datetime import datetime, timedelta

def parse_iso(ts):
    return datetime.fromisoformat(ts.replace("Z","+00:00"))

def bursty_users(events, k, T_minutes):
    per = defaultdict(list)
    for u, ts in events: per[u].append(parse_iso(ts))
    viol = set()
    window = timedelta(minutes=T_minutes)
    for u, times in per.items():
        times.sort()
        dq = deque()
        for t in times:
            dq.append(t)
            while dq and t - dq[0] > window:
                dq.popleft()
            if len(dq) > k:
                viol.add(u); break
    return sorted(viol)

print(bursty_users(events, k, T)) # ["u1"]
