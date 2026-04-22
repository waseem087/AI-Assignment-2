"""
fitness.py - Multi-Objective Fitness Function
AI2002 - Artificial Intelligence | Spring 2026 | Assignment 02

Fitness = 0.30*S_time + 0.25*S_gap + 0.20*S_friend
        + 0.15*S_workload + 0.10*S_lunch - Penalties

All component scores normalised to [0,1].
Prereqs are satisfied by completed_courses OR courses taken this semester.
"""

from collections import defaultdict
from chromosome import decode_chromosome
from utils import has_time_conflict, violates_blocked


def _safe_slots(course):
    """Return schedule list, guarding against malformed entries."""
    sched = course.get('schedule') or []
    safe  = []
    for s in sched:
        try:
            safe.append({'day': s['day'], 'time': int(s['time'])})
        except (TypeError, KeyError):
            pass
    return safe


# -- Penalty -----------------------------------------------------------

def _penalties(chromosome, courses_catalog, students_data, penalties):
    decoded = decode_chromosome(chromosome, courses_catalog)
    total   = 0

    for sid, course_list in decoded.items():
        req     = students_data[sid]
        blocked = req['time_preferences']['blocked']['slots']

        # Credits
        if sum(c['credits'] for c in course_list) != 15:
            total += penalties.get('missing_credits', -800)

        # Time conflicts
        n = len(course_list)
        for i in range(n):
            si = _safe_slots(course_list[i])
            for j in range(i+1, n):
                sj = _safe_slots(course_list[j])
                if has_time_conflict(si, sj):
                    total += penalties.get('time_conflict', -1000)

        # Blocked times
        for c in course_list:
            if violates_blocked(_safe_slots(c), blocked):
                total += penalties.get('blocked_time', -1000)

        # Max 3 courses/day
        day_cnt = defaultdict(int)
        for c in course_list:
            for s in _safe_slots(c):
                day_cnt[s['day']] += 1
        for day, cnt in day_cnt.items():
            if cnt > 3:
                total += penalties.get('too_many_courses', -500)

        # Prerequisites: satisfied by completed OR this-semester courses
        completed = set(req['completed_courses'])
        this_sem  = {c['course_id'] for c in course_list}
        available = completed | this_sem
        for c in course_list:
            for prereq in courses_catalog[c['course_id']]['prerequisites']:
                if prereq not in available:
                    total += penalties.get('hard_constraint', -1000)

    return total


# -- Component scores (all in [0,1]) -----------------------------------

def _time_pref(decoded, students_data):
    total = 0.0
    n     = len(decoded)
    if n == 0: return 0.0
    for sid, course_list in decoded.items():
        req      = students_data[sid]
        pref     = set(req['time_preferences']['preferred']['time_slots'])
        blocked  = {(b['day'], b['time'])
                    for b in req['time_preferences']['blocked']['slots']}
        special  = req.get('special_constraints', {})
        penalty_t = special.get('penalty_time', 8) if special.get('avoid_early') else None
        score = 0; n_cls = 0
        for c in course_list:
            for s in _safe_slots(c):
                n_cls += 1
                if s['time'] in pref:          score += 1
                if (s['day'], s['time']) in blocked: score -= 1
                if penalty_t and s['time'] == penalty_t: score -= 0.5
        if n_cls > 0:
            total += max(0.0, min(1.0, (score + n_cls) / (2 * n_cls)))
        else:
            total += 0.0
    return total / n


def _gap_min(decoded, students_data):
    days  = ["Monday","Tuesday","Wednesday","Thursday","Friday"]
    total = 0.0
    n     = len(decoded)
    if n == 0: return 0.0
    MAX_GAP = 9
    for sid, course_list in decoded.items():
        total_gap  = 0
        active_days = 0
        for day in days:
            times = []
            for c in course_list:
                for s in _safe_slots(c):
                    if s['day'] == day:
                        times.append(s['time'])
            if len(times) < 2: continue
            active_days += 1
            times.sort()
            gap = (times[-1] - times[0] + 1) - len(times)
            total_gap += gap
        if active_days > 0:
            norm = 1.0 - (total_gap / (MAX_GAP * active_days))
        else:
            norm = 1.0
        total += max(0.0, min(1.0, norm))
    return total / n


