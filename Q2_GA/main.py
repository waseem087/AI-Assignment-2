"""
main.py - Main GA Loop for University Course Scheduling
AI2002 - Artificial Intelligence | Spring 2026 | Assignment 02

Usage:
  python main.py                   # single run, seed=42
  python main.py --seed 123
  python main.py --runs 10         # 10 independent runs (full experiment)
  python main.py --analyze         # same as --runs 10
"""

import sys, io
# Ensure UTF-8 output on Windows (avoids cp1252 UnicodeEncodeError)
try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
except AttributeError:
    pass

import os, copy, random, argparse, time, statistics, itertools
import sys

os.makedirs("results", exist_ok=True)
os.makedirs("plots",   exist_ok=True)
os.makedirs("logs",    exist_ok=True)

from utils       import (load_data, available_sections, get_valid_electives,
                         repair_time_conflicts, get_course_schedule,
                         has_time_conflict, violates_blocked, print_schedule_grid)
from chromosome  import (decode_chromosome, validate_chromosome,
                          chromosome_signature)
from fitness     import calculate_fitness, calculate_fitness_components
from selection   import select_parent, elitism_selection
from operators   import crossover, mutate

STUDENT_IDS = ['S1','S2','S3','S4','S5']


# ======================================================================
# Population Initialisation
# ======================================================================

def _build_student_schedule(sid, student_data, courses_catalog,
                              prefer_time=False, friend_sections=None):
    """
    Backtracking initialiser: assign a conflict-free section to every course.
    Tries multiple elective combos until a valid schedule is found.
    """
    req         = student_data['required_courses']
    core_ids    = list(req['core'])
    n_electives = req.get('electives', 0)
    blocked_set = {(b['day'], b['time'])
                   for b in student_data['time_preferences']['blocked']['slots']}
    pref_times  = (set(student_data['time_preferences']['preferred']['time_slots'])
                   if prefer_time else set())

    # Build valid elective pool
    valid_pool = get_valid_electives(None, student_data, courses_catalog)
    if len(valid_pool) < n_electives:
        valid_pool = list(req.get('elective_pool', []))

    # Generate elective combos to try
    if n_electives == 0:
        elec_combos = [[]]
    elif n_electives <= len(valid_pool):
        all_c = list(itertools.combinations(valid_pool, n_electives))
        random.shuffle(all_c)
        elec_combos = [list(c) for c in all_c[:20]]
    else:
        elec_combos = [list(valid_pool)]

    def _try(all_courses):
        def bt(idx, assigned, used_slots):
            if idx == len(all_courses):
                return [dict(e) for e in assigned]
            cid  = all_courses[idx]
            secs = list(courses_catalog[cid]['sections'])
            if pref_times:
                secs = sorted(secs,
                              key=lambda s: -sum(1 for sl in s['schedule']
                                                 if sl['time'] in pref_times))
            else:
                random.shuffle(secs)
            if friend_sections and cid in friend_sections:
                fs   = friend_sections[cid]
                secs = sorted(secs, key=lambda s: 0 if s['section_id']==fs else 1)
            for sec in secs:
                slots = {(sl['day'], sl['time']) for sl in sec['schedule']}
                if slots & used_slots:   continue
                if slots & blocked_set:  continue
                assigned.append({'course_id': cid, 'section': sec['section_id']})
                result = bt(idx+1, assigned, used_slots | slots)
                if result is not None: return result
                assigned.pop()
            return None
        for _ in range(6):
            shuffled = all_courses[:]
            random.shuffle(shuffled)
            result = bt(0, [], set())
            if result is not None:
                mapping = {e['course_id']: e for e in result}
                return [mapping[c] for c in all_courses if c in mapping]
        return None

    for electives in elec_combos:
        result = _try(core_ids + electives)
        if result is not None:
            return result

    # Fallback: random sections
    fallback = []
    electives = elec_combos[0] if elec_combos else []
    for cid in core_ids + electives:
        sec = random.choice(courses_catalog[cid]['sections'])['section_id']
        fallback.append({'course_id': cid, 'section': sec})
    return fallback


def _init_random(students_data, courses_catalog):
    return {sid: _build_student_schedule(sid, students_data[sid],
                                          courses_catalog, prefer_time=False)
            for sid in STUDENT_IDS}


