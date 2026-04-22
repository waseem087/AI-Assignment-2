"""
utils.py - Helper Functions
AI2002 - Artificial Intelligence | Spring 2026 | Assignment 02
"""

import json, copy, random, itertools
from collections import defaultdict

STUDENT_IDS = ['S1', 'S2', 'S3', 'S4', 'S5']


# -- Data Loaders ------------------------------------------------------

def load_data(catalog_path="course_catalog.json",
              students_path="student_requirements.json",
              config_path="config.yaml"):
    with open(catalog_path, 'r') as f:
        catalog = json.load(f)
    with open(students_path, 'r') as f:
        students_raw = json.load(f)
    try:
        import yaml
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
    except Exception:
        config = _default_config()
    return (catalog['courses'],
            students_raw['students'],
            students_raw['friend_pairs'],
            config)


def _default_config():
    return {
        'population': {'size': 60,
                       'elitism': {'rate': 0.10},
                       'initialization_strategy': {
                           'random_valid': 0.40,
                           'greedy_time':  0.40,
                           'greedy_friend':0.20}},
        'crossover': {'probability': 0.80},
        'mutation':  {'base_rates': {
                          'section_change': 0.12,
                          'course_swap':    0.10,
                          'time_shift':     0.08,
                          'friend_align':   0.15},
                      'adaptive': {
                          'diversity_threshold': 0.30,
                          'rate_multiplier':     1.5,
                          'check_interval':      10}},
        'termination': {'max_generations': 300,
                        'convergence': {'patience': 40,
                                        'improvement_threshold': 0.001},
                        'similarity':  {'threshold': 0.85, 'tolerance': 0.02}},
        'fitness': {'weights': {'time_preference': 0.30,
                                'gap_minimization': 0.25,
                                'friend_satisfaction': 0.20,
                                'workload_balance': 0.15,
                                'lunch_break': 0.10},
                    'penalties': {'hard_constraint': -1000,
                                  'time_conflict':   -1000,
                                  'missing_credits': -800,
                                  'too_many_courses':-500,
                                  'blocked_time':    -1000}},
    }


# -- Schedule helpers --------------------------------------------------

def get_course_schedule(course_id, section_id, courses):
    cdata = courses.get(course_id)
    if not cdata:
        return []
    for sec in cdata['sections']:
        if sec['section_id'] == section_id:
            return sec['schedule']
    return []


def has_time_conflict(schedule1, schedule2):
    s1 = {(s['day'], s['time']) for s in schedule1 if 'day' in s and 'time' in s}
    s2 = {(s['day'], s['time']) for s in schedule2 if 'day' in s and 'time' in s}
    return bool(s1 & s2)


def violates_blocked(schedule, blocked_slots):
    blocked_set = {(b['day'], b['time']) for b in blocked_slots}
    for s in schedule:
        if (s.get('day'), s.get('time')) in blocked_set:
            return True
    return False


def available_sections(course_id, courses_catalog, student_data,
                        existing_courses, _unused=None):
    """Return section IDs (1-3) that are conflict- and blocked-free."""
    blocked_set = {(b['day'], b['time'])
                   for b in student_data['time_preferences']['blocked']['slots']}
    # Build used slots from existing courses
    used = set()
    for ec in existing_courses:
        for s in get_course_schedule(ec['course_id'], ec['section'],
                                     courses_catalog):
            used.add((s.get('day'), s.get('time')))

    valid = []
    course = courses_catalog.get(course_id)
    if not course:
        return [1]
    for sec in course['sections']:
        sec_slots = {(s.get('day'), s.get('time')) for s in sec['schedule']}
        if sec_slots & blocked_set:
            continue
        if sec_slots & used:
            continue
        valid.append(sec['section_id'])
    return valid


def get_valid_electives(_, student_data, courses_catalog):
    """Electives whose prereqs are satisfied by completed + this-sem core."""
    completed = set(student_data['completed_courses'])
    core      = set(student_data['required_courses']['core'])
    available = completed | core
    pool      = student_data['required_courses'].get('elective_pool', [])
    valid     = [c for c in pool
                 if set(courses_catalog[c]['prerequisites']).issubset(available)]
    return valid if valid else list(pool)


def repair_time_conflicts(sid, student_courses, student_data,
                           courses_catalog, max_attempts=10):
    """Fix time conflicts by reassigning sections. Never drops courses."""
    courses     = copy.deepcopy(student_courses)
    blocked_set = {(b['day'], b['time'])
                   for b in student_data['time_preferences']['blocked']['slots']}

    for _ in range(max_attempts):
        conflict_idx = None
        n = len(courses)
        for i in range(n):
            si = get_course_schedule(courses[i]['course_id'],
                                     courses[i]['section'], courses_catalog)
            si_slots = {(s.get('day'), s.get('time')) for s in si}
            if si_slots & blocked_set:
                conflict_idx = i; break
            for j in range(i+1, n):
                sj = get_course_schedule(courses[j]['course_id'],
                                         courses[j]['section'], courses_catalog)
                if has_time_conflict(si, sj):
                    conflict_idx = random.choice([i, j]); break
            if conflict_idx is not None:
                break
        if conflict_idx is None:
            break
        idx  = conflict_idx
        cid  = courses[idx]['course_id']
        others = [courses[k] for k in range(n) if k != idx]
        valid  = available_sections(cid, courses_catalog, student_data,
                                     others, courses_catalog)
        if valid:
            courses[idx]['section'] = random.choice(valid)
        else:
            all_secs = [s['section_id']
                        for s in courses_catalog[cid]['sections']]
            courses[idx]['section'] = random.choice(all_secs)
    return courses


# -- Schedule grid printer ---------------------------------------------

def print_schedule_grid(chromosome, courses_catalog, student_ids):
    from chromosome import decode_chromosome
    decoded = decode_chromosome(chromosome, courses_catalog)

    labels = {'S1':'[S1]','S2':'[S2]','S3':'[S3]','S4':'[S4]','S5':'[S5]'}
    days   = ["Monday","Tuesday","Wednesday","Thursday","Friday"]
    times  = list(range(8, 18))

    print("\n" + "=" * 90)
    print("WEEKLY SCHEDULE GRID (All Students)")
    print("=" * 90)
    col_w  = 16
    header = f"{'Time':<14}" + "".join(f"{d:^{col_w}}" for d in days)
    print(header)
    print("-" * len(header))

    for t in times:
        label = f"{t}:00-{t+1}:00"
        row   = f"{label:<14}"
        for d in days:
            cell = ""
            if t == 12:
                cell = "LUNCH"
                for sid in student_ids:
                    for c in decoded.get(sid, []):
                        for slot in c['schedule']:
                            if slot.get('day') == d and slot.get('time') == 12:
                                cell = f"{labels[sid]}{c['course_id']}"
            else:
                for sid in student_ids:
                    for c in decoded.get(sid, []):
                        for slot in c['schedule']:
                            if slot.get('day') == d and slot.get('time') == t:
                                cell += f"{labels[sid]}{c['course_id']} "
                cell = cell.strip()
            row += f"{cell[:col_w-1]:^{col_w}}"
        print(row)

    print("=" * 90)
    print("Legend: " + "  ".join(f"{labels[s]}={s}" for s in student_ids))
