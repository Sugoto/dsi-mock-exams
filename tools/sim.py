"""Small simulators used to compute (not hand-derive) numeric answer keys."""


def lru(cap, trace):
    """Return (misses, evictions) for an LRU buffer that starts empty."""
    order, misses, evictions = [], 0, []
    for p in trace:
        if p in order:
            order.remove(p)
            order.append(p)
            continue
        misses += 1
        if len(order) == cap:
            evictions.append(order.pop(0))
        order.append(p)
    return misses, evictions


def twoq(cap, trace):
    """Course 2Q: shared capacity; first touch -> FIFO; hit in FIFO -> LRU (MRU end);
    hit in LRU -> MRU end; on a full miss evict FIFO head if FIFO nonempty, else LRU head."""
    fifo, hot, misses, evictions = [], [], 0, []
    for p in trace:
        if p in fifo:
            fifo.remove(p)
            hot.append(p)
        elif p in hot:
            hot.remove(p)
            hot.append(p)
        else:
            misses += 1
            if len(fifo) + len(hot) == cap:
                evictions.append(fifo.pop(0) if fifo else hot.pop(0))
            fifo.append(p)
    return misses, evictions, fifo, hot


def double_hash(size, keys, h2):
    table, slots = [None] * size, {}
    for k in keys:
        for i in range(size):
            s = (k % size + i * h2(k)) % size
            if table[s] is None:
                table[s] = k
                slots[k] = s
                break
        else:
            raise ValueError(f"double hashing could not place {k}")
    return slots


def quadratic(size, keys):
    """Return (slots, total probes) for (h + i^2) mod size inserts into an empty table."""
    table, slots, probes = [None] * size, {}, 0
    for k in keys:
        for i in range(size):
            s = (k % size + i * i) % size
            probes += 1
            if table[s] is None:
                table[s] = k
                slots[k] = s
                break
        else:
            raise ValueError(f"quadratic probing could not place {k}")
    return slots, probes


EMPTY, TOMB = "empty", "tomb"


def linear_ops(cap, ops):
    """Linear probing with tombstones. ops: ('ins', key) or ('del', key).
    Lookup stops at never-used, skips tombstones. Insert remembers the first tombstone,
    keeps probing for an existing copy of the key (update in place), else reuses the
    tombstone, else uses the never-used slot. Returns the slot of the last insert."""
    table = [EMPTY] * cap
    last = None
    for op, k in ops:
        first_tomb, target = None, None
        for i in range(cap):
            s = (k + i) % cap
            if table[s] == EMPTY:
                target = s if first_tomb is None else first_tomb
                break
            if table[s] == TOMB:
                if first_tomb is None:
                    first_tomb = s
                continue
            if table[s] == k:
                target = s
                break
        if op == "ins":
            if target is None:
                target = first_tomb
            table[target] = k
            last = target
        else:
            if target is not None and table[target] == k:
                table[target] = TOMB
    return last


def free_list(n_occupied, ops):
    """Fixed-length slots 0..n-1 occupied; deletes push onto the free-list head;
    inserts pop the head, or use next_unused if the list is empty."""
    free, nxt, last = [], n_occupied, None
    for op in ops:
        if op == "ins":
            if free:
                last = free.pop(0)
            else:
                last, nxt = nxt, nxt + 1
        else:
            free.insert(0, op[1])
    return last


def max_disjoint(edges):
    best = 0

    def go(i, used, count):
        nonlocal best
        best = max(best, count)
        if i == len(edges) or count + (len(edges) - i) <= best:
            return
        a, b = edges[i]
        if a not in used and b not in used:
            go(i + 1, used | {a, b}, count + 1)
        go(i + 1, used, count)

    go(0, frozenset(), 0)
    return best


def rw_proceed(cap, requests):
    """requests: list of ('r'|'w', key). Granted requests hold their lock for the step;
    blocked requests hold nothing."""
    held, ok = {}, 0
    for mode, k in requests:
        s = k % cap
        cur = held.get(s, [])
        if (mode == "r" and "w" not in cur) or (mode == "w" and not cur):
            held[s] = cur + [mode]
            ok += 1
    return ok


def join_count(r, s):
    return sum(r.count(k) * s.count(k) for k in set(r))


def linear_slots(cap, keys):
    """Plain linear-probing inserts into an empty table. Returns {key: slot}."""
    table, slots = [None] * cap, {}
    for k in keys:
        for i in range(cap):
            s = (k + i) % cap
            if table[s] is None:
                table[s] = k
                slots[k] = s
                break
    return slots


def lookup_probes(cap, ops, key):
    """Slots examined by a linear-probing lookup for `key` after ops (see linear_ops rules).
    Stops at a never-used slot (counted) or at the key."""
    table = [EMPTY] * cap
    for op, k in ops:
        for i in range(cap):
            s = (k + i) % cap
            if op == "ins" and table[s] in (EMPTY, TOMB):
                table[s] = k
                break
            if op == "del" and table[s] == k:
                table[s] = TOMB
                break
            if op == "del" and table[s] == EMPTY:
                break
    probes = 0
    for i in range(cap):
        probes += 1
        s = (key + i) % cap
        if table[s] == EMPTY or table[s] == key:
            break
    return probes


# --- Validate against answers known from the course practice sheet -------------
assert twoq(5, [1, 2, 1, 3, 2, 4, 5, 6, 1, 2, 7, 8, 1, 2])[1][2] == 5
assert twoq(3, [1, 2, 1, 3, 4])[1][0] == 2
_, _, f, h = twoq(10, [1, 2, 1, 3, 2])
assert f == [3] and h == [1, 2]
assert sum(double_hash(10, [2, 12, 22, 32], lambda k: 1 + k % 9)[k] for k in (12, 22, 32)) == 21
assert quadratic(10, [2, 12, 22, 32])[1] == 10
assert free_list(10, [("d", 3), ("d", 7), "ins", ("d", 2), "ins", "ins", "ins"]) == 10
m, ev = lru(4, [1, 2, 3, 4, 1, 5, 6, 1, 2])
assert (m + len(ev)) * 8192 == 81920
assert max_disjoint([(1, 2), (2, 3), (3, 1), (4, 5), (5, 6), (7, 8), (8, 9)]) == 3
assert rw_proceed(10, [("w", 12), ("r", 22), ("r", 32), ("r", 47), ("w", 57), ("r", 68)]) == 3
assert linear_ops(10, [("ins", 15), ("ins", 25)]) == 6
assert join_count([1, 1, 1, 2, 2, 4], [1, 1, 2, 2, 2, 2, 3, 3, 3, 4]) == 15
