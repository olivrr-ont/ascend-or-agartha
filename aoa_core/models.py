from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import hashlib, time

from .rng import wchoice

# Weighted feature tables
EYE_W = [("Blue",5),("Brown",40),("Hazel",20),("Green",15),("Black",20)]
HAIR_W = [("Blonde",5),("Brown",50),("Black",35),("Ginger",10)]
ETH_W  = [("Agarthan",5),("Midlander",40),("Sundweller",25),("Highlander",10),("Eastborne",20)]

@dataclass
class Flags:
    contactsActive: bool=False
    hairDyed: bool=False
    eyeSurgery: bool=False
    eyeSurgeryFailed: bool=False
    ateJunkToday: bool=False
    riskyCooldown: int=0
    selfDestructArmed: bool=False
    rawMilkBuffDays: int=0

@dataclass
class Streaks:
    skincareDays: int=0
    noJunkDays: int=0
    tanLevel: int=0
    workoutsThisWeek: int=0
    weeksConsistent: int=0

@dataclass
class PSL:
    true: float=0.0
    displayed: Optional[int]=None
    lastForumImageHash: Optional[str]=None

@dataclass
class Stats:
    genes: int
    skinQuality: int
    bloat: int
    boneMass: int
    coloring: int

@dataclass
class Player:
    id: str
    features: Dict[str,str]
    stats: Stats
    physiqueTier: int=1
    wallet: int=50
    psl: PSL=field(default_factory=PSL)
    flags: Flags=field(default_factory=Flags)
    streaks: Streaks=field(default_factory=Streaks)
    inventory: Dict[str,int]=field(default_factory=dict)
    relationships: Dict[str,float]=field(default_factory=dict)

@dataclass
class Shop:
    id: str
    name: str
    inventory: List[str]
    hours: Dict[str,int]

@dataclass
class Job:
    id: str
    name: str
    pslMin: int
    wage: int

@dataclass
class World:
    day: int=1
    hour: int=8
    shops: Dict[str,Shop]=field(default_factory=dict)
    jobs: Dict[str,Job]=field(default_factory=dict)
    dialogue: Dict[str,List[str]]=field(default_factory=dict)

def mk_player() -> Player:
    eye = wchoice(EYE_W)
    hair = wchoice(HAIR_W)
    eth  = wchoice(ETH_W)
    import random
    stats = Stats(
        genes=random.randint(1,30),
        skinQuality=random.randint(1,20),
        bloat=random.randint(5,10),
        boneMass=random.randint(1,15),
        coloring=0,
    )
    pid = hashlib.md5(f"{time.time()}".encode()).hexdigest()[:12]
    return Player(
        id=pid,
        features={"eye":eye,"hair":hair,"ethnicity":eth},
        stats=stats
    )