def _init_greedy_time(students_data, courses_catalog):
    return {sid: _build_student_schedule(sid, students_data[sid],
                                          courses_catalog, prefer_time=True)
            for sid in STUDENT_IDS}


def _init_greedy_friend(students_data, courses_catalog, friend_pairs):
    chrom = {}
    order = ['S1','S3','S5','S2','S4']
    for sid in order:
        friend_secs = {}
        for fp in friend_pairs:
            other = fp[1] if fp[0]==sid else (fp[0] if fp[1]==sid else None)
            if other and other in chrom:
                for ec in chrom[other]:
                    friend_secs[ec['course_id']] = ec['section']
        chrom[sid] = _build_student_schedule(
            sid, students_data[sid], courses_catalog,
            friend_sections=friend_secs)
    return chrom


def initialise_population(pop_size, students_data, courses_catalog, friend_pairs,
                            strategy_ratios=None):
    if strategy_ratios is None:
        strategy_ratios = {'random_valid':0.40,'greedy_time':0.40,'greedy_friend':0.20}
    n_r = int(pop_size * strategy_ratios['random_valid'])
    n_t = int(pop_size * strategy_ratios['greedy_time'])
    n_f = pop_size - n_r - n_t
    pop = []
    for _ in range(n_r): pop.append(_init_random(students_data, courses_catalog))
    for _ in range(n_t): pop.append(_init_greedy_time(students_data, courses_catalog))
    for _ in range(n_f): pop.append(_init_greedy_friend(students_data, courses_catalog, friend_pairs))
    random.shuffle(pop)
    return pop


# ======================================================================
# Diversity
# ======================================================================

def compute_diversity(population):
    sigs = set(chromosome_signature(c) for c in population)
    return len(sigs) / len(population) if population else 0.0


# ======================================================================
# Termination
# ======================================================================

def should_terminate(generation, max_gen, best_history, patience,
                      improvement_thresh, fitnesses, sim_thresh, sim_tol):
    if generation >= max_gen:
        return True, "max_generations_reached"
    if len(best_history) >= patience:
        recent = best_history[-patience:]
        if recent[-1] != 0:
            improvement = (recent[-1] - recent[0]) / (abs(recent[0]) + 1e-12)
            if improvement < improvement_thresh:
                return True, "fitness_converged"
    if fitnesses:
        avg = statistics.mean(fitnesses)
        similar = sum(1 for f in fitnesses
                       if abs(f - avg) / (abs(avg) + 1e-6) < sim_tol)
        if similar / len(fitnesses) >= sim_thresh:
            return True, "population_converged"
    return False, ""


# ======================================================================
# Core GA
# ======================================================================

