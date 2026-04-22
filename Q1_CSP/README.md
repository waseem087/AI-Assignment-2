# Q1 - CSP University Timetabling

## Overview

This project implements a **Constraint Satisfaction Problem (CSP)** based **University Timetabling System** supporting multiple algorithms, heuristics, and experimental evaluations.

The system generates:

* Schedule Grid View
* Performance Metrics
* Algorithm Comparison Results
* Heuristic Impact Analysis
* Phase Transition Analysis
* Systematic vs Local Search Comparison

---

# Setup

```bash
pip install matplotlib pyyaml
```

---

# Run Commands

## Solve Timetable Using Different Algorithms

```bash
python main.py --input-dir instances/small --algorithm mac
python main.py --input-dir instances/small --algorithm backtrack
python main.py --input-dir instances/small --algorithm fc
python main.py --input-dir instances/small --algorithm minconflicts
```

---

# Schedule Grid View Output

Each algorithm produces a **Schedule Grid View** similar to:

```
===========================================================
SCHEDULE GRID VIEW
===========================================================
Room      MWF-10  MWF-11  MWF-12  MWF-8  MWF-9  TTh-11
-----------------------------------------------------------
L301      [EMPTY] ...
M101      MATH101-01 ...
...
```

### Algorithm-wise Outputs

#### MAC Algorithm

```bash
python main.py --input-dir instances/small --algorithm mac
```

**Output**

* Schedule Grid View
* Performance Metrics

Attach Screenshot:

```
/results/backtrack_schedule.png



/results/mac_metrics.png
```
<img width="866" height="405" alt="image" src="https://github.com/user-attachments/assets/a2b75407-7399-4609-8510-1a6a7718b10d" />

<img width="632" height="189" alt="image" src="https://github.com/user-attachments/assets/b779f0b6-111a-43f0-af64-4c7fd930099d" />

---

#### Backtracking Algorithm

```bash
python main.py --input-dir instances/small --algorithm backtrack
```

**Output**

* Schedule Grid View
* Performance Metrics

Attach Screenshot:

```
/results/backtrack_schedule.png
/results/backtrack_metrics.png
```
<img width="898" height="596" alt="image" src="https://github.com/user-attachments/assets/7e20f199-5fa2-4cc9-a511-09b846c486b7" />

---

#### Forward Checking

```bash
python main.py --input-dir instances/small --algorithm fc
```

**Output**

* Schedule Grid View
* Performance Metrics

Attach Screenshot:

```
/results/fc_schedule.png
/results/fc_metrics.png
```
<img width="853" height="548" alt="image" src="https://github.com/user-attachments/assets/9cd8c765-aa13-43c5-99cb-080d95edba04" />

---

#### Min-Conflicts

```bash
python main.py --input-dir instances/small --algorithm minconflicts
```

**Output**

* Schedule Grid View
* Performance Metrics

Attach Screenshot:

```
/results/minconflicts_schedule.png
/results/minconflicts_metrics.png
```
<img width="875" height="564" alt="image" src="https://github.com/user-attachments/assets/cd2238f5-067d-4ca8-80f0-a7ca07db0806" />

---

# Generate New Instance

```bash
python main.py --generate --courses 20 --rooms 16 --slots 30 --density 0.5 --output-dir instances/test/
```

---

# Experiments

## Experiment 1 — Algorithm Comparison

```bash
python main.py --experiment 1
```

**Output**

* Execution Time Comparison
* Constraint Checks
* Backtracks
* Success Rate

Attach:

```
/results/experiment1.png
```
<img width="771" height="125" alt="image" src="https://github.com/user-attachments/assets/6e0d4058-6406-4f98-b9e6-e5247e93d04d" />

---

## Experiment 2 — Heuristic Impact

```bash
python main.py --experiment 2
```

Includes:

* MRV vs No MRV
* Degree Heuristic
* LCV Comparison

Attach:

```
/results/experiment2.png
```
<img width="781" height="145" alt="image" src="https://github.com/user-attachments/assets/06494482-6433-479b-b807-72590cd83941" />

---

## Experiment 3 — Phase Transition

```bash
python main.py --experiment 3
```

Output:

* Constraint Density vs Solvability

Attach:

```
/results/experiment3.png
```
<img width="645" height="274" alt="image" src="https://github.com/user-attachments/assets/be7b43c4-6fe7-40db-838f-622eaad09f1a" />

---

## Experiment 4 — Systematic vs Local Search

```bash
python main.py --experiment 4
```

Output:

* Backtracking vs Min-Conflicts Comparison

Attach:

```
/results/experiment4.png
```
<img width="833" height="417" alt="image" src="https://github.com/user-attachments/assets/0ad3df7f-7ebe-4fb6-b9d3-9abbdd290c86" />

---

# Run All Experiments

```bash
python main.py --experiment all
```

---

# Performance Metrics

Each run displays:

* Execution Time
* Nodes Explored
* Backtracks
* Constraint Checks
* Success Status

Example:

```
===================================
Performance Metrics
===================================
Execution Time : 0.45s
Backtracks     : 120
Constraint Checks : 2340
Status         : Success
```

---

# Files

```
csp.py         -- Generic CSP framework
timetable.py   -- TimetableCSP: CSV parsing + constraint registration
algorithms.py  -- Backtracking, Forward Checking, MAC/AC-3, Min-Conflicts
heuristics.py  -- MRV, Degree, LCV
metrics.py     -- Performance tracking
generator.py   -- Instance generator
experiments.py -- All experiments
main.py        -- CLI
```

---

# Key Design Decisions

* heuristics.py builds {(vi,vj): [fn]} dictionary for fast lookup
* AC-3 uses early-exit optimization
* LCV caps neighbor evaluation
* Generator ensures satisfiable instances
* 30-second timeout per solve

---

# Folder Structure

```
Q1_CSP/
│
├── instances/
├── results/
├── main.py
├── csp.py
├── timetable.py
├── algorithms.py
├── heuristics.py
├── metrics.py
├── generator.py
└── experiments.py
```

---

# Author

**Waseem Akhtar**
AI Assignment 2 — CSP University Timetabling
