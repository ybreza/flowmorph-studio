"""
FlowMorph Studio: Next-Generation Optical Flow Video Frame Interpolator
Main application entry point.
"""

import sys
import argparse
import ctypes

# Enable Windows Hardware Per-Monitor DPI Awareness (eliminates window dragging lag & DWM blur)
if sys.platform == "win32":
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


def launch_gui():
    """Launches the modern desktop CustomTkinter GUI."""
    from gui import FlowMorphApp

    app = FlowMorphApp()
    app.mainloop()


def launch_cli(args):
    """Headless CLI mode for batch processing and automated pipelines."""
    import cv2
    from core import OpticalFlowFrameInterpolator

    preset_map = {
        "ultrafast": cv2.DISOPTICAL_FLOW_PRESET_ULTRAFAST,
        "fast": cv2.DISOPTICAL_FLOW_PRESET_FAST,
        "medium": cv2.DISOPTICAL_FLOW_PRESET_MEDIUM,
    }

    print(f"Starting FlowMorph CLI: {args.input} -> {args.output}")
    print(f"Target FPS: {args.fps} | Preset: {args.preset} | Consistency: {args.consistency_threshold}")
    print(f"Device: {args.device.upper()} | Codec: {args.codec.upper()} | CRF: {args.crf} | Audio: {args.preserve_audio}")

    interpolator = OpticalFlowFrameInterpolator(
        target_fps=args.fps,
        flow_preset=preset_map[args.preset],
        consistency_threshold=args.consistency_threshold,
    )

    encoder_cfg = {
        "device": args.device,
        "codec": args.codec,
        "quality_mode": "crf",
        "crf": args.crf,
        "preset": "medium",
        "preserve_audio": args.preserve_audio,
    }

    def print_progress(pct: int):
        sys.stdout.write(f"\rProgress: {pct}%")
        sys.stdout.flush()

    interpolator.process_video(
        args.input,
        args.output,
        cb=print_progress,
        encoder_config=encoder_cfg,
        active_encoder_callback=lambda enc: print(f"\nActive Encoder: {enc}"),
    )
    print("\nInterpolation complete successfully!")


def main():
    if len(sys.argv) > 1 and ("--cli" in sys.argv or "-c" in sys.argv or "--help" in sys.argv or "-h" in sys.argv):
        parser = argparse.ArgumentParser(
            description="FlowMorph Studio: Dense Optical Flow Video Frame Interpolation"
        )
        parser.add_argument("--cli", "-c", action="store_true", help="Run in headless CLI mode")
        parser.add_argument("--input", "-i", type=str, help="Input video file (.mp4)")
        parser.add_argument("--output", "-o", type=str, help="Output destination (.mp4)")
        parser.add_argument("--fps", "-f", type=float, default=60.0, help="Target FPS (default: 60.0)")
        parser.add_argument(
            "--preset",
            "-p",
            choices=["ultrafast", "fast", "medium"],
            default="medium",
            help="DIS optical flow preset",
        )
        parser.add_argument(
            "--consistency-threshold",
            "-t",
            type=float,
            default=0.15,
            help="Consistency occlusion threshold (default: 0.15)",
        )
        parser.add_argument(
            "--device",
            "-d",
            choices=["cpu", "nvidia"],
            default="nvidia",
            help="Render & acceleration device (default: nvidia if available, else cpu)",
        )
        parser.add_argument(
            "--codec",
            choices=["h264", "hevc", "mp4v"],
            default="h264",
            help="Video output codec (default: h264)",
        )
        parser.add_argument(
            "--crf",
            type=int,
            default=20,
            help="Constant Rate Factor encoding quality (14-32, default: 20)",
        )
        parser.add_argument(
            "--preserve-audio",
            action="store_true",
            default=True,
            help="Preserve source audio track (default: True)",
        )
        parsed_args = parser.parse_args()

        if parsed_args.cli:
            if not parsed_args.input or not parsed_args.output:
                parser.error("--input and --output are required when using --cli mode.")
            launch_cli(parsed_args)
            return

    # Default: launch desktop GUI
    launch_gui()


if __name__ == "__main__":
    main()
