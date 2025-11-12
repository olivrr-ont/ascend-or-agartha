import json, pathlib

DATA_DIR = pathlib.Path(__file__).parent / "data"

def load_json(name: str):
    p = DATA_DIR / name
    return json.loads(p.read_text(encoding="utf-8"))
