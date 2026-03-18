"""
DayZ Custom Model Config Generator
A GUI tool for creating config.cpp entries for custom 3D models (.p3d) and new items.
Supports both model-swapped retextures and entirely new item definitions.
"""

import json
import os
import re
import sys
import copy
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext, simpledialog
from dataclasses import dataclass, field, asdict

VERSION = "1.0.0"

# ─── Data Directory ──────────────────────────────────────────────────────────

if getattr(sys, 'frozen', False):
    _APP_DIR = os.path.dirname(sys.executable)
else:
    _APP_DIR = os.path.dirname(os.path.abspath(__file__))

_DATA_DIR = os.path.join(os.environ.get("APPDATA", _APP_DIR), "DayZ Config Generator")
os.makedirs(_DATA_DIR, exist_ok=True)

# ─── Preset Base Classes ─────────────────────────────────────────────────────

BASE_CLASSES = {
    "Inventory_Base": {
        "required_addons": ["DZ_Data"], "description": "Generic item",
        "defaults": {
            "item_size_w": 2, "item_size_h": 2, "weight": 200,
            "types_category": "tools", "types_usage": "Town",
            "types_nominal": 10, "types_min": 5, "types_lifetime": 14400,
        },
    },
    "Clothing_Base": {
        "required_addons": ["DZ_Characters"], "description": "Wearable clothing",
        "defaults": {
            "item_size_w": 3, "item_size_h": 3, "weight": 500, "absorbency": 0.5,
            "types_category": "clothes", "types_usage": "Town",
            "types_nominal": 10, "types_min": 5, "types_lifetime": 14400,
        },
    },
    "Container_Base": {
        "required_addons": ["DZ_Gear_Containers"], "description": "Bags/cases with cargo",
        "defaults": {
            "item_size_w": 4, "item_size_h": 4, "weight": 300,
            "cargo_size_w": 6, "cargo_size_h": 6,
            "types_category": "tools", "types_usage": "Town",
            "types_nominal": 10, "types_min": 5, "types_lifetime": 14400,
        },
    },
    "Edible_Base": {
        "required_addons": ["DZ_Gear_Consumables"], "description": "Consumable food/drink",
        "defaults": {
            "item_size_w": 1, "item_size_h": 2, "weight": 300,
            "types_category": "tools", "types_usage": "Town",
            "types_nominal": 15, "types_min": 7, "types_lifetime": 10800,
        },
    },
    "Weapon_Base": {
        "required_addons": ["DZ_Weapons_Firearms"], "description": "Firearms (generic)",
        "defaults": {
            "item_size_w": 6, "item_size_h": 2, "weight": 2500,
            "types_category": "weapons", "types_usage": "Military",
            "types_nominal": 5, "types_min": 2, "types_lifetime": 28800,
        },
    },
    "Rifle_Base": {
        "required_addons": ["DZ_Weapons_Firearms"], "description": "Rifles",
        "defaults": {
            "item_size_w": 8, "item_size_h": 2, "weight": 3000,
            "types_category": "weapons", "types_usage": "Military",
            "types_nominal": 5, "types_min": 2, "types_lifetime": 28800,
        },
    },
    "Pistol_Base": {
        "required_addons": ["DZ_Weapons_Firearms"], "description": "Pistols",
        "defaults": {
            "item_size_w": 3, "item_size_h": 2, "weight": 1000,
            "types_category": "weapons", "types_usage": "Military",
            "types_nominal": 8, "types_min": 3, "types_lifetime": 28800,
        },
    },
    "ItemOptics": {
        "required_addons": ["DZ_Weapons_Firearms"], "description": "Weapon optics",
        "defaults": {
            "item_size_w": 2, "item_size_h": 1, "weight": 300,
            "types_category": "weapons", "types_usage": "Military",
            "types_nominal": 6, "types_min": 3, "types_lifetime": 28800,
        },
    },
    "ItemSuppressor": {
        "required_addons": ["DZ_Weapons_Firearms"], "description": "Muzzle attachments",
        "defaults": {
            "item_size_w": 2, "item_size_h": 1, "weight": 200,
            "types_category": "weapons", "types_usage": "Military",
            "types_nominal": 4, "types_min": 2, "types_lifetime": 28800,
        },
    },
    "HouseNoDestruct": {
        "required_addons": ["DZ_Data"], "description": "Static objects/buildings",
        "defaults": {
            "item_size_w": 1, "item_size_h": 1, "weight": 0,
            "types_nominal": 0, "types_min": 0, "types_lifetime": 3888000,
        },
    },
    "Backpack_Base": {
        "required_addons": ["DZ_Characters"], "description": "Backpacks",
        "defaults": {
            "item_size_w": 6, "item_size_h": 6, "weight": 800,
            "cargo_size_w": 10, "cargo_size_h": 10,
            "types_category": "clothes", "types_usage": "Town",
            "types_nominal": 8, "types_min": 4, "types_lifetime": 14400,
        },
    },
    "HeadGear_Base": {
        "required_addons": ["DZ_Characters"], "description": "Helmets/hats",
        "defaults": {
            "item_size_w": 3, "item_size_h": 3, "weight": 400,
            "types_category": "clothes", "types_usage": "Town",
            "types_nominal": 10, "types_min": 5, "types_lifetime": 14400,
        },
    },
    "Vest_Base": {
        "required_addons": ["DZ_Characters"], "description": "Vests/plate carriers",
        "defaults": {
            "item_size_w": 4, "item_size_h": 4, "weight": 1500,
            "cargo_size_w": 6, "cargo_size_h": 4,
            "types_category": "clothes", "types_usage": "Military",
            "types_nominal": 5, "types_min": 2, "types_lifetime": 14400,
        },
    },
    "TentBase": {
        "required_addons": ["DZ_Gear_Camping"], "description": "Tent-like deployables",
        "defaults": {
            "item_size_w": 5, "item_size_h": 5, "weight": 5000,
            "cargo_size_w": 10, "cargo_size_h": 10,
            "types_category": "tools", "types_usage": "Town",
            "types_nominal": 3, "types_min": 1, "types_lifetime": 3888000,
        },
    },
}

TYPES_CATEGORIES = ["clothes", "tools", "weapons", "vehicles", "zombies", "animals"]
TYPES_USAGES = ["Town", "Village", "Military", "Police", "Medic", "Firefighter", "Industrial",
                "Farm", "Coast", "Hunting", "Office", "School", "Prison", "Sea"]

# ─── Template Presets ─────────────────────────────────────────────────────────

TEMPLATE_PRESETS = {
    "Weapons": [
        {"name": "Assault Rifle", "data": {
            "mode": "new_item", "base_class": "Rifle_Base",
            "class_name": "MyMod_AssaultRifle", "display_name": "Custom Assault Rifle",
            "description": "A custom assault rifle",
            "required_addons": ["DZ_Weapons_Firearms"],
            "item_size_w": 8, "item_size_h": 2, "weight": 3500,
            "hidden_selections": ["skin"],
            "types_category": "weapons", "types_usage": "Military",
            "types_nominal": 5, "types_min": 2, "types_lifetime": 28800, "types_cost": 100,
        }},
        {"name": "Sniper Rifle", "data": {
            "mode": "new_item", "base_class": "Rifle_Base",
            "class_name": "MyMod_SniperRifle", "display_name": "Custom Sniper Rifle",
            "description": "A custom sniper rifle",
            "required_addons": ["DZ_Weapons_Firearms"],
            "item_size_w": 10, "item_size_h": 2, "weight": 4500,
            "hidden_selections": ["skin"],
            "types_category": "weapons", "types_usage": "Military",
            "types_nominal": 3, "types_min": 1, "types_lifetime": 28800, "types_cost": 100,
        }},
        {"name": "Pistol", "data": {
            "mode": "new_item", "base_class": "Pistol_Base",
            "class_name": "MyMod_Pistol", "display_name": "Custom Pistol",
            "description": "A custom pistol",
            "required_addons": ["DZ_Weapons_Firearms"],
            "item_size_w": 3, "item_size_h": 2, "weight": 1000,
            "hidden_selections": ["skin"],
            "types_category": "weapons", "types_usage": "Military",
            "types_nominal": 8, "types_min": 3, "types_lifetime": 28800, "types_cost": 100,
        }},
    ],
    "Clothing": [
        {"name": "Tactical Vest", "data": {
            "mode": "new_item", "base_class": "Vest_Base",
            "class_name": "MyMod_TacticalVest", "display_name": "Custom Tactical Vest",
            "description": "A custom tactical vest",
            "required_addons": ["DZ_Characters"],
            "item_size_w": 4, "item_size_h": 4, "weight": 1500,
            "cargo_size_w": 6, "cargo_size_h": 4,
            "hidden_selections": ["skin"],
            "types_category": "clothes", "types_usage": "Military",
            "types_nominal": 5, "types_min": 2, "types_lifetime": 14400, "types_cost": 100,
        }},
        {"name": "Plate Carrier", "data": {
            "mode": "new_item", "base_class": "Vest_Base",
            "class_name": "MyMod_PlateCarrier", "display_name": "Custom Plate Carrier",
            "description": "A custom plate carrier vest",
            "required_addons": ["DZ_Characters"],
            "item_size_w": 4, "item_size_h": 4, "weight": 3000,
            "cargo_size_w": 8, "cargo_size_h": 5,
            "hidden_selections": ["skin"],
            "types_category": "clothes", "types_usage": "Military",
            "types_nominal": 3, "types_min": 1, "types_lifetime": 14400, "types_cost": 100,
        }},
        {"name": "Helmet", "data": {
            "mode": "new_item", "base_class": "HeadGear_Base",
            "class_name": "MyMod_Helmet", "display_name": "Custom Helmet",
            "description": "A custom helmet",
            "required_addons": ["DZ_Characters"],
            "item_size_w": 3, "item_size_h": 3, "weight": 800,
            "hidden_selections": ["skin"],
            "types_category": "clothes", "types_usage": "Military",
            "types_nominal": 6, "types_min": 3, "types_lifetime": 14400, "types_cost": 100,
        }},
        {"name": "Hat / Cap", "data": {
            "mode": "new_item", "base_class": "HeadGear_Base",
            "class_name": "MyMod_Hat", "display_name": "Custom Hat",
            "description": "A custom hat",
            "required_addons": ["DZ_Characters"],
            "item_size_w": 2, "item_size_h": 2, "weight": 150,
            "hidden_selections": ["skin"],
            "types_category": "clothes", "types_usage": "Town",
            "types_nominal": 12, "types_min": 6, "types_lifetime": 14400, "types_cost": 100,
        }},
    ],
    "Bags": [
        {"name": "Backpack (Small)", "data": {
            "mode": "new_item", "base_class": "Backpack_Base",
            "class_name": "MyMod_SmallBackpack", "display_name": "Custom Small Backpack",
            "description": "A small custom backpack",
            "required_addons": ["DZ_Characters"],
            "item_size_w": 5, "item_size_h": 5, "weight": 600,
            "cargo_size_w": 6, "cargo_size_h": 7,
            "hidden_selections": ["skin"],
            "types_category": "clothes", "types_usage": "Town",
            "types_nominal": 10, "types_min": 5, "types_lifetime": 14400, "types_cost": 100,
        }},
        {"name": "Backpack (Large)", "data": {
            "mode": "new_item", "base_class": "Backpack_Base",
            "class_name": "MyMod_LargeBackpack", "display_name": "Custom Large Backpack",
            "description": "A large custom backpack",
            "required_addons": ["DZ_Characters"],
            "item_size_w": 7, "item_size_h": 7, "weight": 1200,
            "cargo_size_w": 10, "cargo_size_h": 10,
            "hidden_selections": ["skin"],
            "types_category": "clothes", "types_usage": "Town",
            "types_nominal": 5, "types_min": 2, "types_lifetime": 14400, "types_cost": 100,
        }},
    ],
    "Consumables": [
        {"name": "Food Item", "data": {
            "mode": "new_item", "base_class": "Edible_Base",
            "class_name": "MyMod_FoodItem", "display_name": "Custom Food",
            "description": "A custom food item",
            "required_addons": ["DZ_Gear_Consumables"],
            "item_size_w": 1, "item_size_h": 2, "weight": 300,
            "var_quantity_init": 100, "var_quantity_min": 0, "var_quantity_max": 100,
            "hidden_selections": ["skin"],
            "types_category": "tools", "types_usage": "Town",
            "types_nominal": 15, "types_min": 7, "types_lifetime": 10800, "types_cost": 100,
        }},
        {"name": "Drink Item", "data": {
            "mode": "new_item", "base_class": "Edible_Base",
            "class_name": "MyMod_DrinkItem", "display_name": "Custom Drink",
            "description": "A custom drink item",
            "required_addons": ["DZ_Gear_Consumables"],
            "item_size_w": 1, "item_size_h": 2, "weight": 500,
            "var_quantity_init": 100, "var_quantity_min": 0, "var_quantity_max": 100,
            "hidden_selections": ["skin"],
            "types_category": "tools", "types_usage": "Town",
            "types_nominal": 15, "types_min": 7, "types_lifetime": 10800, "types_cost": 100,
        }},
    ],
    "Objects": [
        {"name": "Building / Static Object", "data": {
            "mode": "new_item", "base_class": "HouseNoDestruct",
            "class_name": "MyMod_Building", "display_name": "Custom Building",
            "description": "A custom static object",
            "required_addons": ["DZ_Data"],
            "item_size_w": 1, "item_size_h": 1, "weight": 0,
            "types_nominal": 0, "types_min": 0, "types_lifetime": 3888000, "types_cost": 100,
        }},
    ],
}