def run_ga(seed=None, pop_size=60, max_generations=300, patience=40,
           improvement_thresh=0.001, tournament_size=5, tournament_rate=0.70,
           elite_rate=0.10, crossover_prob=0.80, diversity_threshold=0.30,
           diversity_check_interval=10, diversity_injection_rate=0.20,
           mutation_rate_multiplier=1.5, base_mutation_rates=None,
           verbose=True, catalog_path="course_catalog.json",
           students_path="student_requirements.json", config_path="config.yaml"):

    if seed is not None:
        random.seed(seed)
    if base_mutation_rates is None:
        base_mutation_rates = {'section_change':0.12,'course_swap':0.10,
                                'time_shift':0.08,'friend_align':0.15}

    courses_catalog, students_data, friend_pairs, config = load_data(
        catalog_path, students_path, config_path)

    if verbose:
        print(f"\n[GA] Initialising population of {pop_size} chromosomes ...")
    population = initialise_population(pop_size, students_data, courses_catalog, friend_pairs)

    weights   = config['fitness']['weights']
    penalties = config['fitness']['penalties']

    def fitness_fn(chrom):
        return calculate_fitness(chrom, courses_catalog, students_data,
                                  friend_pairs, weights, penalties)

    fitnesses = [fitness_fn(c) for c in population]

    best_idx  = max(range(len(fitnesses)), key=lambda i: fitnesses[i])
    best_chrom = copy.deepcopy(population[best_idx])
    best_fit   = fitnesses[best_idx]

    stats = {
        'best_fitness_per_gen':  [best_fit],
        'avg_fitness_per_gen':   [statistics.mean(fitnesses)],
        'worst_fitness_per_gen': [min(fitnesses)],
        'diversity_per_gen':     [compute_diversity(population)],
        'total_generations':     0,
        'termination_reason':    '',
        'seed': seed,
    }

    cur_rates = copy.copy(base_mutation_rates)

    for gen in range(1, max_generations + 1):
        elites   = elitism_selection(population, fitnesses, elite_rate)
        n_elites = len(elites)

        # Diversity maintenance
        if gen % diversity_check_interval == 0:
            div = compute_diversity(population)
            if div < diversity_threshold:
                n_inj = max(1, int(pop_size * diversity_injection_rate))
                for _ in range(n_inj):
                    ni = _init_random(students_data, courses_catalog)
                    population.append(ni)
                    fitnesses.append(fitness_fn(ni))
                pairs_sorted = sorted(zip(fitnesses, population),
                                       key=lambda x: x[0], reverse=True)
                fitnesses  = [p[0] for p in pairs_sorted[:pop_size]]
                population = [p[1] for p in pairs_sorted[:pop_size]]
                cur_rates  = {k: v * mutation_rate_multiplier
                               for k, v in base_mutation_rates.items()}
                if verbose:
                    print(f"  [Gen {gen}] Diversity {div:.2%} < threshold -- "
                          f"injected {n_inj} individuals, boosted mutation")
            else:
                cur_rates = copy.copy(base_mutation_rates)

        # Build next generation
        next_pop  = list(elites)
        next_fits = [fitness_fn(e) for e in elites]

        while len(next_pop) < pop_size:
            p1 = select_parent(population, fitnesses, True,
                                tournament_rate, tournament_size)
            p2 = select_parent(population, fitnesses, True,
                                tournament_rate, tournament_size)
            c1, c2 = crossover(p1, p2, students_data, courses_catalog,
                                crossover_prob)
            c1 = mutate(c1, students_data, courses_catalog, cur_rates)
            c2 = mutate(c2, students_data, courses_catalog, cur_rates)
            for child in [c1, c2]:
                if len(next_pop) < pop_size:
                    next_pop.append(child)
                    next_fits.append(fitness_fn(child))

        population = next_pop
        fitnesses  = next_fits

        gen_best_idx = max(range(len(fitnesses)), key=lambda i: fitnesses[i])
        gen_best_fit = fitnesses[gen_best_idx]
        if gen_best_fit > best_fit:
            best_fit   = gen_best_fit
            best_chrom = copy.deepcopy(population[gen_best_idx])

        avg_fit   = statistics.mean(fitnesses)
        worst_fit = min(fitnesses)
        div       = compute_diversity(population)
        stats['best_fitness_per_gen'].append(best_fit)
        stats['avg_fitness_per_gen'].append(avg_fit)
        stats['worst_fitness_per_gen'].append(worst_fit)
        stats['diversity_per_gen'].append(div)

        if verbose and gen % 10 == 0:
            print(f"  Gen {gen:4d} | Best: {best_fit:8.4f} "
                  f"| Avg: {avg_fit:8.4f} | Diversity: {div:.2%}")

        terminate, reason = should_terminate(
            gen, max_generations, stats['best_fitness_per_gen'],
            patience, improvement_thresh, fitnesses, 0.85, 0.02)
        if terminate:
            stats['termination_reason'] = reason
            stats['total_generations']  = gen
            if verbose:
                print(f"\n[GA] Terminated at generation {gen}: {reason}")
            break
    else:
        stats['termination_reason'] = 'max_generations_reached'
        stats['total_generations']  = max_generations

    return best_chrom, best_fit, stats, courses_catalog, students_data, friend_pairs


# ======================================================================
# Output
# ======================================================================

