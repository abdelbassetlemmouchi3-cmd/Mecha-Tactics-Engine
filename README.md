# 🤖 Mecha Tactics: Earth Light (Open Source Tactical Engine)

Welcome to **Mecha Tactics**, a deeply strategic, turn-based tactical RPG engine built entirely in Python and Pygame. Command custom mechs like *Zain Vanguard* and *Naya Artillery* on a procedural hex-grid battlefield.

This project is designed not just as a game, but as an **expandable Tactical Game Engine**. Developers and creators are encouraged to fork, modify, and add their own mechs, abilities, and campaigns!

## ✨ Key Features
* **Smart Tactical AI:** The enemy doesn't just attack the closest unit. The AI uses a dynamic scoring system to seek defensive terrain (Nebulas), prioritize low-HP targets, and relentlessly hunt your Command Base.
* **Professional Map Editor (`map_editor.py`):** Includes a built-in GUI map editor. Paint terrains, place units, dynamically resize the map grid, and export straight to JSON. The main game will auto-detect and load your custom levels!
* **Phased Animation System:** No sudden teleportation. Units glide across the hex grid calculating the shortest path, and combat triggers cinematic split-screen attacks.
* **Strategic Win/Loss Conditions:** Defend your Command Base at all costs while pushing to obliterate the Enemy Base.

## 🛠️ Installation & Setup
1. Ensure you have Python 3.x installed.
2. Clone this repository to your local machine.
3. Install the required dependencies:
   ```bash
   pip install pygame
4.Run the main game: python main.py
🤝 How to Contribute (Expand the Game!)
To design your own levels:

Run python map_editor.py.

Use the UI Buttons to dynamically expand or shrink the map grid.

Click the bottom Asset Palette to select terrains (Asteroids, Craters) or Units.

Left-Click to place, Right-Click to erase.

Press [S], type your map name (e.g., boss_level), and hit Enter. The game will now read this JSON file in the Main Menu automatically!

🤝 How to Contribute (Expand the Game!)
This engine is built for modularity! Here is how you can add your own content:

Add New Mechs: Open mecha.py and add a new Mecha() object inside load_level_units(). Define its HP, Attack, Defense, Weakness, and sprite name. The Map Editor will instantly display it!

Add New Terrains: Open hex_map.py and add a new entry to TERRAIN_TYPES. The engine automatically handles hex-masking and pathfinding cost.

Custom Artwork: Replace the placeholder PNGs in assets/units/ and assets/terrain/ with your own pixel art.

📜 Credits
Core Engine & Architecture: Dudu (Lead Developer)

AI & Pathfinding Systems: Dudu & AI Assistant

Built with ❤️ using Pygame.

If you build a cool campaign or design an epic Mecha using this engine, please share it! The Void awaits, Commander.
