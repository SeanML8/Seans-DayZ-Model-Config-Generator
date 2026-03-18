# DayZ Model Config Generator

A GUI tool for creating `config.cpp` and `types.xml` entries for custom DayZ mods. Supports both model-swapped retextures and entirely new item definitions.

![Python](https://img.shields.io/badge/Python-3.10+-blue) ![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey) ![Version](https://img.shields.io/github/v/release/SeanML8/DayZ-Model-Config-Generator)

## Features

- **Two item modes**: Model Swap (retexture with a custom .p3d) or New Item (define everything from scratch)
- **Live preview**: See your config.cpp and types.xml output update in real-time as you edit
- **Template presets**: Quickly create items from 12 pre-built templates across 5 categories (Weapons, Clothing, Bags, Consumables, Objects)
- **Batch folder scan**: Point at a mod folder to auto-discover .p3d models, textures (.paa), and materials (.rvmat)
- **Auto-fill defaults**: Sensible inventory sizes, weights, and spawn values auto-populate when you select a base class
- **Import existing configs**: Parse an existing config.cpp to load items back into the editor
- **Session save/load**: Save your work as a JSON session file and pick up where you left off
- **Auto-update**: Checks for new releases on startup and can install updates in-app
- **Dark/Light theme**: Toggle between dark and light mode
- **Export**: Generate ready-to-use config.cpp and types.xml files

## Download

Grab the latest `DayZ Model Config Generator.exe` from the [Releases](../../releases) page. No Python installation required. The app will notify you when updates are available.

## Supported Base Classes

Inventory_Base, Clothing_Base, Container_Base, Edible_Base, Weapon_Base, Rifle_Base, Pistol_Base, ItemOptics, ItemSuppressor, HouseNoDestruct, Backpack_Base, HeadGear_Base, Vest_Base, TentBase

## Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| Ctrl+N | Add new item |
| Ctrl+T | Open template menu |
| Ctrl+Shift+S | Scan folder for models |
| Ctrl+E | Export config.cpp and types.xml |
| Delete | Remove selected item |

## How It Works

1. Set your **Patch Name** (used for CfgPatches)
2. Add items using **+ Add Item**, **From Template**, **Scan Folder**, or **Import Config**
3. Edit each item's properties in the tabbed editor (General, Model, Textures, Inventory, Types.xml)
4. Review the **Live Preview** panel
5. Click **Export** to save config.cpp and types.xml

## License

MIT
