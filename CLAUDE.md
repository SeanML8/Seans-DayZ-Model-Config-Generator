# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

DayZ Custom Model Config Generator — a single-file Python/tkinter GUI tool that generates `config.cpp` and `types.xml` files for DayZ modding. Users define custom items (model-swapped retextures or entirely new items) and the tool outputs valid DayZ config files.

## Running

```bash
python model_config_generator.py
```

The pre-built exe (`DayZ Model Config Generator.exe`) is also in the repo root. No build system, tests, or linter are configured.

## Architecture

Everything lives in `model_config_generator.py` (~1635 lines). The code is organized top-to-bottom into these sections:

1. **Constants & Data Model** (lines 1–99) — `BASE_CLASSES` dict maps DayZ base classes to their required addons. `ItemDefinition` dataclass holds all per-item state (mode, class name, textures, inventory props, types.xml overrides). Serializes via `to_dict()`/`from_dict()`.

2. **Config Generation** (lines 101–228) — Pure functions that take `ItemDefinition` objects and produce config text:
   - `generate_item_entry()` → single CfgVehicles class entry
   - `generate_full_config()` → complete config.cpp with CfgPatches + CfgVehicles
   - `generate_types_entry()` / `generate_types_xml()` → types.xml output

3. **Config Parser** (lines 232–357) — `parse_config_for_import()` reads an existing config.cpp back into `ItemDefinition` objects using regex-based parsing (`_extract_class_body`, `_parse_string_value`, etc.).

4. **GUI** (lines 390–1634) — `ModelConfigApp` class owns all UI state. Key patterns:
   - Editor fields use tkinter `StringVar`/`IntVar` with `trace_add` callbacks that funnel through `_on_field_change()` → `_save_current_to_item()` → `_schedule_preview()` (150ms debounce)
   - Dynamic rows (hidden selections, textures, materials, attachments) are managed by `_add_dynamic_row()` / `_remove_dynamic_row()` / `_clear_dynamic_rows()`
   - `_suppress_traces` flag prevents recursive update loops when programmatically loading item data into editor fields
   - Two item modes: "model_swap" (retexture with texture slot count) and "new_item" (full item definition with inventory/selections/materials)

## Persistence

- App settings (theme, window geometry, patch name) save to `%APPDATA%/DayZ Config Generator/model_settings.json`
- Sessions (item list + patch name) save/load as user-chosen JSON files
- When frozen (PyInstaller exe), `_APP_DIR` points to the exe directory instead of the script directory

## Key Domain Concepts

- **config.cpp**: DayZ mod config file containing `CfgPatches` (mod metadata, required addons) and `CfgVehicles` (item class definitions inheriting from base classes like `Clothing_Base`, `Weapon_Base`, etc.)
- **types.xml**: Controls item spawning — nominal count, lifetime, restock, spawn locations (usage), and categories
- **hiddenSelections/Textures/Materials**: DayZ's texture replacement system — selections name model regions, textures (.paa) and materials (.rvmat) are mapped to those regions
- **Model swap vs New item**: Model swap inherits everything from a base class and just overrides the model + textures. New item defines all properties from scratch.
