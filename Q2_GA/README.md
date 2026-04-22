# Q2 - Genetic Algorithm Course Scheduling

## Setup
pip install matplotlib pyyaml

## Run Commands

# Single run
python main.py --seed 42

# 10 independent runs (full Part B experiment)
python main.py --runs 10 --seed 42
# or:
python main.py --analyze

## Files
main.py        -- GA loop, population init, diversity, termination, CLI
chromosome.py  -- Encoding: {S1..S5: [{course_id, section}x5]}
fitness.py     -- 5-component weighted fitness + penalty system
operators.py   -- 3 crossover + 4 mutation operators
selection.py   -- Tournament (70%) + Roulette (30%) + Elitism (10%)
utils.py       -- Data loaders, schedule helpers, conflict checking
config.yaml    -- All GA parameters (provided)
course_catalog.json      -- 15 courses (provided)
student_requirements.json -- 5 student profiles (provided)

## Chromosome Encoding
chromosome = {
    'S1': [{'course_id': 'DS',  'section': 2},   # section 1-3 from catalog
           {'course_id': 'ALG', 'section': 1},
           ...   # exactly 5 entries = 15 credits],
    'S2': [...], ...
}
Section encodes day+time implicitly via catalog. 25 integers total.

## Fitness
Fitness = 0.30*S_time + 0.25*S_gap + 0.20*S_friend
        + 0.15*S_workload + 0.10*S_lunch - Penalties

Penalties: time conflict -1000, missing credits -800, blocked -1000

## Verified Results (10 runs, seed=42..51)
Best fitness:  0.7471
Mean fitness:  0.7375 +/- 0.0052
Avg convergence generation: 60
Termination: fitness_converged (all 10 runs)
All students: 15 credits, zero penalties
