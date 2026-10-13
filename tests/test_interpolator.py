"""
Unit and integration tests for FlowMorph interpolation engine.
"""

import os
import pytest
import cv2
import numpy as np
from core.interpolator import OpticalFlowFrameInterpolator, probe_video


@pytest.fixture
def sample_video(tmp_path):
    video_path = os.path.join(tmp_path, "test_input.mp4")
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(video_path, fourcc, 10.0, (120, 120))
    for i in range(6):
        frame = np.zeros((120, 120, 3), dtype=np.uint8)
        cv2.circle(frame, (20 + i * 15, 60), 12, (253, 103, 0), -1)
        writer.write(frame)
    writer.release()
    return video_path


def test_probe_video(sample_video):
    meta = probe_video(sample_video)
    assert meta["fps"] == 10.0
    assert meta["frame_count"] == 6
    assert meta["width"] == 120
    assert meta["height"] == 120
    assert meta["thumbnail"] is not None


def test_interpolation_execution(sample_video, tmp_path):
    output_path = os.path.join(tmp_path, "test_output.mp4")
    interpolator = OpticalFlowFrameInterpolator(
        target_fps=20.0,
        flow_preset=cv2.DISOPTICAL_FLOW_PRESET_ULTRAFAST,
        consistency_threshold=0.15,
    )

    progress_events = []
    interpolator.process_video(sample_video, output_path, cb=lambda p: progress_events.append(p))

    assert os.path.isfile(output_path)
    assert os.path.getsize(output_path) > 0
    assert len(progress_events) > 0
    assert progress_events[-1] == 100

    out_meta = probe_video(output_path)
    assert out_meta["fps"] == 20.0
    assert out_meta["frame_count"] > 6


def test_interpolation_cancellation(sample_video, tmp_path):
    output_path = os.path.join(tmp_path, "test_cancelled.mp4")
    interpolator = OpticalFlowFrameInterpolator(target_fps=60.0)

    # Trigger cancellation immediately
    with pytest.raises(InterruptedError):
        interpolator.process_video(
            sample_video,
            output_path,
            cancel_check=lambda: True,
        )


def test_interpolation_with_cpu_encoder(sample_video, tmp_path):
    output_path = os.path.join(tmp_path, "test_cpu_enc.mp4")
    interpolator = OpticalFlowFrameInterpolator(target_fps=20.0, flow_preset=cv2.DISOPTICAL_FLOW_PRESET_ULTRAFAST)

    enc_cfg = {
        "device": "cpu",
        "codec": "h264",
        "quality_mode": "crf",
        "crf": 22,
        "preset": "ultrafast",
        "preserve_audio": False,
    }

    active_enc = []
    interpolator.process_video(
        sample_video,
        output_path,
        encoder_config=enc_cfg,
        active_encoder_callback=lambda enc: active_enc.append(enc),
    )

    assert os.path.isfile(output_path)
    assert os.path.getsize(output_path) > 0
    assert len(active_enc) > 0
    assert "libx264" in active_enc[0] or "mp4v" in active_enc[0]


def test_interpolation_with_nvidia_encoder(sample_video, tmp_path):
    output_path = os.path.join(tmp_path, "test_nvidia_enc.mp4")
    interpolator = OpticalFlowFrameInterpolator(target_fps=20.0, flow_preset=cv2.DISOPTICAL_FLOW_PRESET_ULTRAFAST)

    enc_cfg = {
        "device": "nvidia",
        "codec": "h264",
        "quality_mode": "crf",
        "crf": 20,
        "preset": "fast",
        "preserve_audio": False,
    }

    active_enc = []
    interpolator.process_video(
        sample_video,
        output_path,
        encoder_config=enc_cfg,
        active_encoder_callback=lambda enc: active_enc.append(enc),
    )

    assert os.path.isfile(output_path)
    assert os.path.getsize(output_path) > 0
    assert len(active_enc) > 0

