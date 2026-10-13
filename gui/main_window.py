"""
FlowMorph Studio - Main Application Window
Modern Desktop Python GUI for Dense Optical Flow Video Frame Interpolation.
Full English interface, brand-aligned styling, vector-rendered icons, no emojis.
"""

import os
import sys
import time
import math
import subprocess
import threading
from typing import Optional, Dict, Any
from PIL import Image, ImageTk

import cv2
import customtkinter as ctk
from tkinter import filedialog, messagebox

from core.interpolator import OpticalFlowFrameInterpolator, probe_video
from core.device import get_cpu_info, get_nvidia_gpu_info, detect_encoder_capabilities
from .theme import (
    COLOR_BG_ROOT,
    COLOR_BG_CARD,
    COLOR_BG_CARD_ALT,
    COLOR_BG_INPUT,
    COLOR_BORDER,
    COLOR_BORDER_LIGHT,
    COLOR_BORDER_FOCUS,
    COLOR_PRIMARY,
    COLOR_PRIMARY_HOVER,
    COLOR_PRIMARY_ACTIVE,
    COLOR_PRIMARY_SUBTLE,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    COLOR_TEXT_MUTED,
    COLOR_SUCCESS,
    COLOR_SUCCESS_HOVER,
    COLOR_DANGER,
    COLOR_DANGER_HOVER,
    COLOR_WARNING,
    FONT_TITLE,
    FONT_SUBTITLE,
    FONT_SECTION,
    FONT_BODY,
    FONT_BODY_BOLD,
    FONT_SMALL,
    FONT_MONO,
    FONT_METRIC_VALUE,
    FONT_METRIC_LABEL,
)
from .icons import get_icon, get_logo_image, LOGO_PATH, ASSETS_DIR
from .components import CardFrame, MetricBox, StatusPill


