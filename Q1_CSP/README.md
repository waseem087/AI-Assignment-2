# Q1 - CSP University Timetabling

## Setup
pip install matplotlib pyyaml

## Run Commands

# Solve the default small instance
python main.py --input-dir instances/small --algorithm mac
python main.py --input-dir instances/small --algorithm backtrack --var-heuristic mrv_degree --val-heuristic lcv
python main.py --input-dir instances/small --algorithm fc
python main.py --input-dir instances/small --algorithm minconflicts

# Generate a new instance
python main.py --generate --courses 20 --rooms 16 --slots 30 --density 0.5 --output-dir instances/test/

# Run experiments
python main.py --experiment 1   # Algorithm comparison
python main.py --experiment 2   # Heuristic impact
python main.py --experiment 3   # Phase transition
python main.py --experiment 4   # Systematic vs local
python main.py --experiment all # All four experiments

## Files
csp.py         -- Generic CSP framework
timetable.py   -- TimetableCSP: CSV parsing + constraint registration
algorithms.py  -- Backtracking, Forward Checking, MAC/AC-3, Min-Conflicts
heuristics.py  -- MRV, Degree, LCV (cached constraint index for speed)
metrics.py     -- Performance tracking
generator.py   -- Satisfiable random instance generator
experiments.py -- All four experiments
main.py        -- CLI

## Key Design Decisions
- heuristics.py builds a {(vi,vj): [fn]} dict once -> O(1) per constraint check
- AC-3 _revise uses early-exit (break on first support found)
- LCV caps at 8 neighbours to stay tractable on large instances
- generator.py builds a valid assignment first (guarantees satisfiability)
- Each solve has a 30-second wall-clock timeout
