import random
from typing import Sequence, Tuple, TypeVar

T = TypeVar("T")

def seed(value: int | None = None):
    random.seed(value)

def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))

def wchoice(table: Sequence[Tuple[T, float]]) -> T:
    total = sum(w for _, w in table)
    r = random.uniform(0, total)
    s = 0.0
    for v, w in table:
        s += w
        if r <= s:
            return v
    return table[-1][0]

def randn(mu=0.0, sigma=1.0) -> float:
    return random.gauss(mu, sigma)

def chance(p: float) -> bool:
    return random.random() < p
