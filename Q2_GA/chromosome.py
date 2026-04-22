"""
chromosome.py - Chromosome Encoding/Decoding
AI2002 - Artificial Intelligence | Spring 2026 | Assignment 02

Encoding
--------
A chromosome is a dict keyed by student ID (S1..S5).
Each value is a list of exactly 5 course entries:

    chromosome = {
        'S1': [
            {'course_id': 'DS',  'section': 2},
            {'course_id': 'ALG', 'section': 1},
            ...   # 5 entries = 15 credits
        ],
        ...
    }

'section' (1-3) implicitly encodes day+time via the course catalog.

Why this encoding?
- Compact: 25 integers total for 5 students x 5 courses.
- Credit constraint naturally maintained (exactly 5 x 3-credit courses).
- Friend alignment: compare (course_id, section) pairs across students.
- Easy repair: change 'section' without touching course list structure.
"""

import copy


def decode_chromosome(chromosome, courses_catalog):
    """Expand section IDs into full schedule info for each student."""
    decoded = {}
    for sid, course_list in chromosome.items():
        decoded[sid] = []
        for entry in course_list:
            cid  = entry['course_id']
            sec  = entry['section']
            cdata = courses_catalog.get(cid)
            if not cdata:
                continue
            sec_data = next((s for s in cdata['sections']
                             if s['section_id'] == sec), None)
            if sec_data is None:
                continue
            decoded[sid].append({
                'course_id': cid,
                'section':   sec,
                'name':      cdata['name'],
                'type':      cdata['type'],
                'credits':   cdata['credits'],
                'difficulty':cdata['difficulty'],
                'schedule':  sec_data['schedule'],
                'professor': sec_data['professor'],
            })
    return decoded


def validate_chromosome(chromosome, courses_catalog, students_data):
    """Return (is_valid, [violation_strings])."""
    from utils import has_time_conflict, violates_blocked
    violations = []
    decoded    = decode_chromosome(chromosome, courses_catalog)

    for sid, course_list in decoded.items():
        req     = students_data[sid]
        blocked = req['time_preferences']['blocked']['slots']

        # Credit check
        credits = sum(c['credits'] for c in course_list)
        if credits != 15:
            violations.append(f"{sid}: credits={credits} != 15")

        # Time conflicts
        for i in range(len(course_list)):
            for j in range(i+1, len(course_list)):
                if has_time_conflict(course_list[i]['schedule'],
                                     course_list[j]['schedule']):
                    violations.append(
                        f"{sid}: time conflict {course_list[i]['course_id']} "
                        f"vs {course_list[j]['course_id']}")

        # Blocked times
        for c in course_list:
            if violates_blocked(c['schedule'], blocked):
                violations.append(
                    f"{sid}: {c['course_id']} hits blocked time")

        # Max 3 courses per day
        from collections import Counter
        day_cnt = Counter()
        for c in course_list:
            for s in c['schedule']:
                day_cnt[s['day']] += 1
        for day, cnt in day_cnt.items():
            if cnt > 3:
                violations.append(f"{sid}: {cnt} classes on {day} > 3")

        # Prerequisites (completed + this-semester courses satisfy them)
        completed = set(req['completed_courses'])
        this_sem  = {c['course_id'] for c in course_list}
        available = completed | this_sem
        for c in course_list:
            for prereq in courses_catalog[c['course_id']]['prerequisites']:
                if prereq not in available:
                    violations.append(
                        f"{sid}: missing prereq {prereq} for {c['course_id']}")

    return len(violations) == 0, violations


def chromosome_signature(chromosome):
    """Hashable signature for diversity comparison."""
    sig = []
    for sid in sorted(chromosome):
        for e in sorted(chromosome[sid], key=lambda x: x['course_id']):
            sig.append((sid, e['course_id'], e['section']))
    return tuple(sig)
