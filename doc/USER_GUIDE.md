# FlowMorph Studio User Guide

Welcome to **FlowMorph Studio**, a desktop video frame interpolation application powered by dense optical flow motion synthesis.

---

## 1. Quick Start

### 1.1 Running with Launcher (Windows)
Double-click `run.bat` in the project root directory. The launcher will automatically verify dependencies and open FlowMorph Studio.

### 1.2 Running from Terminal
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Launch the desktop GUI
python main.py
```

---

## 2. Using the Desktop Interface

```
+--------------------------------------------------------------------------+
|  [LOGO] FLOWMORPH STUDIO - Optical Flow Interpolator       [Status: Ready] |
+------------------------------------+-------------------------------------+
| LEFT PANEL: SOURCE & PREVIEW       | RIGHT PANEL: CONTROLS & RENDER      |
|                                    |                                     |
| [1] Source Video File (.mp4)       | [3] Target FPS: [60] [120] [144]... |
|     Browse MP4 video from disk     |     Slider: 15.0 - 240.0 FPS        |
|                                    |                                     |
| [2] Inspection & Metadata          | [4] Preset: Ultrafast / Fast/ Medium|
|     - Thumbnail Preview            |                                     |
|     - Original FPS & Resolution    | [5] Consistency Threshold (0.15)    |
|     - Frame count & duration       |                                     |
|     - Estimated output frame count | [6] Output Destination Path         |
|                                    |                                     |
|                                    | [7] [ START INTERPOLATION ]         |
|                                    |     Progress Bar & ETA Monitor      |
|                                    |     [Play Video] [Show in Folder]   |
+------------------------------------+-------------------------------------+
```

### Step 1: Select Source Video
- Click **Browse** under *Source Video File*.
- Choose any valid MP4 video.
- FlowMorph will inspect the file and populate the metadata card with native resolution, frame count, FPS, and an instant thumbnail preview.

### Step 2: Configure Target FPS
- Click one of the quick preset buttons:
  - **60 FPS**: Standard high-smoothness target (ideal for web and 60Hz displays).
  - **120 FPS / 144 FPS**: High-refresh gaming and monitor playback.
  - **2x / 4x Speed**: Multiplies your native framerate by 2 or 4.
- Or use the fine-tune slider to choose any exact framerate up to 240.0 FPS.

### Step 3: Choose Quality Preset
- **Ultrafast**: Maximum throughput with minimal variational iterations. Best for quick drafts or low-motion clips.
- **Fast**: Balanced preset offering high speed with good visual fidelity.
- **Medium (Recommended)**: Best optical flow estimation quality with 5 variational iterations and spatial propagation. Eliminates stutter in complex scenes.

### Step 4: Hardware Acceleration & Encoding Settings
- **Render Device**:
  - **CPU (Multi-Thread)**: Standard multi-threaded software processing across all available CPU cores.
  - **NVIDIA GPU (Hardware)**: Hardware-accelerated pipeline utilizing NVIDIA GPU hardware encoding (NVENC / Media Foundation MFT) and GPU stream dispatch. Automatically detects GPU VRAM and driver.
- **Output Video Codec**:
  - **H.264 (AVC)**: Universally supported by web browsers, phones, TVs, and editing suites.
  - **H.265 (HEVC)**: Modern high-efficiency compression, producing ~40% smaller files at comparable visual clarity.
  - **MPEG-4**: Classic baseline format for older media players.
- **Encoding Quality (CRF)**:
  - Constant Rate Factor slider (14 - 32):
    - `14 - 16`: Near lossless (higher bitrate).
    - `18 - 22`: High fidelity (recommended sweet spot).
    - `24 - 30`: Compact file size for faster sharing.
- **Audio Stream Retention**:
  - Toggle **Preserve Source Audio Track** to losslessly mux the original soundtrack and dialogue directly into the newly interpolated video file.

### Step 5: Consistency Threshold
- Sets the sensitivity for occlusion detection:
  - **Lower (0.05 - 0.10)**: Strict ghosting suppression, favors source frame nearest in time when uncertainty arises.
  - **Default (0.15)**: Optimal balance for natural camera motion and smooth transitions.
  - **Higher (0.20 - 0.35)**: Allows stronger optical flow warping in fast-action sequences.

### Step 6: Start Interpolation
- Click the prominent **START INTERPOLATION** button.
- Monitor real-time progress:
  - Percentage completed
  - Processed frames vs. total frames
  - Processing speed in frames per second
  - Accurate countdown Estimated Time of Arrival (ETA)
- When finished, click **Play Video** to preview immediately in your default media player, or **Show in Folder** to locate the generated file.

---

## 3. Headless / CLI Usage

FlowMorph also includes a command-line interface for automated pipelines and headless servers:

```bash
# Basic 60 FPS upsample using NVIDIA GPU acceleration
python main.py --cli --input input.mp4 --output output_60fps.mp4 --fps 60.0 --device nvidia

# CPU software encoding with H.265 (HEVC) and custom CRF quality
python main.py --cli --input source.mp4 --output upscaled.mp4 --fps 120.0 --device cpu --codec hevc --crf 18
```

### CLI Arguments
| Flag | Description | Default |
|---|---|---|
| `--cli`, `-c` | Enables headless CLI mode | `False` |
| `--input`, `-i` | Input video file path | *Required* |
| `--output`, `-o` | Destination video file path | *Required* |
| `--fps`, `-f` | Target frame rate | `60.0` |
| `--device`, `-d` | Render device (`cpu` or `nvidia`) | `nvidia` |
| `--codec` | Video codec (`h264`, `hevc`, `mp4v`) | `h264` |
| `--crf` | Constant Rate Factor (14 - 32) | `20` |
| `--preset`, `-p` | DIS preset (`ultrafast`, `fast`, `medium`) | `medium` |
| `--consistency-threshold`, `-t` | Occlusion threshold | `0.15` |
| `--preserve-audio` | Preserve original audio track | `True` |
