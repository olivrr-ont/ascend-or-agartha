from pathlib import Path
from aoa_core.sim import new_game, end_day_apply, can_enter_agartha, evaluate_endings, refresh_psl, use_risky_bone_option
from aoa_core.forum import forum_rate
from aoa_core.save import write_save, read_save
from aoa_core.effects import Effect
from aoa_core.economy import PriceBook
from aoa_core.items import load_items, load_shops, buy_item, use_item, remove_from_inventory

ACTIVE_EFFECTS: list[Effect] = []
ITEMS_DB = load_items()
SHOPS = load_shops()
PRICES = PriceBook()

def print_player(p, w):
    print("\n=== Day", w.day, "Hour", w.hour, "===")
    print(f"PSL_true={p.psl.true:.2f} | PSL_display={p.psl.displayed}")
    print(f"Features: eyes={p.features['eye']} hair={p.features['hair']} eth={p.features['ethnicity']}")
    s=p.stats
    print(f"Stats: genes={s.genes} skin={s.skinQuality} bloat={s.bloat} bone={s.boneMass} coloring={s.coloring}")
    print(f"Physique Tier={p.physiqueTier} | Wallet=${p.wallet}")
    print(f"Streaks: skincare={p.streaks.skincareDays} noJunk={p.streaks.noJunkDays} tan={p.streaks.tanLevel}")

def list_inventory(p):
    if not p.inventory:
        print("Inventory: (empty)")
        return
    print("Inventory:")
    for iid, qty in p.inventory.items():
        print(f" - {iid} x{qty} ({ITEMS_DB[iid]['name']})")

def shop_menu(p):
    print("\nShops:")
    for sid, s in SHOPS.items():
        print(f" [{sid}] {s['name']}")
    sid = input("Enter shop id (blank to cancel): ").strip()
    if not sid or sid not in SHOPS:
        return
    s = SHOPS[sid]
    print(f"\n{s['name']} (open {s['hours']['open']}:00–{s['hours']['close']}:00)")
    print("Items:")
    for iid in s["inventory"]:
        price = PRICES.prices.get(iid, "?")
        print(f" - {iid:15} ${price:>4}  {ITEMS_DB[iid]['name']}")
    iid = input("Enter item id to buy (blank to cancel): ").strip()
    if not iid:
        return
    ok, msg = buy_item(p, s, iid, PRICES, ITEMS_DB)
    print(msg)

def inventory_menu(p):
    list_inventory(p)
    iid = input("Enter item id to use (blank to cancel): ").strip()
    if not iid:
        return
    if not p.inventory.get(iid):
        print("You don’t have that.")
        return
    ok, msg = use_item(p, iid, ITEMS_DB, ACTIVE_EFFECTS)
    if ok:
        remove_from_inventory(p, iid, 1)
    print(msg)

def main():
    if Path("save.json").exists():
        p, w = read_save("save.json")
    else:
        p, w = new_game()

    print("=== Ascend or Agartha (Local CLI) ===")
    while True:
        refresh_psl(p)
        print_player(p, w)
        print("\nChoose:")
        print("[1] Skincare (+streak)")
        print("[2] Eat junk (skin decay)")
        print("[3] Gym workout")
        print("[4] Post selfie (normal)")
        print("[5] Post selfie (fraud mode)")
        print("[6] Use contacts (+Coloring temp)")
        print("[7] Risky bone feature (fictional)")
        print("[8] Sleep (end day)")
        print("[9] Agartha Gate check]")
        print("[B] Browse shop / buy")
        print("[I] Inventory / use")
        print("[S] Save & Quit")
        choice = input("> ").strip().lower()

        if choice=="1":
            p.streaks.skincareDays += 1
            print("You did skincare. (+streak)")
        elif choice=="2":
            p.flags.ateJunkToday = True
            p.streaks.noJunkDays = 0
            print("You ate junk today (skin may decay at night).")
        elif choice=="3":
            p.streaks.workoutsThisWeek += 1
            print("You worked out.")
        elif choice=="4":
            rating, comments = forum_rate(p, b"demo-image", fraud=False)
            print(f"Forum rating: {rating} | Comments: {', '.join(comments)}")
        elif choice=="5":
            rating, comments = forum_rate(p, b"demo-image-fraud", fraud=True)
            print(f"Forum rating: {rating} | Comments: {', '.join(comments)}")
        elif choice=="6":
            ACTIVE_EFFECTS.append(Effect(stat="coloring", delta=2, durationDays=1))
            print("Contacts used: +2 Coloring (until tomorrow).")
        elif choice=="7":
            print("Warning: This is a risky in-game action with negative side effects. Proceed? (y/N)")
            if input("> ").strip().lower().startswith("y"):
                print(use_risky_bone_option(p))
        elif choice=="8":
            end_day_apply(p, w, ACTIVE_EFFECTS)
            ending = evaluate_endings(p)
            if ending:
                print(f"\n=== Ending reached: {ending} ===")
                print("Returning to main menu.")
                break
        elif choice=="9":
            print("Agartha Gate:", "OPEN" if can_enter_agartha(p) else "Locked")
        elif choice=="b":
            shop_menu(p)
        elif choice=="i":
            inventory_menu(p)
        elif choice=="s":
            write_save(p, w, "save.json")
            print("Saved to save.json. Bye!")
            break
        else:
            print("Unknown choice.")

if __name__ == "__main__":
    main()
