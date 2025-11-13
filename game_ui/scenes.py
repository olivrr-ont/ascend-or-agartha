from __future__ import annotations
import os
import json
from typing import Callable

import pygame as pg

from game_ui.maps import MapDef, get_maps, Hotspot
from game_ui.sprites import (
    PlayerSprite,
    try_load,
    multiply_tint,
    eye_rgb,
    hair_rgb,
    TARGET_FACE_H,
    TARGET_FACE_W,
    TARGET_FRAME_H,
    TARGET_FRAME_W,
)

# -------------------------------------------------
# Helpers
# -------------------------------------------------
def _font(size=22) -> pg.font.Font:
    return pg.font.SysFont("consolas", size)

def _blit_text(surf: pg.Surface, text: str, pos: tuple[int,int], size=22, color=(230,230,230)):
    surf.blit(_font(size).render(text, True, color), pos)

def _centered_text(surf: pg.Surface, text: str, center: tuple[int,int], size=16, color=(220,220,220)):
    img = _font(size).render(text, True, color)
    rect = img.get_rect(center=center)
    surf.blit(img, rect.topleft)

def _draw_dialog_box(surf: pg.Surface, text: str):
    w, h = surf.get_size()
    box = pg.Rect(40, h-160, w-80, 120)
    pg.draw.rect(surf, (30,30,34), box, border_radius=8)
    pg.draw.rect(surf, (90,90,100), box, width=2, border_radius=8)
    _blit_text(surf, text, (box.x+16, box.y+16), size=24)

def _prices():
    from aoa_core.economy import PriceBook
    return PriceBook().prices

# -------------------------------------------------
# Scene base & manager
# -------------------------------------------------
class Scene:
    def on_push(self): ...
    def on_pop(self): ...
    def handle_event(self, e) -> bool: return False
    def update(self, dt: float): ...
    def draw(self, surf: pg.Surface): ...
    def on_escape(self) -> bool: return False

class SceneManager:
    def __init__(self):
        self.stack: list[Scene] = []

    def set(self, scene: Scene):
        self.stack = [scene]
        scene.on_push()

    def push(self, scene: Scene):
        self.stack.append(scene)
        scene.on_push()

    def pop(self):
        if self.stack:
            self.stack[-1].on_pop()
            self.stack.pop()

    def current(self): return self.stack[-1] if self.stack else None

    def handle_escape(self):
        cur = self.current()
        if cur and cur.on_escape():
            return True
        if len(self.stack) > 1:
            self.pop()
            return True
        return False

    def handle_event(self, e) -> bool:
        cur = self.current()
        return cur.handle_event(e) if cur else False

    def update(self, dt: float):
        if self.stack:
            self.stack[-1].update(dt)

    def draw(self, surf: pg.Surface):
        if self.stack:
            self.stack[-1].draw(surf)

