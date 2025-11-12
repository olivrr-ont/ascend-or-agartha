import json, hashlib, pathlib
from .models import Player, World, Stats, PSL, Flags, Streaks

def _checksum(payload: str) -> str:
    return hashlib.sha256(payload.encode()).hexdigest()

def write_save(player: Player, world: World, path: str):
    blob = {
        "saveVersion": 1,
        "player": player.__dict__ | {
            "stats": player.stats.__dict__,
            "psl": player.psl.__dict__,
            "flags": player.flags.__dict__,
            "streaks": player.streaks.__dict__,
        },
        "world": world.__dict__,
    }
    payload = json.dumps(blob, separators=(",", ":"))
    wrapper = {"checksum": _checksum(payload), "payload": payload}
    pathlib.Path(path).write_text(json.dumps(wrapper, indent=2))

def read_save(path: str) -> tuple[Player, World]:
    raw = json.loads(pathlib.Path(path).read_text())
    assert _checksum(raw["payload"]) == raw["checksum"], "Save checksum mismatch"
    data = json.loads(raw["payload"])
    p = data["player"]; w = data["world"]
    player = Player(
        id=p["id"], features=p["features"],
        stats=Stats(**p["stats"]),
        physiqueTier=p["physiqueTier"], wallet=p["wallet"],
        psl=PSL(**p["psl"]), flags=Flags(**p["flags"]), streaks=Streaks(**p["streaks"]),
        inventory=p.get("inventory",{}), relationships=p.get("relationships",{})
    )
    world = World(**w)
    return player, world
