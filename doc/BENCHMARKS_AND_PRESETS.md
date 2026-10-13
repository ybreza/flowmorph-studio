# FlowMorph Presets & Benchmark Guidelines

This document provides technical guidelines on choosing the appropriate interpolation preset and consistency threshold for your hardware and source material.

---

## 1. Optical Flow Presets Compared

FlowMorph relies on OpenCV's Dense Inverse Search (DIS) optical flow engine. The three available presets adjust patch-based matching iterations and spatial refinement depth:

| Preset | OpenCV Constant | Spatial Propagation | Variational Refinement | Typical Speed (1080p) | Artifact Resistance | Recommended Use Case |
|---|---|---|---|---|---|---|
| **Ultrafast** | `DISOPTICAL_FLOW_PRESET_ULTRAFAST` | Yes | 1 iteration | ~35 - 50 FPS | Moderate | Quick drafts, animation with simple geometric motion, low-power CPUs |
| **Fast** | `DISOPTICAL_FLOW_PRESET_FAST` | Yes | 3 iterations | ~20 - 35 FPS | High | Everyday video clips, medium-motion footage, gameplay recordings |
| **Medium** *(Default)* | `DISOPTICAL_FLOW_PRESET_MEDIUM` | Yes | 5 iterations | ~12 - 22 FPS | Maximum | Complex motion, organic scenes, panning shots, high-detail footage |

> [!TIP]
> For standard 1080p video on modern multi-core CPUs, **Medium** is recommended because the additional variational iterations minimize warping shear near high-frequency textures (hair, leaves, text).

---

## 2. Consistency Threshold Tuning

The **Consistency Threshold** ($\tau$) dictates the sensitivity of the occlusion rejection mask:

$$\Delta(\mathbf{x}) = \frac{1}{3 \times 255} \sum_{c \in \{R,G,B\}} |\hat{I}_0^c(\mathbf{x}) - \hat{I}_1^c(\mathbf{x})|$$
$$\beta(\mathbf{x}) = \text{clip}\left(\frac{\Delta(\mathbf{x}) - \tau}{1.0 - \tau}, 0.0, 1.0\right)$$

### Guidelines by Scene Type:
- **0.10 - 0.12 (Strict Occlusion)**:
  - Best for footage with fast foreground objects passing across textured backgrounds (e.g., cars driving past trees).
  - Prevents "tearing" and "ghost trails" by falling back to temporal nearest-neighbor blending when warped predictions disagree.
- **0.15 (Default - Universal)**:
  - Validated across diverse real-world clips. Smoothly transitions between motion estimation and fallback blending without noticeable softness.
- **0.20 - 0.25 (Permissive Warping)**:
  - Best for camera pans, drone footage, and landscape flyovers where the whole scene moves cohesively and few occlusions occur.

---

## 3. Recommended Input Video Practices

1. **Clean Input Codec**: Standard H.264 / MP4 clips work natively.
2. **Avoid Heavy Compression**: Heavy macroblocking in low-bitrate source videos can confuse optical flow gradients. If possible, provide source footage with minimal compression artifacts.
3. **Framerate Consideration**: Interpolating $24 \to 60\text{ FPS}$ (2.5x) or $30 \to 60\text{ FPS}$ (2x) yields the cleanest perceptual results. Upscaling beyond $8x$ in a single pass may benefit from high-contrast boundary footage.
