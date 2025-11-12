# Ascend or Agartha

**A 2D/2.5D life-simulation RPG with dynamic appearance-based systems, open exploration, and branching endings.**

Ascend or Agartha is a top–down pixel-style life-sim RPG featuring a stat-driven social world, daily routine mechanics, cosmetic customization, a forum rating system, and multiple unlockable endings.
You spawn with randomized traits and try to climb the PSL ladder, explore the city, post selfies, build your character, and discover the secrets of Agartha.

This repository contains the full source code, assets, and tools required to run the game locally.

---

## ✨ Features

### **🎭 Dynamic Character Generator**

* Randomized traits: eye color, hair color, ethnicity
* Genetic stats: Genes, Skin Quality, Bone Mass, Bloat, Coloring
* Cosmetic overlays applied at runtime (hair color, eye color, etc.)

### **📸 Forum & Selfie System**

* Take selfies using the front-view portrait mode
* Fraud mode for boosted ratings
* Dynamic PSL estimation with comment banks
* Mirror portraits that adapt to ethnicity and appearance

### **🏙️ Open-World Exploration**

* Player’s house, streets, shops, city center, gym
* Interactable hotspots (doors, beds, mirrors, shops, laptops)
* Smooth 2.5D-style movement with pixel-art bobbing animations

### **🛒 Economy & Stores**

* Buy skincare, food, supplements, cosmetics, and tools
* Each item influences stats, effects, and routines
* Daily stat resolution at bedtime

### **💻 Jobs & Progression**

* Jobs unlock with higher PSL
* Physique training with multi-week progression
* Build relationships with NPCs (WIP)

### **🔮 Endings**

* Marriage route
* Agartha gate ending
* Secret “True Adam” route
* Game-over path with safety messaging

---

## 🖼️ Technical Overview

* **Engine:** Python + pygame
* **UI:** In-game menus, panels, shops, inventory
* **Maps:** Custom JSON-based tile maps with collision and hotspots
* **Scenes:** World scene, face/mirror scene, shop scene, cutscenes
* **Rendering:** 2D/2.5D hybrid (isometric-inspired depth sorting)
* **Sprites:** Moddable, including player parts, portrait masks, and item icons

---

## 📦 Installation

### **Prerequisites**

* Python **3.10+**
* Pygame (`pip install pygame`)

### **Run the game**

From the project root:

```bash
python -m game_ui.main
```

The game will launch in a window and load the starter house map.

---

## 🛠️ Development

### **Modding**

All game code and assets may be modified and redistributed under the selected license.
Credit to the original creator is required in all public redistributions.

### **Contributing**

Pull requests that improve performance, add content, or extend systems are welcome.
For large features, please open an issue first.

### **Planned additions**

* NPC schedules and relationships
* Animated cutscenes
* Expanded city districts
* Additional portraits and trait variations
* Save system refinements
