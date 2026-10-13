"""
Generates side-by-side demo comparison video and animated GIF for FlowMorph Studio README showcase.
"""

import os
import subprocess
import imageio_ffmpeg

def main():
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    os.makedirs("assets", exist_ok=True)
    
    input_video = "input/input.mp4"
    output_video = "output/2_input_interpolated_60fps.mp4"
    
    font_src = "C:/Windows/Fonts/segoeuib.ttf"
    if not os.path.exists(font_src):
        font_src = "C:/Windows/Fonts/arialbd.ttf"
    font_target = "assets/font.ttf"
    if not os.path.exists(font_target) and os.path.exists(font_src):
        import shutil
        shutil.copyfile(font_src, font_target)
    
    font_param = f"fontfile='{font_target}'" if os.path.exists(font_target) else ""

    # Filter complex:
    # 1. Trim 2.5s to 6.5s (4-second smooth motion window)
    # 2. Scale each side to 360x640
    # 3. Add 2px dark separator between left and right
    # 4. Draw stylish badges
    fp = (font_param + ":") if font_param else ""
    filter_base = (
        f"[0:v]trim=start=2.5:end=6.5,setpts=PTS-STARTPTS,scale=360:640,"
        f"pad=362:640:0:0:color=0x283042,"
        f"drawtext={fp}text='Original  24 FPS':fontcolor=white:fontsize=18:box=1:boxcolor=black@0.65:boxborderw=8:x=(360-text_w)/2:y=24[left];"
        f"[1:v]trim=start=2.5:end=6.5,setpts=PTS-STARTPTS,scale=360:640,"
        f"drawtext={fp}text='FlowMorph  60 FPS':fontcolor=0xFD6700:fontsize=18:box=1:boxcolor=black@0.65:boxborderw=8:x=(w-text_w)/2:y=24[right];"
        f"[left][right]hstack=inputs=2[v]"
    )

    # 1. Output MP4 comparison
    mp4_target = "assets/demo_comparison.mp4"
    print("Generating demo MP4:", mp4_target)
    cmd_mp4 = [
        ffmpeg, "-y",
        "-i", input_video,
        "-i", output_video,
        "-filter_complex", filter_base,
        "-map", "[v]",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-crf", "20",
        mp4_target
    ]
    subprocess.run(cmd_mp4, check=True)
    print(f"MP4 generated successfully: {os.path.getsize(mp4_target):,} bytes")

    # 2. Output GIF comparison (optimized for GitHub README)
    gif_target = "assets/demo_comparison.gif"
    print("Generating demo GIF:", gif_target)
    gif_filter = (
        filter_base + ";[v]fps=24,scale=544:-1:flags=lanczos,split[s0][s1];"
        "[s0]palettegen=max_colors=96:stats_mode=diff[p];"
        "[s1][p]paletteuse=dither=bayer:bayer_scale=3[out]"
    )
    cmd_gif = [
        ffmpeg, "-y",
        "-i", input_video,
        "-i", output_video,
        "-filter_complex", gif_filter,
        "-map", "[out]",
        gif_target
    ]
    subprocess.run(cmd_gif, check=True)
    print(f"GIF generated successfully: {os.path.getsize(gif_target):,} bytes")

if __name__ == "__main__":
    main()
