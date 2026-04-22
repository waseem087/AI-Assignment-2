"""
operators.py - Crossover (3) and Mutation (4) Operators
AI2002 - Artificial Intelligence | Spring 2026 | Assignment 02

Crossover operators:
  A) Single-Point  - cut at random student boundary
  B) Uniform       - per-student random pick from P1 or P2
  C) Course-Based  - exchange section choices per course

Mutation operators:
  1. Section Change  - change one course to a different section
  2. Course Swap     - change a randomly picked course's section (preserves course set)
  3. Time Slot Shift - reassign one course to a different non-conflicting section
  4. Friend Alignment- align sections so friend pairs share classes
"""

import copy, random
from utils import available_sections, repair_time_conflicts, get_course_schedule, has_time_conflict

STUDENT_IDS  = ['S1','S2','S3','S4','S5']
FRIEND_PAIRS = [('S1','S3'),('S2','S4'),('S3','S5')]


def _repair(sid, courses, student_data, courses_catalog):
    return repair_time_conflicts(sid, courses, student_data, courses_catalog)


# -- A: Single-Point Crossover -----------------------------------------

def single_point_crossover(p1, p2, students_data, courses_catalog):
    cut = random.randint(1, len(STUDENT_IDS)-1)
    c1, c2 = {}, {}
    for i, sid in enumerate(STUDENT_IDS):
        if i < cut:
            c1[sid] = copy.deepcopy(p1.get(sid, []))
            c2[sid] = copy.deepcopy(p2.get(sid, []))
        else:
            c1[sid] = copy.deepcopy(p2.get(sid, []))
            c2[sid] = copy.deepcopy(p1.get(sid, []))
    for sid in STUDENT_IDS:
        c1[sid] = _repair(sid, c1[sid], students_data[sid], courses_catalog)
        c2[sid] = _repair(sid, c2[sid], students_data[sid], courses_catalog)
    return c1, c2


# -- B: Uniform Crossover ----------------------------------------------

def uniform_crossover(p1, p2, students_data, courses_catalog):
    c1, c2 = {}, {}
    for sid in STUDENT_IDS:
        if random.random() < 0.5:
            c1[sid] = copy.deepcopy(p1.get(sid, []))
            c2[sid] = copy.deepcopy(p2.get(sid, []))
        else:
            c1[sid] = copy.deepcopy(p2.get(sid, []))
            c2[sid] = copy.deepcopy(p1.get(sid, []))
    for sid in STUDENT_IDS:
        c1[sid] = _repair(sid, c1[sid], students_data[sid], courses_catalog)
        c2[sid] = _repair(sid, c2[sid], students_data[sid], courses_catalog)
    return c1, c2


# -- C: Course-Based Crossover -----------------------------------------

def course_based_crossover(p1, p2, students_data, courses_catalog):
    """
    For each student: keep the same course set as p1, but for each course
    randomly pick the section from p1 or p2. Repair conflicts.
    """
    c1, c2 = {}, {}
    for sid in STUDENT_IDS:
        p1c = p1.get(sid, [])
        p2c = p2.get(sid, [])
        p1_sec = {e['course_id']: e['section'] for e in p1c}
        p2_sec = {e['course_id']: e['section'] for e in p2c}
        child1_list, child2_list = [], []
        for entry in p1c:
            cid = entry['course_id']
            if cid in p2_sec and random.random() < 0.5:
                child1_list.append({'course_id': cid, 'section': p2_sec[cid]})
            else:
                child1_list.append({'course_id': cid, 'section': p1_sec[cid]})
            if cid in p2_sec and random.random() < 0.5:
                child2_list.append({'course_id': cid, 'section': p1_sec[cid]})
            else:
                child2_list.append({'course_id': cid, 'section': p2_sec.get(cid, p1_sec[cid])})
        c1[sid] = _repair(sid, child1_list, students_data[sid], courses_catalog)
        c2[sid] = _repair(sid, child2_list, students_data[sid], courses_catalog)
    return c1, c2


# -- Crossover dispatcher ----------------------------------------------

def crossover(p1, p2, students_data, courses_catalog,
              crossover_prob=0.80, weights=None):
    if weights is None:
        weights = {'single_point': 0.35, 'uniform': 0.35, 'course_based': 0.30}
    if random.random() > crossover_prob:
        return copy.deepcopy(p1), copy.deepcopy(p2)
    r = random.random()
    if r < weights['single_point']:
        return single_point_crossover(p1, p2, students_data, courses_catalog)
    elif r < weights['single_point'] + weights['uniform']:
        return uniform_crossover(p1, p2, students_data, courses_catalog)
    else:
        return course_based_crossover(p1, p2, students_data, courses_catalog)


