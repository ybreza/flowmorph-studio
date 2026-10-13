"""
Design tokens, color palette, and styling constants for FlowMorph Studio.
Harmonized with the official brand logo (Electric Amber #FD6700 / Dark Slate Obsidian).
"""

# Brand Primary Colors
COLOR_PRIMARY = "#FD6700"          # Vibrant Brand Amber
COLOR_PRIMARY_HOVER = "#FF7E24"    # Lighter Amber on hover
COLOR_PRIMARY_ACTIVE = "#E05A00"   # Deep Amber on press
COLOR_PRIMARY_SUBTLE = "#331E10"   # Translucent tint for badges

# Dark Surfaces & Backgrounds
COLOR_BG_ROOT = "#0C0E12"          # Main Window Background
COLOR_BG_CARD = "#151821"          # Elevated Card Background
COLOR_BG_CARD_ALT = "#1A1E29"      # Nested Card / Inner Input Surface
COLOR_BG_INPUT = "#1F2432"         # Text / Numeric Inputs

# Borders & Separators
COLOR_BORDER = "#283042"           # Subtle container borders
COLOR_BORDER_LIGHT = "#353F55"     # Highlighted borders
COLOR_BORDER_FOCUS = "#FD6700"     # Active / focused borders

# Typography
COLOR_TEXT_PRIMARY = "#FFFFFF"     # Crisp White Headings / Active Text
COLOR_TEXT_SECONDARY = "#94A3B8"   # Slate Muted / Subtitles / Hints
COLOR_TEXT_MUTED = "#64748B"       # Subtle timestamps / placeholders

# Semantic Indicators
COLOR_SUCCESS = "#10B981"          # Emerald Green (Completion)
COLOR_SUCCESS_HOVER = "#059669"
COLOR_DANGER = "#EF4444"           # Crimson Red (Cancel / Error)
COLOR_DANGER_HOVER = "#DC2626"
COLOR_WARNING = "#F59E0B"          # Amber (Warnings / Notices)
COLOR_INFO = "#38BDF8"             # Cyan (Informational pills)

# Typography Constants
FONT_FAMILY = "Segoe UI"
FONT_TITLE = (FONT_FAMILY, 18, "bold")
FONT_SUBTITLE = (FONT_FAMILY, 14, "bold")
FONT_SECTION = (FONT_FAMILY, 12, "bold")
FONT_BODY = (FONT_FAMILY, 11)
FONT_BODY_BOLD = (FONT_FAMILY, 11, "bold")
FONT_SMALL = (FONT_FAMILY, 9)
FONT_MONO = ("Consolas", 10)
FONT_METRIC_VALUE = (FONT_FAMILY, 16, "bold")
FONT_METRIC_LABEL = (FONT_FAMILY, 9)
