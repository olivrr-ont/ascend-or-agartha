from .rng import clamp

def _norm(x: float, lo: float, hi: float) -> float:
    return (x - lo) / (hi - lo)

def coloring_from_traits(eye: str, hair: str, eth: str, lifestyle_bonus: int) -> int:
    eye_pts = {"Blue":3,"Green":2,"Hazel":1,"Black":1,"Brown":0}.get(eye,0)
    hair_pts= {"Blonde":3,"Ginger":2,"Black":1,"Brown":0}.get(hair,0)
    eth_pts = {"Agarthan":3,"Highlander":2,"Eastborne":1,"Sundweller":1,"Midlander":0}.get(eth,0)
    base = min(15, eye_pts + hair_pts + eth_pts)
    return int(clamp(base + min(5, lifestyle_bonus), 0, 20))

def calc_psl_true(genes:int, skin:int, bloat:int, bone:int, coloring:int) -> float:
    bloat_norm = 1 - _norm(bloat, 1, 10)
    score01 = (
        0.30 * _norm(genes, 1, 30) +
        0.20 * _norm(skin, 1, 20) +
        0.10 * bloat_norm +
        0.20 * _norm(bone, 1, 20) +
        0.20 * _norm(coloring, 1, 20)
    )
    return clamp(2 + score01 * 7, 2, 9.99)

def bracket_from_psl(psl_true_or_display: float | int) -> int:
    return int(max(2, min(9, round(psl_true_or_display))))
