"""
selection.py - Tournament and Roulette Wheel Selection
AI2002 - Artificial Intelligence | Spring 2026 | Assignment 02
"""
import random, copy


def tournament_selection(population, fitnesses, tournament_size=5):
    candidates = random.sample(range(len(population)),
                                min(tournament_size, len(population)))
    winner = max(candidates, key=lambda i: fitnesses[i])
    return copy.deepcopy(population[winner])


def roulette_wheel_selection(population, fitnesses):
    min_f   = min(fitnesses)
    shifted = [f - min_f + 1e-6 for f in fitnesses]
    total   = sum(shifted)
    pick    = random.uniform(0, total)
    cumul   = 0.0
    for i, w in enumerate(shifted):
        cumul += w
        if cumul >= pick:
            return copy.deepcopy(population[i])
    return copy.deepcopy(population[-1])


def select_parent(population, fitnesses, use_tournament=True,
                  tournament_rate=0.70, tournament_size=5):
    if use_tournament and random.random() < tournament_rate:
        return tournament_selection(population, fitnesses, tournament_size)
    return roulette_wheel_selection(population, fitnesses)


def elitism_selection(population, fitnesses, elite_rate=0.10):
    n_elite = max(1, int(len(population) * elite_rate))
    sorted_idx = sorted(range(len(population)),
                         key=lambda i: fitnesses[i], reverse=True)
    return [copy.deepcopy(population[i]) for i in sorted_idx[:n_elite]]
