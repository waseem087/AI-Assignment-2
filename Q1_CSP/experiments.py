"""
experiments.py - Experimental Evaluation (Q1)
AI2002 - Artificial Intelligence | Spring 2026 | Assignment 02

LCV is disabled in Experiments 1/3/4 for speed; Experiment 2 compares it.
Each run has a 30-second wall-clock cap (set in algorithms.py).
"""

import os, copy, time, statistics
from generator import generate_instance
from timetable import TimetableCSP, load_courses, load_rooms, load_timeslots, load_students
from algorithms import backtracking_search, forward_checking_search, mac_search, min_conflicts_search

INSTANCES_DIR = "instances"
RESULTS_DIR   = "results"
os.makedirs(INSTANCES_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR,   exist_ok=True)


def _load_csp(data_dir):
    return TimetableCSP(
        load_courses(  os.path.join(data_dir, "courses.csv")),
        load_rooms(    os.path.join(data_dir, "rooms.csv")),
        load_timeslots(os.path.join(data_dir, "timeslots.csv")),
        load_students( os.path.join(data_dir, "students.csv")),
    )


def _run_algo(csp_factory, algo_fn, algo_kwargs, n_runs=5):
    results = []
    for _ in range(n_runs):
        csp = csp_factory()
        t0  = time.perf_counter()
        result, m = algo_fn(csp, **algo_kwargs)
        summary = m.summary()
        summary['solved']  = result is not None
        summary['elapsed'] = round(time.perf_counter() - t0, 4)
        results.append(summary)
    return results


def _avg(lst, key):
    return round(statistics.mean(r[key] for r in lst), 4)

def _success(lst):
    return round(sum(r['solved'] for r in lst) / len(lst) * 100, 1)

def _print_table(title, rows):
    col_w = 15
    if title: print(title)
    print("-" * (col_w * len(rows[0])))
    for row in rows:
        print("".join(str(c).ljust(col_w) for c in row))
    print()


# -- Experiment 1: Algorithm Comparison -------------------------------

def experiment_1():
    print("\n" + "=" * 60)
    print("EXPERIMENT 1 - Algorithm Comparison")
    print("=" * 60)

    configs = [
        (10,  8, 20, 0.3, 0.3),
        (20, 16, 30, 0.5, 0.5),
        (30, 24, 40, 0.5, 0.5),
        (30, 24, 40, 0.7, 0.7),
    ]
    algorithms = [
        ("Backtracking",    backtracking_search,    {'use_mrv':False,'use_degree':False,'use_lcv':False}),
        ("ForwardChecking", forward_checking_search, {'use_mrv':True, 'use_degree':True, 'use_lcv':False}),
        ("MAC",             mac_search,              {'use_mrv':True, 'use_degree':True, 'use_lcv':False}),
        ("MinConflicts",    min_conflicts_search,    {'max_steps':5000}),
    ]

    for (nc,nr,ns,density,tight) in configs:
        print(f"\n--- Config: courses={nc}, rooms={nr}, slots={ns}, "
              f"density={density}, tightness={tight} ---")
        dirs = []
        for run_i in range(5):
            d = os.path.join(INSTANCES_DIR,
                             f"exp1_c{nc}_r{nr}_s{ns}_d{density}_t{tight}_run{run_i}")
            generate_instance(nc,nr,ns,density,tight,output_dir=d,seed=42+run_i)
            dirs.append(d)

        rows = [["Algorithm","SuccessRate","AvgTime(s)","AvgBacktracks","AvgChecks"]]
        for name, fn, kwargs in algorithms:
            all_res = []
            for d in dirs:
                all_res.extend(_run_algo(lambda dd=d: _load_csp(dd), fn, kwargs, n_runs=1))
            rows.append([name, f"{_success(all_res)}%",
                         f"{_avg(all_res,'elapsed')}",
                         f"{_avg(all_res,'backtracks'):.0f}",
                         f"{_avg(all_res,'constraint_checks'):.0f}"])
        _print_table("", rows)

    with open(os.path.join(RESULTS_DIR,"experiment1.txt"),"w") as f:
        f.write("Experiment 1 complete.\n")
    print("Experiment 1 results saved to results/experiment1.txt")


# -- Experiment 2: Heuristic Impact -----------------------------------