def print_best_schedule(best_chrom, best_fit, courses_catalog,
                          students_data, friend_pairs):
    print("\n" + "=" * 70)
    print("BEST SCHEDULE FOUND")
    print("=" * 70)
    print(f"Fitness Score: {best_fit:.4f}")

    decoded = decode_chromosome(best_chrom, courses_catalog)

    for sid in STUDENT_IDS:
        sdata   = students_data[sid]
        courses = decoded.get(sid, [])
        print(f"\n{'---'*20}")
        print(f"{sid} ({sdata['name']}) -- Year {sdata['year']}")
        print(f"{'---'*20}")
        credits = sum(c['credits'] for c in courses)
        print(f"  Total Credits: {credits}")
        for c in sorted(courses, key=lambda x: x['course_id']):
            times = ", ".join(f"{s['day'][:3]} {s['time']}:00"
                               for s in c['schedule'])
            print(f"  [{c['course_id']}] {c['name']} "
                  f"(Sec {c['section']}, {c['type']}, Diff:{c['difficulty']}) -- {times}")

    print(f"\n{'---'*20}")
    print("FRIEND PAIR OVERLAPS:")
    for (sa, sb) in friend_pairs:
        a = {(c['course_id'], c['section']) for c in decoded.get(sa, [])}
        b = {(c['course_id'], c['section']) for c in decoded.get(sb, [])}
        shared = a & b
        print(f"  {sa} <-> {sb}: {len(shared)} shared: "
              f"{', '.join(c for c,_ in shared) if shared else 'None'}")

    comp = calculate_fitness_components(best_chrom, courses_catalog,
                                         students_data, friend_pairs)
    print(f"\n{'---'*20}")
    print("FITNESS BREAKDOWN:")
    print(f"  Time Preference  (x0.30): {comp['time_preference']:.3f}")
    print(f"  Gap Minimisation (x0.25): {comp['gap_minimization']:.3f}")
    print(f"  Friend Satisf.   (x0.20): {comp['friend_satisfaction']:.3f}")
    print(f"  Workload Balance (x0.15): {comp['workload_balance']:.3f}")
    print(f"  Lunch Break      (x0.10): {comp['lunch_break']:.3f}")
    print(f"  Penalties               : {comp['penalty']:.1f}")
    print(f"  {'---'*10}")
    print(f"  TOTAL FITNESS           : {comp['total']:.4f}")
    print("=" * 70)

    print_schedule_grid(best_chrom, courses_catalog, STUDENT_IDS)


def save_convergence_plot(all_stats, path="plots/convergence.png"):
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import numpy as np

        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        ax = axes[0]
        for stats in all_stats:
            gens = range(len(stats['best_fitness_per_gen']))
            ax.plot(gens, stats['best_fitness_per_gen'],
                    alpha=0.4, color='steelblue', linewidth=0.8)
        max_len = max(len(s['best_fitness_per_gen']) for s in all_stats)
        padded  = [s['best_fitness_per_gen'] + [s['best_fitness_per_gen'][-1]] *
                   (max_len - len(s['best_fitness_per_gen'])) for s in all_stats]
        ax.plot(np.mean(padded, axis=0), color='navy', linewidth=2, label='Mean Best')
        ax.set_title("Convergence -- Best Fitness (All Runs)")
        ax.set_xlabel("Generation"); ax.set_ylabel("Fitness")
        ax.legend(); ax.grid(alpha=0.3)

        ax2 = axes[1]
        for stats in all_stats:
            ax2.plot(range(len(stats['diversity_per_gen'])),
                     stats['diversity_per_gen'],
                     alpha=0.4, color='darkorange', linewidth=0.8)
        padded_d = [s['diversity_per_gen'] + [s['diversity_per_gen'][-1]] *
                    (max_len - len(s['diversity_per_gen'])) for s in all_stats]
        ax2.plot(np.mean(padded_d, axis=0), color='chocolate',
                 linewidth=2, label='Mean Diversity')
        ax2.axhline(0.30, color='red', linestyle='--', label='Threshold 30%')
        ax2.set_title("Population Diversity Over Generations")
        ax2.set_xlabel("Generation"); ax2.set_ylabel("Diversity")
        ax2.set_ylim(0, 1); ax2.legend(); ax2.grid(alpha=0.3)

        plt.tight_layout()
        plt.savefig(path, dpi=120)
        plt.close()
        print(f"[Plot] Saved to '{path}'")
    except ImportError:
        print("[Plot] matplotlib not installed -- skipping")


# ======================================================================
# Multi-run Experiment
# ======================================================================

