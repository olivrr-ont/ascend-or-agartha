from __future__ import annotations
from typing import Tuple
from .models import Player, World, mk_player
from .psl import calc_psl_true, coloring_from_traits
from .effects import daily_resolution
from .rng import chance

# --- Sleep behavior ---
WAKE_HOUR = 8  # change this if you want a different morning time

def sleep_to_morning(world: World, wake_hour: int = WAKE_HOUR):
    """Advance the world clock to the NEXT day at wake_hour."""
    world.day += 1
    world.hour = wake_hour

# --- Core lifecycle ---

def new_game(seed: int | None = None) -> Tuple[Player, World]:
    if seed is not None:
        import random; random.seed(seed)
    p = mk_player()
    p.stats.coloring = coloring_from_traits(
        p.features["eye"], p.features["hair"], p.features["ethnicity"], 0
    )
    p.psl.true = calc_psl_true(
        p.stats.genes, p.stats.skinQuality, p.stats.bloat, p.stats.boneMass, p.stats.coloring
    )
    w = World()
    return p, w

def refresh_psl(p: Player):
    p.psl.true = calc_psl_true(
        p.stats.genes, p.stats.skinQuality, p.stats.bloat, p.stats.boneMass, p.stats.coloring
    )

def next_hour(world: World):
    """Generic time pass helper (not used by sleep)."""
    world.hour += 1
    if world.hour >= 24:
        world.hour = 0
        world.day += 1

def end_day_apply(player: Player, world: World, active_effects: list):
    """
    Resolve nightly effects/streaks, update PSL, handle physique progression,
    then jump straight to next morning at WAKE_HOUR.
    """
    # Nightly pipeline (effects, streaks, decay, procs)
    daily_resolution(player, active_effects)
    refresh_psl(player)

    # Physique progression: 3 workouts/week => +1 "consistent week".
    # Every 3 consistent weeks => +1 physique tier (max 5).
    if player.streaks.workoutsThisWeek >= 3:
        player.streaks.weeksConsistent += 1
        player.streaks.workoutsThisWeek = 0
        if player.streaks.weeksConsistent % 3 == 0:
            player.physiqueTier = min(5, player.physiqueTier + 1)

    # Jump to next morning
    sleep_to_morning(world, WAKE_HOUR)

def can_enter_agartha(p: Player) -> bool:
    # Use displayed PSL if available; else round(true)
    shown = p.psl.displayed if p.psl.displayed is not None else round(p.psl.true)
    if shown < 6:
        return False
    eye, hair, eth = p.features["eye"], p.features["hair"], p.features["ethnicity"]
    return (
        (eth == "Agarthan" and hair == "Blonde") or
        (hair == "Blonde" and eth == "Highlander") or
        (hair == "Blonde" and eye == "Blue")
    )

def evaluate_endings(p: Player) -> str | None:
    # Secret narrative ending
    if p.psl.true >= 9.9:
        return "True Adam"
    if can_enter_agartha(p):
        return "Agartha"
    # Marriage example gate (can tune later)
    if (p.psl.displayed or round(p.psl.true)) >= 6 and p.physiqueTier >= 5 and sum(p.relationships.values()) >= 1.0:
        return "Marriage"
    return None

def use_risky_bone_option(player: Player) -> str:
    """
    Fictional high-risk action with clear negative side-effects.
    Gated by cooldown; no real-world guidance.
    """
    if player.flags.riskyCooldown > 0:
        return "Risky feature on cooldown."
    player.flags.riskyCooldown = 7

    # 35% success chance; 15% of successes grant +1 extra
    if chance(0.35):
        from .rng import chance as ch
        inc = 1 + (1 if ch(0.15) else 0)
        player.stats.boneMass = min(20, player.stats.boneMass + inc)

    # Guaranteed side effects
    player.stats.skinQuality = max(1, player.stats.skinQuality - 2)
    player.stats.bloat = min(10, player.stats.bloat + 1)

    refresh_psl(player)
    return "Applied risky feature (fictional). Negative side effects occurred."