def experiment_2():
    print("\n" + "=" * 60)
    print("EXPERIMENT 2 - Heuristic Impact")
    print("=" * 60)

    d = os.path.join(INSTANCES_DIR, "exp2_instance")
    generate_instance(20, 16, 30, 0.5, 0.5, output_dir=d, seed=99)

    configs = [
        ("No heuristics",      False, False, False),
        ("MRV only",           True,  False, False),
        ("MRV + Degree",       True,  True,  False),
        ("MRV + Degree + LCV", True,  True,  True),
    ]
    rows = [["Heuristics","AvgBacktracks","AvgChecks","AvgTime(s)","Success"]]
    for label, mrv, deg, lcv in configs:
        results = _run_algo(lambda: _load_csp(d), mac_search,
                            {'use_mrv':mrv,'use_degree':deg,'use_lcv':lcv}, n_runs=5)
        rows.append([label,
                     f"{_avg(results,'backtracks'):.0f}",
                     f"{_avg(results,'constraint_checks'):.0f}",
                     f"{_avg(results,'elapsed')}",
                     f"{_success(results)}%"])
    _print_table("Heuristic comparison (MAC, 20 courses, 5 runs):", rows)

    with open(os.path.join(RESULTS_DIR,"experiment2.txt"),"w") as f:
        f.write("Experiment 2 complete.\n")
    print("Experiment 2 results saved to results/experiment2.txt")


# -- Experiment 3: Phase Transition -----------------------------------

def experiment_3():
    print("\n" + "=" * 60)
    print("EXPERIMENT 3 - Phase Transition")
    print("=" * 60)
    print("Fixing 20 courses, varying tightness 0.1 -> 0.9\n")

    rows = [["Tightness","SolvedRate","AvgBacktracks","AvgTime(s)"]]
    for tight in [round(0.1*i,1) for i in range(1,10)]:
        d = os.path.join(INSTANCES_DIR, f"exp3_tight{tight}")
        generate_instance(20, 16, 30, 0.5, tight, output_dir=d, seed=77)
        results = _run_algo(lambda dd=d: _load_csp(dd), mac_search,
                            {'use_mrv':True,'use_degree':True,'use_lcv':False}, n_runs=5)
        rows.append([tight, f"{_success(results)}%",
                     f"{_avg(results,'backtracks'):.0f}",
                     f"{_avg(results,'elapsed')}"])
    _print_table("Phase transition (20 courses, MAC, 5 runs):", rows)

    with open(os.path.join(RESULTS_DIR,"experiment3.txt"),"w") as f:
        f.write("Experiment 3 complete.\n")
    print("Experiment 3 results saved to results/experiment3.txt")


# -- Experiment 4: Systematic vs Local --------------------------------

def experiment_4():
    print("\n" + "=" * 60)
    print("EXPERIMENT 4 - Systematic vs. Local Search")
    print("=" * 60)

    configs = [
        (10,  8, 20, 0.3, 0.3, "Easy"),
        (20, 16, 30, 0.5, 0.5, "Medium"),
        (30, 24, 40, 0.7, 0.7, "Hard"),
    ]
    rows = [["Config","MACSuccess","MACTime(s)","MACBacktracks",
             "MinCSuccess","MinCTime(s)"]]
    for (nc,nr,ns,density,tight,label) in configs:
        d = os.path.join(INSTANCES_DIR, f"exp4_{label.lower()}")
        generate_instance(nc,nr,ns,density,tight,output_dir=d,seed=55)
        mac_r = _run_algo(lambda dd=d: _load_csp(dd), mac_search,
                          {'use_mrv':True,'use_degree':True,'use_lcv':False}, n_runs=5)
        mc_r  = _run_algo(lambda dd=d: _load_csp(dd), min_conflicts_search,
                          {'max_steps':10000}, n_runs=5)
        rows.append([label,
                     f"{_success(mac_r)}%", f"{_avg(mac_r,'elapsed')}",
                     f"{_avg(mac_r,'backtracks'):.0f}",
                     f"{_success(mc_r)}%",  f"{_avg(mc_r,'elapsed')}"])
    _print_table("Systematic (MAC) vs. Local Search (Min-Conflicts):", rows)

    with open(os.path.join(RESULTS_DIR,"experiment4.txt"),"w") as f:
        f.write("Experiment 4 complete.\n")
    print("Experiment 4 results saved to results/experiment4.txt")


def run_all():
    experiment_1()
    experiment_2()
    experiment_3()
    experiment_4()
    print("\nAll experiments complete. Results in 'results/' directory.")
