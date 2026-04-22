"""
algorithms.py - Backtracking, Forward Checking, MAC, Min-Conflicts
AI2002 - Artificial Intelligence | Spring 2026 | Assignment 02
AIMA 4th ed., Chapter 6.
"""

import copy, random, time
from collections import deque
from heuristics import select_unassigned_variable, order_domain_values, _check_pair
from metrics import Metrics

_TIMEOUT = 30.0   # per-solve wall-clock deadline (seconds)


# -- Algorithm 1: Plain Backtracking ----------------------------------

def backtracking_search(csp, use_mrv=False, use_degree=False, use_lcv=False,
                        metrics=None):
    if metrics is None: metrics = Metrics()
    metrics.start()
    saved    = copy.deepcopy(csp.domains)
    deadline = time.perf_counter() + _TIMEOUT
    result   = _backtrack({}, csp, use_mrv, use_degree, use_lcv,
                           metrics, None, deadline)
    metrics.stop()
    if result is None: csp.domains = saved
    return result, metrics


def _backtrack(assignment, csp, use_mrv, use_degree, use_lcv,
               metrics, inference, deadline):
    if time.perf_counter() > deadline: return None
    if csp.is_complete(assignment):    return assignment

    var = select_unassigned_variable(csp, assignment, use_mrv, use_degree)
    for value in order_domain_values(csp, var, assignment, use_lcv, metrics):
        metrics.record_check(
            sum(1 for (a, b, _) in csp.constraints
                if (a == var and b in assignment)
                or (b == var and a in assignment))
        )
        if csp.is_consistent(var, value, assignment):
            assignment[var] = value
            metrics.record_assignment()
            saved = copy.deepcopy(csp.domains)
            ok = True
            if   inference == 'fc':  ok, _ = _forward_check(csp, var, value, assignment, metrics)
            elif inference == 'mac': ok, _ = _mac(csp, var, assignment, metrics)
            if ok:
                result = _backtrack(assignment, csp, use_mrv, use_degree,
                                     use_lcv, metrics, inference, deadline)
                if result is not None: return result
            csp.domains = saved
            del assignment[var]
            metrics.record_backtrack()
    return None


# -- Algorithm 2: Forward Checking ------------------------------------

def forward_checking_search(csp, use_mrv=True, use_degree=True, use_lcv=True,
                             metrics=None):
    if metrics is None: metrics = Metrics()
    metrics.start()
    saved    = copy.deepcopy(csp.domains)
    deadline = time.perf_counter() + _TIMEOUT
    result   = _backtrack({}, csp, use_mrv, use_degree, use_lcv,
                           metrics, 'fc', deadline)
    metrics.stop()
    if result is None: csp.domains = saved
    return result, metrics


def _forward_check(csp, var, value, assignment, metrics):
    for nb in csp.neighbours[var]:
        if nb in assignment: continue
        to_remove = []
        for nval in csp.domains[nb]:
            metrics.record_check()
            if not _check_pair(csp, var, value, nb, nval):
                to_remove.append(nval)
        for v in to_remove:
            csp.domains[nb].remove(v)
        if not csp.domains[nb]:
            return False, {}
    return True, {}


# -- Algorithm 3: MAC (AC-3) ------------------------------------------

def mac_search(csp, use_mrv=True, use_degree=True, use_lcv=True,
               metrics=None):
    if metrics is None: metrics = Metrics()
    metrics.start()
    saved    = copy.deepcopy(csp.domains)
    deadline = time.perf_counter() + _TIMEOUT
    result   = _backtrack({}, csp, use_mrv, use_degree, use_lcv,
                           metrics, 'mac', deadline)
    metrics.stop()
    if result is None: csp.domains = saved
    return result, metrics


def _mac(csp, var, assignment, metrics):
    queue = deque()
    for (vi, vj, _) in csp.constraints:
        if vi not in assignment: queue.append((vi, vj))
        if vj not in assignment: queue.append((vj, vi))
    return _ac3(csp, queue, assignment, metrics), {}


def _ac3(csp, queue, assignment, metrics):
    while queue:
        xi, xj = queue.popleft()
        if _revise(csp, xi, xj, assignment, metrics):
            if not csp.domains[xi]: return False
            for xk in csp.neighbours[xi]:
                if xk != xj: queue.append((xk, xi))
    return True


def _revise(csp, xi, xj, assignment, metrics):
    xj_vals   = [assignment[xj]] if xj in assignment else csp.domains[xj]
    to_remove = []
    for xi_val in list(csp.domains[xi]):
        supported = False
        for xj_val in xj_vals:
            metrics.record_check()
            if _check_pair(csp, xi, xi_val, xj, xj_val):
                supported = True
                break          # early exit: one support is enough
        if not supported:
            to_remove.append(xi_val)
    for v in to_remove:
        csp.domains[xi].remove(v)
    return len(to_remove) > 0


# -- Algorithm 4: Min-Conflicts ---------------------------------------

def min_conflicts_search(csp, max_steps=10000, metrics=None):
    if metrics is None: metrics = Metrics()
    metrics.start()
    assignment = {}
    for var in csp.variables:
        if csp.domains[var]:
            assignment[var] = random.choice(csp.domains[var])
        else:
            metrics.stop(); return None, metrics
    metrics.record_assignment()
    for _ in range(max_steps):
        conflicted = [v for v in csp.variables
                      if _has_conflict(csp, v, assignment[v], assignment, metrics)]
        if not conflicted:
            metrics.stop(); return assignment, metrics
        var      = random.choice(conflicted)
        best_val = min(csp.domains[var],
                       key=lambda v: csp.count_conflicts(var, v, assignment))
        metrics.record_check(len(csp.domains[var]))
        assignment[var] = best_val
        metrics.record_assignment()
    metrics.stop()
    return None, metrics


def _has_conflict(csp, var, value, assignment, metrics):
    for nb in csp.neighbours[var]:
        if nb not in assignment: continue
        metrics.record_check()
        if not _check_pair(csp, var, value, nb, assignment[nb]):
            return True
    return False
