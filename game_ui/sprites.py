from __future__ import annotations
import os, math
from typing import Dict, List, Tuple, Optional
import pygame as pg

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")

# Target sizes (you can tweak)
TARGET_FRAME_W, TARGET_FRAME_H = 32, 48     # player frame size
TARGET_FACE_W,  TARGET_FACE_H  = 320, 240   # mirror portrait size

# ----------------- Color maps -----------------
EYE_RGB = {
    "Blue":   (70, 140, 255),
    "Green":  (90, 170, 110),
    "Hazel":  (155, 120, 60),
    "Brown":  (95, 60, 35),
    "Black":  (30, 30, 30),
}
HAIR_RGB = {
    "Blonde": (235, 215, 120),
    "Brown":  (120, 80, 45),
    "Black":  (30, 30, 30),
    "Ginger": (200, 70, 45),
}
def eye_rgb(eye: str) -> Tuple[int,int,int]:  return EYE_RGB.get(eye, (200,200,200))
def hair_rgb(hair: str) -> Tuple[int,int,int]: return HAIR_RGB.get(hair, (200,200,200))

# ----------------- Helpers -----------------
def _load(path: str) -> Optional[pg.Surface]:
    if not os.path.exists(path): return None
    try:
        img = pg.image.load(path).convert_alpha()
        return img
    except Exception as e:
        print(f"[SPRITES] Failed to load {path}: {e}")
        return None

def try_load(path: str) -> Optional[pg.Surface]:
    return _load(path)

def multiply_tint(surface: pg.Surface, rgb: Tuple[int,int,int]) -> pg.Surface:
    s = surface.copy()
    tint = pg.Surface(s.get_size(), pg.SRCALPHA)
    tint.fill((*rgb, 255))
    s.blit(tint, (0,0), special_flags=pg.BLEND_RGBA_MULT)
    return s

def _rescaled(s: pg.Surface, w: int, h: int) -> pg.Surface:
    if s.get_width() == w and s.get_height() == h: return s
    return pg.transform.scale(s, (w, h))

def _auto_frame_scale(s: pg.Surface) -> pg.Surface:
    """Rescale any weird frame to TARGET_FRAME_* with console log."""
    if s.get_width() != TARGET_FRAME_W or s.get_height() != TARGET_FRAME_H:
        print(f"[SPRITES] Auto-rescale frame {s.get_width()}x{s.get_height()} -> {TARGET_FRAME_W}x{TARGET_FRAME_H}")
        s = _rescaled(s, TARGET_FRAME_W, TARGET_FRAME_H)
    return s