# -------------------------------------------------
# World (maps, movement, interaction). Rendering via subclass.
# -------------------------------------------------
class WorldScene(Scene):
    """
    Open-world logic scene:
      - grid movement & collision
      - doors / hotspots
      - edge-trigger interaction on KEYUP E
    """
    def __init__(
        self,
        player_ref,
        world_ref,
        on_sleep: Callable[[], None],
        on_open_face: Callable[[str], None],
        on_open_shop: Callable[[str], None],
        on_start_cutscene: Callable[[str], None],
        tile=32,
        start_map="house",
        start_pos=(6,6),
    ):
        self.player_ref = player_ref
        self.world_ref = world_ref
        self.on_sleep = on_sleep
        self.on_open_face = on_open_face
        self.on_open_shop = on_open_shop
        self.on_start_cutscene = on_start_cutscene
        self.tile = tile
        self.speed = 140.0

        self.maps: dict[str, MapDef] = get_maps()
        self.map_id: str = start_map
        self.px, self.py = float(start_pos[0]), float(start_pos[1])

        # camera in world pixels (projection-specific meaning in renderer subclass)
        self.camx, self.camy = 0.0, 0.0

        # anim state
        self._moving = False
        self._last_dx, self._last_dy = 0.0, 0.0

        # player sprite (with cosmetics support)
        self.player_sprite = PlayerSprite(scale=1.0)

    def curmap(self) -> MapDef: return self.maps[self.map_id]
    def _blocked(self, tx: int, ty: int) -> bool: return (tx, ty) in self.curmap().walls

    def _try_move(self, dx: int, dy: int, dt: float):
        nx = self.px + dx * self.speed * dt / self.tile
        ny = self.py + dy * self.speed * dt / self.tile
        tx, ty = int(round(nx)), int(round(ny))
        W, H = self.curmap().size
        tx = max(1, min(W-2, tx))
        ty = max(1, min(H-2, ty))
        if not self._blocked(tx, ty):
            self.px, self.py = nx, ny

    def _nearest_hotspot(self, radius=0.8) -> tuple[str, Hotspot] | None:
        best = None; bestd = 999
        for name, hs in self.curmap().hotspots.items():
            x, y = hs.pos
            d = abs(self.px - x) + abs(self.py - y)
            if d <= radius*2 and d < bestd:
                best = (name, hs); bestd = d
        return best

    def _use_hotspot(self, hs: Hotspot):
        t = hs.type
        if t == "door":
            target = hs.data.get("target"); spawn = hs.data.get("spawn", (2,2))
            if target in self.maps:
                self.map_id = target
                self.px, self.py = float(spawn[0]), float(spawn[1])
        elif t == "bed":
            self.on_sleep()
        elif t == "mirror":
            self.on_open_face("normal")
        elif t == "laptop":
            self.on_open_face("selfie")
        elif t == "shop":
            sid = hs.data.get("shop_id")
            if sid: self.on_open_shop(sid)
        elif t == "gate":
            self.on_start_cutscene("game_ui/cutscenes/intro.json")

    # Edge-trigger: interact on KEYUP E
    def handle_event(self, e) -> bool:
        if e.type == pg.KEYUP and e.key == pg.K_e:
            near = self._nearest_hotspot(radius=0.8)
            if near:
                self._use_hotspot(near[1])
                return True
        return False

    def update(self, dt: float):
        keys = pg.key.get_pressed()
        dx = (keys[pg.K_d] or keys[pg.K_RIGHT]) - (keys[pg.K_a] or keys[pg.K_LEFT])
        dy = (keys[pg.K_s] or keys[pg.K_DOWN]) - (keys[pg.K_w] or keys[pg.K_UP])
        self._try_move(dx, dy, dt)

        self._moving = (dx != 0 or dy != 0)
        self._last_dx, self._last_dy = dx, dy
        self.player_sprite.update(dt, self._moving, dx, dy)

        # default (orthographic) camera; iso subclass overrides
        vw, vh = pg.display.get_surface().get_size()
        px_pix, py_pix = self.px * self.tile, self.py * self.tile
        W, H = self.curmap().size
        self.camx = max(0, min(px_pix - vw//2, W*self.tile - vw))
        self.camy = max(0, min(py_pix - vh//2, H*self.tile - vh))

    def draw(self, surf: pg.Surface):
        """
        Minimal orthographic renderer so WorldScene is never abstract at runtime.
        Your IsometricWorldScene still overrides this for 2.5D.
        """
        m = self.curmap()
        tile = self.tile

        # background
        surf.fill(m.floor_color)

        # regions
        for r in m.regions:
            rect = pg.Rect(r.x*tile - self.camx, r.y*tile - self.camy, r.w*tile, r.h*tile)
            pg.draw.rect(surf, r.color, rect)

        # walls
        for (x, y) in m.walls:
            pg.draw.rect(surf, (12,12,16), pg.Rect(x*tile - self.camx, y*tile - self.camy, tile, tile))

        # hotspots (colored tiles + labels + [E] hint)
        color_map = {"door":(180,190,220),"bed":(100,120,180),"mirror":(140,220,240),
                     "laptop":(200,200,80),"shop":(120,200,120),"gate":(220,200,140)}
        for _, hs in m.hotspots.items():
            x, y = hs.pos
            rect = pg.Rect(x*tile - self.camx, y*tile - self.camy, tile, tile)
            pg.draw.rect(surf, color_map.get(hs.type, (200,200,200)), rect)
            _centered_text(surf, hs.label, (rect.centerx, rect.top-10))
            if abs(self.px - x) <= 0.8 and abs(self.py - y) <= 0.8:
                hints = {"door":"[E] Enter","bed":"[E] Sleep","mirror":"[E] Face",
                         "laptop":"[E] Face","shop":"[E] Shop","gate":"[E] Approach"}
                _centered_text(surf, hints[hs.type], (rect.centerx, rect.bottom+12), color=(255,245,140))

        # player (uses your cosmetic sprite)
        px, py = int(self.px*tile - self.camx), int(self.py*tile - self.camy)
        # shadow
        pg.draw.ellipse(surf, (0,0,0,80), pg.Rect(px-14, py+10, 28, 10))
        # tints from player features
        p = self.player_ref()
        from game_ui.sprites import eye_rgb, hair_rgb  # local import to avoid cycles
        e_rgb = eye_rgb(p.features.get("eye","Brown"))
        h_rgb = hair_rgb(p.features.get("hair","Brown"))
        self.player_sprite.draw(surf, px, py, moving=self._moving, eye_color=e_rgb, hair_color=h_rgb)

# -------------------------------------------------
# Isometric renderer (2.5D)
# -------------------------------------------------
ISO_TILE_W, ISO_TILE_H = 64, 32  # diamond footprint

def iso_project(gx: float, gy: float, camx: float, camy: float) -> tuple[int,int]:
    sx = (gx - gy) * (ISO_TILE_W // 2) - camx
    sy = (gx + gy) * (ISO_TILE_H // 2) - camy
    return int(sx), int(sy)

class IsometricWorldScene(WorldScene):
    """Renders WorldScene in a 2.5D isometric style with depth sorting."""
    def update(self, dt: float):
        super().update(dt)
        # camera in iso pixels centered on player
        vw, vh = pg.display.get_surface().get_size()
        px_iso, py_iso = iso_project(self.px, self.py, 0, 0)
        W, H = self.curmap().size
        map_w_px = (W + H) * (ISO_TILE_W // 2)
        map_h_px = (W + H) * (ISO_TILE_H // 2)
        self.camx = max(0, min(px_iso - vw//2, map_w_px - vw))
        self.camy = max(0, min(py_iso - vh//2, map_h_px - vh))

    def draw(self, surf: pg.Surface):
        m = self.curmap()
        surf.fill((22,24,28))

        W, H = m.size
        # Floor diamonds (diagonal order for pleasing fill)
        for s in range(0, W+H):
            for gx in range(max(0, s-(H-1)), min(W-1, s)+1):
                gy = s - gx
                if gy < 0 or gy >= H: continue
                sx, sy = iso_project(gx, gy, self.camx, self.camy)
                hw, hh = ISO_TILE_W//2, ISO_TILE_H//2
                poly = [(sx, sy+hh), (sx+hw, sy), (sx, sy-hh), (sx-hw, sy)]
                pg.draw.polygon(surf, m.floor_color, poly)

        # Regions (colored slabs)
        for r in m.regions:
            for gx in range(r.x, r.x + r.w):
                for gy in range(r.y, r.y + r.h):
                    sx, sy = iso_project(gx, gy, self.camx, self.camy)
                    hw, hh = ISO_TILE_W//2, ISO_TILE_H//2
                    poly = [(sx, sy+hh), (sx+hw, sy), (sx, sy-hh), (sx-hw, sy)]
                    pg.draw.polygon(surf, r.color, poly)

        # Walls (simple extruded blocks)
        wall_top = (40,40,46)
        wall_r = (30,30,36)
        wall_l = (26,26,32)
        height_px = 24
        for (gx, gy) in m.walls:
            sx, sy = iso_project(gx, gy, self.camx, self.camy)
            hw, hh = ISO_TILE_W//2, ISO_TILE_H//2
            top = [(sx, sy+hh), (sx+hw, sy), (sx, sy-hh), (sx-hw, sy)]
            pg.draw.polygon(surf, wall_top, top)
            pg.draw.polygon(surf, wall_r, [(sx, sy+hh), (sx+hw, sy), (sx+hw, sy+height_px), (sx, sy+hh+height_px)])
            pg.draw.polygon(surf, wall_l, [(sx, sy+hh), (sx-hw, sy), (sx-hw, sy+height_px), (sx, sy+hh+height_px)])

        # Depth-sorted drawables: hotspots + player (keyed by gx+gy)
        color_map = {"door":(180,190,220),"bed":(100,120,180),"mirror":(140,220,240),
                     "laptop":(200,200,80),"shop":(120,200,120),"gate":(220,200,140)}
        drawables: list[tuple[float,int,int,object]] = []
        for _, hs in m.hotspots.items():
            sx, sy = iso_project(hs.pos[0], hs.pos[1], self.camx, self.camy)
            drawables.append((hs.pos[0] + hs.pos[1], sx, sy, hs))

        px_key = self.px + self.py
        px_iso, py_iso = iso_project(self.px, self.py, self.camx, self.camy)
        drawables.append((px_key, px_iso, py_iso, "PLAYER"))
        drawables.sort(key=lambda t: t[0])

        for _, sx, sy, obj in drawables:
            if obj == "PLAYER":
                # subtle shadow
                pg.draw.ellipse(surf, (0,0,0,80), pg.Rect(int(px_iso-14), int(py_iso+10), 28, 10))
                # cosmetics tints from player features
                p = self.player_ref()
                e_rgb = eye_rgb(p.features.get("eye","Brown"))
                h_rgb = hair_rgb(p.features.get("hair","Brown"))
                self.player_sprite.draw(
                    surf, int(px_iso), int(py_iso),
                    moving=self._moving,
                    eye_color=e_rgb, hair_color=h_rgb
                )
            else:
                hs: Hotspot = obj
                col = color_map.get(hs.type, (200,200,200))
                pg.draw.polygon(surf, col, [(sx, sy-10), (sx+6, sy), (sx, sy+10), (sx-6, sy)])
                _centered_text(surf, hs.label, (sx, sy-22))
                if abs(self.px - hs.pos[0]) <= 0.8 and abs(self.py - hs.pos[1]) <= 0.8:
                    hints = {"door":"[E] Enter","bed":"[E] Sleep","mirror":"[E] Face",
                             "laptop":"[E] Face","shop":"[E] Shop","gate":"[E] Approach"}
                    _centered_text(surf, hints[hs.type], (sx, sy+18), color=(255,245,140))

# -------------------------------------------------
# Face (front-view) scene with dynamic mirror portrait
# -------------------------------------------------
class FaceScene(Scene):
    """
    Front-facing portrait with dynamic ethnicity/bracket, tinted hair/eyes.
    Uses mask *alpha* to apply color (robust even if mask RGB is black).
    """
    TARGET_W, TARGET_H = 320, 240  # normalized portrait size

    def __init__(self, mode, player_ref, world_ref, on_snap, on_skincare):
        self.player_ref = player_ref
        self.world_ref = world_ref
        self.on_snap = on_snap
        self.on_skincare = on_skincare
        self.fraud = False
        self.msg = "Face Mode: SPACE=Selfie  F=Toggle Fraud  S=Skincare  ESC=Back"

        self._mirror_cache: dict[tuple[str,int], pg.Surface] = {}
        self._hair_mask: pg.Surface | None = None
        self._eyes_mask: pg.Surface | None = None
        self._load_masks()

    # ---------- internal helpers ----------
    def _load_masks(self):
        base = os.path.join(os.path.dirname(__file__), "assets", "mirror", "masks")
        self._hair_mask = try_load(os.path.join(base, "hair_mask.png"))
        self._eyes_mask = try_load(os.path.join(base, "eyes_mask.png"))
        for attr in ("_hair_mask", "_eyes_mask"):
            surf = getattr(self, attr)
            if surf is None: continue
            if surf.get_size() != (self.TARGET_W, self.TARGET_H):
                print(f"[MIRROR] Rescale {attr} {surf.get_size()} -> {(self.TARGET_W, self.TARGET_H)}")
                setattr(self, attr, pg.transform.scale(surf, (self.TARGET_W, self.TARGET_H)))

    def _psl_bracket(self, p) -> int:
        shown = p.psl.displayed if p.psl.displayed is not None else round(p.psl.true)
        return max(2, min(9, int(shown)))

    def _load_mirror_base(self, eth: str, bracket: int) -> pg.Surface:
        key = (eth, bracket)
        if key in self._mirror_cache:
            return self._mirror_cache[key]
        base_dir = os.path.join(os.path.dirname(__file__), "assets", "mirror")
        search = [
            os.path.join(base_dir, eth, f"{bracket}.png"),
            os.path.join(base_dir, eth, "default.png"),
            os.path.join(base_dir, f"{bracket}.png"),
            os.path.join(base_dir, "default.png"),
        ]
        surf = None
        for pth in search:
            if os.path.exists(pth):
                try:
                    surf = pg.image.load(pth).convert_alpha()
                    print(f"[MIRROR] Loaded portrait: {pth} ({surf.get_width()}x{surf.get_height()})")
                    break
                except Exception as e:
                    print(f"[MIRROR] Failed {pth}: {e}")
        if surf is None:
            print("[MIRROR] No portrait found -> using placeholder.")
            surf = pg.Surface((self.TARGET_W, self.TARGET_H), pg.SRCALPHA)
            surf.fill((40, 42, 48, 255))
            pg.draw.rect(surf, (70, 72, 78), pg.Rect(20, 20, self.TARGET_W-40, self.TARGET_H-40), border_radius=8)
        if surf.get_size() != (self.TARGET_W, self.TARGET_H):
            print(f"[MIRROR] Rescale base {surf.get_size()} -> {(self.TARGET_W, self.TARGET_H)}")
            surf = pg.transform.scale(surf, (self.TARGET_W, self.TARGET_H))
        self._mirror_cache[key] = surf
        return surf

    def _tint_layer_from_mask(self, mask: pg.Surface, color: tuple[int,int,int]) -> pg.Surface:
        """
        Create a solid color layer whose per-pixel ALPHA comes from mask's ALPHA.
        This avoids blacking out the base even if the mask RGB is black.
        """
        w, h = mask.get_size()
        # Make a solid color surface
        layer = pg.Surface((w, h), pg.SRCALPHA)
        layer.fill((*color, 255))
        # Extract mask alpha as a surface and use it to modulate layer alpha
        # Approach: multiply 'layer' by mask's alpha using special blend trick:
        #   - Create an alpha-only surface 'a' from mask by copying to RGB then using MULT
        alpha_src = mask.copy()  # uses mask's alpha channel
        # Zero RGB so RGB MULT won't change color; but keep alpha
        alpha_src.fill((255, 255, 255, 0))  # set RGB to 255, keep alpha unchanged by next blit
        # We need the layer's alpha = layer.alpha * mask.alpha / 255
        # Pygame doesn't expose direct alpha writes per pixel without surfarray.
        # Practical trick: use mask as a stencil by blitting the mask onto a blank surface,
        # then use it to 'erase' transparent parts from the color layer.
        stencil = pg.Surface((w, h), pg.SRCALPHA)
        stencil.blit(mask, (0, 0))  # we only care about its alpha

        # Clear layer where mask alpha == 0 via blending: use mask as a "keep" via SRCALPHA
        # Composite: layer = layer * (mask_alpha)  (approx via per-pixel alpha modulation)
        # Workaround: per-pixel alpha via pixel array if available
        try:
            import numpy as np
            arr_layer = pg.surfarray.pixels_alpha(layer)
            arr_mask = pg.surfarray.pixels_alpha(stencil)
            # multiply layer alpha by mask alpha (0..255)
            arr_layer[:] = (arr_layer.astype(np.uint16) * arr_mask.astype(np.uint16) // 255).astype(np.uint8)
            del arr_layer, arr_mask  # unlock surfaces
        except Exception:
            # Fallback: if surfarray unavailable, approximate by erasing where mask is fully transparent
            layer.blit(stencil, (0, 0), special_flags=pg.BLEND_RGBA_MULT)

        return layer

    # ---------- input ----------
    def handle_event(self, e) -> bool:
        if e.type == pg.KEYUP:
            if e.key == pg.K_SPACE:
                self.on_snap(self.fraud); return True
            if e.key == pg.K_f:
                self.fraud = not self.fraud; return True
            if e.key == pg.K_s:
                self.on_skincare(); return True
        return False

    # ---------- draw ----------
    def draw(self, surf: pg.Surface):
        from game_ui.sprites import eye_rgb, hair_rgb
        w, h = surf.get_size()
        surf.fill((8,8,10))

        p = self.player_ref()
        eth = p.features.get("ethnicity", "Midlander")
        bracket = self._psl_bracket(p)

        base = self._load_mirror_base(eth, bracket).copy()

        # Build tint layers from mask alpha
        if self._hair_mask:
            hair_col = hair_rgb(p.features.get("hair", "Brown"))
            hair_layer = self._tint_layer_from_mask(self._hair_mask, hair_col)
            base.blit(hair_layer, (0, 0))  # normal alpha blend

        if self._eyes_mask:
            eye_col = eye_rgb(p.features.get("eye", "Brown"))
            eyes_layer = self._tint_layer_from_mask(self._eyes_mask, eye_col)
            base.blit(eyes_layer, (0, 0))  # normal alpha blend

        # Fraud overlay (subtle warm lift)
        if self.fraud:
            fraud_overlay = pg.Surface(base.get_size(), pg.SRCALPHA)
            fraud_overlay.fill((255, 220, 160, 30))
            base.blit(fraud_overlay, (0,0), special_flags=pg.BLEND_RGBA_ADD)

        rect = base.get_rect(center=(w//2, h//2))
        surf.blit(base, rect.topleft)

        _blit_text(surf, self.msg, (20, h-30), color=(210,210,210))
        _blit_text(surf, f"Fraud: {'ON' if self.fraud else 'OFF'} | Eth: {eth} | PSL≈{bracket}", (20, 20))

# -------------------------------------------------
# Shop list scene (edge-triggered)
# -------------------------------------------------
class ShopScene(Scene):
    """
    Simple list UI:
      UP/DOWN on KEYDOWN to move
      ENTER on KEYUP to buy
    """
    def __init__(self, shop_id, player_ref, items_db, shop_def, on_buy):
        self.shop_id = shop_id
        self.player_ref = player_ref
        self.items = items_db
        self.shop = shop_def
        self.on_buy = on_buy
        self.sel = 0

    def handle_event(self, e) -> bool:
        if e.type == pg.KEYDOWN:
            if e.key == pg.K_DOWN:
                self.sel = (self.sel + 1) % len(self.shop["inventory"]); return True
            if e.key == pg.K_UP:
                self.sel = (self.sel - 1) % len(self.shop["inventory"]); return True
        if e.type == pg.KEYUP and e.key == pg.K_RETURN:
            iid = self.shop["inventory"][self.sel]
            self.on_buy(iid, self.shop)
            return True
        return False

    def draw(self, surf: pg.Surface):
        surf.fill((18,18,24))
        _blit_text(surf, self.shop["name"], (24, 20), size=28)
        _blit_text(surf, "UP/DOWN select, ENTER buy, ESC back", (24, 52), color=(200,200,200))
        y = 90
        for i, iid in enumerate(self.shop["inventory"]):
            name = self.items[iid]["name"]
            price = str(_prices().get(iid, "?"))
            marker = "▶ " if i==self.sel else "  "
            col = (255,255,255) if i==self.sel else (200,200,200)
            _blit_text(surf, f"{marker}{name}  ${price}", (48, y), color=col)
            y += 28

# -------------------------------------------------
# Cutscene player (say/wait/end)
# -------------------------------------------------
class CutsceneScene(Scene):
    """
    Minimal cutscene runner:
      lines: [{cmd:'say',text:'...'}, {cmd:'wait',time:0.8}, {cmd:'end'}]
    """
    def __init__(self, path, player_ref, world_ref, notifier=None):
        self.player_ref = player_ref
        self.world_ref = world_ref
        self.notifier = notifier
        with open(path, "r", encoding="utf-8") as f:
            self.script = json.load(f)
        self.idx = 0
        self.time_acc = 0.0
        self.current_text = ""

    def handle_event(self, e) -> bool:
        # ESC pops via SceneManager
        return False

    def update(self, dt: float):
        if self.idx >= len(self.script["lines"]): return
        cmd = self.script["lines"][self.idx]
        if cmd["cmd"] == "say":
            self.current_text = cmd["text"]
            self.idx += 1
        elif cmd["cmd"] == "wait":
            self.time_acc += dt
            if self.time_acc >= float(cmd.get("time", 0.5)):
                self.time_acc = 0.0
                self.idx += 1
        elif cmd["cmd"] == "end":
            if self.notifier: self.notifier.push("Cutscene finished.")
            self.idx = len(self.script["lines"])
        else:
            self.idx += 1
