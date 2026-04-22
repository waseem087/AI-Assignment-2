"""
main.py - CLI for Q1 CSP Timetabling
AI2002 - Artificial Intelligence | Spring 2026 | Assignment 02

Usage:
  python main.py --input-dir instances/small --algorithm mac
  python main.py --input-dir instances/small --algorithm backtrack --var-heuristic mrv_degree --val-heuristic lcv
  python main.py --generate --courses 20 --rooms 16 --slots 30 --density 0.5 --output-dir instances/test/
  python main.py --experiment 1          # Algorithm comparison
  python main.py --experiment 2          # Heuristic impact
  python main.py --experiment 3          # Phase transition
  python main.py --experiment 4          # Systematic vs local
  python main.py --experiment all
"""

import sys, io
# Ensure UTF-8 output on Windows (avoids cp1252 UnicodeEncodeError)
try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
except AttributeError:
    pass

import argparse, os
from timetable import (TimetableCSP, load_courses, load_rooms, load_timeslots,
                        load_students, load_availability, print_solution)
from algorithms import backtracking_search, forward_checking_search, mac_search, min_conflicts_search
from generator  import generate_instance
import experiments as exp_module


def build_csp(input_dir):
    courses  = load_courses(  os.path.join(input_dir, "courses.csv"))
    rooms    = load_rooms(    os.path.join(input_dir, "rooms.csv"))
    slots    = load_timeslots(os.path.join(input_dir, "timeslots.csv"))
    students = load_students( os.path.join(input_dir, "students.csv"))
    avail_p  = os.path.join(input_dir, "instructor_availability.csv")
    avail    = load_availability(avail_p) if os.path.exists(avail_p) else {}
    return TimetableCSP(courses, rooms, slots, students, availability=avail)


def solve(args):
    csp        = build_csp(args.input_dir)
    use_mrv    = args.var_heuristic in ("mrv","mrv_degree")
    use_degree = args.var_heuristic == "mrv_degree"
    use_lcv    = args.val_heuristic == "lcv"

    algo = args.algorithm.lower()
    if algo == "backtrack":
        name = f"Backtracking (mrv={use_mrv}, degree={use_degree}, lcv={use_lcv})"
        result, m = backtracking_search(csp, use_mrv=use_mrv, use_degree=use_degree, use_lcv=use_lcv)
    elif algo == "fc":
        name = f"Forward Checking (mrv={use_mrv}, degree={use_degree}, lcv={use_lcv})"
        result, m = forward_checking_search(csp, use_mrv=use_mrv, use_degree=use_degree, use_lcv=use_lcv)
    elif algo == "mac":
        name = f"MAC / AC-3 (mrv={use_mrv}, degree={use_degree}, lcv={use_lcv})"
        result, m = mac_search(csp, use_mrv=use_mrv, use_degree=use_degree, use_lcv=use_lcv)
    elif algo == "minconflicts":
        name = "Min-Conflicts Local Search"
        result, m = min_conflicts_search(csp, max_steps=10000)
    else:
        print(f"Unknown algorithm: {algo}"); sys.exit(1)

    status = "SOLUTION FOUND" if result else "UNSATISFIABLE / TIMEOUT"
    print_solution(result or {}, csp, name, m, status)


def main():
    parser = argparse.ArgumentParser(description="CSP University Timetabling Solver")
    parser.add_argument("--input-dir",     default=None)
    parser.add_argument("--algorithm",     default="mac",
                        choices=["backtrack","fc","mac","minconflicts"])
    parser.add_argument("--var-heuristic", default="mrv_degree",
                        choices=["none","mrv","mrv_degree"])
    parser.add_argument("--val-heuristic", default="lcv",
                        choices=["none","lcv"])
    parser.add_argument("--generate",      action="store_true")
    parser.add_argument("--courses",       type=int, default=10)
    parser.add_argument("--rooms",         type=int, default=None)
    parser.add_argument("--slots",         type=int, default=20)
    parser.add_argument("--density",       type=float, default=0.5)
    parser.add_argument("--tightness",     type=float, default=0.5)
    parser.add_argument("--output-dir",    default="instances/generated")
    parser.add_argument("--experiment",    default=None,
                        choices=["1","2","3","4","all"])
    parser.add_argument("--seed",          type=int, default=42)
    args = parser.parse_args()

    if args.experiment:
        {"1": exp_module.experiment_1,
         "2": exp_module.experiment_2,
         "3": exp_module.experiment_3,
         "4": exp_module.experiment_4,
         "all": exp_module.run_all}[args.experiment]()
        return

    if args.generate:
        generate_instance(args.courses, args.rooms, args.slots,
                          args.density, args.tightness,
                          output_dir=args.output_dir, seed=args.seed)
        return

    if args.input_dir is None:
        args.input_dir = "instances/small"
        if not os.path.isdir(args.input_dir):
            print("No --input-dir given and 'instances/small/' not found.")
            print("Run: python main.py --generate --output-dir instances/small/")
            sys.exit(1)

    solve(args)


if __name__ == "__main__":
    main()
