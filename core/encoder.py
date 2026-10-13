"""
Advanced Video Encoding Pipeline for FlowMorph Studio.
Supports CPU and NVIDIA GPU hardware-accelerated rendering, codec selection (H.264, HEVC, MPEG-4),
quality rate control (CRF & Bitrate), and optional lossless audio passthrough.
"""

import os
import subprocess
from typing import Optional, Dict, Any, Tuple
import cv2
import numpy as np
import imageio_ffmpeg

from .device import detect_encoder_capabilities, get_nvidia_gpu_info


class VideoWriterStream:
    """
    Abstract stream interface for writing synthesized video frames.
    """

    def write(self, frame: np.ndarray) -> None:
        raise NotImplementedError

    def release(self) -> None:
        raise NotImplementedError


class OpenCVVideoWriter(VideoWriterStream):
    """Fallback OpenCV VideoWriter wrapper."""

    def __init__(self, output_path: str, fps: float, width: int, height: int, fourcc_code: str = "mp4v"):
        self.output_path = output_path
        fourcc = cv2.VideoWriter_fourcc(*fourcc_code)
        self.writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        if not self.writer.isOpened():
            # Fallback to mp4v
            fourcc_fallback = cv2.VideoWriter_fourcc(*"mp4v")
            self.writer = cv2.VideoWriter(output_path, fourcc_fallback, fps, (width, height))
            if not self.writer.isOpened():
                raise IOError(f"Failed to open OpenCV VideoWriter for {output_path}")

    def write(self, frame: np.ndarray) -> None:
        self.writer.write(frame)

    def release(self) -> None:
        self.writer.release()


class FFmpegPipeWriter(VideoWriterStream):
    """
    High-performance FFmpeg video writer streaming raw BGR24 frames via stdin.
    Supports CPU (libx264/libx265) and NVIDIA GPU (NVENC/Media Foundation) hardware acceleration.
    """

    def __init__(
        self,
        output_path: str,
        fps: float,
        width: int,
        height: int,
        device: str = "cpu",
        codec: str = "h264",
        quality_mode: str = "crf",
        crf: int = 20,
        bitrate_kbps: Optional[int] = None,
        preset: str = "medium",
    ):
        self.output_path = output_path
        self.ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        self.width = width
        self.height = height
        self.fps = fps
        self.active_encoder = "libx264"

        caps = detect_encoder_capabilities()
        gpu_info = get_nvidia_gpu_info()

        # Determine video encoder
        encoder_args = []
        if device.lower() == "nvidia" and gpu_info.get("available", False):
            if codec == "hevc":
                if caps.get("nvenc_hevc", False):
                    self.active_encoder = "hevc_nvenc"
                    encoder_args.extend(["-c:v", "hevc_nvenc", "-preset", "p4"])
                else:
                    self.active_encoder = "libx265"
                    encoder_args.extend(["-c:v", "libx265", "-preset", "fast"])
            else:  # h264 or mp4v
                if caps.get("nvenc_h264", False):
                    self.active_encoder = "h264_nvenc"
                    encoder_args.extend(["-c:v", "h264_nvenc", "-preset", "p4"])
                elif caps.get("mf_h264", False):
                    self.active_encoder = "h264_mf"
                    encoder_args.extend(["-c:v", "h264_mf"])
                else:
                    self.active_encoder = "libx264"
                    encoder_args.extend(["-c:v", "libx264", "-preset", preset])
        else:
            # CPU Software rendering
            if codec == "hevc":
                self.active_encoder = "libx265"
                encoder_args.extend(["-c:v", "libx265", "-preset", preset])
            elif codec == "mp4v":
                self.active_encoder = "mpeg4"
                encoder_args.extend(["-c:v", "mpeg4", "-q:v", "3"])
            else:
                self.active_encoder = "libx264"
                encoder_args.extend(["-c:v", "libx264", "-preset", preset])

        # Rate control / Quality parameters
        if "nvenc" in self.active_encoder:
            if quality_mode == "crf":
                encoder_args.extend(["-cq", str(crf)])
            elif bitrate_kbps:
                encoder_args.extend(["-b:v", f"{bitrate_kbps}k"])
        elif "libx" in self.active_encoder:
            if quality_mode == "crf":
                encoder_args.extend(["-crf", str(crf)])
            elif bitrate_kbps:
                encoder_args.extend(["-b:v", f"{bitrate_kbps}k"])
        elif self.active_encoder == "h264_mf":
            if bitrate_kbps:
                encoder_args.extend(["-b:v", f"{bitrate_kbps}k"])
            else:
                # Default high-quality bitrate for MF
                encoder_args.extend(["-b:v", "15000k"])

        # Pixel format and output command
        cmd = [
            self.ffmpeg_exe,
            "-y",
            "-f", "rawvideo",
            "-vcodec", "rawvideo",
            "-s", f"{width}x{height}",
            "-pix_fmt", "bgr24",
            "-r", str(fps),
            "-i", "-",
            *encoder_args,
            "-pix_fmt", "yuv420p",
            output_path,
        ]

        self.proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def write(self, frame: np.ndarray) -> None:
        if self.proc and self.proc.stdin:
            self.proc.stdin.write(frame.tobytes())

    def release(self) -> None:
        if self.proc:
            if self.proc.stdin:
                try:
                    self.proc.stdin.close()
                except Exception:
                    pass
            try:
                self.proc.wait(timeout=10)
            except Exception:
                self.proc.kill()
            self.proc = None


def mux_audio_from_source(source_video_path: str, interpolated_video_path: str) -> bool:
    """
    Copies original audio stream from source video into the newly interpolated video file.
    Does not re-encode audio; performs lossless stream copy (-c:a copy).
    """
    if not os.path.isfile(source_video_path) or not os.path.isfile(interpolated_video_path):
        return False

    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    temp_muxed = interpolated_video_path + ".muxed.mp4"

    cmd = [
        ffmpeg_exe,
        "-y",
        "-i", interpolated_video_path,
        "-i", source_video_path,
        "-c:v", "copy",
        "-c:a", "copy",
        "-map", "0:v:0",
        "-map", "1:a:0?",
        "-shortest",
        temp_muxed,
    ]

    try:
        res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=20)
        if res.returncode == 0 and os.path.isfile(temp_muxed) and os.path.getsize(temp_muxed) > 0:
            os.replace(temp_muxed, interpolated_video_path)
            return True
    except Exception:
        pass
    finally:
        if os.path.exists(temp_muxed):
            try:
                os.remove(temp_muxed)
            except Exception:
                pass
    return False


def create_video_writer(
    output_path: str,
    fps: float,
    width: int,
    height: int,
    device: str = "cpu",
    codec: str = "h264",
    quality_mode: str = "crf",
    crf: int = 20,
    bitrate_kbps: Optional[int] = None,
    preset: str = "medium",
) -> Tuple[VideoWriterStream, str]:
    """
    Factory function creating an accelerated FFmpeg stream writer or fallback OpenCV writer.
    Returns (writer_instance, active_encoder_name).
    """
    try:
        writer = FFmpegPipeWriter(
            output_path=output_path,
            fps=fps,
            width=width,
            height=height,
            device=device,
            codec=codec,
            quality_mode=quality_mode,
            crf=crf,
            bitrate_kbps=bitrate_kbps,
            preset=preset,
        )
        return writer, writer.active_encoder
    except Exception as e:
        print(f"Warning: Falling back to OpenCV VideoWriter: {e}")
        writer = OpenCVVideoWriter(output_path, fps, width, height, fourcc_code="mp4v")
        return writer, "opencv_mp4v"
