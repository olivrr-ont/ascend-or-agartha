from dataclasses import dataclass
from typing import Dict

@dataclass
class PriceBook:
    prices: Dict[str, int]
    def __init__(self):
        self.prices = {
            "skincare_basic": 30, "gua_sha": 20, "bananas": 2, "coconut_water": 4,
            "junk_food": 3, "soda": 2, "supp_basic": 25, "contacts": 15,
            "dye": 30, "eye_surgery": 2000, "raw_milk": 6, "risky_bone": 100,
            "gym_week": 50
        }

def can_afford(player, item_id: str, pricebook: PriceBook) -> bool:
    return player.wallet >= pricebook.prices.get(item_id, 1_000_000)

def spend(player, amount: int):
    player.wallet = max(0, player.wallet - amount)

def earn(player, amount: int):
    player.wallet += amount
