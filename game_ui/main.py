import os, sys, time
import pygame as pg

from aoa_core.sim import new_game, end_day_apply, evaluate_endings, refresh_psl, can_enter_agartha
from aoa_core.effects import Effect
from aoa_core.items import load_items, load_shops, buy_item, use_item, remove_from_inventory
from aoa_core.forum import forum_rate
from game_ui.scenes import SceneManager, IsometricWorldScene, FaceScene, ShopScene, CutsceneScene


from game_ui.scenes import SceneManager, WorldScene, FaceScene, ShopScene, CutsceneScene
from game_ui.ui import HUD, InventoryPanel, Notifier

W, H = 1280, 720
FPS = 75
TILE = 32

def init_pygame():
    os.environ["SDL_VIDEO_CENTERED"] = "1"
    pg.init()
    pg.display.set_caption("Ascend or Agartha")
    screen = pg.display.set_mode((W, H))
    clock = pg.time.Clock()
    return screen, clock

def main():
    screen, clock = init_pygame()

    # ---- Game state (engine) ----
    if os.path.exists("save.json"):
        from aoa_core.save import read_save
        player, world = read_save("save.json")
    else:
        player, world = new_game(seed=int(time.time()))
    active_effects: list[Effect] = []

    # Data (shops/items)
    ITEMS_DB = load_items()
    SHOPS_DB = load_shops()

    # ---- UI helpers ----
    hud = HUD()
    inv_panel = InventoryPanel()
    notify = Notifier()

    # ---- Scene manager ----
    sm = SceneManager()
    world_scene = IsometricWorldScene(
        player_ref=lambda: player,
        world_ref=lambda: world,
        on_sleep=lambda: on_sleep(player, world, active_effects, notify),
        on_open_face=lambda mode: sm.push(FaceScene(mode=mode, player_ref=lambda: player, world_ref=lambda: world,
                                                    on_snap=lambda fraud: do_forum_snap(player, fraud, notify),
                                                on_skincare=lambda: do_skincare(player, notify))),
        on_open_shop=lambda shop_id: sm.push(ShopScene(shop_id=shop_id, player_ref=lambda: player,
                                                   items_db=ITEMS_DB, shop_def=SHOPS_DB.get(shop_id),
                                                   on_buy=lambda iid, shop_def: do_buy(player, iid, shop_def, ITEMS_DB, notify))),
        on_start_cutscene=lambda path: sm.push(CutsceneScene(path, player_ref=lambda:player, world_ref=lambda:world, notifier=notify)),
        tile=TILE,
        start_map="house",
        start_pos=(6,6),
    )
    sm.set(world_scene)


    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        for e in pg.event.get():
            if e.type == pg.QUIT:
                running = False
                continue
            consumed = sm.handle_event(e)
            if not consumed and e.type == pg.KEYDOWN:
                if e.key == pg.K_ESCAPE:
                    if not sm.handle_escape(): running = False
                elif e.key == pg.K_i:
                    inv_panel.toggle()
                elif e.key == pg.K_F5:
                    save(player, world); notify.push("Saved.")
        # Inventory (edge-trigger inside panel)
        if inv_panel.open:
            inv_action = inv_panel.update_and_consume_action(player, ITEMS_DB)
            if inv_action:
                iid = inv_action
                if player.inventory.get(iid,0)>0:
                    ok, msg = use_item(player, iid, ITEMS_DB, active_effects)
                    if ok: remove_from_inventory(player, iid, 1)
                    notify.push(msg)
                else:
                    notify.push("You don't have that item.")

        sm.update(dt)
        refresh_psl(player)

        screen.fill((20,20,24))
        sm.draw(screen)
        hud.draw(screen, player, world)
        if inv_panel.open: inv_panel.draw(screen, player, ITEMS_DB)
        notify.draw(screen)
        pg.display.flip()

    save(player, world)
    pg.quit(); sys.exit(0)

def save(player, world):
    from aoa_core.save import write_save
    write_save(player, world, "save.json")

def on_sleep(player, world, active_effects, notify):
    end_day_apply(player, world, active_effects)
    ending = evaluate_endings(player)
    if ending:
        notify.push(f"Ending reached: {ending}")
    elif can_enter_agartha(player):
        notify.push("Agartha Gate is now OPEN for you.")
    else:
        notify.push(f"New day: {world.day}, 08:00")

def do_forum_snap(player, fraud, notify):
    img_bytes = f"face-{time.time_ns()}-{fraud}".encode()
    rating, comments = forum_rate(player, img_bytes, fraud=fraud)
    notify.push(f"Forum rating: {rating} / 9")
    notify.push("Comments: " + " | ".join(comments))

def do_skincare(player, notify):
    player.streaks.skincareDays += 1
    notify.push("Skincare done (+streak).")

def do_buy(player, item_id, shop_def, items_db, notify):
    from aoa_core.economy import PriceBook
    ok, msg = buy_item(player, shop_def, item_id, PriceBook(), items_db)
    notify.push(msg)

if __name__ == "__main__":
    main()
