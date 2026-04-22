"""
timetable.py - University Timetabling CSP
AI2002 - Artificial Intelligence | Spring 2026 | Assignment 02
"""

import csv, copy
from csp import CSP


def load_courses(path):
    courses = {}
    with open(path, newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            row = {k.strip(): v.strip() for k, v in row.items()}
            courses[row['CourseID']] = {
                'name':       row['CourseName'],
                'instructor': row['Instructor'],
                'enrollment': int(row['Enrollment']),
                'duration':   int(row['Duration']),
                'features':   set(row['RoomFeatures'].split(';')),
            }
    return courses


def load_rooms(path):
    rooms = {}
    with open(path, newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            row = {k.strip(): v.strip() for k, v in row.items()}
            rooms[row['RoomID']] = {
                'building': row['Building'],
                'capacity': int(row['Capacity']),
                'features': set(row['Features'].split(';')),
            }
    return rooms


def load_timeslots(path):
    slots = {}
    with open(path, newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            row = {k.strip(): v.strip() for k, v in row.items()}
            slots[row['SlotID']] = {
                'days':     row['Days'],
                'start':    row['StartTime'],
                'duration': int(row['Duration']),
            }
    return slots


def load_students(path):
    enrollment = {}
    with open(path, newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            row = {k.strip(): v.strip() for k, v in row.items()}
            sid = row['StudentID']
            for cid in row['EnrolledCourses'].split(';'):
                cid = cid.strip()
                if cid:
                    enrollment.setdefault(cid, set()).add(sid)
    return enrollment


def load_availability(path):
    avail = {}
    with open(path, newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            row = {k.strip(): v.strip() for k, v in row.items()}
            avail[row['Instructor']] = {
                'available': [s.strip() for s in row['AvailableSlots'].split(';') if s.strip()],
                'preferred': [s.strip() for s in row['PreferredSlots'].split(';') if s.strip()],
            }
    return avail


class TimetableCSP(CSP):
    def __init__(self, courses, rooms, timeslots, student_enrollment,
                 availability=None):
        super().__init__()
        self.courses            = courses
        self.rooms              = rooms
        self.timeslots          = timeslots
        self.student_enrollment = student_enrollment
        self.availability       = availability or {}
        self._build()

    def _build(self):
        # Step 1: unary domain pruning
        for cid, course in self.courses.items():
            domain = []
            for sid, slot in self.timeslots.items():
                if slot['duration'] != course['duration']:
                    continue
                inst = course['instructor']
                if inst in self.availability:
                    if sid not in self.availability[inst]['available']:
                        continue
                for rid, room in self.rooms.items():
                    if not course['features'].issubset(room['features']):
                        continue
                    if room['capacity'] < course['enrollment']:
                        continue
                    domain.append((sid, rid))
            self.add_variable(cid, domain)

        # Step 2: binary constraints between every pair
        cids = list(self.courses.keys())
        for i in range(len(cids)):
            for j in range(i + 1, len(cids)):
                ci, cj = cids[i], cids[j]
                self.add_constraint(ci, cj, self._make_check(ci, cj))

    def _make_check(self, ci, cj):
        ci_inst   = self.courses[ci]['instructor']
        cj_inst   = self.courses[cj]['instructor']
        same_inst = (ci_inst == cj_inst)
        ci_stu    = self.student_enrollment.get(ci, set())
        cj_stu    = self.student_enrollment.get(cj, set())
        shared_st = bool(ci_stu & cj_stu)
        ci_cap    = self.courses[ci]['enrollment']
        cj_cap    = self.courses[cj]['enrollment']

        def check(vi, vj):
            si, ri = vi
            sj, rj = vj
            if si == sj and ri == rj:  return False   # room occupancy
            if same_inst and si == sj: return False   # instructor conflict
            if shared_st and si == sj: return False   # student conflict
            if ri == rj and si != sj:                 # capacity cross-check
                room = self.rooms[ri]
                if room['capacity'] < ci_cap: return False
                if room['capacity'] < cj_cap: return False
            return True

        return check


def _fmt_time(start, duration):
    h, m = map(int, start.split(':'))
    em = m + duration
    eh = h + em // 60
    em %= 60
    return f"{start}-{eh:02d}:{em:02d}"


def print_solution(assignment, csp, algo_name, metrics, status="SOLUTION FOUND"):
    courses   = csp.courses
    rooms     = csp.rooms
    timeslots = csp.timeslots
    n_total   = len(csp.variables)
    n_sched   = len(assignment) if assignment else 0

    print("=" * 60)
    print("UNIVERSITY TIMETABLE SOLUTION")
    print("=" * 60)
    print(f"Algorithm : {algo_name}")
    print(f"Status    : {status}")
    print("=" * 60)

    if assignment:
        print("\nCOURSE SCHEDULE:")
        print("-" * 40)
        for cid in sorted(assignment):
            sid, rid  = assignment[cid]
            slot      = timeslots[sid]
            room      = rooms[rid]
            course    = courses[cid]
            tstr      = _fmt_time(slot['start'], slot['duration'])
            print(f"{cid}: {course['name']}")
            print(f"  Instructor : {course['instructor']}")
            print(f"  Time Slot  : {sid} ({slot['days']} {tstr})")
            print(f"  Room       : {rid} ({room['building']}, Cap:{room['capacity']})")
            print(f"  Enrolled   : {course['enrollment']}")

    print("\n" + "=" * 60)
    print("SCHEDULE GRID VIEW")
    print("=" * 60)
    if assignment:
        slot_ids = sorted(timeslots.keys())
        room_ids = sorted(rooms.keys())
        col_w    = 12
        header   = f"{'Room':<10}" + "".join(f"{s:^{col_w}}" for s in slot_ids)
        print(header)
        print("-" * len(header))
        srmap = {(rid, sid): cid for cid, (sid, rid) in assignment.items()}
        for rid in room_ids:
            row = f"{rid:<10}"
            for sid in slot_ids:
                cell = srmap.get((rid, sid), "[EMPTY]")
                row += f"{cell:^{col_w}}"
            print(row)

    print("\n" + "=" * 60)
    print("PERFORMANCE METRICS")
    print("=" * 60)
    m = metrics.summary()
    print(f"Total Courses Scheduled : {n_sched}/{n_total}")
    print(f"Variable Assignments    : {m['assignments']}")
    print(f"Backtracks              : {m['backtracks']}")
    print(f"Constraint Checks       : {m['constraint_checks']}")
    print(f"Execution Time          : {m['elapsed']:.4f} seconds")
    if assignment and n_sched == n_total:
        print("Solution Quality        : All hard constraints satisfied")
    elif assignment:
        print("Solution Quality        : Partial solution")
    else:
        print("Solution Quality        : UNSATISFIABLE / TIMEOUT")
    print("=" * 60)