def _friend_sat(decoded, friend_pairs):
    if not friend_pairs: return 0.0
    total = 0.0
    MAX   = 5
    for (sa, sb) in friend_pairs:
        a = {(c['course_id'], c['section']) for c in decoded.get(sa, [])}
        b = {(c['course_id'], c['section']) for c in decoded.get(sb, [])}
        total += min(len(a & b) / MAX, 1.0)
    return total / len(friend_pairs)


def _workload_bal(decoded):
    total = 0.0
    n     = len(decoded)
    if n == 0: return 0.0
    for sid, course_list in decoded.items():
        day_diff = defaultdict(int)
        for c in course_list:
            days_used = set(s['day'] for s in _safe_slots(c))
            for d in days_used:
                day_diff[d] += c['difficulty']
        if not day_diff:
            total += 1.0
            continue
        max_d = max(day_diff.values())
        total += max(0.0, min(1.0, 1.0 - max_d / 9.0))
    return total / n


def _lunch(decoded):
    days  = ["Monday","Tuesday","Wednesday","Thursday","Friday"]
    total = 0.0
    n     = len(decoded)
    if n == 0: return 0.0
    for sid, course_list in decoded.items():
        busy = set()
        for c in course_list:
            for s in _safe_slots(c):
                if s['time'] == 12:
                    busy.add(s['day'])
        free = len(days) - len(busy)
        total += min(free / 3.0, 1.0)
    return total / n


# -- Public API --------------------------------------------------------

def calculate_fitness(chromosome, courses_catalog, students_data, friend_pairs,
                      weights=None, penalties=None):
    if weights is None:
        weights = {'time_preference':0.30,'gap_minimization':0.25,
                   'friend_satisfaction':0.20,'workload_balance':0.15,
                   'lunch_break':0.10}
    if penalties is None:
        penalties = {'hard_constraint':-1000,'time_conflict':-1000,
                     'missing_credits':-800,'too_many_courses':-500,
                     'blocked_time':-1000}
    decoded = decode_chromosome(chromosome, courses_catalog)
    soft = (weights['time_preference']    * _time_pref(decoded, students_data)
          + weights['gap_minimization']   * _gap_min(decoded, students_data)
          + weights['friend_satisfaction']* _friend_sat(decoded, friend_pairs)
          + weights['workload_balance']   * _workload_bal(decoded)
          + weights['lunch_break']        * _lunch(decoded))
    return soft + _penalties(chromosome, courses_catalog, students_data, penalties)


def calculate_fitness_components(chromosome, courses_catalog, students_data,
                                  friend_pairs, weights=None, penalties=None):
    if weights is None:
        weights = {'time_preference':0.30,'gap_minimization':0.25,
                   'friend_satisfaction':0.20,'workload_balance':0.15,
                   'lunch_break':0.10}
    if penalties is None:
        penalties = {'hard_constraint':-1000,'time_conflict':-1000,
                     'missing_credits':-800,'too_many_courses':-500,
                     'blocked_time':-1000}
    decoded  = decode_chromosome(chromosome, courses_catalog)
    s_time   = _time_pref(decoded, students_data)
    s_gap    = _gap_min(decoded, students_data)
    s_friend = _friend_sat(decoded, friend_pairs)
    s_work   = _workload_bal(decoded)
    s_lunch  = _lunch(decoded)
    pen      = _penalties(chromosome, courses_catalog, students_data, penalties)
    total    = (weights['time_preference']*s_time + weights['gap_minimization']*s_gap
              + weights['friend_satisfaction']*s_friend + weights['workload_balance']*s_work
              + weights['lunch_break']*s_lunch + pen)
    return {'total':total,'time_preference':s_time,'gap_minimization':s_gap,
            'friend_satisfaction':s_friend,'workload_balance':s_work,
            'lunch_break':s_lunch,'penalty':pen}
