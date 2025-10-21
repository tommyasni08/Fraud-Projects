# Problem: Count distinct users per device_id and return top-N by that count (ties by device_id asc).

logs = [
  {"user":"u1","device":"dA"}, {"user":"u2","device":"dA"},
  {"user":"u2","device":"dB"}, {"user":"u3","device":"dB"},
  {"user":"u4","device":"dA"}
]
N = 2

from collections import defaultdict

def top_shared_devices(logs, N):
    m = defaultdict(set)
    for r in logs:
        m[r["device"]].add(r["user"])
    pairs = [(d, len(users)) for d, users in m.items()]
    pairs.sort(key=lambda x: (-x[1], x[0]))
    return pairs[:N]

print(top_shared_devices(logs, N)) # [("dA", 3), ("dB", 2)]
