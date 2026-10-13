"""
Icon loader and manager for FlowMorph Studio.
Provides high-DPI CTkImage instances for crisp rendering without any emojis.
"""

import sys
import os
from typing import Dict, Tuple, Optional
from PIL import Image
import customtkinter as ctk

# Base directory for assets (supports both source script and PyInstaller frozen executable)
if getattr(sys, "frozen", False):
    BASE_DIR = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ASSETS_DIR = os.path.join(BASE_DIR, "assets")
ICONS_DIR = os.path.join(ASSETS_DIR, "icons")
LOGO_PATH = os.path.join(ASSETS_DIR, "logo.png")

_ICON_CACHE: Dict[Tuple[str, int, int], ctk.CTkImage] = {}


def ensure_icons_exist() -> None:
    """Ensures icon files exist on disk, generating them if necessary."""
    if not os.path.exists(ICONS_DIR) or not os.path.exists(os.path.join(ICONS_DIR, "video.png")):
        from assets.generate_icons import generate_all
        generate_all()


def get_icon(name: str, size: Tuple[int, int] = (20, 20)) -> Optional[ctk.CTkImage]:
    """
    Retrieves a cached CTkImage for the specified icon name and pixel dimensions.
    Returns None if icon file cannot be loaded.
    """
    cache_key = (name, size[0], size[1])
    if cache_key in _ICON_CACHE:
        return _ICON_CACHE[cache_key]

    ensure_icons_exist()
    filename = f"{name}.png" if not name.endswith(".png") else name
    filepath = os.path.join(ICONS_DIR, filename)

    if not os.path.isfile(filepath):
        # Fallback to assets root if logo or special graphic
        filepath = os.path.join(ASSETS_DIR, filename)

    if not os.path.isfile(filepath):
        return None

    try:
        pil_img = Image.open(filepath)
        ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=size)
        _ICON_CACHE[cache_key] = ctk_img
        return ctk_img
    except Exception as e:
        print(f"Warning: Failed to load icon {name}: {e}")
        return None


def get_logo_image(size: Tuple[int, int] = (40, 40)) -> Optional[ctk.CTkImage]:
    """Returns the official brand logo as a CTkImage."""
    return get_icon("logo.png", size=size)
