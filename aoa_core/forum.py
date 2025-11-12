import hashlib, random
from .rng import randn, clamp
from .psl import bracket_from_psl

SAFE_EPS_CLAMP = 0.4

def image_hash(img_bytes: bytes) -> str:
    return hashlib.sha1(img_bytes).hexdigest()

def forum_rate(player, image_bytes: bytes, fraud=False, comments_bank=None):
    """
    Returns (display_rating:int, comments:list[str])
    - Same image hash => same numeric rating (new comments allowed).
    """
    ih = image_hash(image_bytes)
    if player.psl.lastForumImageHash == ih and player.psl.displayed is not None:
        rating = player.psl.displayed
    else:
        eps = clamp(randn(0,0.15), -SAFE_EPS_CLAMP, SAFE_EPS_CLAMP)
        fraud_boost = 0.5 if fraud else 0.0
        rating = round(clamp(player.psl.true + eps + fraud_boost, 2, 9))
        player.psl.displayed = rating
        player.psl.lastForumImageHash = ih

    bracket = bracket_from_psl(rating)
    bank_key = "low" if bracket <= 3 else "mid" if bracket <= 6 else "high"
    pool = (comments_bank or {
        "low":["not your best pic","harsh angle, fix lighting"],
        "mid":["potential","MTN","normie looking"],
        "high":["HTN","Chadlite","OMG"]
    })[bank_key]
    comments = random.sample(pool, k=2 if len(pool)>=2 else 1)
    return rating, comments
