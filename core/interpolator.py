"""
FlowMorph Engine: Dense Optical Flow Video Frame Interpolation
Core algorithm preserved exactly as designed for maximum mathematical fidelity and visual stability.
Now supports CPU and NVIDIA GPU hardware rendering and advanced encoding settings.
"""

from typing import List, Optional, Tuple, Callable, Dict, Any
import os
import cv2
import numpy as np

from .encoder import create_video_writer, mux_audio_from_source


class OpticalFlowFrameInterpolator:
    """
    High-performance optical flow video frame rate upsampler utilizing OpenCV DIS
    (Dense Inverse Search) optical flow with bidirectional flow estimation,
    backward warping, and occlusion-aware photometric blending.
    """

    def __init__(
        self,
        target_fps: float = 60.0,
        flow_preset: int = cv2.DISOPTICAL_FLOW_PRESET_MEDIUM,
        consistency_threshold: float = 0.15,
        device: str = "cpu",
    ) -> None:
        self.target_fps = target_fps
        self.consistency_threshold = consistency_threshold
        self.device = str(device).lower()
        self.use_gpu = ("nvidia" in self.device or "gpu" in self.device)

        # Hardware compute backend configuration
        if self.use_gpu and cv2.ocl.haveOpenCL():
            cv2.ocl.setUseOpenCL(True)
            try:
                self.active_device_name = cv2.ocl.Device.getDefault().name()
            except Exception:
                self.active_device_name = "NVIDIA GPU (OpenCL)"
        else:
            cv2.ocl.setUseOpenCL(False)
            self.active_device_name = "CPU (Multi-Thread)"

        self.flow_engine = cv2.DISOpticalFlow_create(flow_preset)
        self.flow_engine.setUseSpatialPropagation(True)
        self.flow_engine.setVariationalRefinementIterations(5)
        self._grid_x: Optional[np.ndarray] = None
        self._grid_y: Optional[np.ndarray] = None

    def _ensure_grid(self, height: int, width: int) -> None:
        if self._grid_x is None or self._grid_x.shape != (height, width):
            self._grid_x, self._grid_y = np.meshgrid(
                np.arange(width, dtype=np.float32),
                np.arange(height, dtype=np.float32),
            )

    def _backward_warp(self, frame: np.ndarray, flow: np.ndarray) -> np.ndarray:
        self._ensure_grid(frame.shape[0], frame.shape[1])
        map_x = (self._grid_x + flow[..., 0]).astype(np.float32)
        map_y = (self._grid_y + flow[..., 1]).astype(np.float32)
        return cv2.remap(
            frame,
            map_x,
            map_y,
            interpolation=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_REPLICATE,
        )

    @staticmethod
    def _estimate_intermediate_flows(
        flow01: np.ndarray, flow10: np.ndarray, alpha: float
    ) -> Tuple[np.ndarray, np.ndarray]:
        flow_t0 = (-(1.0 - alpha) * alpha) * flow01 + (alpha * alpha) * flow10
        flow_t1 = ((1.0 - alpha) ** 2) * flow01 - (alpha * (1.0 - alpha)) * flow10
        return flow_t0, flow_t1

    def _occlusion_aware_weights(
        self, warped0: np.ndarray, warped1: np.ndarray, alpha: float
    ) -> Tuple[np.ndarray, np.ndarray]:
        disagreement = (
            np.abs(warped0.astype(np.float32) - warped1.astype(np.float32)).mean(
                axis=2, keepdims=True
            )
            / 255.0
        )
        occlusion_bias = np.clip(
            (disagreement - self.consistency_threshold)
            / (1.0 - self.consistency_threshold),
            0.0,
            1.0,
        )
        nearer_source_weight = 1.0 if alpha < 0.5 else 0.0
        weight0 = (1.0 - occlusion_bias) * (1.0 - alpha) + occlusion_bias * nearer_source_weight
        weight1 = 1.0 - weight0
        return weight0, weight1

    def synthesize_intermediate_frame(
        self,
        frame0: np.ndarray,
        frame1: np.ndarray,
        flow01: np.ndarray,
        flow10: np.ndarray,
        alpha: float,
    ) -> np.ndarray:
        flow_t0, flow_t1 = self._estimate_intermediate_flows(flow01, flow10, alpha)
        warped0 = self._backward_warp(frame0, flow_t0)
        warped1 = self._backward_warp(frame1, flow_t1)
        weight0, weight1 = self._occlusion_aware_weights(warped0, warped1, alpha)
        blended = warped0.astype(np.float32) * weight0 + warped1.astype(np.float32) * weight1
        return np.clip(blended, 0.0, 255.0).astype(np.uint8)

    def _compute_bidirectional_flow(
        self,
        gray0: np.ndarray,
        gray1: np.ndarray,
        prev01: Optional[np.ndarray],
        prev10: Optional[np.ndarray],
    ) -> Tuple[np.ndarray, np.ndarray]:
        if self.use_gpu and cv2.ocl.useOpenCL():
            u_g0 = cv2.UMat(gray0)
            u_g1 = cv2.UMat(gray1)
            u_p01 = cv2.UMat(prev01) if prev01 is not None else None
            u_p10 = cv2.UMat(prev10) if prev10 is not None else None

            f01 = self.flow_engine.calc(u_g0, u_g1, u_p01)
            f10 = self.flow_engine.calc(u_g1, u_g0, u_p10)

            flow01 = f01.get() if hasattr(f01, "get") else f01
            flow10 = f10.get() if hasattr(f10, "get") else f10
        else:
            flow01 = self.flow_engine.calc(gray0, gray1, prev01)
            flow10 = self.flow_engine.calc(gray1, gray0, prev10)
        return flow01, flow10

    @staticmethod
    def _build_output_timeline(
        num_input_frames: int, fps_in: float, fps_out: float
    ) -> List[Tuple[int, int, float]]:
        duration = (num_input_frames - 1) / fps_in
        num_output_frames = int(round(duration * fps_out)) + 1
        timeline: List[Tuple[int, int, float]] = []
        for output_index in range(num_output_frames):
            source_position = (output_index / fps_out) * fps_in
            lower_index = int(np.floor(source_position))
            if lower_index >= num_input_frames - 1:
                lower_index = num_input_frames - 2
                alpha = 1.0
            else:
                alpha = source_position - lower_index
            timeline.append((lower_index, lower_index + 1, float(alpha)))
        return timeline

    def process_video(
        self,
        input_path: str,
        output_path: str,
        cb: Optional[Callable[[int], None]] = None,
        detailed_cb: Optional[Callable[[int, int, int], None]] = None,
        cancel_check: Optional[Callable[[], bool]] = None,
        encoder_config: Optional[Dict[str, Any]] = None,
        active_encoder_callback: Optional[Callable[[str], None]] = None,
    ) -> None:
        reader = cv2.VideoCapture(input_path)
        if not reader.isOpened():
            raise IOError(f"Cannot open input video: {input_path}")
        try:
            fps_in = reader.get(cv2.CAP_PROP_FPS)
            if fps_in <= 1e-2:
                raise ValueError("Unable to determine a valid input frame rate")
            width = int(reader.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(reader.get(cv2.CAP_PROP_FRAME_HEIGHT))
            frames: List[np.ndarray] = []
            grayscale_frames: List[np.ndarray] = []
            while True:
                if cancel_check and cancel_check():
                    raise InterruptedError("Interpolation cancelled during video decoding")
                success, frame = reader.read()
                if not success:
                    break
                frames.append(frame)
                grayscale_frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY))
        finally:
            reader.release()

        if len(frames) < 2:
            raise ValueError("Input video must contain at least two frames")

        timeline = self._build_output_timeline(len(frames), fps_in, self.target_fps)
        total_frames = len(timeline)

        # Initialize video encoder stream
        writer = None
        active_encoder = "opencv_mp4v"

        if encoder_config is not None:
            writer, active_encoder = create_video_writer(
                output_path=output_path,
                fps=self.target_fps,
                width=width,
                height=height,
                device=encoder_config.get("device", "cpu"),
                codec=encoder_config.get("codec", "h264"),
                quality_mode=encoder_config.get("quality_mode", "crf"),
                crf=encoder_config.get("crf", 20),
                bitrate_kbps=encoder_config.get("bitrate_kbps", None),
                preset=encoder_config.get("preset", "medium"),
            )
        else:
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            writer = cv2.VideoWriter(output_path, fourcc, self.target_fps, (width, height))
            if not writer.isOpened():
                raise IOError(f"Cannot open output video for writing: {output_path}")

        if active_encoder_callback:
            active_encoder_callback(active_encoder)

        try:
            active_pair_index = -1
            flow01: Optional[np.ndarray] = None
            flow10: Optional[np.ndarray] = None
            for i, (lower_index, upper_index, alpha) in enumerate(timeline):
                if cancel_check and cancel_check():
                    raise InterruptedError("Interpolation cancelled by user")

                if lower_index != active_pair_index:
                    flow01, flow10 = self._compute_bidirectional_flow(
                        grayscale_frames[lower_index],
                        grayscale_frames[upper_index],
                        flow01,
                        flow10,
                    )
                    active_pair_index = lower_index

                if alpha <= 1e-3:
                    output_frame = frames[lower_index]
                elif alpha >= 1.0 - 1e-3:
                    output_frame = frames[upper_index]
                else:
                    output_frame = self.synthesize_intermediate_frame(
                        frames[lower_index], frames[upper_index], flow01, flow10, alpha
                    )
                writer.write(output_frame)

                pct = int(((i + 1) / total_frames) * 100)
                if cb:
                    cb(pct)
                if detailed_cb:
                    detailed_cb(i + 1, total_frames, pct)
        finally:
            writer.release()

        # If audio passthrough is requested, mux original audio losslessly
        if encoder_config and encoder_config.get("preserve_audio", True):
            mux_audio_from_source(input_path, output_path)


def probe_video(input_path: str) -> Dict[str, Any]:
    """
    Inspects input video parameters without decoding all frames.
    Returns metadata dictionary with fps, resolution, frame count, duration.
    """
    if not os.path.isfile(input_path):
        raise FileNotFoundError(f"File not found: {input_path}")

    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        raise IOError(f"Could not open video file: {input_path}")

    try:
        fps = float(cap.get(cv2.CAP_PROP_FPS))
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration = frame_count / fps if fps > 0 else 0.0

        ret, frame = cap.read()
        thumbnail = frame if ret else None

        return {
            "fps": fps,
            "frame_count": frame_count,
            "width": width,
            "height": height,
            "duration": duration,
            "thumbnail": thumbnail,
            "file_size": os.path.getsize(input_path),
        }
    finally:
        cap.release()
