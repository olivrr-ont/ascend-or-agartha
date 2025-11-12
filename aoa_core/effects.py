from dataclasses import dataclass
from typing import Literal
from .rng import clamp, chance
from .psl import coloring_from_traits

@dataclass
class Effect:
    stat: Literal["bloat","skinQuality","boneMass","coloring"]
    delta: float
    durationDays: int
    stacking: Literal["linear","diminishing"]="linear"

def apply_once(stats, eff: Effect):
    if eff.stat=="bloat":
        stats.bloat = int(clamp(stats.bloat + eff.delta, 1, 10))
    elif eff.stat=="skinQuality":
        stats.skinQuality = int(clamp(stats.skinQuality + eff.delta, 1, 20))
    elif eff.stat=="boneMass":
        stats.boneMass = int(clamp(stats.boneMass + eff.delta, 1, 20))
    elif eff.stat=="coloring":
        stats.coloring = int(clamp(stats.coloring + eff.delta, 0, 20))

def daily_resolution(player, active_effects: list[Effect]):
    # 1) resolve timed effects
    for eff in list(active_effects):
        apply_once(player.stats, eff)
        eff.durationDays -= 1
        if eff.durationDays <= 0:
            active_effects.remove(eff)

    # 2) lifestyle streaks -> coloring bonus
    bonus = 0
    bonus += min(2, player.streaks.skincareDays//5)
    bonus += min(2, player.streaks.noJunkDays//5)
    bonus += min(3, player.streaks.tanLevel)
    bonus = min(5, bonus)

    player.stats.coloring = coloring_from_traits(
        player.features["eye"], player.features["hair"], player.features["ethnicity"], bonus
    )

    # 3) junk decay
    if player.flags.ateJunkToday:
        player.stats.skinQuality = max(1, player.stats.skinQuality - 1)
        player.flags.ateJunkToday = False

    # 4) raw milk nightly proc (3%)
    if chance(0.03):
        player.stats.boneMass = min(20, player.stats.boneMass + 1)

    # 5) risky cooldown tick
    if player.flags.riskyCooldown > 0:
        player.flags.riskyCooldown -= 1

    return active_effects
