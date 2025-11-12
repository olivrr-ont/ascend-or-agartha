from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Tuple, List, Literal, Callable

Tile = Tuple[int, int]

@dataclass
class Region:
    x: int
    y: int
    w: int
    h: int
    color: Tuple[int,int,int]

@dataclass
class Hotspot:
    pos: Tile
    type: Literal["door","bed","mirror","laptop","shop","gate"]
    label: str
    data: dict = field(default_factory=dict)  # e.g. {"target":"city_center","spawn":(35,18)} for doors

@dataclass
class MapDef:
    id: str
    size: Tuple[int,int]               # (tiles_w, tiles_h)
    floor_color: Tuple[int,int,int]
    walls: set[Tile] = field(default_factory=set)
    regions: List[Region] = field(default_factory=list)  # colored rectangles (streets, buildings)
    hotspots: Dict[str, Hotspot] = field(default_factory=dict)

def border_walls(w: int, h: int) -> set[Tile]:
    s: set[Tile] = set()
    for x in range(w):
        s.add((x,0)); s.add((x,h-1))
    for y in range(h):
        s.add((0,y)); s.add((w-1,y))
    return s

def rect_walls(x: int, y: int, w: int, h: int) -> set[Tile]:
    s: set[Tile] = set()
    for xx in range(x, x+w):
        s.add((xx, y)); s.add((xx, y+h-1))
    for yy in range(y, y+h):
        s.add((x, yy)); s.add((x+w-1, yy))
    return s

def house_map() -> MapDef:
    W,H = 24, 16
    m = MapDef(
        id="house",
        size=(W,H),
        floor_color=(36,38,44),
    )
    m.walls |= border_walls(W,H)
    # simple room rectangle (inner walls as obstacles)
    m.walls |= rect_walls(3,3,18,10)
    # door tile in the inner wall (gap)
    m.walls.discard((12,3))
    # regions (rugs/furniture blobs)
    m.regions.append(Region(4,4,6,4,(48,50,70)))   # rug
    m.regions.append(Region(16,4,4,3,(60,40,40)))  # bed top
    # hotspots
    m.hotspots["bed"]   = Hotspot((17,5), "bed",   "Bed")
    m.hotspots["mirror"]= Hotspot((7,5),  "mirror","Mirror")
    m.hotspots["door_out"] = Hotspot((12,2), "door", "Door",
                                     data={"target":"streets","spawn":(12,10)})
    m.hotspots["laptop"]= Hotspot((10,6), "laptop","Laptop")
    return m

def streets_map() -> MapDef:
    W,H = 48, 32
    m = MapDef(
        id="streets",
        size=(W,H),
        floor_color=(28,30,34),
    )
    m.walls |= border_walls(W,H)

    # Big asphalt street bands (regions)
    m.regions.append(Region(0,12,W,6,(40,40,46)))     # horizontal avenue
    m.regions.append(Region(18,0,6,H,(40,40,46)))     # vertical avenue

    # Sidewalk/buildings (colored rectangles)
    m.regions.append(Region(2,4,12,6,(56,56,64)))     # block
    m.regions.append(Region(26,4,18,6,(56,56,64)))
    m.regions.append(Region(3,22,12,6,(56,56,64)))
    m.regions.append(Region(28,22,15,6,(56,56,64)))

    # City center door
    m.hotspots["to_center"] = Hotspot((30,15), "door", "To City Center",
                                      data={"target":"city_center","spawn":(10,18)})

    # Back to house door (position where you appear from house door)
    m.hotspots["to_house"] = Hotspot((12,11), "door", "To House",
                                     data={"target":"house","spawn":(12,4)})

    # Optional gate teaser somewhere on the map
    m.hotspots["gate_teaser"] = Hotspot((44,6), "gate", "Agartha Gate")

    return m

def city_center_map() -> MapDef:
    W,H = 64, 36
    m = MapDef(
        id="city_center",
        size=(W,H),
        floor_color=(30,32,36),
    )
    m.walls |= border_walls(W,H)
    # Plaza
    m.regions.append(Region(6,10,52,16,(38,40,46)))  # stone plaza
    # Buildings around plaza
    m.regions.append(Region(8,6,16,4,(66,60,64)))    # north shop block
    m.regions.append(Region(28,6,16,4,(66,60,64)))
    m.regions.append(Region(48,6,10,4,(66,60,64)))
    m.regions.append(Region(8,26,16,6,(66,60,64)))   # south block
    m.regions.append(Region(30,26,16,6,(66,60,64)))
    m.regions.append(Region(50,26,8,6,(66,60,64)))

    # Shops hotspots (on plaza edge)
    m.hotspots["shop_grocer"]   = Hotspot((12,12), "shop", "Grocer",   data={"shop_id":"grocer01"})
    m.hotspots["shop_pharmacy"] = Hotspot((20,12), "shop", "Pharmacy", data={"shop_id":"pharmacy01"})

    # Door back to streets
    m.hotspots["to_streets"] = Hotspot((10,19), "door", "To Streets",
                                       data={"target":"streets","spawn":(30,14)})

    # Mirror & laptop kiosks (for quick face mode without going home)
    m.hotspots["mirror_kiosk"] = Hotspot((32,18), "mirror", "Mirror Kiosk")
    m.hotspots["selfie_booth"] = Hotspot((34,18), "laptop", "Selfie Booth")

    return m

def get_maps() -> dict[str, MapDef]:
    return {
        "house": house_map(),
        "streets": streets_map(),
        "city_center": city_center_map(),
    }