# ----------------- Player sprite -----------------
class PlayerSprite:
    """
    Loads:
      assets/player/idle_{dir}_0.png
      assets/player/walk_{dir}_{i}.png
    Optional overlays:
      assets/player/overlays/hair.png or hair_{key}_{i}.png
      assets/player/overlays/eyes.png or eyes_{key}_{i}.png
    Auto-rescales everything to 32x48 by default.
    """
    def __init__(self, scale: float = 1.0):
        self.scale = scale
        self.frames: Dict[str, List[pg.Surface]] = {k: [] for k in [
            "idle_down","idle_left","idle_right","idle_up",
            "walk_down","walk_left","walk_right","walk_up"
        ]}
        self.over_hair: Dict[str, List[pg.Surface]] = {k: [] for k in self.frames}
        self.over_eyes: Dict[str, List[pg.Surface]] = {k: [] for k in self.frames}
        self.over_hair_single: Optional[pg.Surface] = None
        self.over_eyes_single: Optional[pg.Surface] = None

        self.anim_time = 0.0
        self.anim_speed = 8.0
        self.bob_amp = 2
        self.bob_speed = 8.0
        self.last_dir = "down"

        self._load_frames()
        self._load_overlays()
        self.fallback = self._make_fallback()

    # ---------- load ----------
    def _load_series(self, base_dir: str, key: str) -> List[pg.Surface]:
        i = 0; out = []
        while True:
            p = os.path.join(base_dir, f"{key}_{i}.png")
            s = _load(p)
            if s is None: break
            s = _auto_frame_scale(s)
            out.append(s)
            i += 1
        if out:
            print(f"[SPRITES] Loaded {key}: {len(out)} frames, {out[0].get_width()}x{out[0].get_height()}")
        return out

    def _load_frames(self):
        base = os.path.join(ASSETS_DIR, "player")
        if not os.path.isdir(base):
            print("[SPRITES] assets/player not found; using fallback box.")
            return
        for key in list(self.frames.keys()):
            arr = self._load_series(base, key)
            if arr: self.frames[key] = arr
        self._ensure_dirs(self.frames)

        # If absolutely nothing loaded, tell the user
        if not any(self.frames.values()):
            print("[SPRITES] No player frames found. Expected at least walk_down_0.png, walk_down_1.png.")

    def _load_overlays(self):
        base = os.path.join(ASSETS_DIR, "player", "overlays")
        if not os.path.isdir(base):
            print("[SPRITES] overlays folder missing (ok).")
            return
        # Per-key series
        for key in list(self.over_hair.keys()):
            self.over_hair[key] = self._load_series(base, f"hair_{key}")
            self.over_eyes[key] = self._load_series(base, f"eyes_{key}")
        # Single overlays
        hair_single = _load(os.path.join(base, "hair.png"))
        eyes_single = _load(os.path.join(base, "eyes.png"))
        if hair_single:
            self.over_hair_single = _auto_frame_scale(hair_single)
            print(f"[SPRITES] Loaded overlays/hair.png {self.over_hair_single.get_width()}x{self.over_hair_single.get_height()}")
        if eyes_single:
            self.over_eyes_single = _auto_frame_scale(eyes_single)
            print(f"[SPRITES] Loaded overlays/eyes.png {self.over_eyes_single.get_width()}x{self.over_eyes_single.get_height()}")

        self._ensure_dirs(self.over_hair)
        self._ensure_dirs(self.over_eyes)

    def _ensure_dirs(self, bank: Dict[str, List[pg.Surface]]):
        def mirror(prefix: str):
            L=f"{prefix}_left"; R=f"{prefix}_right"; D=f"{prefix}_down"; U=f"{prefix}_up"
            if not bank[L] and bank[R]:
                bank[L] = [pg.transform.flip(s, True, False) for s in bank[R]]
                print(f"[SPRITES] Mirrored {prefix}_right -> {prefix}_left")
            if not bank[R] and bank[L]:
                bank[R] = [pg.transform.flip(s, True, False) for s in bank[L]]
                print(f"[SPRITES] Mirrored {prefix}_left -> {prefix}_right")
            if not bank[U] and bank[D]:
                bank[U] = bank[D]
                print(f"[SPRITES] Reused {prefix}_down for {prefix}_up")
        mirror("idle"); mirror("walk")

    # ---------- anim/draw ----------
    def _make_fallback(self) -> pg.Surface:
        surf = pg.Surface((TARGET_FRAME_W, TARGET_FRAME_H), pg.SRCALPHA)
        pg.draw.rect(surf, (240,240,240), pg.Rect(6, 8, TARGET_FRAME_W-12, TARGET_FRAME_H-10))
        pg.draw.rect(surf, (20,20,20), pg.Rect(TARGET_FRAME_W//2-6, 12, 4, 4))
        pg.draw.rect(surf, (20,20,20), pg.Rect(TARGET_FRAME_W//2+2, 12, 4, 4))
        return surf

    def _pick_dir(self, dx: float, dy: float) -> str:
        if abs(dx) > abs(dy): return "right" if dx > 0 else "left"
        else: return "down" if dy >= 0 else "up"

    def update(self, dt: float, moving: bool, dx: float, dy: float):
        self.anim_time += dt if moving else -dt*2
        if self.anim_time < 0: self.anim_time = 0
        if moving and (dx or dy): self.last_dir = self._pick_dir(dx, dy)

    def _frame_key_idx(self, moving: bool) -> tuple[str,int]:
        state = "walk" if moving else "idle"
        key = f"{state}_{self.last_dir}"
        arr = self.frames.get(key) or []
        if arr:
            idx = int(self.anim_time * self.anim_speed) % max(1, len(arr))
            return key, idx
        return "idle_down", 0

    def draw(self, surf: pg.Surface, screen_x: int, screen_y: int, moving: bool,
             eye_color: Tuple[int,int,int] | None = None,
             hair_color: Tuple[int,int,int] | None = None):
        key, idx = self._frame_key_idx(moving)
        arr = self.frames.get(key) or []
        frame = arr[idx] if arr else self.fallback

        # walking bob
        bob = int(self.bob_amp * math.sin(self.anim_time * self.bob_speed)) if moving else 0
        dst = frame.get_rect(midbottom=(int(screen_x), int(screen_y - bob)))
        surf.blit(frame, dst)

        # overlays
        hair_series = self.over_hair.get(key) or []
        eyes_series = self.over_eyes.get(key) or []
        hair_frame = hair_series[idx % len(hair_series)] if hair_series else self.over_hair_single
        eyes_frame = eyes_series[idx % len(eyes_series)] if eyes_series else self.over_eyes_single

        if hair_frame:
            layer = multiply_tint(hair_frame, hair_color or (255,255,255))
            surf.blit(layer, dst)
        if eyes_frame:
            layer = multiply_tint(eyes_frame, eye_color or (255,255,255))
            surf.blit(layer, dst)