# ─── Data Model ──────────────────────────────────────────────────────────────

@dataclass
class ItemDefinition:
    mode: str = "model_swap"  # "model_swap" or "new_item"
    class_name: str = ""
    base_class: str = "Inventory_Base"
    display_name: str = ""
    description: str = ""
    model_path: str = ""
    required_addons: list = field(default_factory=lambda: ["DZ_Data"])
    # Hidden selections (new item mode)
    hidden_selections: list = field(default_factory=list)
    hidden_selections_textures: list = field(default_factory=list)
    hidden_selections_materials: list = field(default_factory=list)
    # Texture slot count for model swap mode
    texture_slot_count: int = 1
    # Inventory properties (new item mode)
    item_size_w: int = 1
    item_size_h: int = 1
    weight: int = 0
    absorbency: float = 0.0
    cargo_size_w: int = 0
    cargo_size_h: int = 0
    attachments: list = field(default_factory=list)
    rotation_flags: int = 0
    var_quantity_init: int = 0
    var_quantity_min: int = 0
    var_quantity_max: int = 0
    # Types.xml overrides
    types_nominal: int = 10
    types_min: int = 5
    types_lifetime: int = 14400
    types_restock: int = 0
    types_cost: int = 100
    types_category: str = "tools"
    types_usage: str = "Town"

    def to_dict(self):
        return asdict(self)

    @staticmethod
    def from_dict(d):
        item = ItemDefinition()
        for k, v in d.items():
            if hasattr(item, k):
                setattr(item, k, v)
        return item


# ─── Config Generation ───────────────────────────────────────────────────────

def generate_item_entry(item):
    """Generate a single class entry for config.cpp."""
    display_name = item.display_name.replace('"', '')
    description = item.description.replace('"', '')

    lines = []
    lines.append(f"        scope = 2;")
    lines.append(f'        displayName = "{display_name}";')
    lines.append(f'        descriptionShort = "{description}";')
    lines.append(f'        model = "{item.model_path}";')

    if item.mode == "new_item":
        if item.weight > 0:
            lines.append(f"        weight = {item.weight};")
        if item.item_size_w > 0 and item.item_size_h > 0:
            lines.append(f"        itemSize[] = {{{item.item_size_w},{item.item_size_h}}};")
        if item.absorbency > 0:
            lines.append(f"        absorbency = {item.absorbency};")
        if item.cargo_size_w > 0 and item.cargo_size_h > 0:
            lines.append(f"        itemsCargoSize[] = {{{item.cargo_size_w},{item.cargo_size_h}}};")
        if item.rotation_flags > 0:
            lines.append(f"        rotationFlags = {item.rotation_flags};")
        if item.var_quantity_max > 0:
            lines.append(f"        varQuantityInit = {item.var_quantity_init};")
            lines.append(f"        varQuantityMin = {item.var_quantity_min};")
            lines.append(f"        varQuantityMax = {item.var_quantity_max};")
        if item.hidden_selections:
            sel_items = ",\n".join(f'            "{s}"' for s in item.hidden_selections)
            lines.append(f"        hiddenSelections[] =\n        {{\n{sel_items}\n        }};")
        if item.attachments:
            att_items = ",\n".join(f'            "{a}"' for a in item.attachments)
            lines.append(f"        attachments[] =\n        {{\n{att_items}\n        }};")

    # Textures
    if item.mode == "new_item":
        tex_list = item.hidden_selections_textures
    else:
        tex_list = item.hidden_selections_textures[:item.texture_slot_count] if item.hidden_selections_textures else []
    if tex_list:
        tex_items = ",\n".join(f'            "{t}"' for t in tex_list)
        lines.append(f"        hiddenSelectionsTextures[] =\n        {{\n{tex_items}\n        }};")

    # Materials (new item only)
    if item.mode == "new_item" and item.hidden_selections_materials:
        mat_items = ",\n".join(f'            "{m}"' for m in item.hidden_selections_materials)
        lines.append(f"        hiddenSelectionsMaterials[] =\n        {{\n{mat_items}\n        }};")

    body = "\n".join(lines)
    return (
        f"    class {item.base_class};\n"
        f"    class {item.class_name}: {item.base_class}\n"
        f"    {{\n"
        f"{body}\n"
        f"    }};"
    )


def generate_full_config(patch_name, required_addons, entries):
    """Generate a complete config.cpp file."""
    addons_str = ", ".join(f'"{a}"' for a in sorted(required_addons))
    entries_str = "\n".join(entries)
    return (
        f"class CfgPatches\n"
        f"{{\n"
        f"    class {patch_name}\n"
        f"    {{\n"
        f"        units[] = {{}};\n"
        f"        weapons[] = {{}};\n"
        f"        requiredVersion = 0.1;\n"
        f"        requiredAddons[] = {{\n"
        f"            {addons_str}\n"
        f"        }};\n"
        f"    }};\n"
        f"}};\n"
        f"\n"
        f"class CfgVehicles\n"
        f"{{\n"
        f"{entries_str}\n"
        f"}};\n"
    )


def generate_types_entry(class_name, overrides=None):
    """Generate a single types.xml entry."""
    o = overrides or {}
    nominal = o.get("nominal", 10)
    lifetime = o.get("lifetime", 14400)
    restock = o.get("restock", 0)
    min_val = o.get("min", 5)
    cost = o.get("cost", 100)
    category = o.get("category", "tools")
    usage = o.get("usage", "Town")
    return (
        f'    <type name="{class_name}">\n'
        f'        <nominal>{nominal}</nominal>\n'
        f'        <lifetime>{lifetime}</lifetime>\n'
        f'        <restock>{restock}</restock>\n'
        f'        <min>{min_val}</min>\n'
        f'        <quantmin>-1</quantmin>\n'
        f'        <quantmax>-1</quantmax>\n'
        f'        <cost>{cost}</cost>\n'
        f'        <flags count_in_cargo="0" count_in_holomap="0" count_in_map="1" count_in_player="0" crafted="0" deloot="0"/>\n'
        f'        <category name="{category}"/>\n'
        f'        <usage name="{usage}"/>\n'
        f'    </type>'
    )


def generate_types_xml(items):
    """Generate a complete types.xml file from a list of ItemDefinitions."""
    parts = []
    for item in items:
        if not item.class_name:
            continue
        overrides = {
            "nominal": item.types_nominal,
            "min": item.types_min,
            "lifetime": item.types_lifetime,
            "restock": item.types_restock,
            "cost": item.types_cost,
            "category": item.types_category,
            "usage": item.types_usage,
        }
        parts.append(generate_types_entry(item.class_name, overrides))
    entries = "\n".join(parts)
    return f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<types>\n{entries}\n</types>\n'


# ─── Config Parser (for import) ──────────────────────────────────────────────

def _extract_class_body(content, start_pos):
    """Extract the full body of a class definition by matching braces from start_pos."""
    depth = 0
    i = start_pos
    while i < len(content):
        if content[i] == '{':
            depth += 1
        elif content[i] == '}':
            depth -= 1
            if depth == 0:
                return content[start_pos + 1:i]
        i += 1
    return ""


def _parse_string_value(body, prop_name):
    """Extract a string property value from a class body."""
    m = re.search(rf'{prop_name}\s*=\s*"([^"]*)"', body)
    return m.group(1) if m else ""


def _parse_int_value(body, prop_name, default=0):
    """Extract an integer property value from a class body."""
    m = re.search(rf'{prop_name}\s*=\s*(\d+)', body)
    return int(m.group(1)) if m else default


def _parse_float_value(body, prop_name, default=0.0):
    """Extract a float property value from a class body."""
    m = re.search(rf'{prop_name}\s*=\s*([\d.]+)', body)
    return float(m.group(1)) if m else default


def _parse_string_array(body, prop_name):
    """Extract a string array property from a class body."""
    m = re.search(rf'{prop_name}\s*\[\]\s*=\s*\{{([^}}]*)\}}', body, re.DOTALL)
    if not m:
        return []
    raw = m.group(1)
    return [s.strip().strip('"') for s in raw.split(',') if s.strip().strip('"')]


def _parse_int_array(body, prop_name):
    """Extract an integer array property from a class body."""
    m = re.search(rf'{prop_name}\s*\[\]\s*=\s*\{{([^}}]*)\}}', body)
    if not m:
        return []
    raw = m.group(1)
    result = []
    for s in raw.split(','):
        s = s.strip()
        if s.isdigit():
            result.append(int(s))
    return result


