"""Reproducible Lotofácil combinatorics; does not predict random outcomes."""
from collections import Counter
from math import comb

NUMBERS = frozenset(range(1, 26))

def validate_draw(numbers):
    if not isinstance(numbers, (tuple, list, set)):
        raise ValueError("A draw needs a list, tuple or set")
    if len(numbers) != 15 or any(type(n) is not int or n not in NUMBERS for n in numbers):
        raise ValueError("Each draw needs 15 integers from 1 to 25")
    selected = frozenset(numbers)
    if len(selected) != 15:
        raise ValueError("Repeated numbers")
    return selected

def matching_distribution():
    """Exact probabilities for the number of hits in a random 15-number bet."""
    total = comb(25, 15)
    return {k: comb(15, k) * comb(10, 15 - k) / total for k in range(5, 16)}

def frequency(draws):
    draws = [validate_draw(draw) for draw in draws]
    counts = Counter(n for draw in draws for n in draw)
    return {"draw_count": len(draws), "frequency": {n: counts[n] for n in range(1, 26)},
            "caveat": "Past occurrences do not increase a number's chance in an independent draw."}

def hits(bet, draw):
    return len(validate_draw(bet) & validate_draw(draw))