class FlowMorphApp(ctk.CTk):
    """
    Main application window for FlowMorph Studio.
    """

    def __init__(self):
        # Enable Hardware Per-Monitor DPI Awareness (eliminates window dragging lag & DWM blur on Windows)
        if sys.platform == "win32":
            try:
                import ctypes
                ctypes.windll.shcore.SetProcessDpiAwareness(2)
            except Exception:
                try:
                    import ctypes
                    ctypes.windll.user32.SetProcessDPIAware()
                except Exception:
                    pass

        super().__init__()

        # Appearance configuration
        ctk.set_appearance_mode("dark")
        self.configure(fg_color=COLOR_BG_ROOT)

        # Window properties
        self.title("FlowMorph Studio - Video Frame Interpolator")
        self.geometry("1140x820")
        self.minsize(980, 720)

        # Set Window Icon
        icon_path = os.path.join(ASSETS_DIR, "icon.ico")
        if os.path.isfile(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass

        # State Variables
        self.input_file_path: Optional[str] = None
        self.output_file_path: Optional[str] = None
        self.video_meta: Optional[Dict[str, Any]] = None
        self.is_processing = False
        self.cancel_requested = False
        self.worker_thread: Optional[threading.Thread] = None
        self.start_time: float = 0.0

        # Hardware Capabilities
        self.cpu_info = get_cpu_info()
        self.gpu_info = get_nvidia_gpu_info()
        self.enc_caps = detect_encoder_capabilities()

        # UI Initialization
        self._build_header()
        self._build_main_layout()

        # Initial Status
        self.log_message("FlowMorph Studio initialized. Select a video file to begin.")
        if self.gpu_info["available"]:
            self.log_message(
                f"Hardware Ready: {self.gpu_info['name']} ({self.gpu_info['vram_mb']} MB VRAM, Driver {self.gpu_info['driver_version']})"
            )
        else:
            self.log_message(f"Hardware Ready: {self.cpu_info['name']}")

    def _build_header(self):
        """Builds top branding bar."""
        header_frame = ctk.CTkFrame(
            self,
            fg_color=COLOR_BG_CARD,
            border_width=1,
            border_color=COLOR_BORDER,
            corner_radius=0,
            height=68,
        )
        header_frame.pack(fill="x", side="top")
        header_frame.pack_propagate(False)

        # Left branding
        brand_container = ctk.CTkFrame(header_frame, fg_color="transparent")
        brand_container.pack(side="left", padx=20, pady=10)

        logo_img = get_logo_image(size=(38, 38))
        if logo_img:
            self.logo_label = ctk.CTkLabel(brand_container, text="", image=logo_img)
            self.logo_label.pack(side="left", padx=(0, 12))

        title_box = ctk.CTkFrame(brand_container, fg_color="transparent")
        title_box.pack(side="left")

        app_title = ctk.CTkLabel(
            title_box,
            text="FLOWMORPH STUDIO",
            font=FONT_TITLE,
            text_color=COLOR_TEXT_PRIMARY,
        )
        app_title.pack(anchor="w")

        app_subtitle = ctk.CTkLabel(
            title_box,
            text="Optical Flow Video Interpolation Engine",
            font=FONT_SMALL,
            text_color=COLOR_PRIMARY,
        )
        app_subtitle.pack(anchor="w")

        # Right header controls
        right_container = ctk.CTkFrame(header_frame, fg_color="transparent")
        right_container.pack(side="right", padx=20, pady=12)

        self.status_pill = StatusPill(right_container, text="Idle", color=COLOR_TEXT_MUTED)
        self.status_pill.pack(side="left", padx=(0, 12))

        reset_btn = ctk.CTkButton(
            right_container,
            text="Reset",
            image=get_icon("refresh", size=(14, 14)),
            font=FONT_SMALL,
            width=80,
            height=30,
            fg_color=COLOR_BG_CARD_ALT,
            hover_color=COLOR_BORDER,
            border_width=1,
            border_color=COLOR_BORDER,
            command=self.reset_form,
        )
        reset_btn.pack(side="left")

    def _build_main_layout(self):
        """Constructs two-column responsive workspace."""
        scroll_container = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=COLOR_BORDER,
            scrollbar_button_hover_color=COLOR_PRIMARY,
        )
        scroll_container.pack(fill="both", expand=True, padx=20, pady=16)

        # Grid configuration
        scroll_container.grid_columnconfigure(0, weight=4, minsize=420)
        scroll_container.grid_columnconfigure(1, weight=5, minsize=500)

        # ------------------ LEFT COLUMN: INPUT & PREVIEW ------------------
        left_col = ctk.CTkFrame(scroll_container, fg_color="transparent")
        left_col.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        # 1. Source Video Card
        self.source_card = CardFrame(left_col, title="Source Video File", icon_name="video")
        self.source_card.pack(fill="x", pady=(0, 14))

        picker_box = ctk.CTkFrame(self.source_card, fg_color="transparent")
        picker_box.pack(fill="x", padx=16, pady=(4, 14))

        self.path_entry = ctk.CTkEntry(
            picker_box,
            placeholder_text="No video file selected (.mp4)...",
            font=FONT_BODY,
            fg_color=COLOR_BG_INPUT,
            border_color=COLOR_BORDER,
            text_color=COLOR_TEXT_PRIMARY,
            height=38,
        )
        self.path_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        browse_btn = ctk.CTkButton(
            picker_box,
            text="Browse",
            image=get_icon("folder", size=(16, 16)),
            font=FONT_BODY_BOLD,
            fg_color=COLOR_PRIMARY,
            hover_color=COLOR_PRIMARY_HOVER,
            width=110,
            height=38,
            command=self.browse_input_file,
        )
        browse_btn.pack(side="right")

        # 2. Video Preview & Metadata Card
        self.preview_card = CardFrame(left_col, title="Video Inspection & Preview", icon_name="info")
        self.preview_card.pack(fill="x", pady=(0, 14))

        # Thumbnail canvas
        self.thumb_container = ctk.CTkFrame(
            self.preview_card,
            fg_color=COLOR_BG_CARD_ALT,
            border_width=1,
            border_color=COLOR_BORDER,
            height=210,
            corner_radius=8,
        )
        self.thumb_container.pack(fill="x", padx=16, pady=(4, 12))
        self.thumb_container.pack_propagate(False)

        self.thumb_label = ctk.CTkLabel(
            self.thumb_container,
            text="Select an MP4 video to inspect metadata and preview frames",
            font=FONT_SMALL,
            text_color=COLOR_TEXT_MUTED,
            image=get_icon("video", size=(48, 48)),
            compound="top",
        )
        self.thumb_label.pack(expand=True)

        # Metadata Grid
        stats_frame = ctk.CTkFrame(self.preview_card, fg_color="transparent")
        stats_frame.pack(fill="x", padx=16, pady=(0, 14))
        stats_frame.grid_columnconfigure((0, 1, 2), weight=1)

        self.box_resolution = MetricBox(stats_frame, label="Resolution", value="-", height=58)
        self.box_resolution.grid(row=0, column=0, padx=(0, 6), pady=4, sticky="ew")

        self.box_fps = MetricBox(stats_frame, label="Original FPS", value="-", unit="fps", height=58)
        self.box_fps.grid(row=0, column=1, padx=3, pady=4, sticky="ew")

        self.box_duration = MetricBox(stats_frame, label="Duration", value="-", height=58)
        self.box_duration.grid(row=0, column=2, padx=(6, 0), pady=4, sticky="ew")

        self.box_frames = MetricBox(stats_frame, label="Total Frames", value="-", height=58)
        self.box_frames.grid(row=1, column=0, padx=(0, 6), pady=4, sticky="ew")

        self.box_size = MetricBox(stats_frame, label="File Size", value="-", height=58)
        self.box_size.grid(row=1, column=1, padx=3, pady=4, sticky="ew")

        self.box_est_out = MetricBox(stats_frame, label="Est. Output", value="-", unit="frames", height=58)
        self.box_est_out.grid(row=1, column=2, padx=(6, 0), pady=4, sticky="ew")

        # ------------------ RIGHT COLUMN: CONTROLS & RENDER ------------------
        right_col = ctk.CTkFrame(scroll_container, fg_color="transparent")
        right_col.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        # 3. Interpolation Parameters Card
        self.params_card = CardFrame(right_col, title="Interpolation Settings", icon_name="sliders")
        self.params_card.pack(fill="x", pady=(0, 14))

        params_content = ctk.CTkFrame(self.params_card, fg_color="transparent")
        params_content.pack(fill="x", padx=16, pady=(4, 14))

        # Target FPS Selection
        fps_label_box = ctk.CTkFrame(params_content, fg_color="transparent")
        fps_label_box.pack(fill="x", pady=(2, 4))

        fps_title = ctk.CTkLabel(
            fps_label_box,
            text="Target Frame Rate (FPS)",
            font=FONT_BODY_BOLD,
            text_color=COLOR_TEXT_PRIMARY,
        )
        fps_title.pack(side="left")

        self.fps_value_label = ctk.CTkLabel(
            fps_label_box,
            text="60.0 FPS",
            font=FONT_BODY_BOLD,
            text_color=COLOR_PRIMARY,
        )
        self.fps_value_label.pack(side="right")

        # Quick Preset Buttons for FPS
        preset_bar = ctk.CTkFrame(params_content, fg_color="transparent")
        preset_bar.pack(fill="x", pady=(0, 8))
        preset_fps_values = [("60 FPS", 60.0), ("120 FPS", 120.0), ("144 FPS", 144.0), ("2x Speed", "2x"), ("4x Speed", "4x")]

        for label_text, val in preset_fps_values:
            btn = ctk.CTkButton(
                preset_bar,
                text=label_text,
                font=FONT_SMALL,
                height=26,
                fg_color=COLOR_BG_CARD_ALT,
                hover_color=COLOR_BORDER_LIGHT,
                border_width=1,
                border_color=COLOR_BORDER,
                command=lambda v=val: self.apply_fps_preset(v),
            )
            btn.pack(side="left", padx=(0, 6), expand=True, fill="x")

        # FPS Slider
        self.fps_slider = ctk.CTkSlider(
            params_content,
            from_=15.0,
            to=240.0,
            number_of_steps=225,
            progress_color=COLOR_PRIMARY,
            button_color=COLOR_PRIMARY,
            button_hover_color=COLOR_PRIMARY_HOVER,
            command=self._on_fps_slider_changed,
        )
        self.fps_slider.set(60.0)
        self.fps_slider.pack(fill="x", pady=(2, 14))

        # Calculation Preset
        calc_label_box = ctk.CTkFrame(params_content, fg_color="transparent")
        calc_label_box.pack(fill="x", pady=(2, 4))

        calc_title = ctk.CTkLabel(
            calc_label_box,
            text="Optical Flow Preset",
            font=FONT_BODY_BOLD,
            text_color=COLOR_TEXT_PRIMARY,
        )
        calc_title.pack(side="left")

        self.preset_desc_label = ctk.CTkLabel(
            calc_label_box,
            text="DIS Medium (High Precision)",
            font=FONT_SMALL,
            text_color=COLOR_TEXT_MUTED,
        )
        self.preset_desc_label.pack(side="right")

        self.preset_selector = ctk.CTkSegmentedButton(
            params_content,
            values=["Ultrafast", "Fast", "Medium"],
            selected_color=COLOR_PRIMARY,
            selected_hover_color=COLOR_PRIMARY_HOVER,
            unselected_color=COLOR_BG_CARD_ALT,
            unselected_hover_color=COLOR_BORDER,
            font=FONT_BODY_BOLD,
            command=self._on_preset_changed,
        )
        self.preset_selector.set("Medium")
        self.preset_selector.pack(fill="x", pady=(2, 14))

        # Consistency Threshold
        thresh_label_box = ctk.CTkFrame(params_content, fg_color="transparent")
        thresh_label_box.pack(fill="x", pady=(2, 4))

        thresh_title = ctk.CTkLabel(
            thresh_label_box,
            text="Consistency Threshold (Occlusion Tolerance)",
            font=FONT_BODY_BOLD,
            text_color=COLOR_TEXT_PRIMARY,
        )
        thresh_title.pack(side="left")

        self.thresh_value_label = ctk.CTkLabel(
            thresh_label_box,
            text="0.15",
            font=FONT_BODY_BOLD,
            text_color=COLOR_PRIMARY,
        )
        self.thresh_value_label.pack(side="right")

        self.thresh_slider = ctk.CTkSlider(
            params_content,
            from_=0.01,
            to=0.50,
            number_of_steps=49,
            progress_color=COLOR_PRIMARY,
            button_color=COLOR_PRIMARY,
            button_hover_color=COLOR_PRIMARY_HOVER,
            command=self._on_thresh_slider_changed,
        )
        self.thresh_slider.set(0.15)
        self.thresh_slider.pack(fill="x", pady=(2, 8))

        thresh_note = ctk.CTkLabel(
            params_content,
            text="Filters occlusion artifacts and rapid boundary changes. 0.15 offers ideal natural stability.",
            font=FONT_SMALL,
            text_color=COLOR_TEXT_MUTED,
            anchor="w",
            justify="left",
        )
        thresh_note.pack(fill="x")

        # 4. Hardware Render & Encoding Profile Card
        self.encoder_card = CardFrame(right_col, title="Hardware Render & Encoding Profile", icon_name="gpu")
        self.encoder_card.pack(fill="x", pady=(0, 14))

        encoder_content = ctk.CTkFrame(self.encoder_card, fg_color="transparent")
        encoder_content.pack(fill="x", padx=16, pady=(4, 14))

        # Render Device (CPU vs NVIDIA GPU)
        device_label_box = ctk.CTkFrame(encoder_content, fg_color="transparent")
        device_label_box.pack(fill="x", pady=(2, 4))

        device_title = ctk.CTkLabel(
            device_label_box,
            text="Render & Acceleration Device",
            font=FONT_BODY_BOLD,
            text_color=COLOR_TEXT_PRIMARY,
        )
        device_title.pack(side="left")

        self.device_badge_label = ctk.CTkLabel(
            device_label_box,
            text="",
            font=FONT_SMALL,
            text_color=COLOR_PRIMARY,
        )
        self.device_badge_label.pack(side="right")

        self.device_selector = ctk.CTkSegmentedButton(
            encoder_content,
            values=["CPU (Multi-Thread)", "NVIDIA GPU (Hardware)"],
            selected_color=COLOR_PRIMARY,
            selected_hover_color=COLOR_PRIMARY_HOVER,
            unselected_color=COLOR_BG_CARD_ALT,
            unselected_hover_color=COLOR_BORDER,
            font=FONT_BODY_BOLD,
            command=self._on_device_changed,
        )
        default_dev = "NVIDIA GPU (Hardware)" if self.gpu_info["available"] else "CPU (Multi-Thread)"
        self.device_selector.set(default_dev)
        self.device_selector.pack(fill="x", pady=(2, 4))

        self.device_detail_label = ctk.CTkLabel(
            encoder_content,
            text="",
            font=FONT_SMALL,
            text_color=COLOR_TEXT_MUTED,
            anchor="w",
            justify="left",
        )
        self.device_detail_label.pack(fill="x", pady=(0, 10))

        # Video Codec Selection
        codec_label_box = ctk.CTkFrame(encoder_content, fg_color="transparent")
        codec_label_box.pack(fill="x", pady=(2, 4))

        codec_title = ctk.CTkLabel(
            codec_label_box,
            text="Output Video Codec",
            font=FONT_BODY_BOLD,
            text_color=COLOR_TEXT_PRIMARY,
        )
        codec_title.pack(side="left")

        self.codec_desc_label = ctk.CTkLabel(
            codec_label_box,
            text="Standard MP4 (Highest Compatibility)",
            font=FONT_SMALL,
            text_color=COLOR_TEXT_MUTED,
        )
        self.codec_desc_label.pack(side="right")

        self.codec_selector = ctk.CTkSegmentedButton(
            encoder_content,
            values=["H.264 (AVC)", "H.265 (HEVC)", "MPEG-4"],
            selected_color=COLOR_PRIMARY,
            selected_hover_color=COLOR_PRIMARY_HOVER,
            unselected_color=COLOR_BG_CARD_ALT,
            unselected_hover_color=COLOR_BORDER,
            font=FONT_BODY_BOLD,
            command=self._on_codec_changed,
        )
        self.codec_selector.set("H.264 (AVC)")
        self.codec_selector.pack(fill="x", pady=(2, 10))

        # Quality (CRF) Rate Control
        rate_box = ctk.CTkFrame(encoder_content, fg_color="transparent")
        rate_box.pack(fill="x", pady=(2, 4))

        rate_title = ctk.CTkLabel(
            rate_box,
            text="Encoding Quality (Constant Rate Factor)",
            font=FONT_BODY_BOLD,
            text_color=COLOR_TEXT_PRIMARY,
        )
        rate_title.pack(side="left")

        self.crf_value_label = ctk.CTkLabel(
            rate_box,
            text="CRF 20 (High Fidelity)",
            font=FONT_BODY_BOLD,
            text_color=COLOR_PRIMARY,
        )
        self.crf_value_label.pack(side="right")

        self.crf_slider = ctk.CTkSlider(
            encoder_content,
            from_=14,
            to=32,
            number_of_steps=18,
            progress_color=COLOR_PRIMARY,
            button_color=COLOR_PRIMARY,
            button_hover_color=COLOR_PRIMARY_HOVER,
            command=self._on_crf_slider_changed,
        )
        self.crf_slider.set(20)
        self.crf_slider.pack(fill="x", pady=(2, 8))

        # Audio Stream Retention
        self.audio_switch = ctk.CTkSwitch(
            encoder_content,
            text="Preserve Source Audio Track (Lossless Stream Muxing)",
            font=FONT_BODY,
            progress_color=COLOR_PRIMARY,
            button_color=COLOR_TEXT_PRIMARY,
            button_hover_color=COLOR_PRIMARY_HOVER,
        )
        self.audio_switch.select()
        self.audio_switch.pack(anchor="w", pady=(4, 2))

        # Initialize device labels
        self._on_device_changed(default_dev)

        # 5. Output Destination Card
        self.dest_card = CardFrame(right_col, title="Output Destination", icon_name="folder")
        self.dest_card.pack(fill="x", pady=(0, 14))

        dest_box = ctk.CTkFrame(self.dest_card, fg_color="transparent")
        dest_box.pack(fill="x", padx=16, pady=(4, 14))

        self.dest_entry = ctk.CTkEntry(
            dest_box,
            placeholder_text="Output video path (.mp4)...",
            font=FONT_BODY,
            fg_color=COLOR_BG_INPUT,
            border_color=COLOR_BORDER,
            text_color=COLOR_TEXT_PRIMARY,
            height=38,
        )
        self.dest_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        dest_browse_btn = ctk.CTkButton(
            dest_box,
            text="Save As",
            font=FONT_BODY_BOLD,
            fg_color=COLOR_BG_CARD_ALT,
            hover_color=COLOR_BORDER_LIGHT,
            border_width=1,
            border_color=COLOR_BORDER,
            width=90,
            height=38,
            command=self.browse_output_file,
        )
        dest_browse_btn.pack(side="right")

        # 5. Execution & Real-Time Monitoring Card
        self.render_card = CardFrame(right_col, title="Process & Real-Time Status", icon_name="speed")
        self.render_card.pack(fill="x", pady=(0, 14))

        render_content = ctk.CTkFrame(self.render_card, fg_color="transparent")
        render_content.pack(fill="x", padx=16, pady=(4, 14))

        # Action Buttons
        btn_action_box = ctk.CTkFrame(render_content, fg_color="transparent")
        btn_action_box.pack(fill="x", pady=(2, 12))

        self.start_btn = ctk.CTkButton(
            btn_action_box,
            text="START INTERPOLATION",
            image=get_icon("play", size=(18, 18)),
            font=FONT_BODY_BOLD,
            fg_color=COLOR_PRIMARY,
            hover_color=COLOR_PRIMARY_HOVER,
            height=46,
            corner_radius=8,
            command=self.start_interpolation,
        )
        self.start_btn.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.cancel_btn = ctk.CTkButton(
            btn_action_box,
            text="Cancel",
            image=get_icon("stop", size=(16, 16)),
            font=FONT_BODY_BOLD,
            fg_color=COLOR_BG_CARD_ALT,
            hover_color=COLOR_DANGER,
            border_width=1,
            border_color=COLOR_BORDER,
            width=100,
            height=46,
            corner_radius=8,
            state="disabled",
            command=self.cancel_interpolation,
        )
        self.cancel_btn.pack(side="right")

        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(
            render_content,
            progress_color=COLOR_PRIMARY,
            fg_color=COLOR_BG_CARD_ALT,
            border_width=1,
            border_color=COLOR_BORDER,
            height=14,
            corner_radius=7,
        )
        self.progress_bar.set(0.0)
        self.progress_bar.pack(fill="x", pady=(4, 10))

        # Real-time metrics line
        stats_line = ctk.CTkFrame(render_content, fg_color="transparent")
        stats_line.pack(fill="x", pady=(0, 10))

        self.pct_label = ctk.CTkLabel(
            stats_line,
            text="Progress: 0%",
            font=FONT_BODY_BOLD,
            text_color=COLOR_TEXT_PRIMARY,
        )
        self.pct_label.pack(side="left")

        self.frames_progress_label = ctk.CTkLabel(
            stats_line,
            text="Frame: 0 / 0",
            font=FONT_SMALL,
            text_color=COLOR_TEXT_MUTED,
        )
        self.frames_progress_label.pack(side="left", padx=16)

        self.eta_label = ctk.CTkLabel(
            stats_line,
            text="ETA: --:--",
            font=FONT_SMALL,
            text_color=COLOR_TEXT_SECONDARY,
        )
        self.eta_label.pack(side="right")

        # Success Banner Box (initially hidden)
        self.success_frame = ctk.CTkFrame(
            render_content,
            fg_color="#0F291E",
            border_width=1,
            border_color=COLOR_SUCCESS,
            corner_radius=8,
        )
        # Built inside, packed conditionally upon completion
        success_inner = ctk.CTkFrame(self.success_frame, fg_color="transparent")
        success_inner.pack(fill="x", padx=12, pady=10)

        success_icon = ctk.CTkLabel(success_inner, text="", image=get_icon("check", size=(22, 22)))
        success_icon.pack(side="left", padx=(0, 10))

        success_text = ctk.CTkLabel(
            success_inner,
            text="Interpolation successfully completed!",
            font=FONT_BODY_BOLD,
            text_color=COLOR_TEXT_PRIMARY,
        )
        success_text.pack(side="left")

        self.open_video_btn = ctk.CTkButton(
            success_inner,
            text="Play Video",
            image=get_icon("play", size=(14, 14)),
            font=FONT_SMALL,
            fg_color=COLOR_SUCCESS,
            hover_color=COLOR_SUCCESS_HOVER,
            width=95,
            height=30,
            command=self.open_output_video,
        )
        self.open_video_btn.pack(side="right", padx=(6, 0))

        self.open_folder_btn = ctk.CTkButton(
            success_inner,
            text="Show in Folder",
            image=get_icon("folder", size=(14, 14)),
            font=FONT_SMALL,
            fg_color=COLOR_BG_CARD_ALT,
            hover_color=COLOR_BORDER_LIGHT,
            border_width=1,
            border_color=COLOR_BORDER,
            width=110,
            height=30,
            command=self.open_output_folder,
        )
        self.open_folder_btn.pack(side="right")

        # Minimal Log Terminal
        self.log_box = ctk.CTkTextbox(
            render_content,
            height=95,
            fg_color=COLOR_BG_INPUT,
            border_width=1,
            border_color=COLOR_BORDER,
            font=FONT_MONO,
            text_color=COLOR_TEXT_SECONDARY,
        )
        self.log_box.pack(fill="x", pady=(4, 0))

    # ------------------ EVENT HANDLERS & LOGIC ------------------

    def log_message(self, message: str) -> None:
        """Appends formatted timestamped message to log box."""
        timestamp = time.strftime("%H:%M:%S")
        self.log_box.insert("end", f"[{timestamp}] {message}\n")
        self.log_box.see("end")

    def _on_fps_slider_changed(self, value: float) -> None:
        val = round(float(value), 1)
        self.fps_value_label.configure(text=f"{val:.1f} FPS")
        self._update_estimated_output()

    def _on_thresh_slider_changed(self, value: float) -> None:
        val = round(float(value), 2)
        self.thresh_value_label.configure(text=f"{val:.2f}")

    def _on_preset_changed(self, value: str) -> None:
        descs = {
            "Ultrafast": "Fastest computation (Lower variational refinement)",
            "Fast": "Balanced for real-time preview & faster clips",
            "Medium": "DIS Medium (Highest precision with 5 refinement iterations)",
        }
        self.preset_desc_label.configure(text=descs.get(value, value))

    def _on_device_changed(self, value: str) -> None:
        if "NVIDIA" in value:
            if self.gpu_info.get("available", False):
                vram = self.gpu_info.get("vram_mb", 2048)
                drv = self.gpu_info.get("driver_version", "Active")
                self.device_badge_label.configure(text="Hardware Acceleration")
                if self.enc_caps.get("nvenc_h264", False):
                    pipeline_desc = "NVIDIA NVENC Dedicated Hardware Encoder"
                elif self.enc_caps.get("mf_h264", False):
                    pipeline_desc = "NVIDIA Hardware MFT Accelerated Pipeline"
                else:
                    pipeline_desc = "NVIDIA Hardware Accelerated Pipeline"
                self.device_detail_label.configure(
                    text=f"Detected: {self.gpu_info['name']} ({vram} MB VRAM, Driver {drv}) | {pipeline_desc}"
                )
            else:
                self.device_badge_label.configure(text="GPU Not Found")
                self.device_detail_label.configure(
                    text="No NVIDIA GPU detected on this system. Falling back automatically to CPU execution."
                )
        else:
            self.device_badge_label.configure(text=f"{self.cpu_info['cores']} Threads Active")
            self.device_detail_label.configure(
                text=f"Engine: Multi-Core CPU Software Processing ({self.cpu_info['name']})"
            )

    def _on_codec_changed(self, value: str) -> None:
        descs = {
            "H.264 (AVC)": "Standard MP4 (Highest Compatibility across players and browsers)",
            "H.265 (HEVC)": "High Efficiency Video Coding (~40% smaller file size at same quality)",
            "MPEG-4": "Classic MPEG-4 Part 2 (Universal raw stream compatibility)",
        }
        self.codec_desc_label.configure(text=descs.get(value, value))

    def _on_crf_slider_changed(self, value: float) -> None:
        val = int(round(float(value)))
        if val <= 16:
            desc = f"CRF {val} (Near Lossless / Large File)"
        elif val <= 22:
            desc = f"CRF {val} (High Fidelity / Recommended)"
        elif val <= 26:
            desc = f"CRF {val} (Balanced Quality)"
        else:
            desc = f"CRF {val} (Compact / Smaller File)"
        self.crf_value_label.configure(text=desc)

    def _on_active_encoder_detected(self, enc_name: str) -> None:
        is_hw = "nvenc" in enc_name or "mf" in enc_name
        hw_tag = "NVIDIA Hardware Accelerated" if is_hw else "CPU Software Encoder"
        self.log_message(f"Encoding Pipeline: {enc_name} ({hw_tag})")

    def apply_fps_preset(self, val) -> None:
        if isinstance(val, (int, float)):
            target = float(val)
        elif self.video_meta and "fps" in self.video_meta:
            multiplier = float(str(val).replace("x", ""))
            target = round(self.video_meta["fps"] * multiplier, 1)
        else:
            target = 60.0

        target = max(15.0, min(240.0, target))
        self.fps_slider.set(target)
        self._on_fps_slider_changed(target)

    def browse_input_file(self) -> None:
        file_path = filedialog.askopenfilename(
            title="Select Source Video File",
            filetypes=[("MP4 Video Files", "*.mp4"), ("All Video Files", "*.mp4;*.avi;*.mov;*.mkv")],
        )
        if not file_path:
            return

        self.input_file_path = os.path.normpath(file_path)
        self.path_entry.delete(0, "end")
        self.path_entry.insert(0, self.input_file_path)

        # Suggest default output path
        base, ext = os.path.splitext(self.input_file_path)
        fps_target = int(self.fps_slider.get())
        default_out = f"{base}_interpolated_{fps_target}fps{ext}"
        self.dest_entry.delete(0, "end")
        self.dest_entry.insert(0, default_out)
        self.output_file_path = default_out

        # Probe video
        try:
            self.video_meta = probe_video(self.input_file_path)
            self._update_video_inspection_ui()
            self.log_message(
                f"Video loaded: {os.path.basename(self.input_file_path)} "
                f"({self.video_meta['width']}x{self.video_meta['height']} @ {self.video_meta['fps']:.2f} fps)"
            )
            self.status_pill.update_status("Ready", COLOR_PRIMARY)
        except Exception as e:
            messagebox.showerror("Video Read Error", f"Unable to read video file:\n{str(e)}")
            self.log_message(f"Error reading video: {str(e)}")

    def browse_output_file(self) -> None:
        initial = self.dest_entry.get().strip() or "output_interpolated.mp4"
        file_path = filedialog.asksaveasfilename(
            title="Select Destination Video File",
            initialfile=os.path.basename(initial),
            filetypes=[("MP4 Video", "*.mp4")],
            defaultextension=".mp4",
        )
        if file_path:
            self.output_file_path = os.path.normpath(file_path)
            self.dest_entry.delete(0, "end")
            self.dest_entry.insert(0, self.output_file_path)

    def _update_video_inspection_ui(self) -> None:
        if not self.video_meta:
            return

        meta = self.video_meta
        self.box_resolution.set_value(f"{meta['width']} x {meta['height']}")
        self.box_fps.set_value(f"{meta['fps']:.2f}")

        # Format duration
        mins = int(meta["duration"] // 60)
        secs = meta["duration"] % 60
        self.box_duration.set_value(f"{mins:02d}:{secs:05.2f}")

        self.box_frames.set_value(f"{meta['frame_count']:,}")

        # File size
        size_mb = meta["file_size"] / (1024 * 1024)
        self.box_size.set_value(f"{size_mb:.1f} MB")

        self._update_estimated_output()

        # Update thumbnail preview
        thumb_cv = meta.get("thumbnail")
        if thumb_cv is not None:
            rgb_thumb = cv2.cvtColor(thumb_cv, cv2.COLOR_BGR2RGB)
            pil_thumb = Image.fromarray(rgb_thumb)

            # Fit into preview container (max width 380, max height 200)
            max_w, max_h = 380, 200
            pil_thumb.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)

            ctk_thumb = ctk.CTkImage(light_image=pil_thumb, dark_image=pil_thumb, size=pil_thumb.size)
            self.thumb_label.configure(image=ctk_thumb, text="")
            self.thumb_label.image = ctk_thumb

    def _update_estimated_output(self) -> None:
        if not self.video_meta or self.video_meta["fps"] <= 0:
            self.box_est_out.set_value("-")
            return

        fps_in = self.video_meta["fps"]
        fps_out = self.fps_slider.get()
        num_in = self.video_meta["frame_count"]
        duration = (num_in - 1) / fps_in
        num_out = int(round(duration * fps_out)) + 1
        self.box_est_out.set_value(f"{num_out:,}")

    def reset_form(self) -> None:
        if self.is_processing:
            messagebox.showwarning("Busy", "Cannot reset settings while interpolation is active.")
            return

        self.input_file_path = None
        self.output_file_path = None
        self.video_meta = None
        self.path_entry.delete(0, "end")
        self.dest_entry.delete(0, "end")

        self.box_resolution.set_value("-")
        self.box_fps.set_value("-")
        self.box_duration.set_value("-")
        self.box_frames.set_value("-")
        self.box_size.set_value("-")
        self.box_est_out.set_value("-")

        self.thumb_label.configure(
            image=get_icon("video", size=(48, 48)),
            text="Select an MP4 video to inspect metadata and preview frames",
            compound="top",
        )
        self.fps_slider.set(60.0)
        self._on_fps_slider_changed(60.0)
        self.preset_selector.set("Medium")
        self._on_preset_changed("Medium")
        self.thresh_slider.set(0.15)
        self._on_thresh_slider_changed(0.15)

        default_dev = "NVIDIA GPU (Hardware)" if self.gpu_info.get("available", False) else "CPU (Multi-Thread)"
        self.device_selector.set(default_dev)
        self._on_device_changed(default_dev)
        self.codec_selector.set("H.264 (AVC)")
        self._on_codec_changed("H.264 (AVC)")
        self.crf_slider.set(20)
        self._on_crf_slider_changed(20)
        self.audio_switch.select()

        self.progress_bar.set(0.0)
        self.pct_label.configure(text="Progress: 0%")
        self.frames_progress_label.configure(text="Frame: 0 / 0")
        self.eta_label.configure(text="ETA: --:--")
        self.status_pill.update_status("Idle", COLOR_TEXT_MUTED)

        if self.success_frame.winfo_ismapped():
            self.success_frame.pack_forget()

        self.log_message("Parameters reset to factory defaults.")

    def start_interpolation(self) -> None:
        if self.is_processing:
            return

        in_path = self.path_entry.get().strip()
        out_path = self.dest_entry.get().strip()

        if not in_path or not os.path.isfile(in_path):
            messagebox.showwarning("File Required", "Please choose a valid input video file.")
            return

        if not out_path:
            messagebox.showwarning("Destination Required", "Please specify an output video file destination.")
            return

        # Ensure destination directory exists
        out_dir = os.path.dirname(os.path.abspath(out_path))
        if out_dir and not os.path.exists(out_dir):
            try:
                os.makedirs(out_dir, exist_ok=True)
            except Exception as e:
                messagebox.showerror("Directory Error", f"Cannot create output directory:\n{str(e)}")
                return

        preset_lookup = {
            "Ultrafast": cv2.DISOPTICAL_FLOW_PRESET_ULTRAFAST,
            "Fast": cv2.DISOPTICAL_FLOW_PRESET_FAST,
            "Medium": cv2.DISOPTICAL_FLOW_PRESET_MEDIUM,
        }

        target_fps = float(self.fps_slider.get())
        flow_preset = preset_lookup.get(self.preset_selector.get(), cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
        consistency = float(self.thresh_slider.get())

        # Update state
        self.is_processing = True
        self.cancel_requested = False
        self.start_time = time.time()

        if self.success_frame.winfo_ismapped():
            self.success_frame.pack_forget()

        # UI State updates
        self.start_btn.configure(state="disabled", fg_color=COLOR_BORDER)
        self.cancel_btn.configure(state="normal", fg_color=COLOR_DANGER)
        self.status_pill.update_status("Processing", COLOR_PRIMARY)
        self.progress_bar.set(0.0)

        # Build encoder configuration
        device_mode = "nvidia" if "NVIDIA" in self.device_selector.get() and self.gpu_info.get("available", False) else "cpu"
        codec_raw = self.codec_selector.get()
        codec_mode = "h264" if "H.264" in codec_raw else ("hevc" if "H.265" in codec_raw else "mp4v")
        crf_val = int(round(float(self.crf_slider.get())))
        preserve_audio = bool(self.audio_switch.get())

        encoder_cfg = {
            "device": device_mode,
            "codec": codec_mode,
            "quality_mode": "crf",
            "crf": crf_val,
            "preset": "medium",
            "preserve_audio": preserve_audio,
        }

        self.log_message(
            f"Starting interpolation: Target {target_fps:.1f} FPS, Preset={self.preset_selector.get()}, "
            f"Device={device_mode.upper()}, Codec={codec_mode.upper()}, CRF={crf_val}"
        )

        # Launch background worker
        self.worker_thread = threading.Thread(
            target=self._run_worker,
            args=(in_path, out_path, target_fps, flow_preset, consistency, encoder_cfg),
            daemon=True,
        )
        self.worker_thread.start()

    def cancel_interpolation(self) -> None:
        if not self.is_processing:
            return

        self.cancel_requested = True
        self.cancel_btn.configure(state="disabled")
        self.log_message("Cancelling interpolation... Releasing video writer.")
        self.status_pill.update_status("Cancelling", COLOR_WARNING)

    def _run_worker(
        self,
        in_path: str,
        out_path: str,
        fps: float,
        preset: int,
        consistency: float,
        encoder_cfg: Dict[str, Any],
    ) -> None:
        try:
            device_choice = encoder_cfg.get("device", "cpu")
            interpolator = OpticalFlowFrameInterpolator(
                target_fps=fps,
                flow_preset=preset,
                consistency_threshold=consistency,
                device=device_choice,
            )
            self.after(0, self.log_message, f"Compute Engine: {interpolator.active_device_name}")

            last_ui_time = [0.0]
            last_pct = [-1]

            def detailed_progress(current: int, total: int, pct: int):
                now = time.time()
                # Rate limit UI dispatches to ~12 FPS or integer percentage increments
                if (now - last_ui_time[0] >= 0.08) or (pct != last_pct[0]) or (current >= total):
                    last_ui_time[0] = now
                    last_pct[0] = pct
                    self.after(0, self._on_frame_progress, current, total, pct)

            def on_active_encoder(enc_name: str):
                self.after(0, self._on_active_encoder_detected, enc_name)

            interpolator.process_video(
                input_path=in_path,
                output_path=out_path,
                detailed_cb=detailed_progress,
                cancel_check=lambda: self.cancel_requested,
                encoder_config=encoder_cfg,
                active_encoder_callback=on_active_encoder,
            )

            # Finished successfully
            self.after(0, self._on_interpolation_complete, out_path)

        except InterruptedError:
            self.after(0, self._on_interpolation_cancelled, out_path)
        except Exception as e:
            self.after(0, self._on_interpolation_error, str(e))

    def _on_frame_progress(self, current: int, total: int, pct: int) -> None:
        if not self.is_processing:
            return

        progress_val = max(0.0, min(1.0, current / total)) if total > 0 else 0.0
        self.progress_bar.set(progress_val)
        self.pct_label.configure(text=f"Progress: {pct}%")
        self.frames_progress_label.configure(text=f"Frame: {current:,} / {total:,}")

        # Compute speed and ETA
        elapsed = time.time() - self.start_time
        if elapsed > 0.5 and current > 0:
            speed = current / elapsed
            remaining_frames = max(0, total - current)
            eta_seconds = int(remaining_frames / speed)
            eta_m, eta_s = divmod(eta_seconds, 60)
            self.eta_label.configure(text=f"Speed: {speed:.1f} fps  •  ETA: {eta_m:02d}:{eta_s:02d}")

    def _on_interpolation_complete(self, out_path: str) -> None:
        self.is_processing = False
        elapsed = time.time() - self.start_time
        self.progress_bar.set(1.0)
        self.pct_label.configure(text="Progress: 100%")
        self.status_pill.update_status("Completed", COLOR_SUCCESS)

        self.start_btn.configure(state="normal", fg_color=COLOR_PRIMARY)
        self.cancel_btn.configure(state="disabled", fg_color=COLOR_BG_CARD_ALT)

        # Show success banner
        self.success_frame.pack(fill="x", pady=(10, 0))

        mins = int(elapsed // 60)
        secs = elapsed % 60
        self.log_message(f"Interpolation completed in {mins:02d}:{secs:05.2f}!")
        self.log_message(f"Saved output file: {out_path}")

    def _on_interpolation_cancelled(self, out_path: str) -> None:
        self.is_processing = False
        self.status_pill.update_status("Cancelled", COLOR_WARNING)
        self.start_btn.configure(state="normal", fg_color=COLOR_PRIMARY)
        self.cancel_btn.configure(state="disabled", fg_color=COLOR_BG_CARD_ALT)
        self.log_message("Operation cancelled by user.")

    def _on_interpolation_error(self, err_msg: str) -> None:
        self.is_processing = False
        self.status_pill.update_status("Failed", COLOR_DANGER)
        self.start_btn.configure(state="normal", fg_color=COLOR_PRIMARY)
        self.cancel_btn.configure(state="disabled", fg_color=COLOR_BG_CARD_ALT)
        self.log_message(f"Error during interpolation: {err_msg}")
        messagebox.showerror("Interpolation Error", f"An error occurred while processing:\n{err_msg}")

    def open_output_video(self) -> None:
        out_path = self.dest_entry.get().strip()
        if out_path and os.path.isfile(out_path):
            try:
                os.startfile(out_path)
            except Exception as e:
                messagebox.showerror("Launch Error", f"Failed to play video:\n{str(e)}")

    def open_output_folder(self) -> None:
        out_path = self.dest_entry.get().strip()
        if out_path:
            folder = os.path.dirname(os.path.abspath(out_path))
            if os.path.isdir(folder):
                try:
                    subprocess.run(["explorer", "/select,", os.path.abspath(out_path)])
                except Exception:
                    os.startfile(folder)