def parse_config_for_import(config_path):
    """Parse a config.cpp file and return a list of ItemDefinitions."""
    items = []
    try:
        with open(config_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except (FileNotFoundError, PermissionError):
        return items

    # Find CfgVehicles block
    cfg_match = re.search(r'class\s+CfgVehicles\s*\{', content)
    if not cfg_match:
        return items
    cfg_body = _extract_class_body(content, cfg_match.end() - 1)
    if not cfg_body:
        return items

    # Find all class definitions inside CfgVehicles
    for m in re.finditer(r'class\s+(\w+)\s*:\s*(\w+)\s*\{', cfg_body):
        class_name = m.group(1)
        base_class = m.group(2)
        brace_pos = cfg_body.index('{', m.start())
        body = _extract_class_body(cfg_body, brace_pos)
        if not body:
            continue

        item = ItemDefinition()
        item.class_name = class_name
        item.base_class = base_class
        item.display_name = _parse_string_value(body, "displayName")
        item.description = _parse_string_value(body, "descriptionShort")
        item.model_path = _parse_string_value(body, "model")

        item.hidden_selections = _parse_string_array(body, "hiddenSelections")
        item.hidden_selections_textures = _parse_string_array(body, "hiddenSelectionsTextures")
        item.hidden_selections_materials = _parse_string_array(body, "hiddenSelectionsMaterials")
        item.attachments = _parse_string_array(body, "attachments")

        item.weight = _parse_int_value(body, "weight")
        item.absorbency = _parse_float_value(body, "absorbency")
        item.rotation_flags = _parse_int_value(body, "rotationFlags")
        item.var_quantity_init = _parse_int_value(body, "varQuantityInit")
        item.var_quantity_min = _parse_int_value(body, "varQuantityMin")
        item.var_quantity_max = _parse_int_value(body, "varQuantityMax")

        item_size = _parse_int_array(body, "itemSize")
        if len(item_size) >= 2:
            item.item_size_w, item.item_size_h = item_size[0], item_size[1]

        cargo_size = _parse_int_array(body, "itemsCargoSize")
        if len(cargo_size) >= 2:
            item.cargo_size_w, item.cargo_size_h = cargo_size[0], cargo_size[1]

        # Determine mode based on whether hiddenSelections is defined
        if item.hidden_selections:
            item.mode = "new_item"
        else:
            item.mode = "model_swap"
            item.texture_slot_count = max(1, len(item.hidden_selections_textures))

        # Set required_addons from base class preset if known
        if base_class in BASE_CLASSES:
            item.required_addons = list(BASE_CLASSES[base_class]["required_addons"])
        else:
            item.required_addons = ["DZ_Data"]

        items.append(item)

    return items


# ─── Folder Scanner ───────────────────────────────────────────────────────────

def _sanitize_class_name(name):
    """Sanitize a filename into a valid C++ identifier."""
    name = re.sub(r'[^A-Za-z0-9_]', '_', name)
    if name and name[0].isdigit():
        name = '_' + name
    return name or '_Item'


def scan_folder_for_p3d(root_dir):
    """Scan a directory recursively for .p3d files and create ItemDefinitions."""
    items = []
    used_names = set()

    for dirpath, _dirnames, filenames in os.walk(root_dir):
        for fname in filenames:
            if not fname.lower().endswith('.p3d'):
                continue

            full_path = os.path.join(dirpath, fname)
            rel_path = os.path.relpath(full_path, root_dir)
            model_path = '\\' + rel_path.replace('/', '\\')

            stem = os.path.splitext(fname)[0]
            class_name = _sanitize_class_name(stem)

            # Deduplicate class names within the batch
            base_name = class_name
            counter = 2
            while class_name in used_names:
                class_name = f"{base_name}_{counter}"
                counter += 1
            used_names.add(class_name)

            display_name = stem.replace('_', ' ').title()

            # Discover textures and materials in same dir and data/ subdir
            search_dirs = [dirpath]
            data_path = os.path.join(dirpath, 'data')
            if os.path.isdir(data_path):
                search_dirs.append(data_path)

            textures = []
            materials = []
            seen_lower = set()
            for sdir in search_dirs:
                try:
                    for f in os.listdir(sdir):
                        f_lower = f.lower()
                        f_rel = os.path.relpath(os.path.join(sdir, f), root_dir)
                        f_path = '\\' + f_rel.replace('/', '\\')
                        f_path_lower = f_path.lower()
                        if f_path_lower in seen_lower:
                            continue
                        seen_lower.add(f_path_lower)
                        if f_lower.endswith('.paa'):
                            textures.append(f_path)
                        elif f_lower.endswith('.rvmat'):
                            materials.append(f_path)
                except OSError:
                    continue

            item = ItemDefinition()
            item.class_name = class_name
            item.display_name = display_name
            item.model_path = model_path
            item.required_addons = ["DZ_Data"]

            if textures or materials:
                item.mode = "new_item"
                item.hidden_selections = [f"skin{'' if i == 0 else i + 1}" for i in range(max(len(textures), 1))]
                item.hidden_selections_textures = textures
                item.hidden_selections_materials = materials
            else:
                item.mode = "model_swap"
                item.texture_slot_count = 1

            items.append(item)

    return items


# ─── Tooltip ──────────────────────────────────────────────────────────────────

class ToolTip:
    def __init__(self, widget, text, bg="#ffffe0", fg="#000000"):
        self.widget = widget
        self.text = text
        self.bg = bg
        self.fg = fg
        self.tip_window = None
        widget.bind("<Enter>", self._show)
        widget.bind("<Leave>", self._hide)

    def _show(self, event=None):
        if self.tip_window:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 4
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, justify=tk.LEFT, wraplength=320,
                         background=self.bg, foreground=self.fg,
                         relief=tk.SOLID, borderwidth=1,
                         font=("Segoe UI", 9), padx=6, pady=4)
        label.pack()

    def _hide(self, event=None):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None


# ─── GUI Application ─────────────────────────────────────────────────────────

class ModelConfigApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"DayZ Custom Model Config Generator v{VERSION}")

        # Center window on screen
        win_w, win_h = 1400, 950
        try:
            import ctypes
            from ctypes import wintypes
            rect = wintypes.RECT()
            ctypes.windll.user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(rect), 0)
            work_w = rect.right - rect.left
            work_h = rect.bottom - rect.top
            work_x = rect.left
            work_y = rect.top
        except Exception:
            work_w = self.root.winfo_screenwidth()
            work_h = self.root.winfo_screenheight()
            work_x, work_y = 0, 0
        margin = 40
        max_w = work_w - margin * 2
        max_h = work_h - margin * 2
        win_w = min(win_w, max_w)
        win_h = min(win_h, max_h)
        x = work_x + (work_w - win_w) // 2
        y = work_y + (work_h - win_h) // 2
        self.root.geometry(f"{win_w}x{win_h}+{x}+{y}")
        self.root.minsize(min(1050, max_w), min(750, max_h))

        # Settings
        self._settings_path = os.path.join(_DATA_DIR, "model_settings.json")

        # State
        self.items = []  # list of ItemDefinition
        self._selected_index = -1
        self._preview_after_id = None
        self._suppress_traces = False
        self._autofill_enabled = tk.BooleanVar(value=True)

        # Theme
        self.dark_mode = True
        self._load_theme_setting()

        # Style
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self._configure_styles()
        # Set combobox dropdown colors at init
        c = self._colors
        self.root.option_add("*TCombobox*Listbox.background", c["entry_bg"])
        self.root.option_add("*TCombobox*Listbox.foreground", c["fg"])
        self.root.option_add("*TCombobox*Listbox.selectBackground", c["accent"])
        self.root.option_add("*TCombobox*Listbox.selectForeground", c["selected_fg"])

        self._build_ui()
        self._load_settings()

        # Save settings on close
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # Keyboard shortcuts
        self.root.bind("<Control-n>", lambda e: self._add_item())
        self.root.bind("<Control-e>", lambda e: self._export())
        self.root.bind("<Delete>", lambda e: self._remove_item())
        self.root.bind("<Control-t>", lambda e: self._show_template_menu())
        self.root.bind("<Control-Shift-S>", lambda e: self._scan_folder())

    # ── Theme ─────────────────────────────────────────────────────────────

    def _get_theme_colors(self):
        if self.dark_mode:
            return {
                "bg": "#1e1e1e", "fg": "#d4d4d4", "accent": "#569cd6",
                "entry_bg": "#2d2d2d", "btn_bg": "#3c3c3c", "btn_active": "#505050",
                "title_fg": "#ffffff", "subtitle_fg": "#808080", "section_fg": "#ffffff",
                "warning_fg": "#cca700", "accent_active": "#4a8abf",
                "selected_fg": "#ffffff",
                "list_bg": "#2d2d2d", "list_fg": "#d4d4d4", "list_select_bg": "#569cd6",
                "list_highlight": "#569cd6", "list_highlight_bg": "#3c3c3c",
                "output_bg": "#1a1a1a", "output_fg": "#d4d4d4",
                "match_good": "#6a9955", "match_bad": "#f44747",
                "placeholder_fg": "#666666", "error_fg": "#f44747",
                "tooltip_bg": "#3c3c3c", "tooltip_fg": "#d4d4d4",
                "sash_bg": "#444444",
                "separator_fg": "#444444",
            }
        else:
            return {
                "bg": "#f5f5f5", "fg": "#1e1e1e", "accent": "#0066cc",
                "entry_bg": "#ffffff", "btn_bg": "#e0e0e0", "btn_active": "#c8c8c8",
                "title_fg": "#1e1e1e", "subtitle_fg": "#666666", "section_fg": "#1e1e1e",
                "warning_fg": "#a67c00", "accent_active": "#004c99",
                "selected_fg": "#ffffff",
                "list_bg": "#ffffff", "list_fg": "#1e1e1e", "list_select_bg": "#0066cc",
                "list_highlight": "#0066cc", "list_highlight_bg": "#cccccc",
                "output_bg": "#ffffff", "output_fg": "#1e1e1e",
                "match_good": "#2d8a30", "match_bad": "#cc0000",
                "placeholder_fg": "#999999", "error_fg": "#cc0000",
                "tooltip_bg": "#ffffe0", "tooltip_fg": "#1e1e1e",
                "sash_bg": "#cccccc",
                "separator_fg": "#cccccc",
            }

    def _configure_styles(self):
        c = self._get_theme_colors()
        self._colors = c
        self.root.configure(bg=c["bg"])
        self.style.configure("TFrame", background=c["bg"])
        self.style.configure("TLabel", background=c["bg"], foreground=c["fg"], font=("Segoe UI", 10))
        self.style.configure("Title.TLabel", background=c["bg"], foreground=c["title_fg"], font=("Segoe UI", 14, "bold"))
        self.style.configure("Subtitle.TLabel", background=c["bg"], foreground=c["subtitle_fg"], font=("Segoe UI", 9))
        self.style.configure("Section.TLabel", background=c["bg"], foreground=c["section_fg"], font=("Segoe UI", 10, "bold"))
        self.style.configure("TButton", background=c["btn_bg"], foreground=c["fg"], font=("Segoe UI", 9), borderwidth=0, padding=(8, 4))
        self.style.map("TButton", background=[("active", c["btn_active"])])
        self.style.configure("Accent.TButton", background=c["accent"], foreground=c["selected_fg"], font=("Segoe UI", 9, "bold"), padding=(12, 5))
        self.style.map("Accent.TButton", background=[("active", c["accent_active"])])
        self.style.configure("TEntry", fieldbackground=c["entry_bg"], foreground=c["fg"], insertcolor=c["fg"], borderwidth=0, padding=6)
        self.style.configure("TLabelframe", background=c["bg"], foreground=c["fg"])
        self.style.configure("TLabelframe.Label", background=c["bg"], foreground=c["section_fg"], font=("Segoe UI", 10, "bold"))
        self.style.configure("TSeparator", background=c["separator_fg"])
        self.style.configure("Treeview", background=c["list_bg"], foreground=c["fg"], fieldbackground=c["list_bg"], font=("Consolas", 9), borderwidth=0)
        self.style.configure("Treeview.Heading", background=c["btn_bg"], foreground=c["fg"], font=("Segoe UI", 9, "bold"))
        self.style.map("Treeview", background=[("selected", c["accent"])], foreground=[("selected", c["selected_fg"])])
        self.style.configure("TCheckbutton", background=c["bg"], foreground=c["fg"], font=("Segoe UI", 9))
        self.style.map("TCheckbutton", background=[("active", c["bg"])])
        self.style.configure("TNotebook", background=c["bg"], borderwidth=0)
        self.style.configure("TNotebook.Tab", background=c["btn_bg"], foreground=c["fg"], font=("Segoe UI", 9), padding=(10, 4))
        self.style.map("TNotebook.Tab", background=[("selected", c["accent"])], foreground=[("selected", c["selected_fg"])])
        self.style.configure("TRadiobutton", background=c["bg"], foreground=c["fg"], font=("Segoe UI", 9))
        self.style.map("TRadiobutton", background=[("active", c["bg"])])
        self.style.configure("TSpinbox", fieldbackground=c["entry_bg"], foreground=c["fg"], insertcolor=c["fg"], borderwidth=0, padding=4)
        self.style.configure("TCombobox", fieldbackground=c["entry_bg"], foreground=c["fg"], insertcolor=c["fg"], borderwidth=0, padding=4)
        self.style.map("TCombobox", fieldbackground=[("readonly", c["entry_bg"])])

    def _load_theme_setting(self):
        try:
            with open(self._settings_path, "r", encoding="utf-8") as f:
                settings = json.load(f)
            if "dark_mode" in settings:
                self.dark_mode = settings["dark_mode"]
        except (FileNotFoundError, json.JSONDecodeError):
            pass

    def _toggle_theme(self):
        self.dark_mode = not self.dark_mode
        self._configure_styles()
        self.theme_btn.configure(text="Light Mode" if self.dark_mode else "Dark Mode")
        self._apply_theme_to_widgets()
        self._build_template_menu()
        self._save_settings()

    def _apply_theme_to_widgets(self):
        c = self._colors
        self.preview_text.configure(
            bg=c["output_bg"], fg=c["output_fg"],
            highlightcolor=c["list_highlight"], highlightbackground=c["list_highlight_bg"],
            insertbackground=c["output_fg"],
        )
        self.output_text.configure(
            bg=c["output_bg"], fg=c["output_fg"],
            highlightcolor=c["list_highlight"], highlightbackground=c["list_highlight_bg"],
            insertbackground=c["output_fg"],
        )
        self.content_pane.configure(bg=c["bg"])
        # Theme the combobox dropdown list
        self.root.option_add("*TCombobox*Listbox.background", c["entry_bg"])
        self.root.option_add("*TCombobox*Listbox.foreground", c["fg"])
        self.root.option_add("*TCombobox*Listbox.selectBackground", c["accent"])
        self.root.option_add("*TCombobox*Listbox.selectForeground", c["selected_fg"])

    # ── Settings Persistence ──────────────────────────────────────────────

    def _load_settings(self):
        try:
            with open(self._settings_path, "r", encoding="utf-8") as f:
                settings = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return
        if settings.get("window_geometry"):
            try:
                self.root.geometry(settings["window_geometry"])
            except tk.TclError:
                pass
        if settings.get("patch_name"):
            self.patch_name_var.set(settings["patch_name"])

    def _save_settings(self):
        settings = {
            "dark_mode": self.dark_mode,
            "window_geometry": self.root.geometry(),
            "patch_name": self.patch_name_var.get(),
        }
        try:
            with open(self._settings_path, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=2)
        except OSError:
            pass

    def _on_close(self):
        if self.items:
            if not messagebox.askyesno("Unsaved Items",
                                       f"You have {len(self.items)} item(s) that haven't been exported.\n\n"
                                       "Close anyway?"):
                return
        self._save_settings()
        self.root.destroy()

    # ── Build UI ──────────────────────────────────────────────────────────

    def _build_ui(self):
        c = self._colors

        # Main container
        main = ttk.Frame(self.root, padding=(12, 8, 12, 12))
        main.pack(fill=tk.BOTH, expand=True)

        # Title bar
        title_frame = ttk.Frame(main)
        title_frame.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(title_frame, text=f"DayZ Custom Model Config Generator", style="Title.TLabel").pack(side=tk.LEFT)
        self.theme_btn = ttk.Button(title_frame, text="Light Mode" if self.dark_mode else "Dark Mode",
                                    command=self._toggle_theme)
        self.theme_btn.pack(side=tk.RIGHT)

        # Toolbar
        toolbar = ttk.Frame(main)
        toolbar.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(toolbar, text="Patch Name:", style="Section.TLabel").pack(side=tk.LEFT, padx=(0, 4))
        self.patch_name_var = tk.StringVar(value="MyMod_CustomItems")
        patch_entry = ttk.Entry(toolbar, textvariable=self.patch_name_var, width=25)
        patch_entry.pack(side=tk.LEFT, padx=(0, 12))
        self.patch_name_var.trace_add("write", lambda *a: self._schedule_preview())

        _tt = lambda w, t: ToolTip(w, t, bg=c["tooltip_bg"], fg=c["tooltip_fg"])

        add_btn = ttk.Button(toolbar, text="+ Add Item", command=self._add_item)
        add_btn.pack(side=tk.LEFT, padx=2)
        _tt(add_btn, "Add a new blank item (Ctrl+N)")

        dup_btn = ttk.Button(toolbar, text="Duplicate", command=self._duplicate_item)
        dup_btn.pack(side=tk.LEFT, padx=2)
        _tt(dup_btn, "Duplicate the selected item")

        rem_btn = ttk.Button(toolbar, text="Remove", command=self._remove_item)
        rem_btn.pack(side=tk.LEFT, padx=2)
        _tt(rem_btn, "Remove the selected item (Delete)")

        sep = ttk.Frame(toolbar, width=20)
        sep.pack(side=tk.LEFT)

        import_btn = ttk.Button(toolbar, text="Import Config", command=self._import_config)
        import_btn.pack(side=tk.LEFT, padx=2)
        _tt(import_btn, "Import items from an existing config.cpp")

        scan_btn = ttk.Button(toolbar, text="Scan Folder", command=self._scan_folder)
        scan_btn.pack(side=tk.LEFT, padx=2)
        _tt(scan_btn, "Scan a folder for .p3d models and auto-create items (Ctrl+Shift+S)")

        self._template_btn = ttk.Button(toolbar, text="From Template", command=self._show_template_menu)
        self._template_btn.pack(side=tk.LEFT, padx=2)
        _tt(self._template_btn, "Create a new item from a preset template (Ctrl+T)")

        save_btn = ttk.Button(toolbar, text="Save Session", command=self._save_session)
        save_btn.pack(side=tk.LEFT, padx=2)
        _tt(save_btn, "Save all items to a session file (.json)")

        load_btn = ttk.Button(toolbar, text="Load Session", command=self._load_session)
        load_btn.pack(side=tk.LEFT, padx=2)
        _tt(load_btn, "Load items from a saved session file (.json)")

        export_btn = ttk.Button(toolbar, text="Export", style="Accent.TButton", command=self._export)
        export_btn.pack(side=tk.RIGHT, padx=2)
        _tt(export_btn, "Export config.cpp and types.xml (Ctrl+E)")

        self._build_template_menu()

        # Main content: horizontal PanedWindow
        self.content_pane = tk.PanedWindow(main, orient=tk.HORIZONTAL, sashwidth=6,
                                              bg=c["bg"], bd=0, opaqueresize=True,
                                              sashrelief=tk.FLAT)
        content_pane = self.content_pane
        content_pane.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        # Left panel
        left_frame = ttk.Frame(content_pane)
        content_pane.add(left_frame, width=560, minsize=420)

        # Item list
        list_frame = ttk.LabelFrame(left_frame, text="Items", padding=4)
        list_frame.pack(fill=tk.X, pady=(0, 4))

        self.item_tree = ttk.Treeview(list_frame, columns=("mode", "class", "base"), show="headings", height=6)
        self.item_tree.heading("mode", text="Mode")
        self.item_tree.heading("class", text="Class Name")
        self.item_tree.heading("base", text="Base Class")
        self.item_tree.column("mode", width=70, minwidth=55)
        self.item_tree.column("class", width=240, minwidth=140)
        self.item_tree.column("base", width=180, minwidth=120)
        self.item_tree.pack(fill=tk.X)
        self.item_tree.bind("<<TreeviewSelect>>", self._on_item_select)

        # Editor notebook
        self.editor_notebook = ttk.Notebook(left_frame)
        self.editor_notebook.pack(fill=tk.BOTH, expand=True, pady=(4, 0))

        self._build_general_tab()
        self._build_model_tab()
        self._build_textures_tab()
        self._build_inventory_tab()
        self._build_types_tab()

        # Right panel: live preview
        right_frame = ttk.Frame(content_pane)
        content_pane.add(right_frame, minsize=300)

        ttk.Label(right_frame, text="Live Preview", style="Section.TLabel").pack(anchor=tk.W, pady=(0, 4))
        self.preview_text = scrolledtext.ScrolledText(
            right_frame, height=20, bg=c["output_bg"], fg=c["output_fg"],
            font=("Consolas", 9), borderwidth=0, highlightthickness=1,
            highlightcolor=c["list_highlight"], highlightbackground=c["list_highlight_bg"],
            insertbackground=c["output_fg"], wrap=tk.NONE,
        )
        self.preview_text.pack(fill=tk.BOTH, expand=True)
        self.preview_text.configure(state=tk.DISABLED)

        # Output log (bottom)
        log_frame = ttk.LabelFrame(main, text="Output", padding=4)
        log_frame.pack(fill=tk.X, pady=(0, 0))
        self.output_text = scrolledtext.ScrolledText(
            log_frame, height=4, bg=c["output_bg"], fg=c["output_fg"],
            font=("Consolas", 9), borderwidth=0, highlightthickness=1,
            highlightcolor=c["list_highlight"], highlightbackground=c["list_highlight_bg"],
            insertbackground=c["output_fg"], wrap=tk.WORD,
        )
        self.output_text.pack(fill=tk.BOTH, expand=True)
        self.output_text.configure(state=tk.DISABLED)

    # ── General Tab ───────────────────────────────────────────────────────

    def _build_general_tab(self):
        frame = ttk.Frame(self.editor_notebook, padding=8)
        self.editor_notebook.add(frame, text="General")

        # Mode
        mode_frame = ttk.Frame(frame)
        mode_frame.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(mode_frame, text="Mode:", style="Section.TLabel").pack(anchor=tk.W)
        self.mode_var = tk.StringVar(value="model_swap")
        ttk.Radiobutton(mode_frame, text="Model Swap (retexture with custom model)",
                        variable=self.mode_var, value="model_swap",
                        command=self._on_mode_change).pack(anchor=tk.W, padx=(8, 0))
        ttk.Radiobutton(mode_frame, text="New Item (define everything from scratch)",
                        variable=self.mode_var, value="new_item",
                        command=self._on_mode_change).pack(anchor=tk.W, padx=(8, 0))

        _lbl_w = 14  # uniform label width for alignment

        # Class name
        row = ttk.Frame(frame)
        row.pack(fill=tk.X, pady=2)
        ttk.Label(row, text="Class Name:", width=_lbl_w).pack(side=tk.LEFT)
        self.class_name_var = tk.StringVar()
        self.class_name_entry = ttk.Entry(row, textvariable=self.class_name_var)
        self.class_name_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.class_name_var.trace_add("write", lambda *a: self._on_field_change())
        ToolTip(self.class_name_entry, "C++ identifier: letters, digits, underscores (e.g., MyMod_TacticalHelmet)", bg=self._colors["tooltip_bg"], fg=self._colors["tooltip_fg"])

        # Base class
        row = ttk.Frame(frame)
        row.pack(fill=tk.X, pady=2)
        ttk.Label(row, text="Base Class:", width=_lbl_w).pack(side=tk.LEFT)
        base_values = list(BASE_CLASSES.keys()) + ["Custom..."]
        self.base_class_var = tk.StringVar(value="Inventory_Base")
        self.base_class_combo = ttk.Combobox(row, textvariable=self.base_class_var, values=base_values, width=25)
        self.base_class_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.base_class_combo.bind("<<ComboboxSelected>>", self._on_base_class_change)
        self.base_class_var.trace_add("write", lambda *a: self._on_field_change())

        # Base class description + autofill checkbox
        _indent = _lbl_w * 8  # approximate pixel indent to align with fields
        self.base_desc_label = ttk.Label(frame, text="Generic item", style="Subtitle.TLabel")
        self.base_desc_label.pack(anchor=tk.W, padx=(_indent, 0))
        ttk.Checkbutton(frame, text="Auto-fill defaults on base class change",
                        variable=self._autofill_enabled).pack(anchor=tk.W, padx=(_indent, 0), pady=(0, 4))

        # Display name
        row = ttk.Frame(frame)
        row.pack(fill=tk.X, pady=2)
        ttk.Label(row, text="Display Name:", width=_lbl_w).pack(side=tk.LEFT)
        self.display_name_var = tk.StringVar()
        ttk.Entry(row, textvariable=self.display_name_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.display_name_var.trace_add("write", lambda *a: self._on_field_change())

        # Description
        row = ttk.Frame(frame)
        row.pack(fill=tk.X, pady=2)
        ttk.Label(row, text="Description:", width=_lbl_w).pack(side=tk.LEFT)
        self.desc_var = tk.StringVar()
        ttk.Entry(row, textvariable=self.desc_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.desc_var.trace_add("write", lambda *a: self._on_field_change())

        # Required addons
        row = ttk.Frame(frame)
        row.pack(fill=tk.X, pady=2)
        ttk.Label(row, text="requiredAddons:", width=_lbl_w).pack(side=tk.LEFT)
        self.addons_var = tk.StringVar(value="DZ_Data")
        self.addons_entry = ttk.Entry(row, textvariable=self.addons_var)
        self.addons_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.addons_var.trace_add("write", lambda *a: self._on_field_change())
        ToolTip(self.addons_entry, "Comma-separated list (e.g., DZ_Data, DZ_Characters)", bg=self._colors["tooltip_bg"], fg=self._colors["tooltip_fg"])

    # ── Model & Selections Tab ────────────────────────────────────────────

    def _build_model_tab(self):
        frame = ttk.Frame(self.editor_notebook, padding=8)
        self._model_tab_frame = frame
        self.editor_notebook.add(frame, text="Model")

        _lbl_w = 18  # uniform label width for model tab

        # Model path
        row = ttk.Frame(frame)
        row.pack(fill=tk.X, pady=2)
        ttk.Label(row, text="Model Path (.p3d):", width=_lbl_w).pack(side=tk.LEFT)
        self.model_path_var = tk.StringVar()
        ttk.Entry(row, textvariable=self.model_path_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))
        ttk.Button(row, text="Browse", command=self._browse_model).pack(side=tk.RIGHT)
        self.model_path_var.trace_add("write", lambda *a: self._on_field_change())
        ToolTip(row, r"Path to .p3d model file (e.g., \MyMod\data\my_model.p3d)", bg=self._colors["tooltip_bg"], fg=self._colors["tooltip_fg"])

        # Texture slot count (model swap mode)
        self.slot_count_frame = ttk.Frame(frame)
        self.slot_count_frame.pack(fill=tk.X, pady=2)
        ttk.Label(self.slot_count_frame, text="Texture Slot Count:", width=_lbl_w).pack(side=tk.LEFT)
        self.slot_count_var = tk.IntVar(value=1)
        self.slot_count_spin = ttk.Spinbox(self.slot_count_frame, from_=1, to=10,
                                            textvariable=self.slot_count_var, width=5,
                                            command=self._on_slot_count_change)
        self.slot_count_spin.pack(side=tk.LEFT)
        self.slot_count_var.trace_add("write", lambda *a: self._on_slot_count_change())
        ToolTip(self.slot_count_spin, "Number of texture slots inherited from the base class", bg=self._colors["tooltip_bg"], fg=self._colors["tooltip_fg"])

        # Hidden selections (new item mode)
        self.selections_frame = ttk.LabelFrame(frame, text="hiddenSelections[]", padding=4)
        self.selections_frame.pack(fill=tk.BOTH, expand=True, pady=(8, 0))

        sel_toolbar = ttk.Frame(self.selections_frame)
        sel_toolbar.pack(fill=tk.X, pady=(0, 4))
        ttk.Button(sel_toolbar, text="+ Add Slot", command=self._add_selection).pack(side=tk.LEFT, padx=2)
        ttk.Button(sel_toolbar, text="- Remove Last", command=self._remove_selection).pack(side=tk.LEFT, padx=2)

        self.selections_list_frame = ttk.Frame(self.selections_frame)
        self.selections_list_frame.pack(fill=tk.BOTH, expand=True)
        self._selection_vars = []

        # Materials (new item mode)
        self.materials_frame = ttk.LabelFrame(frame, text="hiddenSelectionsMaterials[] (.rvmat)", padding=4)
        self.materials_frame.pack(fill=tk.BOTH, expand=True, pady=(8, 0))

        mat_toolbar = ttk.Frame(self.materials_frame)
        mat_toolbar.pack(fill=tk.X, pady=(0, 4))
        ttk.Button(mat_toolbar, text="+ Add Material", command=self._add_material).pack(side=tk.LEFT, padx=2)
        ttk.Button(mat_toolbar, text="- Remove Last", command=self._remove_material).pack(side=tk.LEFT, padx=2)

        self.materials_list_frame = ttk.Frame(self.materials_frame)
        self.materials_list_frame.pack(fill=tk.BOTH, expand=True)
        self._material_vars = []

    # ── Textures Tab ──────────────────────────────────────────────────────

    def _build_textures_tab(self):
        frame = ttk.Frame(self.editor_notebook, padding=8)
        self.editor_notebook.add(frame, text="Textures")

        ttk.Label(frame, text="hiddenSelectionsTextures[] (.paa)", style="Section.TLabel").pack(anchor=tk.W, pady=(0, 4))
        ttk.Label(frame, text="One texture path per hidden selection slot.", style="Subtitle.TLabel").pack(anchor=tk.W, pady=(0, 8))

        self.textures_list_frame = ttk.Frame(frame)
        self.textures_list_frame.pack(fill=tk.BOTH, expand=True)
        self._texture_vars = []

    # ── Inventory Tab ─────────────────────────────────────────────────────

    def _build_inventory_tab(self):
        frame = ttk.Frame(self.editor_notebook, padding=8)
        self.editor_notebook.add(frame, text="Inventory")
        self._inv_frame = frame

        self.inv_note_label = ttk.Label(frame, text="(Inventory properties are only used in New Item mode)",
                                        style="Subtitle.TLabel")
        self.inv_note_label.pack(anchor=tk.W, pady=(0, 8))

        # Use grid layout for perfect column alignment
        field_grid = ttk.Frame(frame)
        field_grid.pack(fill=tk.X)
        field_grid.columnconfigure(1, weight=1)

        _row = 0
        # Item size
        ttk.Label(field_grid, text="itemSize[]:").grid(row=_row, column=0, sticky=tk.W, pady=2)
        size_frame = ttk.Frame(field_grid)
        size_frame.grid(row=_row, column=1, sticky=tk.W, pady=2, padx=(8, 0))
        self.item_size_w_var = tk.IntVar(value=1)
        ttk.Spinbox(size_frame, from_=1, to=20, textvariable=self.item_size_w_var, width=5).pack(side=tk.LEFT, padx=(0, 2))
        ttk.Label(size_frame, text="x").pack(side=tk.LEFT)
        self.item_size_h_var = tk.IntVar(value=1)
        ttk.Spinbox(size_frame, from_=1, to=20, textvariable=self.item_size_h_var, width=5).pack(side=tk.LEFT, padx=(2, 0))
        self.item_size_w_var.trace_add("write", lambda *a: self._on_field_change())
        self.item_size_h_var.trace_add("write", lambda *a: self._on_field_change())

        _row += 1
        # Weight
        ttk.Label(field_grid, text="weight:").grid(row=_row, column=0, sticky=tk.W, pady=2)
        wt_frame = ttk.Frame(field_grid)
        wt_frame.grid(row=_row, column=1, sticky=tk.W, pady=2, padx=(8, 0))
        self.weight_var = tk.IntVar(value=0)
        ttk.Spinbox(wt_frame, from_=0, to=100000, textvariable=self.weight_var, width=8).pack(side=tk.LEFT)
        ttk.Label(wt_frame, text="(grams)", style="Subtitle.TLabel").pack(side=tk.LEFT, padx=(4, 0))
        self.weight_var.trace_add("write", lambda *a: self._on_field_change())

        _row += 1
        # Absorbency
        ttk.Label(field_grid, text="absorbency:").grid(row=_row, column=0, sticky=tk.W, pady=2)
        self.absorbency_var = tk.DoubleVar(value=0.0)
        ttk.Spinbox(field_grid, from_=0.0, to=1.0, increment=0.1, textvariable=self.absorbency_var, width=5).grid(row=_row, column=1, sticky=tk.W, pady=2, padx=(8, 0))
        self.absorbency_var.trace_add("write", lambda *a: self._on_field_change())

        _row += 1
        # Cargo size
        ttk.Label(field_grid, text="itemsCargoSize[]:").grid(row=_row, column=0, sticky=tk.W, pady=2)
        cargo_frame = ttk.Frame(field_grid)
        cargo_frame.grid(row=_row, column=1, sticky=tk.W, pady=2, padx=(8, 0))
        self.cargo_w_var = tk.IntVar(value=0)
        ttk.Spinbox(cargo_frame, from_=0, to=50, textvariable=self.cargo_w_var, width=5).pack(side=tk.LEFT, padx=(0, 2))
        ttk.Label(cargo_frame, text="x").pack(side=tk.LEFT)
        self.cargo_h_var = tk.IntVar(value=0)
        ttk.Spinbox(cargo_frame, from_=0, to=50, textvariable=self.cargo_h_var, width=5).pack(side=tk.LEFT, padx=(2, 0))
        ttk.Label(cargo_frame, text="(0 = no cargo)", style="Subtitle.TLabel").pack(side=tk.LEFT, padx=(4, 0))
        self.cargo_w_var.trace_add("write", lambda *a: self._on_field_change())
        self.cargo_h_var.trace_add("write", lambda *a: self._on_field_change())

        _row += 1
        # Rotation flags
        ttk.Label(field_grid, text="rotationFlags:").grid(row=_row, column=0, sticky=tk.W, pady=2)
        self.rotation_var = tk.IntVar(value=0)
        rot_combo = ttk.Combobox(field_grid, textvariable=self.rotation_var,
                                  values=[0, 1, 2, 4, 8, 12, 16], width=5, state="readonly")
        rot_combo.grid(row=_row, column=1, sticky=tk.W, pady=2, padx=(8, 0))
        self.rotation_var.trace_add("write", lambda *a: self._on_field_change())

        # varQuantity
        qty_frame = ttk.LabelFrame(frame, text="Quantity (0 = disabled)", padding=4)
        qty_frame.pack(fill=tk.X, pady=(8, 0))

        row = ttk.Frame(qty_frame)
        row.pack(fill=tk.X, pady=2)
        ttk.Label(row, text="Init:").pack(side=tk.LEFT, padx=(0, 4))
        self.qty_init_var = tk.IntVar(value=0)
        ttk.Spinbox(row, from_=0, to=10000, textvariable=self.qty_init_var, width=6).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Label(row, text="Min:").pack(side=tk.LEFT, padx=(0, 4))
        self.qty_min_var = tk.IntVar(value=0)
        ttk.Spinbox(row, from_=0, to=10000, textvariable=self.qty_min_var, width=6).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Label(row, text="Max:").pack(side=tk.LEFT, padx=(0, 4))
        self.qty_max_var = tk.IntVar(value=0)
        ttk.Spinbox(row, from_=0, to=10000, textvariable=self.qty_max_var, width=6).pack(side=tk.LEFT)
        self.qty_init_var.trace_add("write", lambda *a: self._on_field_change())
        self.qty_min_var.trace_add("write", lambda *a: self._on_field_change())
        self.qty_max_var.trace_add("write", lambda *a: self._on_field_change())

        # Attachments
        att_frame = ttk.LabelFrame(frame, text="attachments[]", padding=4)
        att_frame.pack(fill=tk.BOTH, expand=True, pady=(8, 0))

        att_toolbar = ttk.Frame(att_frame)
        att_toolbar.pack(fill=tk.X, pady=(0, 4))
        ttk.Button(att_toolbar, text="+ Add", command=self._add_attachment).pack(side=tk.LEFT, padx=2)
        ttk.Button(att_toolbar, text="- Remove Last", command=self._remove_attachment).pack(side=tk.LEFT, padx=2)

        self.attachments_list_frame = ttk.Frame(att_frame)
        self.attachments_list_frame.pack(fill=tk.BOTH, expand=True)
        self._attachment_vars = []

    # ── Types.xml Tab ─────────────────────────────────────────────────────

    def _build_types_tab(self):
        frame = ttk.Frame(self.editor_notebook, padding=8)
        self.editor_notebook.add(frame, text="Types.xml")

        ttk.Label(frame, text="Types.xml Settings", style="Section.TLabel").pack(anchor=tk.W, pady=(0, 8))

        _lbl_w = 10  # uniform label width for types tab

        # Nominal
        row = ttk.Frame(frame)
        row.pack(fill=tk.X, pady=2)
        ttk.Label(row, text="nominal:", width=_lbl_w).pack(side=tk.LEFT)
        self.types_nominal_var = tk.IntVar(value=10)
        ttk.Spinbox(row, from_=0, to=1000, textvariable=self.types_nominal_var, width=6).pack(side=tk.LEFT)
        self.types_nominal_var.trace_add("write", lambda *a: self._on_field_change())

        # Min
        row = ttk.Frame(frame)
        row.pack(fill=tk.X, pady=2)
        ttk.Label(row, text="min:", width=_lbl_w).pack(side=tk.LEFT)
        self.types_min_var = tk.IntVar(value=5)
        ttk.Spinbox(row, from_=0, to=1000, textvariable=self.types_min_var, width=6).pack(side=tk.LEFT)
        self.types_min_var.trace_add("write", lambda *a: self._on_field_change())

        # Lifetime
        row = ttk.Frame(frame)
        row.pack(fill=tk.X, pady=2)
        ttk.Label(row, text="lifetime:", width=_lbl_w).pack(side=tk.LEFT)
        self.types_lifetime_var = tk.IntVar(value=14400)
        ttk.Spinbox(row, from_=0, to=999999, textvariable=self.types_lifetime_var, width=8).pack(side=tk.LEFT)
        ttk.Label(row, text="(seconds)", style="Subtitle.TLabel").pack(side=tk.LEFT, padx=(4, 0))
        self.types_lifetime_var.trace_add("write", lambda *a: self._on_field_change())

        # Restock
        row = ttk.Frame(frame)
        row.pack(fill=tk.X, pady=2)
        ttk.Label(row, text="restock:", width=_lbl_w).pack(side=tk.LEFT)
        self.types_restock_var = tk.IntVar(value=0)
        ttk.Spinbox(row, from_=0, to=999999, textvariable=self.types_restock_var, width=8).pack(side=tk.LEFT)
        self.types_restock_var.trace_add("write", lambda *a: self._on_field_change())

        # Cost
        row = ttk.Frame(frame)
        row.pack(fill=tk.X, pady=2)
        ttk.Label(row, text="cost:", width=_lbl_w).pack(side=tk.LEFT)
        self.types_cost_var = tk.IntVar(value=100)
        ttk.Spinbox(row, from_=0, to=10000, textvariable=self.types_cost_var, width=6).pack(side=tk.LEFT)
        self.types_cost_var.trace_add("write", lambda *a: self._on_field_change())

        # Category
        row = ttk.Frame(frame)
        row.pack(fill=tk.X, pady=2)
        ttk.Label(row, text="category:", width=_lbl_w).pack(side=tk.LEFT)
        self.types_category_var = tk.StringVar(value="tools")
        ttk.Combobox(row, textvariable=self.types_category_var, values=TYPES_CATEGORIES,
                     width=12, state="readonly").pack(side=tk.LEFT)
        self.types_category_var.trace_add("write", lambda *a: self._on_field_change())

        # Usage
        row = ttk.Frame(frame)
        row.pack(fill=tk.X, pady=2)
        ttk.Label(row, text="usage:", width=_lbl_w).pack(side=tk.LEFT)
        self.types_usage_var = tk.StringVar(value="Town")
        ttk.Combobox(row, textvariable=self.types_usage_var, values=TYPES_USAGES,
                     width=15, state="readonly").pack(side=tk.LEFT)
        self.types_usage_var.trace_add("write", lambda *a: self._on_field_change())

    # ── Dynamic Row Helpers ───────────────────────────────────────────────

    def _add_dynamic_row(self, parent_frame, var_list, label_prefix="", browse_filetypes=None):
        """Add a dynamic entry row to a frame."""
        row = ttk.Frame(parent_frame)
        row.pack(fill=tk.X, pady=1)

        idx = len(var_list)
        if label_prefix:
            ttk.Label(row, text=f"{label_prefix} {idx}:", width=10).pack(side=tk.LEFT, padx=(0, 4))

        var = tk.StringVar()
        entry = ttk.Entry(row, textvariable=var)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))
        var.trace_add("write", lambda *a: self._on_field_change())

        if browse_filetypes:
            def do_browse(v=var, ft=browse_filetypes):
                path = filedialog.askopenfilename(title="Select file", filetypes=ft)
                if path:
                    v.set(path)
            ttk.Button(row, text="...", width=3, command=do_browse).pack(side=tk.RIGHT)

        var_list.append(var)
        row._dynamic_var = var
        return var

    def _remove_dynamic_row(self, parent_frame, var_list):
        """Remove the last dynamic row from a frame."""
        children = parent_frame.winfo_children()
        if children and var_list:
            children[-1].destroy()
            var_list.pop()
            self._on_field_change()

    def _clear_dynamic_rows(self, parent_frame, var_list):
        """Remove all dynamic rows."""
        for child in parent_frame.winfo_children():
            child.destroy()
        var_list.clear()

    # Selection rows
    def _add_selection(self):
        self._add_dynamic_row(self.selections_list_frame, self._selection_vars, "Slot")
        self._sync_texture_rows()

    def _remove_selection(self):
        self._remove_dynamic_row(self.selections_list_frame, self._selection_vars)
        self._sync_texture_rows()

    # Material rows
    def _add_material(self):
        self._add_dynamic_row(self.materials_list_frame, self._material_vars, "Mat",
                              [("RVMAT Files", "*.rvmat"), ("All Files", "*.*")])

    def _remove_material(self):
        self._remove_dynamic_row(self.materials_list_frame, self._material_vars)

    # Texture rows
    def _sync_texture_rows(self):
        """Sync texture rows to match the number of hidden selections or slot count."""
        if self._suppress_traces:
            return
        if self.mode_var.get() == "new_item":
            target_count = len(self._selection_vars)
        else:
            try:
                target_count = self.slot_count_var.get()
            except (tk.TclError, ValueError):
                target_count = 1

        # Save existing values
        existing_values = [v.get() for v in self._texture_vars]

        self._clear_dynamic_rows(self.textures_list_frame, self._texture_vars)

        for i in range(target_count):
            if self.mode_var.get() == "new_item" and i < len(self._selection_vars):
                label = self._selection_vars[i].get() or f"Slot {i}"
            else:
                label = f"Slot {i}"
            var = self._add_dynamic_row(self.textures_list_frame, self._texture_vars, label,
                                         [("PAA Textures", "*.paa"), ("All Files", "*.*")])
            if i < len(existing_values):
                var.set(existing_values[i])

    # Attachment rows
    def _add_attachment(self):
        self._add_dynamic_row(self.attachments_list_frame, self._attachment_vars, "Slot")

    def _remove_attachment(self):
        self._remove_dynamic_row(self.attachments_list_frame, self._attachment_vars)

    # ── Model Browse ──────────────────────────────────────────────────────

    def _browse_model(self):
        path = filedialog.askopenfilename(
            title="Select .p3d model file",
            filetypes=[("P3D Models", "*.p3d"), ("All Files", "*.*")]
        )
        if path:
            self.model_path_var.set(path)

    # ── Mode Change ───────────────────────────────────────────────────────

    def _on_mode_change(self):
        mode = self.mode_var.get()
        is_new = mode == "new_item"

        # Unpack all mode-dependent widgets in the model tab, then repack in order
        self.slot_count_frame.pack_forget()
        self.selections_frame.pack_forget()
        self.materials_frame.pack_forget()

        if is_new:
            self.selections_frame.pack(fill=tk.BOTH, expand=True, pady=(8, 0),
                                        in_=self._model_tab_frame)
            self.materials_frame.pack(fill=tk.BOTH, expand=True, pady=(8, 0),
                                      in_=self._model_tab_frame)
        else:
            self.slot_count_frame.pack(fill=tk.X, pady=2, in_=self._model_tab_frame)

        # Enable/disable inventory tab widgets
        self.inv_note_label.configure(
            text="" if is_new else "(Inventory properties are only used in New Item mode)"
        )

        self._sync_texture_rows()
        self._on_field_change()

    # ── Slot Count Change ─────────────────────────────────────────────────

    def _on_slot_count_change(self, *args):
        if self.mode_var.get() == "model_swap":
            self._sync_texture_rows()

    # ── Base Class Change ─────────────────────────────────────────────────

    def _on_base_class_change(self, event=None):
        val = self.base_class_var.get()
        if val == "Custom...":
            custom = simpledialog.askstring("Custom Base Class",
                                                "Enter base class name:",
                                                parent=self.root)
            if custom and re.match(r'^[A-Za-z_]\w*$', custom):
                self.base_class_var.set(custom)
            else:
                self.base_class_var.set("Inventory_Base")
                if custom:
                    messagebox.showwarning("Invalid Name", "Base class must be a valid C++ identifier.")
                return

        if val in BASE_CLASSES:
            info = BASE_CLASSES[val]
            self.base_desc_label.configure(text=info["description"])
            self.addons_var.set(", ".join(info["required_addons"]))
            if self._autofill_enabled.get():
                defaults = info.get("defaults", {})
                if defaults:
                    self._apply_base_class_defaults(defaults)
        else:
            self.base_desc_label.configure(text="Custom class")

    def _apply_base_class_defaults(self, defaults):
        """Apply base class defaults only to fields still at their ItemDefinition defaults."""
        ref = ItemDefinition()
        field_var_map = {
            "item_size_w": (self.item_size_w_var, ref.item_size_w),
            "item_size_h": (self.item_size_h_var, ref.item_size_h),
            "weight": (self.weight_var, ref.weight),
            "absorbency": (self.absorbency_var, ref.absorbency),
            "cargo_size_w": (self.cargo_w_var, ref.cargo_size_w),
            "cargo_size_h": (self.cargo_h_var, ref.cargo_size_h),
            "types_nominal": (self.types_nominal_var, ref.types_nominal),
            "types_min": (self.types_min_var, ref.types_min),
            "types_lifetime": (self.types_lifetime_var, ref.types_lifetime),
            "types_restock": (self.types_restock_var, ref.types_restock),
            "types_cost": (self.types_cost_var, ref.types_cost),
            "types_category": (self.types_category_var, ref.types_category),
            "types_usage": (self.types_usage_var, ref.types_usage),
        }
        self._suppress_traces = True
        for field_name, new_value in defaults.items():
            if field_name in field_var_map:
                tk_var, default_value = field_var_map[field_name]
                try:
                    current = tk_var.get()
                except (tk.TclError, ValueError):
                    current = default_value
                if current == default_value:
                    tk_var.set(new_value)
        self._suppress_traces = False
        self._on_field_change()

    # ── Field Change Handler ──────────────────────────────────────────────

    def _on_field_change(self):
        """Called when any editor field changes. Saves to current item and updates preview."""
        if self._suppress_traces:
            return
        self._save_current_to_item()
        self._refresh_item_tree()
        self._schedule_preview()

    # ── Item List Management ──────────────────────────────────────────────

    def _add_item(self):
        item = ItemDefinition()
        item.class_name = f"NewItem_{len(self.items) + 1}"
        item.display_name = f"New Item {len(self.items) + 1}"
        self.items.append(item)
        self._refresh_item_tree()
        # Select the new item
        children = self.item_tree.get_children()
        if children:
            self.item_tree.selection_set(children[-1])
            self.item_tree.focus(children[-1])

    def _duplicate_item(self):
        if self._selected_index < 0 or self._selected_index >= len(self.items):
            return
        original = self.items[self._selected_index]
        dupe = ItemDefinition.from_dict(original.to_dict())
        dupe.class_name = original.class_name + "_Copy"
        dupe.display_name = original.display_name + " (Copy)"
        self.items.append(dupe)
        self._refresh_item_tree()
        children = self.item_tree.get_children()
        if children:
            self.item_tree.selection_set(children[-1])
            self.item_tree.focus(children[-1])

    def _remove_item(self):
        if self._selected_index < 0 or self._selected_index >= len(self.items):
            return
        self.items.pop(self._selected_index)
        self._selected_index = -1
        self._refresh_item_tree()
        self._clear_editor()
        self._schedule_preview()

    def _refresh_item_tree(self):
        """Refresh the item list treeview."""
        # Save current selection
        sel = self.item_tree.selection()
        sel_iid = sel[0] if sel else None

        self.item_tree.delete(*self.item_tree.get_children())
        for i, item in enumerate(self.items):
            mode_label = "Swap" if item.mode == "model_swap" else "New"
            iid = self.item_tree.insert("", tk.END, values=(mode_label, item.class_name, item.base_class))
            if sel_iid and i == self._selected_index:
                self.item_tree.selection_set(iid)
                self.item_tree.focus(iid)

    def _on_item_select(self, event=None):
        sel = self.item_tree.selection()
        if not sel:
            self._selected_index = -1
            return
        idx = self.item_tree.index(sel[0])
        if idx == self._selected_index:
            return
        self._selected_index = idx
        self._load_item_to_editor(self.items[idx])

    # ── Editor <-> Item Sync ──────────────────────────────────────────────

    def _save_current_to_item(self):
        """Save current editor state to the selected ItemDefinition."""
        if self._selected_index < 0 or self._selected_index >= len(self.items):
            return
        item = self.items[self._selected_index]

        item.mode = self.mode_var.get()
        item.class_name = self.class_name_var.get()
        item.base_class = self.base_class_var.get()
        item.display_name = self.display_name_var.get()
        item.description = self.desc_var.get()
        item.model_path = self.model_path_var.get()

        # Parse addons
        addons_str = self.addons_var.get()
        item.required_addons = [a.strip() for a in addons_str.split(",") if a.strip()]

        # Hidden selections
        item.hidden_selections = [v.get() for v in self._selection_vars if v.get()]
        item.hidden_selections_textures = [v.get() for v in self._texture_vars]
        item.hidden_selections_materials = [v.get() for v in self._material_vars if v.get()]

        try:
            item.texture_slot_count = self.slot_count_var.get()
        except (tk.TclError, ValueError):
            item.texture_slot_count = 1

        # Inventory
        try:
            item.item_size_w = self.item_size_w_var.get()
        except (tk.TclError, ValueError):
            item.item_size_w = 1
        try:
            item.item_size_h = self.item_size_h_var.get()
        except (tk.TclError, ValueError):
            item.item_size_h = 1
        try:
            item.weight = self.weight_var.get()
        except (tk.TclError, ValueError):
            item.weight = 0
        try:
            item.absorbency = self.absorbency_var.get()
        except (tk.TclError, ValueError):
            item.absorbency = 0.0
        try:
            item.cargo_size_w = self.cargo_w_var.get()
        except (tk.TclError, ValueError):
            item.cargo_size_w = 0
        try:
            item.cargo_size_h = self.cargo_h_var.get()
        except (tk.TclError, ValueError):
            item.cargo_size_h = 0
        try:
            item.rotation_flags = self.rotation_var.get()
        except (tk.TclError, ValueError):
            item.rotation_flags = 0
        try:
            item.var_quantity_init = self.qty_init_var.get()
        except (tk.TclError, ValueError):
            item.var_quantity_init = 0
        try:
            item.var_quantity_min = self.qty_min_var.get()
        except (tk.TclError, ValueError):
            item.var_quantity_min = 0
        try:
            item.var_quantity_max = self.qty_max_var.get()
        except (tk.TclError, ValueError):
            item.var_quantity_max = 0

        item.attachments = [v.get() for v in self._attachment_vars if v.get()]

        # Types.xml
        try:
            item.types_nominal = self.types_nominal_var.get()
        except (tk.TclError, ValueError):
            pass
        try:
            item.types_min = self.types_min_var.get()
        except (tk.TclError, ValueError):
            pass
        try:
            item.types_lifetime = self.types_lifetime_var.get()
        except (tk.TclError, ValueError):
            pass
        try:
            item.types_restock = self.types_restock_var.get()
        except (tk.TclError, ValueError):
            pass
        try:
            item.types_cost = self.types_cost_var.get()
        except (tk.TclError, ValueError):
            pass
        item.types_category = self.types_category_var.get()
        item.types_usage = self.types_usage_var.get()

    def _load_item_to_editor(self, item):
        """Load an ItemDefinition into the editor fields."""
        self._suppress_traces = True

        self.mode_var.set(item.mode)
        self.class_name_var.set(item.class_name)
        self.base_class_var.set(item.base_class)
        self.display_name_var.set(item.display_name)
        self.desc_var.set(item.description)
        self.model_path_var.set(item.model_path)
        self.addons_var.set(", ".join(item.required_addons))
        self.slot_count_var.set(item.texture_slot_count)

        # Update base class description
        if item.base_class in BASE_CLASSES:
            self.base_desc_label.configure(text=BASE_CLASSES[item.base_class]["description"])
        else:
            self.base_desc_label.configure(text="Custom class")

        # Hidden selections
        self._clear_dynamic_rows(self.selections_list_frame, self._selection_vars)
        for sel in item.hidden_selections:
            var = self._add_dynamic_row(self.selections_list_frame, self._selection_vars, "Slot")
            var.set(sel)

        # Materials
        self._clear_dynamic_rows(self.materials_list_frame, self._material_vars)
        for mat in item.hidden_selections_materials:
            var = self._add_dynamic_row(self.materials_list_frame, self._material_vars, "Mat",
                                         [("RVMAT Files", "*.rvmat"), ("All Files", "*.*")])
            var.set(mat)

        # Textures — must sync after selections are loaded
        self._suppress_traces = False
        self._sync_texture_rows()
        self._suppress_traces = True
        for i, tex in enumerate(item.hidden_selections_textures):
            if i < len(self._texture_vars):
                self._texture_vars[i].set(tex)

        # Inventory
        self.item_size_w_var.set(item.item_size_w)
        self.item_size_h_var.set(item.item_size_h)
        self.weight_var.set(item.weight)
        self.absorbency_var.set(item.absorbency)
        self.cargo_w_var.set(item.cargo_size_w)
        self.cargo_h_var.set(item.cargo_size_h)
        self.rotation_var.set(item.rotation_flags)
        self.qty_init_var.set(item.var_quantity_init)
        self.qty_min_var.set(item.var_quantity_min)
        self.qty_max_var.set(item.var_quantity_max)

        # Attachments
        self._clear_dynamic_rows(self.attachments_list_frame, self._attachment_vars)
        for att in item.attachments:
            var = self._add_dynamic_row(self.attachments_list_frame, self._attachment_vars, "Slot")
            var.set(att)

        # Types.xml
        self.types_nominal_var.set(item.types_nominal)
        self.types_min_var.set(item.types_min)
        self.types_lifetime_var.set(item.types_lifetime)
        self.types_restock_var.set(item.types_restock)
        self.types_cost_var.set(item.types_cost)
        self.types_category_var.set(item.types_category)
        self.types_usage_var.set(item.types_usage)

        self._suppress_traces = False
        self._on_mode_change()
        self._schedule_preview()

    def _clear_editor(self):
        """Clear all editor fields."""
        self._suppress_traces = True
        self.mode_var.set("model_swap")
        self.class_name_var.set("")
        self.base_class_var.set("Inventory_Base")
        self.display_name_var.set("")
        self.desc_var.set("")
        self.model_path_var.set("")
        self.addons_var.set("DZ_Data")
        self.slot_count_var.set(1)
        self.base_desc_label.configure(text="Generic item")
        self._clear_dynamic_rows(self.selections_list_frame, self._selection_vars)
        self._clear_dynamic_rows(self.materials_list_frame, self._material_vars)
        self._clear_dynamic_rows(self.textures_list_frame, self._texture_vars)
        self._clear_dynamic_rows(self.attachments_list_frame, self._attachment_vars)
        self.item_size_w_var.set(1)
        self.item_size_h_var.set(1)
        self.weight_var.set(0)
        self.absorbency_var.set(0.0)
        self.cargo_w_var.set(0)
        self.cargo_h_var.set(0)
        self.rotation_var.set(0)
        self.qty_init_var.set(0)
        self.qty_min_var.set(0)
        self.qty_max_var.set(0)
        self.types_nominal_var.set(10)
        self.types_min_var.set(5)
        self.types_lifetime_var.set(14400)
        self.types_restock_var.set(0)
        self.types_cost_var.set(100)
        self.types_category_var.set("tools")
        self.types_usage_var.set("Town")
        self._suppress_traces = False

    # ── Live Preview ──────────────────────────────────────────────────────

    def _schedule_preview(self):
        """Schedule a debounced preview update."""
        if self._preview_after_id:
            self.root.after_cancel(self._preview_after_id)
        self._preview_after_id = self.root.after(150, self._update_preview)

    def _update_preview(self):
        """Regenerate the live preview."""
        self._preview_after_id = None

        if not self.items:
            self._set_preview_text("(No items. Click '+ Add Item' to get started.)")
            return

        # Generate config.cpp
        entries = []
        all_addons = {"DZ_Data"}
        for item in self.items:
            if not item.class_name:
                continue
            entry = generate_item_entry(item)
            entries.append(entry)
            for addon in item.required_addons:
                all_addons.add(addon)

        if not entries:
            self._set_preview_text("(No valid items to preview.)")
            return

        patch_name = self.patch_name_var.get() or "MyMod_CustomItems"
        config_text = generate_full_config(patch_name, all_addons, entries)

        # Add types.xml preview
        types_text = generate_types_xml(self.items)
        full_preview = config_text + "\n// ── types.xml ──\n\n" + types_text

        self._set_preview_text(full_preview)

    def _set_preview_text(self, text):
        self.preview_text.configure(state=tk.NORMAL)
        self.preview_text.delete("1.0", tk.END)
        self.preview_text.insert("1.0", text)
        self.preview_text.configure(state=tk.DISABLED)

    # ── Logging ───────────────────────────────────────────────────────────

    def _log(self, text):
        self.output_text.configure(state=tk.NORMAL)
        self.output_text.insert(tk.END, text + "\n")
        self.output_text.see(tk.END)
        self.output_text.configure(state=tk.DISABLED)

    def _clear_log(self):
        self.output_text.configure(state=tk.NORMAL)
        self.output_text.delete("1.0", tk.END)
        self.output_text.configure(state=tk.DISABLED)

    # ── Export ────────────────────────────────────────────────────────────

    def _export(self):
        if not self.items:
            messagebox.showwarning("No Items", "Add at least one item before exporting.")
            return

        # Validate
        errors = []
        for i, item in enumerate(self.items):
            if not item.class_name:
                errors.append(f"Item {i + 1}: Class name is required.")
            elif not re.match(r'^[A-Za-z_]\w*$', item.class_name):
                errors.append(f"Item {i + 1}: '{item.class_name}' is not a valid C++ identifier.")
            if not item.model_path:
                errors.append(f"Item {i + 1}: Model path is required.")
            if not item.display_name:
                errors.append(f"Item {i + 1}: Display name is required.")
        if errors:
            messagebox.showerror("Validation Errors", "\n".join(errors))
            return

        # Ask where to save
        config_path = filedialog.asksaveasfilename(
            title="Save config.cpp",
            defaultextension=".cpp",
            filetypes=[("Config Files", "*.cpp"), ("All Files", "*.*")],
            initialfile="config.cpp",
        )
        if not config_path:
            return

        # Generate
        entries = []
        all_addons = {"DZ_Data"}
        for item in self.items:
            if not item.class_name:
                continue
            entries.append(generate_item_entry(item))
            for addon in item.required_addons:
                all_addons.add(addon)

        patch_name = self.patch_name_var.get() or "MyMod_CustomItems"
        config_text = generate_full_config(patch_name, all_addons, entries)

        self._clear_log()

        # Write config.cpp
        try:
            with open(config_path, "w", encoding="utf-8") as f:
                f.write(config_text)
            self._log(f"Wrote config.cpp: {config_path}")
        except OSError as e:
            self._log(f"ERROR writing config.cpp: {e}")
            return

        # Write types.xml alongside
        types_path = os.path.join(os.path.dirname(config_path), "types.xml")
        types_text = generate_types_xml(self.items)
        try:
            with open(types_path, "w", encoding="utf-8") as f:
                f.write(types_text)
            self._log(f"Wrote types.xml: {types_path}")
        except OSError as e:
            self._log(f"ERROR writing types.xml: {e}")

        self._log(f"Exported {len(entries)} item(s) successfully.")

    # ── Import Config ─────────────────────────────────────────────────────

    def _import_config(self):
        path = filedialog.askopenfilename(
            title="Import config.cpp",
            filetypes=[("Config Files", "*.cpp"), ("All Files", "*.*")],
        )
        if not path:
            return

        imported = parse_config_for_import(path)
        if not imported:
            messagebox.showinfo("No Items Found", "No class definitions found in the selected config.cpp.")
            return

        self.items.extend(imported)
        self._refresh_item_tree()
        self._schedule_preview()
        self._log(f"Imported {len(imported)} item(s) from {os.path.basename(path)}.")

        # Select first imported item
        children = self.item_tree.get_children()
        if children:
            target = children[len(children) - len(imported)]
            self.item_tree.selection_set(target)
            self.item_tree.focus(target)

    # ── Scan Folder ────────────────────────────────────────────────────────

    def _scan_folder(self):
        folder = filedialog.askdirectory(title="Select Mod Folder to Scan")
        if not folder:
            return

        scanned = scan_folder_for_p3d(folder)
        if not scanned:
            messagebox.showinfo("No Models Found", "No .p3d files were found in the selected folder.")
            return

        # Deduplicate against existing items
        existing_names = {item.class_name for item in self.items}
        for item in scanned:
            base_name = item.class_name
            counter = 2
            while item.class_name in existing_names:
                item.class_name = f"{base_name}_{counter}"
                counter += 1
            existing_names.add(item.class_name)

        n_new = sum(1 for i in scanned if i.mode == "new_item")
        n_swap = len(scanned) - n_new
        messagebox.showinfo("Scan Complete",
                            f"Found {len(scanned)} model(s):\n"
                            f"  {n_new} with textures/materials (new item mode)\n"
                            f"  {n_swap} without (model swap mode)")

        self.items.extend(scanned)
        self._refresh_item_tree()
        self._schedule_preview()
        self._log(f"Scanned folder: found {len(scanned)} .p3d model(s) in {os.path.basename(folder)}.")

        children = self.item_tree.get_children()
        if children:
            target = children[len(children) - len(scanned)]
            self.item_tree.selection_set(target)
            self.item_tree.focus(target)

    # ── Template Presets ──────────────────────────────────────────────────

    def _build_template_menu(self):
        c = self._colors
        self._template_menu = tk.Menu(self.root, tearoff=0,
                                       bg=c["btn_bg"], fg=c["fg"],
                                       activebackground=c["accent"],
                                       activeforeground=c["selected_fg"])
        for category, templates in TEMPLATE_PRESETS.items():
            submenu = tk.Menu(self._template_menu, tearoff=0,
                              bg=c["btn_bg"], fg=c["fg"],
                              activebackground=c["accent"],
                              activeforeground="#ffffff")
            for tmpl in templates:
                submenu.add_command(
                    label=tmpl["name"],
                    command=lambda t=tmpl: self._create_from_template(t)
                )
            self._template_menu.add_cascade(label=category, menu=submenu)

    def _show_template_menu(self):
        try:
            x = self._template_btn.winfo_rootx()
            y = self._template_btn.winfo_rooty() + self._template_btn.winfo_height()
            self._template_menu.tk_popup(x, y)
        finally:
            self._template_menu.grab_release()

    def _create_from_template(self, template):
        data = dict(template["data"])
        base_name = data.get("class_name", "TemplateItem")
        existing_names = {item.class_name for item in self.items}
        name = base_name
        counter = 2
        while name in existing_names:
            name = f"{base_name}_{counter}"
            counter += 1
        data["class_name"] = name

        item = ItemDefinition.from_dict(data)
        self.items.append(item)
        self._refresh_item_tree()
        self._schedule_preview()
        self._log(f"Created '{item.class_name}' from template: {template['name']}")

        children = self.item_tree.get_children()
        if children:
            self.item_tree.selection_set(children[-1])
            self.item_tree.focus(children[-1])

    # ── Session Save/Load ─────────────────────────────────────────────────

    def _save_session(self):
        if not self.items:
            messagebox.showwarning("No Items", "No items to save.")
            return

        path = filedialog.asksaveasfilename(
            title="Save Session",
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")],
            initialfile="model_session.json",
        )
        if not path:
            return

        session = {
            "patch_name": self.patch_name_var.get(),
            "items": [item.to_dict() for item in self.items],
        }
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(session, f, indent=2)
            self._log(f"Session saved: {path}")
        except OSError as e:
            self._log(f"ERROR saving session: {e}")

    def _load_session(self):
        path = filedialog.askopenfilename(
            title="Load Session",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")],
        )
        if not path:
            return

        try:
            with open(path, "r", encoding="utf-8") as f:
                session = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            messagebox.showerror("Load Error", f"Could not load session:\n{e}")
            return

        self.items = [ItemDefinition.from_dict(d) for d in session.get("items", [])]
        if session.get("patch_name"):
            self.patch_name_var.set(session["patch_name"])

        self._selected_index = -1
        self._refresh_item_tree()
        self._clear_editor()
        self._schedule_preview()
        self._log(f"Loaded {len(self.items)} item(s) from {os.path.basename(path)}.")

        # Select first item
        children = self.item_tree.get_children()
        if children:
            self.item_tree.selection_set(children[0])
            self.item_tree.focus(children[0])


# ─── Entry Point ──────────────────────────────────────────────────────────────

def main():
    root = tk.Tk()
    try:
        root.iconbitmap(default="")
    except Exception:
        pass
    app = ModelConfigApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
