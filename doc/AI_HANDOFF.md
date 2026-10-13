# FlowMorph Studio — AI Handoff & Developer Guide

> **To the Next AI Agent or Developer:**
> This repository underwent a complete rebranding from a legacy HTML/FastAPI web interface to **FlowMorph Studio**, a standalone, modern Python desktop application with full English localization and custom-rendered vector icons.
> Read this document thoroughly before proposing or making changes.

---

## 1. Project Context & Motivation

- **Application Purpose**: Optical flow video frame rate upsampling (e.g. 24/30 FPS $\to$ 60/120/240 FPS).
- **Core Engine**: Dense Inverse Search (DIS) optical flow using OpenCV, bidirectional flow warping, and occlusion-aware photometric blending.
- **Previous State**: Relied on a FastAPI web server (`app.py`), Uvicorn, and a web page (`static/index.html`) triggered via a Windows command launcher that popped open Google Chrome.
- **Current State**: Standalone native desktop GUI powered by `CustomTkinter` and `Pillow`, featuring a responsive two-column card UI, live metadata probing, thumbnail preview, background execution thread, and real-time progress monitoring.

---

## 2. Strict Invariants (DO NOT VIOLATE)

### Rule 1: Preserve the Core Algorithm Exactly
The user explicitly required:
> *"jangan rusaki pola algoritma cara program ini bekerja, karena ini sudah yang paling terbaik"*
- **Do NOT alter** the mathematical equations in `core/interpolator.py`:
  - `_estimate_intermediate_flows`:
    $$F_{t \to 0} = -(1 - \alpha)\alpha F_{01} + \alpha^2 F_{10}$$
    $$F_{t \to 1} = (1 - \alpha)^2 F_{01} - \alpha(1 - \alpha) F_{10}$$
  - `_occlusion_aware_weights`:
    $$\text{disagreement} = \frac{|\hat{I}_0 - \hat{I}_1|}{255}$$
    $$\text{occlusion\_bias} = \text{clip}\left(\frac{\text{disagreement} - \tau}{1 - \tau}, 0, 1\right)$$
    $$w_0 = (1 - \text{bias})(1 - \alpha) + \text{bias} \cdot w_{\text{near}}$$
  - `_backward_warp` using `cv2.INTER_LINEAR` and `cv2.BORDER_REPLICATE`.
  - `_build_output_timeline` index mapping.
- All additions to `core/interpolator.py` must only be non-intrusive conveniences (e.g., metadata probing, cancellation hooks, progress callbacks).

### Rule 2: Strictly No Emojis
The user explicitly commanded:
> *"jika memerlukan icon pastikan jangan gunakan emoji, gunakan icon, atau buatkan iconnya."*
- Do NOT use unicode emoji characters anywhere in UI labels, buttons, dialogs, or logs.
- All visual glyphs must be loaded from `gui/icons.py` or rendered programmatically into `assets/icons/*.png` using Pillow via `assets/generate_icons.py`.

### Rule 3: 100% English Language
- Every button, label, log message, error prompt, tooltip, and code docstring in the codebase must remain in English.

### Rule 4: Harmonized Brand Color Palette
- The visual identity is anchored directly to `logo.png`:
  - Primary Brand Amber: `#FD6700`
  - Hover Tint: `#FF7E24`
  - Active Press: `#E05A00`
  - Dark Slate Surfaces: `#0C0E12` (Root), `#151821` (Cards), `#1F2432` (Inputs), `#283042` (Borders).

---

## 3. Directory Layout & Module Responsibilities

```
Video Interpolation/
├── assets/
│   ├── logo.png                # Official brand logo (copied from root)
│   ├── icon.ico                # Multi-size Windows app icon
│   ├── generate_icons.py       # Script to generate crisp high-DPI icons
│   └── icons/                  # 64x64 RGBA icons (video, play, stop, folder, check, gpu, audio, etc.)
├── core/
│   ├── __init__.py             # Exports OpticalFlowFrameInterpolator, probe_video, device & encoder tools
│   ├── device.py               # Hardware detection (CPU threads, NVIDIA GPU, VRAM, NVENC & MFT capabilities)
│   ├── encoder.py              # Video stream writers (FFmpeg pipe + OpenCV fallback, audio muxer)
│   └── interpolator.py         # UNTOUCHED mathematical interpolation engine + probe utility
├── doc/
│   ├── ARCHITECTURE.md         # Detailed math & data flow architecture
│   ├── USER_GUIDE.md           # End-user instruction manual
│   ├── BENCHMARKS_AND_PRESETS.md # Presets & threshold tuning guidelines
│   └── AI_HANDOFF.md           # (This document)
├── gui/
│   ├── __init__.py             # Exports FlowMorphApp
│   ├── theme.py                # Colors, design tokens, fonts
│   ├── icons.py                # Cached high-DPI CTkImage icon manager
│   ├── components.py           # Reusable CardFrame, MetricBox, StatusPill
│   └── main_window.py          # Main desktop GUI window & thread-safe worker logic
├── original/                   # Archived historical scripts for reference
├── static/                     # Legacy HTML files (preserved for backward compatibility)
├── tests/
│   └── test_interpolator.py    # Pytest test suite for engine verification
├── app.py                      # Multi-mode gateway (defaults to Desktop GUI, supports --server)
├── main.py                     # Primary executable entry point (GUI + CLI options)
├── run.bat                     # Windows double-click launcher
├── requirements.txt            # Python dependencies (includes imageio-ffmpeg)
├── README.md                   # Showcase GitHub repository README
├── LICENSE                     # MIT License
└── logo.png                    # Original root brand logo
```

