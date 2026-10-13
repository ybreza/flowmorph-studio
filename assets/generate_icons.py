"""
Asset and Icon Generator for FlowMorph Studio.
Draws crisp, high-resolution vector-style icons rendered via Pillow supersampling.
Strictly adheres to brand styling: Electric Amber (#FD6700), Slate (#94A3B8), White (#FFFFFF).
No emojis are used anywhere in the application.
"""

import os
import math
from PIL import Image, ImageDraw

ICON_DIR = os.path.join(os.path.dirname(__file__), "icons")
os.makedirs(ICON_DIR, exist_ok=True)

# Brand Colors
BRAND_ORANGE = (253, 103, 0, 255)       # #FD6700
BRAND_ORANGE_HOVER = (255, 126, 36, 255) # #FF7E24
BRAND_WHITE = (248, 250, 252, 255)       # #F8FAFC
BRAND_MUTED = (148, 163, 184, 255)       # #94A3B8
BRAND_SUCCESS = (16, 185, 129, 255)      # #10B981
BRAND_DANGER = (239, 68, 68, 255)        # #EF4444


def create_canvas(size=64, scale=4):
    target = size * scale
    img = Image.new("RGBA", (target, target), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    return img, draw, target, scale


def export_icon(img, filename, size=64):
    out = img.resize((size, size), Image.Resampling.LANCZOS)
    filepath = os.path.join(ICON_DIR, filename)
    out.save(filepath, "PNG")
    return filepath


def generate_video_icon():
    img, draw, target, s = create_canvas()
    color = BRAND_ORANGE
    # Video film rectangle with rounded corners
    rect_box = [10 * s, 14 * s, 54 * s, 50 * s]
    draw.rounded_rectangle(rect_box, radius=6 * s, outline=color, width=3 * s)
    # Film sprockets / holes top and bottom
    for i in range(4):
        x = (14 + i * 10) * s
        draw.rectangle([x, 17 * s, x + 5 * s, 21 * s], fill=color)
        draw.rectangle([x, 43 * s, x + 5 * s, 47 * s], fill=color)
    # Center play triangle
    center_play = [(27 * s, 26 * s), (42 * s, 32 * s), (27 * s, 38 * s)]
    draw.polygon(center_play, fill=BRAND_WHITE)
    export_icon(img, "video.png")


def generate_folder_icon():
    img, draw, target, s = create_canvas()
    color = BRAND_WHITE
    # Folder tab and body
    draw.polygon([
        (10 * s, 20 * s), (26 * s, 20 * s), (31 * s, 26 * s),
        (54 * s, 26 * s), (54 * s, 48 * s), (10 * s, 48 * s)
    ], fill=(43, 50, 66, 255), outline=color, width=int(2.5 * s))
    # Front flap
    draw.polygon([
        (8 * s, 28 * s), (56 * s, 28 * s), (52 * s, 50 * s), (12 * s, 50 * s)
    ], fill=BRAND_ORANGE)
    export_icon(img, "folder.png")


def generate_play_icon():
    img, draw, target, s = create_canvas()
    # Crisp play triangle
    pts = [(20 * s, 14 * s), (50 * s, 32 * s), (20 * s, 50 * s)]
    draw.polygon(pts, fill=BRAND_WHITE)
    export_icon(img, "play.png")


def generate_stop_icon():
    img, draw, target, s = create_canvas()
    # Crisp rounded square
    box = [18 * s, 18 * s, 46 * s, 46 * s]
    draw.rounded_rectangle(box, radius=4 * s, fill=BRAND_DANGER)
    export_icon(img, "stop.png")


def generate_settings_icon():
    img, draw, target, s = create_canvas()
    color = BRAND_MUTED
    center = 32 * s
    r_outer = 22 * s
    r_inner = 15 * s
    r_hole = 7 * s
    # 8-tooth gear
    num_teeth = 8
    teeth_pts = []
    for i in range(num_teeth * 2):
        angle = i * (math.pi / num_teeth)
        radius = r_outer if i % 2 == 0 else r_inner
        x = center + radius * math.cos(angle)
        y = center + radius * math.sin(angle)
        teeth_pts.append((x, y))
    draw.polygon(teeth_pts, fill=color)
    # Inner hole
    draw.ellipse([center - r_hole, center - r_hole, center + r_hole, center + r_hole], fill=(0, 0, 0, 0))
    export_icon(img, "settings.png")


def generate_sliders_icon():
    img, draw, target, s = create_canvas()
    color = BRAND_ORANGE
    # 3 horizontal slider tracks with knobs
    y_tracks = [20 * s, 32 * s, 44 * s]
    knob_x = [26 * s, 42 * s, 22 * s]
    for y in y_tracks:
        draw.line([(12 * s, y), (52 * s, y)], fill=BRAND_MUTED, width=int(2.5 * s))
    for x, y in zip(knob_x, y_tracks):
        draw.ellipse([x - 5 * s, y - 5 * s, x + 5 * s, y + 5 * s], fill=color, outline=BRAND_WHITE, width=2 * s)
    export_icon(img, "sliders.png")


def generate_speed_icon():
    img, draw, target, s = create_canvas()
    color = BRAND_ORANGE
    # Speedometer arc
    arc_box = [12 * s, 14 * s, 52 * s, 54 * s]
    draw.arc(arc_box, start=140, end=400, fill=BRAND_MUTED, width=3 * s)
    # Center hub
    draw.ellipse([30 * s, 36 * s, 34 * s, 40 * s], fill=color)
    # Needle pointing towards top right (speed)
    draw.line([(32 * s, 38 * s), (46 * s, 22 * s)], fill=color, width=int(3.5 * s))
    export_icon(img, "speed.png")


def generate_check_icon():
    img, draw, target, s = create_canvas()
    # Circular green badge with white checkmark
    draw.ellipse([10 * s, 10 * s, 54 * s, 54 * s], fill=BRAND_SUCCESS)
    # Checkmark lines
    pts = [(22 * s, 32 * s), (29 * s, 40 * s), (44 * s, 24 * s)]
    draw.line(pts, fill=BRAND_WHITE, width=int(4.5 * s), joint="curve")
    export_icon(img, "check.png")


def generate_info_icon():
    img, draw, target, s = create_canvas()
    color = BRAND_MUTED
    # Circle outline
    draw.ellipse([12 * s, 12 * s, 52 * s, 52 * s], outline=color, width=3 * s)
    # Dot
    draw.ellipse([30 * s, 21 * s, 34 * s, 25 * s], fill=color)
    # Stem
    draw.line([(32 * s, 30 * s), (32 * s, 43 * s)], fill=color, width=int(3.5 * s))
    export_icon(img, "info.png")


def generate_refresh_icon():
    img, draw, target, s = create_canvas()
    color = BRAND_MUTED
    # Circular arrow arc
    box = [14 * s, 14 * s, 50 * s, 50 * s]
    draw.arc(box, start=45, end=300, fill=color, width=int(3.5 * s))
    # Arrow head at the end
    arrow = [(46 * s, 26 * s), (54 * s, 32 * s), (42 * s, 35 * s)]
    draw.polygon(arrow, fill=color)
    export_icon(img, "refresh.png")


def generate_external_icon():
    img, draw, target, s = create_canvas()
    color = BRAND_WHITE
    # Box outline with top-right gap
    draw.line([(34 * s, 18 * s), (16 * s, 18 * s), (16 * s, 48 * s), (46 * s, 48 * s), (46 * s, 30 * s)], fill=BRAND_MUTED, width=int(2.5 * s))
    # Arrow pointing top right
    draw.line([(28 * s, 36 * s), (48 * s, 16 * s)], fill=color, width=int(3 * s))
    draw.polygon([(48 * s, 14 * s), (36 * s, 14 * s), (48 * s, 26 * s)], fill=color)
    export_icon(img, "external.png")


def generate_cpu_icon():
    img, draw, target, s = create_canvas()
    color = BRAND_ORANGE
    # Central chip rectangle
    box = [18 * s, 18 * s, 46 * s, 46 * s]
    draw.rounded_rectangle(box, radius=3 * s, fill=(35, 40, 52, 255), outline=color, width=2 * s)
    # Inner core
    draw.rounded_rectangle([25 * s, 25 * s, 39 * s, 39 * s], radius=2 * s, fill=color)
    # Chip pins on sides
    for offset in [23 * s, 32 * s, 41 * s]:
        draw.line([(12 * s, offset), (18 * s, offset)], fill=BRAND_WHITE, width=2 * s)
        draw.line([(46 * s, offset), (52 * s, offset)], fill=BRAND_WHITE, width=2 * s)
        draw.line([(offset, 12 * s), (offset, 18 * s)], fill=BRAND_WHITE, width=2 * s)
        draw.line([(offset, 46 * s), (offset, 52 * s)], fill=BRAND_WHITE, width=2 * s)
    export_icon(img, "cpu.png")


def generate_threshold_icon():
    img, draw, target, s = create_canvas()
    color = BRAND_ORANGE
    # Wave line representing consistency / optical flow threshold
    pts = []
    for x_step in range(12 * s, 53 * s, s):
        x_norm = (x_step - 12 * s) / (40 * s)
        y = 32 * s - math.sin(x_norm * math.pi * 2) * 12 * s
        pts.append((x_step, y))
    draw.line(pts, fill=color, width=int(3.5 * s), joint="curve")
    # Horizontal threshold reference line
    draw.line([(12 * s, 32 * s), (52 * s, 32 * s)], fill=BRAND_MUTED, width=int(1.5 * s))
    export_icon(img, "threshold.png")


def generate_gpu_icon():
    img, draw, target, s = create_canvas()
    color = BRAND_ORANGE
    # PCIe expansion card representation
    draw.rounded_rectangle([12 * s, 18 * s, 52 * s, 46 * s], radius=3 * s, fill=(28, 32, 44, 255), outline=color, width=2 * s)
    # Fan circles
    for cx in [24 * s, 40 * s]:
        draw.ellipse([cx - 6 * s, 26 * s, cx + 6 * s, 38 * s], outline=BRAND_WHITE, width=int(1.5 * s))
        draw.ellipse([cx - 2 * s, 30 * s, cx + 2 * s, 34 * s], fill=color)
    # PCIe pins on bottom
    draw.rectangle([18 * s, 46 * s, 42 * s, 50 * s], fill=BRAND_WHITE)
    export_icon(img, "gpu.png")


def generate_audio_icon():
    img, draw, target, s = create_canvas()
    color = BRAND_ORANGE
    # Speaker cone
    draw.polygon([(16 * s, 26 * s), (24 * s, 26 * s), (34 * s, 18 * s), (34 * s, 46 * s), (24 * s, 38 * s), (16 * s, 38 * s)], fill=color)
    # Sound waves
    draw.arc([28 * s, 24 * s, 42 * s, 40 * s], start=300, end=60, fill=BRAND_WHITE, width=2 * s)
    draw.arc([32 * s, 18 * s, 50 * s, 46 * s], start=300, end=60, fill=BRAND_MUTED, width=2 * s)
    export_icon(img, "audio.png")


def generate_codec_icon():
    img, draw, target, s = create_canvas()
    color = BRAND_ORANGE
    # Binary / media chip
    draw.rounded_rectangle([14 * s, 16 * s, 50 * s, 48 * s], radius=4 * s, outline=color, width=2 * s)
    draw.line([(22 * s, 26 * s), (42 * s, 26 * s)], fill=BRAND_WHITE, width=2 * s)
    draw.line([(22 * s, 32 * s), (36 * s, 32 * s)], fill=BRAND_MUTED, width=2 * s)
    draw.line([(22 * s, 38 * s), (42 * s, 38 * s)], fill=color, width=2 * s)
    export_icon(img, "codec.png")


def generate_all():
    generate_video_icon()
    generate_folder_icon()
    generate_play_icon()
    generate_stop_icon()
    generate_settings_icon()
    generate_sliders_icon()
    generate_speed_icon()
    generate_check_icon()
    generate_info_icon()
    generate_refresh_icon()
    generate_external_icon()
    generate_cpu_icon()
    generate_gpu_icon()
    generate_audio_icon()
    generate_codec_icon()
    generate_threshold_icon()
    print("All icons generated successfully in:", ICON_DIR)


if __name__ == "__main__":
    generate_all()

