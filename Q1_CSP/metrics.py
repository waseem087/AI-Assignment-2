"""
metrics.py - Performance Tracking
AI2002 - Artificial Intelligence | Spring 2026 | Assignment 02
"""
import time

class Metrics:
    def __init__(self):
        self.assignments      = 0
        self.backtracks       = 0
        self.constraint_checks = 0
        self.start_time       = None
        self.end_time         = None

    def start(self):
        self.assignments = self.backtracks = self.constraint_checks = 0
        self.start_time  = time.perf_counter()
        self.end_time    = None

    def stop(self):
        self.end_time = time.perf_counter()

    @property
    def elapsed(self):
        if self.start_time is None:
            return 0.0
        end = self.end_time or time.perf_counter()
        return end - self.start_time

    def record_assignment(self):  self.assignments      += 1
    def record_backtrack(self):   self.backtracks       += 1
    def record_check(self, n=1):  self.constraint_checks += n

    def summary(self):
        return {
            "assignments":       self.assignments,
            "backtracks":        self.backtracks,
            "constraint_checks": self.constraint_checks,
            "elapsed":           round(self.elapsed, 4),
        }
