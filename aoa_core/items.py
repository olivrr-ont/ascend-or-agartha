from __future__ import annotations
from typing import Dict, Any, Tuple
from .effects import Effect
from .economy import PriceBook, can_afford, spend

def load_items() -> Dict[str, Any]:
    from .dataio import load_json
    items = {it["id"]: it for it in load_json("items.json")}
    return items

def load_shops() -> Dict[str, Any]:
    from .dataio import load_json
    shops = {s["id"]: s for s in load_json("shops.json")}
    return shops

def add_to_inventory(player, item_id: str, qty: int = 1):
    inv = player.inventory
    inv[item_id] = inv.get(item_id, 0) + qty

def remove_from_inventory(player, item_id: str, qty: int = 1) -> bool:
    inv = player.inventory
    if inv.get(item_id, 0) < qty:
        return False
    inv[item_id] -= qty
    if inv[item_id] <= 0:
        del inv[item_id]
    return True

def buy_item(player, shop: Dict[str,Any], item_id: str, pricebook: PriceBook, items_db: Dict[str,Any]) -> Tuple[bool,str]:
    if item_id not in shop["inventory"]:
        return False, "This shop doesn't sell that item."
    price = pricebook.prices.get(item_id)
    if price is None:
        return False, "No price is set for that item."
    if not can_afford(player, item_id, pricebook):
        return False, "You can't afford it."
    spend(player, price)
    add_to_inventory(player, item_id, 1)
    return True, f"Bought 1x {items_db[item_id]['name']} for ${price}."

def use_item(player, item_id: str, items_db: Dict[str,Any], active_effects: list[Effect]) -> Tuple[bool,str]:
    it = items_db.get(item_id)
    if not it:
        return False, "Unknown item."
    # special-case flags that the GDD calls out
    if item_id == "junk_food":
        player.flags.ateJunkToday = True

    # translate JSON effects -> Effect objects and enqueue
    effs = it.get("effects", [])
    if not effs and item_id not in ("raw_milk",):
        # raw_milk has nightly 3% proc handled in daily pipeline already
        pass
    for e in effs:
        active_effects.append(Effect(stat=e["stat"], delta=e["delta"], durationDays=e["durationDays"]))

    return True, f"Used {it['name']}."
