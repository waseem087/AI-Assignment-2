"""
heuristics.py - MRV, Degree, LCV Heuristics
AI2002 - Artificial Intelligence | Spring 2026 | Assignment 02

Fast _check_pair uses a cached per-pair constraint index (O(1) dict lookup)
instead of scanning all constraints (O(|C|) per call).
LCV caps neighbour inspection to 8 to stay tractable on large instances.
"""


def _build_constraint_index(csp):
    idx = {}
    for (a, b, fn) in csp.constraints:
        idx.setdefault((a, b), []).append(fn)
        def _rev(va, vb, f=fn): return f(vb, va)
        idx.setdefault((b, a), []).append(_rev)
    csp._constraint_index = idx


def _check_pair(csp, vi, vi_val, vj, vj_val):
    """Return True if all constraints between vi and vj are satisfied."""
    if not hasattr(csp, '_constraint_index'):
        _build_constraint_index(csp)
    for fn in csp._constraint_index.get((vi, vj), []):
        if not fn(vi_val, vj_val):
            return False
    return True


def select_unassigned_variable(csp, assignment, use_mrv=True, use_degree=True):
    unassigned = csp.get_unassigned(assignment)
    if not unassigned:
        return None
    if not use_mrv:
        return unassigned[0]

    def key(var):
        d = len(csp.domains[var])
        if use_degree:
            deg = sum(1 for n in csp.neighbours[var] if n not in assignment)
            return (d, -deg)
        return (d,)

    return min(unassigned, key=key)


def order_domain_values(csp, var, assignment, use_lcv=True, metrics=None):
    domain = list(csp.domains[var])
    if not use_lcv or len(domain) <= 1:
        return domain

    LCV_CAP = 8   # cap neighbours inspected to keep runtime tractable
    neighbours = sorted(
        [n for n in csp.neighbours[var] if n not in assignment],
        key=lambda n: len(csp.domains[n])
    )[:LCV_CAP]

    def cost(value):
        total = 0
        for nb in neighbours:
            for nval in csp.domains[nb]:
                if metrics:
                    metrics.record_check()
                if not _check_pair(csp, var, value, nb, nval):
                    total += 1
        return total

    return sorted(domain, key=cost)
