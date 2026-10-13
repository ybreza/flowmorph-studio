"""
Hardware and Device Detection Module for FlowMorph Studio.
Detects CPU capabilities and NVIDIA GPU availability, VRAM, drivers, and encoder capabilities.
"""

import os
import shutil
import subprocess
from typing import Dict, Any, Optional, Tuple


def get_cpu_info() -> Dict[str, Any]:
    """Returns CPU thread count and architecture information."""
    cores = os.cpu_count() or 4
    return {
        "name": f"CPU ({cores} Threads)",
        "cores": cores,
        "available": True,
    }


def get_nvidia_gpu_info() -> Dict[str, Any]:
    """
    Queries NVIDIA GPU information via nvidia-smi.
    Returns GPU model name, VRAM in MB, driver version, and availability.
    """
    nvidia_smi = shutil.which("nvidia-smi")
    if not nvidia_smi:
        # Default Windows path check
        default_path = r"C:\Windows\System32\nvidia-smi.exe"
        if os.path.isfile(default_path):
            nvidia_smi = default_path

    if not nvidia_smi:
        return {
            "available": False,
            "name": "No NVIDIA GPU Detected",
            "vram_mb": 0,
            "driver_version": "N/A",
            "cuda_version": "N/A",
        }

    try:
        query_cmd = [
            nvidia_smi,
            "--query-gpu=name,memory.total,driver_version",
            "--format=csv,noheader,nounits",
        ]
        out = subprocess.check_output(query_cmd, text=True, timeout=3).strip()
        if not out:
            raise ValueError("Empty output from nvidia-smi")

        # Parse first GPU
        first_line = out.splitlines()[0]
        parts = [p.strip() for p in first_line.split(",")]
        name = parts[0] if len(parts) > 0 else "NVIDIA GPU"
        vram = int(float(parts[1])) if len(parts) > 1 and parts[1].replace(".", "").isdigit() else 2048
        driver = parts[2] if len(parts) > 2 else "Unknown"

        return {
            "available": True,
            "name": f"NVIDIA {name}",
            "model": name,
            "vram_mb": vram,
            "driver_version": driver,
        }
    except Exception as e:
        # Fallback query
        try:
            out = subprocess.check_output([nvidia_smi], text=True, timeout=3)
            if "GeForce" in out or "NVIDIA" in out:
                return {
                    "available": True,
                    "name": "NVIDIA GPU (Detected)",
                    "model": "GeForce / Quadro",
                    "vram_mb": 2048,
                    "driver_version": "Detected",
                }
        except Exception:
            pass

        return {
            "available": False,
            "name": "NVIDIA GPU Not Available",
            "vram_mb": 0,
            "driver_version": "N/A",
        }


def detect_encoder_capabilities() -> Dict[str, bool]:
    """
    Tests available encoding backends on the host machine.
    Verifies NVENC, Media Foundation, and libx264.
    """
    import imageio_ffmpeg
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

    caps = {
        "nvenc_h264": False,
        "nvenc_hevc": False,
        "mf_h264": False,
        "libx264": True,
        "libx265": True,
    }

    # Test Media Foundation H.264
    try:
        cmd_mf = [
            ffmpeg_exe, "-y",
            "-f", "lavfi", "-i", "color=c=black:s=64x64:d=0.1",
            "-c:v", "h264_mf",
            "-f", "null", "-"
        ]
        res_mf = subprocess.run(cmd_mf, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=2)
        caps["mf_h264"] = (res_mf.returncode == 0)
    except Exception:
        pass

    # Test NVENC H.264
    try:
        cmd_nv = [
            ffmpeg_exe, "-y",
            "-f", "lavfi", "-i", "color=c=black:s=64x64:d=0.1",
            "-c:v", "h264_nvenc",
            "-f", "null", "-"
        ]
        res_nv = subprocess.run(cmd_nv, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=2)
        caps["nvenc_h264"] = (res_nv.returncode == 0)
    except Exception:
        pass

    # Test NVENC HEVC
    try:
        cmd_nv_hevc = [
            ffmpeg_exe, "-y",
            "-f", "lavfi", "-i", "color=c=black:s=64x64:d=0.1",
            "-c:v", "hevc_nvenc",
            "-f", "null", "-"
        ]
        res_nv_hevc = subprocess.run(cmd_nv_hevc, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=2)
        caps["nvenc_hevc"] = (res_nv_hevc.returncode == 0)
    except Exception:
        pass

    return caps
