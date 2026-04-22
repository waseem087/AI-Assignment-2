"""
csp.py - Core CSP Framework
AI2002 - Artificial Intelligence | Spring 2026 | Assignment 02
"""

class CSP:
    def __init__(self):
        self.variables   = []
        self.domains     = {}
        self.constraints = []
        self.neighbours  = {}

    def add_variable(self, var, domain):
        self.variables.append(var)
        self.domains[var]    = list(domain)
        self.neighbours[var] = set()

    def add_constraint(self, var_i, var_j, check_fn):
        self.constraints.append((var_i, var_j, check_fn))
        self.neighbours[var_i].add(var_j)
        self.neighbours[var_j].add(var_i)

    def is_consistent(self, var, value, assignment):
        for (vi, vj, fn) in self.constraints:
            if vi == var and vj in assignment:
                if not fn(value, assignment[vj]):
                    return False
            elif vj == var and vi in assignment:
                if not fn(assignment[vi], value):
                    return False
        return True

    def count_conflicts(self, var, value, assignment):
        count = 0
        for (vi, vj, fn) in self.constraints:
            if vi == var and vj in assignment:
                if not fn(value, assignment[vj]):
                    count += 1
            elif vj == var and vi in assignment:
                if not fn(assignment[vi], value):
                    count += 1
        return count

    def is_complete(self, assignment):
        return len(assignment) == len(self.variables)

    def get_unassigned(self, assignment):
        return [v for v in self.variables if v not in assignment]
