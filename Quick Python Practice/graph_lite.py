# Problem. Given edges user ↔ device, return connected components of users (users linked via shared devices).

edges = [
  ("u1","d1"),("u2","d1"),  # u1-u2 linked
  ("u3","d2"),("u4","d3"),("u3","d3")  # u3-u4 linked via d3
]

from collections import defaultdict, deque

def user_components(edges):
    g = defaultdict(set)
    users = set()
    for u, d in edges:
        users.add(u)
        g[u].add(d); g[d].add(u)  # bipartite

    seen, comps = set(), []
    for u in users:
        if u in seen: continue
        q, comp = deque([u]), set()
        seen.add(u)
        while q:
            x = q.popleft()
            comp.add(x) if x.startswith("u") else None
            for y in g[x]:
                if y not in seen:
                    seen.add(y); q.append(y)
        comps.append(comp)
    return comps


print(user_components(edges)) # [{"u1","u2"}, {"u3","u4"}]

# Practice on BFS (of DFS)