def run_experiments(n_runs=10, base_seed=42,
                    catalog_path="course_catalog.json",
                    students_path="student_requirements.json",
                    config_path="config.yaml"):
    print(f"\n{'='*60}")
    print(f"EXPERIMENT: {n_runs} Independent Runs")
    print(f"{'='*60}")

    all_stats   = []
    all_fitness = []
    best_overall = best_fit_overall = None
    best_catalog = best_students = best_fp = None

    for run in range(n_runs):
        seed = base_seed + run
        print(f"\n--- Run {run+1}/{n_runs} (seed={seed}) ---")
        t0 = time.perf_counter()
        bc, bf, stats, cats, stus, fp = run_ga(seed=seed, verbose=True,
                                                 catalog_path=catalog_path,
                                                 students_path=students_path,
                                                 config_path=config_path)
        elapsed = time.perf_counter() - t0
        all_stats.append(stats)
        all_fitness.append(bf)
        print(f"  Run {run+1} | Best: {bf:.4f} | "
              f"Gen: {stats['total_generations']} | Time: {elapsed:.1f}s")
        if best_fit_overall is None or bf > best_fit_overall:
            best_fit_overall = bf
            best_overall     = bc
            best_catalog     = cats
            best_students    = stus
            best_fp          = fp

    print(f"\n{'='*60}")
    print("EXPERIMENT SUMMARY")
    print(f"{'='*60}")
    print(f"  Best Fitness : {max(all_fitness):.4f}")
    print(f"  Worst Fitness: {min(all_fitness):.4f}")
    print(f"  Mean Fitness : {statistics.mean(all_fitness):.4f}")
    if len(all_fitness) > 1:
        print(f"  Std Dev      : {statistics.stdev(all_fitness):.4f}")
    avg_gen = statistics.mean(s['total_generations'] for s in all_stats)
    print(f"  Avg Conv Gen : {avg_gen:.1f}")
    reasons = {}
    for s in all_stats:
        reasons[s['termination_reason']] = reasons.get(s['termination_reason'],0)+1
    print(f"  Termination  : {reasons}")

    save_convergence_plot(all_stats, "plots/convergence.png")

    if best_overall:
        print_best_schedule(best_overall, best_fit_overall,
                             best_catalog, best_students, best_fp)

    log_path = "logs/experiment_results.txt"
    with open(log_path, "w") as f:
        f.write(f"GA Experiment Results -- {n_runs} runs\n")
        f.write(f"Best:  {max(all_fitness):.4f}\n")
        f.write(f"Mean:  {statistics.mean(all_fitness):.4f}\n")
        if len(all_fitness) > 1:
            f.write(f"Std:   {statistics.stdev(all_fitness):.4f}\n")
        for i, (bf, s) in enumerate(zip(all_fitness, all_stats)):
            f.write(f"Run {i+1}: fitness={bf:.4f} "
                    f"gen={s['total_generations']} "
                    f"reason={s['termination_reason']}\n")
    print(f"\n[Log] Results saved to '{log_path}'")
    return best_overall, best_fit_overall, all_stats


# ======================================================================
# CLI
# ======================================================================

def main():
    parser = argparse.ArgumentParser(
        description="GA University Course Scheduling Optimizer")
    parser.add_argument("--seed",        type=int, default=42)
    parser.add_argument("--runs",        type=int, default=1)
    parser.add_argument("--pop",         type=int, default=60)
    parser.add_argument("--generations", type=int, default=300)
    parser.add_argument("--catalog",     default="course_catalog.json")
    parser.add_argument("--students",    default="student_requirements.json")
    parser.add_argument("--config",      default="config.yaml")
    parser.add_argument("--analyze",     action="store_true")
    args = parser.parse_args()

    if args.analyze or args.runs > 1:
        n = 10 if args.analyze else args.runs
        run_experiments(n_runs=n, base_seed=args.seed,
                        catalog_path=args.catalog,
                        students_path=args.students,
                        config_path=args.config)
    else:
        bc, bf, stats, cats, stus, fp = run_ga(
            seed=args.seed, pop_size=args.pop,
            max_generations=args.generations, verbose=True,
            catalog_path=args.catalog, students_path=args.students,
            config_path=args.config)
        print_best_schedule(bc, bf, cats, stus, fp)
        save_convergence_plot([stats], "plots/convergence_single.png")


if __name__ == "__main__":
    main()
