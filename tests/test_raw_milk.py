import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from aoa_core.effects import RAW_MILK_DURATION_DAYS, daily_resolution
from aoa_core.items import load_items, use_item
from aoa_core.models import Player, Stats


def mk_player():
    stats = Stats(genes=10, skinQuality=10, bloat=5, boneMass=10, coloring=5)
    features = {"eye": "Blue", "hair": "Brown", "ethnicity": "Midlander"}
    return Player(id="test", features=features, stats=stats)


def test_raw_milk_sets_flag_duration():
    player = mk_player()
    items = load_items()
    active_effects = []

    ok, _ = use_item(player, "raw_milk", items, active_effects)

    assert ok is True
    assert player.flags.rawMilkBuffDays == RAW_MILK_DURATION_DAYS


def test_raw_milk_proc_only_while_active(monkeypatch):
    player = mk_player()
    items = load_items()
    active_effects = []

    use_item(player, "raw_milk", items, active_effects)

    procs = []

    def fake_chance(p):
        procs.append(p)
        return True

    monkeypatch.setattr("aoa_core.effects.chance", fake_chance)

    starting_bone_mass = player.stats.boneMass

    for _ in range(RAW_MILK_DURATION_DAYS):
        daily_resolution(player, active_effects)

    assert player.stats.boneMass == starting_bone_mass + RAW_MILK_DURATION_DAYS
    assert player.flags.rawMilkBuffDays == 0
    assert len(procs) == RAW_MILK_DURATION_DAYS

    # Extra day should not roll chance when the buff expired
    daily_resolution(player, active_effects)
    assert len(procs) == RAW_MILK_DURATION_DAYS