# -- Mutation 1: Section Change ----------------------------------------

def section_change_mutation(chromosome, students_data, courses_catalog, rate=0.12):
    mutant = copy.deepcopy(chromosome)
    for sid in STUDENT_IDS:
        if random.random() >= rate: continue
        courses = mutant[sid]
        if not courses: continue
        idx    = random.randint(0, len(courses)-1)
        cid    = courses[idx]['course_id']
        others = [courses[k] for k in range(len(courses)) if k != idx]
        valid  = available_sections(cid, courses_catalog, students_data[sid],
                                     others, courses_catalog)
        if valid:
            mutant[sid][idx]['section'] = random.choice(valid)
    return mutant


# -- Mutation 2: Course Swap (changes section, preserves course set) ---

def course_swap_mutation(chromosome, students_data, courses_catalog, rate=0.10):
    """Pick a random course and assign it a different valid section."""
    mutant = copy.deepcopy(chromosome)
    for sid in STUDENT_IDS:
        if random.random() >= rate: continue
        courses = mutant[sid]
        if not courses: continue
        idx    = random.randint(0, len(courses)-1)
        cid    = courses[idx]['course_id']
        others = [courses[k] for k in range(len(courses)) if k != idx]
        valid  = available_sections(cid, courses_catalog, students_data[sid],
                                     others, courses_catalog)
        if valid:
            mutant[sid][idx]['section'] = random.choice(valid)
    return mutant


# -- Mutation 3: Time Slot Shift ---------------------------------------

def time_shift_mutation(chromosome, students_data, courses_catalog, rate=0.08):
    mutant = copy.deepcopy(chromosome)
    for sid in STUDENT_IDS:
        if random.random() >= rate: continue
        courses = mutant[sid]
        if not courses: continue
        idx    = random.randint(0, len(courses)-1)
        cid    = courses[idx]['course_id']
        others = [courses[k] for k in range(len(courses)) if k != idx]
        valid  = available_sections(cid, courses_catalog, students_data[sid],
                                     others, courses_catalog)
        if valid:
            mutant[sid][idx]['section'] = random.choice(valid)
    return mutant


# -- Mutation 4: Friend Alignment --------------------------------------

def friend_alignment_mutation(chromosome, students_data, courses_catalog, rate=0.15):
    mutant = copy.deepcopy(chromosome)
    for (sa, sb) in FRIEND_PAIRS:
        if random.random() >= rate: continue
        a_ids  = {c['course_id'] for c in mutant.get(sa, [])}
        b_ids  = {c['course_id'] for c in mutant.get(sb, [])}
        shared = list(a_ids & b_ids)
        if not shared: continue
        cid    = random.choice(shared)
        a_idx  = next((i for i,c in enumerate(mutant[sa]) if c['course_id']==cid), None)
        b_idx  = next((i for i,c in enumerate(mutant[sb]) if c['course_id']==cid), None)
        if a_idx is None or b_idx is None: continue
        # Try to align sb to sa's section
        target = mutant[sa][a_idx]['section']
        b_others = [mutant[sb][k] for k in range(len(mutant[sb])) if k != b_idx]
        b_valid  = available_sections(cid, courses_catalog, students_data[sb],
                                       b_others, courses_catalog)
        if target in b_valid:
            mutant[sb][b_idx]['section'] = target
        else:
            target = mutant[sb][b_idx]['section']
            a_others = [mutant[sa][k] for k in range(len(mutant[sa])) if k != a_idx]
            a_valid  = available_sections(cid, courses_catalog, students_data[sa],
                                           a_others, courses_catalog)
            if target in a_valid:
                mutant[sa][a_idx]['section'] = target
    return mutant


# -- Combined mutate ---------------------------------------------------

def mutate(chromosome, students_data, courses_catalog, rates=None):
    if rates is None:
        rates = {'section_change':0.12,'course_swap':0.10,
                 'time_shift':0.08,'friend_align':0.15}
    m = chromosome
    m = section_change_mutation(m, students_data, courses_catalog, rates['section_change'])
    m = course_swap_mutation(   m, students_data, courses_catalog, rates['course_swap'])
    m = time_shift_mutation(    m, students_data, courses_catalog, rates['time_shift'])
    m = friend_alignment_mutation(m, students_data, courses_catalog, rates['friend_align'])
    return m
