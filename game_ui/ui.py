from __future__ import annotations
import pygame as pg

class HUD:
    def __init__(self):
        self.font = pg.font.SysFont("consolas", 20)

    def draw(self, surf, player, world):
        info = [
            f"Day {world.day}  {world.hour:02d}:00",
            f"Wallet: ${player.wallet}",
            f"PSL: {player.psl.displayed if player.psl.displayed is not None else '?'}",
            f"Genes:{player.stats.genes} Skin:{player.stats.skinQuality} Bloat:{player.stats.bloat} Bone:{player.stats.boneMass} Color:{player.stats.coloring}",
            "(E) interact   (I) inventory   (ESC) back",
        ]
        x, y = 10, 8
        for line in info:
            surf.blit(self.font.render(line, True, (220,220,220)), (x,y))
            y += 22

class InventoryPanel:
    def __init__(self):
        self.open = False
        self.sel = 0
        self.cool = 0

    def toggle(self): self.open = not self.open

    def update_and_consume_action(self, player, items_db):
        if not self.open: return None
        keys = pg.key.get_pressed()
        inv_keys = list(player.inventory.keys())
        if not inv_keys:
            return None
        if keys[pg.K_DOWN]:
            self.sel = (self.sel + 1) % len(inv_keys); pg.time.wait(120)
        if keys[pg.K_UP]:
            self.sel = (self.sel - 1) % len(inv_keys); pg.time.wait(120)
        if keys[pg.K_RETURN]:
            iid = inv_keys[self.sel]
            pg.time.wait(120)
            return iid
        return None

    def draw(self, surf, player, items_db):
        w,h = surf.get_size()
        box = pg.Rect(w-360, 20, 340, h-40)
        pg.draw.rect(surf, (26,26,32), box, border_radius=8)
        pg.draw.rect(surf, (90,90,110), box, width=2, border_radius=8)

        font = pg.font.SysFont("consolas", 20)
        surf.blit(font.render("Inventory (ENTER=use, ESC=close)", True, (230,230,230)), (box.x+12, box.y+12))
        y = box.y + 44
        if not player.inventory:
            surf.blit(font.render("(empty)", True, (180,180,180)), (box.x+12, y))
            return
        inv_items = list(player.inventory.items())
        for i,(iid, qty) in enumerate(inv_items):
            name = items_db[iid]["name"]
            marker = "▶ " if i==self.sel else "  "
            col = (255,255,255) if i==self.sel else (200,200,200)
            surf.blit(font.render(f"{marker}{name}  x{qty}", True, col), (box.x+12, y))
            y += 26

class Notifier:
    def __init__(self):
        self.queue: list[tuple[str, float]] = []  # (text, time_remaining)
        self.font = pg.font.SysFont("consolas", 20)

    def push(self, text: str, duration: float=2.2):
        self.queue.append((text, duration))

    def draw(self, surf):
        if not self.queue: return
        # update times
        dt = 1/60.0  # approximate per draw
        self.queue = [(t, tm-dt) for (t,tm) in self.queue if tm-dt > 0]
        # draw last few
        base_y = 80
        for idx,(t,_) in enumerate(self.queue[-3:]):
            y = base_y + idx*24
            surf.blit(self.font.render(t, True, (240,240,140)), (16, y))
