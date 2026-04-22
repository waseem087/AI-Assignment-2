# Q2 - Genetic Algorithm Course Scheduling

## Overview

This project implements a **Genetic Algorithm (GA)** for **multi-student course scheduling** with constraints, preferences, and optimization objectives.

The system generates:

* Best Schedule per Student
* Fitness Progress Graph
* Convergence Analysis
* Multi-run Performance Metrics

---

# Setup

```bash
pip install matplotlib pyyaml
```

---

# Run Commands

## Single Run (Part A)

```bash
python main.py --seed 42
```

### Output

* Best Schedule
* Final Fitness Score
* Convergence Graph
* Performance Metrics

### Attach Screenshots

```
results/single_run_schedule.png
results/single_run_fitness.png
results/single_run_metrics.png
```

---

## 10-Run Experiment (Part B)

```bash
python main.py --runs 10 --seed 42
```

or

```bash
python main.py --analyze
```

### Output

* Best Fitness per Run
* Mean Fitness
* Standard Deviation
* Convergence Generation
* Termination Criteria

### Attach Screenshots

```
results/10run_fitness.png
results/10run_convergence.png
results/10run_summary.png
```

---

# Example Output

## Best Schedule Output

```
Student S1
DS-2 | ALG-1 | AI-3 | DB-1 | OS-2

Student S2
...
```

---

# Performance Metrics

Example:

```
================================
GENETIC ALGORITHM PERFORMANCE
================================
Best Fitness : 0.7471
Mean Fitness : 0.7375
Std Dev      : 0.0052
Generations  : 60
Termination  : fitness_converged
================================
```

---

# Files

```
main.py        -- GA loop, population init, diversity, termination
chromosome.py  -- Encoding structure
fitness.py     -- Fitness calculation
operators.py   -- Crossover & mutation operators
selection.py   -- Selection strategies
utils.py       -- Helper functions
config.yaml    -- GA parameters
course_catalog.json
student_requirements.json
```

---

# Chromosome Encoding

```
chromosome = {
    'S1': [{'course_id': 'DS',  'section': 2},
           {'course_id': 'ALG', 'section': 1},
           {'course_id': 'AI',  'section': 3},
           {'course_id': 'DB',  'section': 1},
           {'course_id': 'OS',  'section': 2}],
    'S2': [...]
}
```

* 5 students
* 5 courses each
* 15 credits per student
* 25 total assignments

---

# Fitness Function

```
Fitness = 0.30*S_time 
        + 0.25*S_gap 
        + 0.20*S_friend
        + 0.15*S_workload 
        + 0.10*S_lunch 
        - Penalties
```

### Penalties

| Constraint      | Penalty |
| --------------- | ------- |
| Time Conflict   | -1000   |
| Missing Credits | -800    |
| Blocked Course  | -1000   |

---

# Verified Results (10 Runs)

```
Best fitness:  0.7471
Mean fitness:  0.7375 +/- 0.0052
Avg convergence generation: 60
Termination: fitness_converged
All students: 15 credits, zero penalties
```

---

# Folder Structure

```
Q2_GA/
│
├── main.py
├── chromosome.py
├── fitness.py
├── operators.py
├── selection.py
├── utils.py
├── config.yaml
├── course_catalog.json
├── student_requirements.json
└── results/
```

---

# Author

**Waseem Akhtar**
AI Assignment 2 — Genetic Algorithm Course Scheduling
