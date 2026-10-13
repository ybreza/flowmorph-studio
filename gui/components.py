"""
Modular UI Components for FlowMorph Studio.
Includes styled Card frames, Metric stats cards, and Header components.
"""

from typing import Optional, Tuple, Callable
import tkinter as tk
import customtkinter as ctk
from .theme import (
    COLOR_BG_CARD,
    COLOR_BG_CARD_ALT,
    COLOR_BORDER,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    COLOR_TEXT_MUTED,
    COLOR_PRIMARY,
    FONT_SECTION,
    FONT_SMALL,
    FONT_METRIC_VALUE,
    FONT_METRIC_LABEL,
)
from .icons import get_icon


class CardFrame(ctk.CTkFrame):
    """
    Styled card container with consistent border, elevation, and optional header.
    """

    def __init__(
        self,
        master,
        title: Optional[str] = None,
        icon_name: Optional[str] = None,
        corner_radius: int = 12,
        border_width: int = 1,
        fg_color: str = COLOR_BG_CARD,
        border_color: str = COLOR_BORDER,
        **kwargs,
    ):
        super().__init__(
            master,
            corner_radius=corner_radius,
            border_width=border_width,
            fg_color=fg_color,
            border_color=border_color,
            **kwargs,
        )

        if title:
            self.header_frame = tk.Frame(self, bg=fg_color)
            self.header_frame.pack(fill="x", padx=16, pady=(14, 8))

            if icon_name:
                icon_img = get_icon(icon_name, size=(18, 18))
                if icon_img:
                    self.icon_label = ctk.CTkLabel(
                        self.header_frame,
                        text="",
                        image=icon_img,
                    )
                    self.icon_label.pack(side="left", padx=(0, 8))

            self.title_label = ctk.CTkLabel(
                self.header_frame,
                text=title,
                font=FONT_SECTION,
                text_color=COLOR_TEXT_PRIMARY,
            )
            self.title_label.pack(side="left")


class MetricBox(ctk.CTkFrame):
    """
    Compact stat badge displaying a label and prominent value.
    """

    def __init__(
        self,
        master,
        label: str,
        value: str = "-",
        unit: str = "",
        fg_color: str = COLOR_BG_CARD_ALT,
        border_color: str = COLOR_BORDER,
        **kwargs,
    ):
        super().__init__(
            master,
            corner_radius=8,
            border_width=1,
            fg_color=fg_color,
            border_color=border_color,
            **kwargs,
        )
        self.pack_propagate(False)

        self.label_widget = ctk.CTkLabel(
            self,
            text=label.upper(),
            font=FONT_METRIC_LABEL,
            text_color=COLOR_TEXT_MUTED,
        )
        self.label_widget.pack(anchor="w", padx=10, pady=(6, 0))

        self.val_frame = tk.Frame(self, bg=fg_color)
        self.val_frame.pack(anchor="w", padx=10, pady=(0, 6))

        self.value_widget = ctk.CTkLabel(
            self.val_frame,
            text=value,
            font=FONT_METRIC_VALUE,
            text_color=COLOR_TEXT_PRIMARY,
        )
        self.value_widget.pack(side="left")

        if unit:
            self.unit_widget = ctk.CTkLabel(
                self.val_frame,
                text=f" {unit}",
                font=FONT_SMALL,
                text_color=COLOR_TEXT_SECONDARY,
            )
            self.unit_widget.pack(side="left", pady=(4, 0))

    def set_value(self, value: str) -> None:
        self.value_widget.configure(text=value)


class StatusPill(ctk.CTkFrame):
    """
    Status indicator pill for execution states (Idle, Ready, Running, Done).
    """

    def __init__(self, master, text: str = "Ready", color: str = COLOR_PRIMARY, **kwargs):
        super().__init__(
            master,
            corner_radius=14,
            fg_color=COLOR_BG_CARD_ALT,
            border_width=1,
            border_color=color,
            height=28,
            **kwargs,
        )
        self.dot = ctk.CTkFrame(self, width=8, height=8, corner_radius=4, fg_color=color)
        self.dot.pack(side="left", padx=(10, 6), pady=4)

        self.text_label = ctk.CTkLabel(
            self,
            text=text,
            font=FONT_SMALL,
            text_color=COLOR_TEXT_PRIMARY,
        )
        self.text_label.pack(side="left", padx=(0, 10), pady=2)

    def update_status(self, text: str, color: str) -> None:
        self.configure(border_color=color)
        self.dot.configure(fg_color=color)
        self.text_label.configure(text=text)