---

## 4. Key Components Walkthrough

### 4.1 `core/device.py`
Provides hardware introspection:
- `get_cpu_info()`: Core count and thread availability.
- `get_nvidia_gpu_info()`: Queries `nvidia-smi` for GPU model name, dedicated VRAM, and installed driver version.
- `detect_encoder_capabilities()`: Performs test probes for `h264_nvenc`, `hevc_nvenc`, `h264_mf`, `libx264`, and `libx265`.

### 4.2 `core/encoder.py`
Provides hardware and software video stream writers:
- `FFmpegPipeWriter`: Streams raw BGR24 frames via stdin pipe to FFmpeg. Automatically routes to NVIDIA hardware encoding (`h264_nvenc` or `h264_mf` Media Foundation hardware acceleration on Windows) when `device="nvidia"` is selected, or to CPU software encoding (`libx264` / `libx265`) when `device="cpu"` is chosen.
- `mux_audio_from_source(src, dest)`: Losslessly muxes original source audio into the interpolated video without re-encoding.
- `OpenCVVideoWriter`: Robust fallback if FFmpeg is unavailable.

### 4.3 `core/interpolator.py`
Contains:
- `OpticalFlowFrameInterpolator`: The core class. Takes `target_fps`, `flow_preset`, `consistency_threshold`, and `device="cpu"|"nvidia"`.
  - When `device="nvidia"`, activates OpenCV OpenCL compute via `cv2.ocl.setUseOpenCL(True)` and dispatches flow calculations on the NVIDIA GPU via `cv2.UMat`.
  - When `device="cpu"`, runs pure multi-threaded AVX/SSE on the host CPU.
  - Exposes `process_video(input_path, output_path, cb, detailed_cb, cancel_check, encoder_config, active_encoder_callback)`.
- `probe_video(input_path)`: Uses `cv2.VideoCapture` to quickly fetch `width`, `height`, `fps`, `frame_count`, `duration`, `file_size`, and extracts the first frame as a thumbnail `np.ndarray` without decoding the entire stream.

### 4.4 `gui/main_window.py`
Contains `FlowMorphApp(ctk.CTk)`:
- Left Column: Video picker, path entry, thumbnail preview (`CTkLabel`), 6-metric grid (`MetricBox`).
- Right Column:
  - Target FPS selector (preset pills + slider).
  - DIS quality segmented button & consistency threshold slider.
  - **Hardware Render & Encoding Profile**: Render device selector (CPU vs NVIDIA GPU), Codec selector (H.264, HEVC, MPEG-4), CRF quality slider, and source audio retention switch.
  - Output path picker, render button, cancel button, progress bar, real-time stats line, and scrolling log terminal.
- Concurrency: `_run_worker` runs inside `threading.Thread(daemon=True)`. Progress is sent to the main loop using `self.after(0, ...)`.

### 4.5 `main.py`
- Running `python main.py` opens the desktop GUI.
- Running `python main.py --cli --input in.mp4 --output out.mp4 --fps 60 --device nvidia --codec h264 --crf 20` executes the headless CLI pipeline.

---

## 5. Verification & Testing

To verify the installation and core engine integrity:

```powershell
# Run the test suite
python -m pytest tests/test_interpolator.py -v

# Verify GUI instantiation without launching mainloop
python -c "from gui import FlowMorphApp; app = FlowMorphApp(); app.update_idletasks(); app.destroy(); print('GUI OK')"

# Verify icon regeneration
python assets/generate_icons.py
```

---

## 6. Recommended Future Enhancements (Non-Breaking)

If you are tasked with further expanding FlowMorph Studio, consider these safe additions:

1. **Audio Passthrough via FFmpeg**:
   - OpenCV `VideoWriter` strips audio streams. You can optionally use `ffmpeg` (if installed on the user's system) to mux the original audio back into the interpolated video stream.
2. **Batch Queue**:
   - Add a multi-file queue list in a separate tab or drawer so users can interpolate a folder of video clips sequentially.
3. **Hardware Acceleration Option**:
   - Provide an optional CuPy or OpenCV CUDA backend for DIS optical flow (`cv2.cuda_OpticalFlowDual_TVL1` or `cv2.cuda_FarnebackOpticalFlow`) if CUDA is available on the host machine.
4. **Resolution Downscaling/Upscaling**:
   - Allow an optional output resolution selector (e.g. 50% downscale for ultra-fast previews).

Always run `python -m pytest` after making modifications.
