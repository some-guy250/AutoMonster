"""Reusable CustomTkinter widgets for the debug tool.

Extracted from debug_tool.py to keep the DebugTool panel manageable.
"""

import customtkinter as ctk
import cv2
import threading
import logging
from pathlib import Path
from PIL import Image

logger = logging.getLogger(__name__)


class SimpleMultiSelectListbox(ctk.CTkFrame):
    """Simple multi-select listbox implementation using CTkScrollableFrame.

    Supports click-to-toggle selection, hover image previews, batch
    insertion/deletion, and debounced filtering.
    """

    def __init__(self, master, command=None, asset_dict=None, template_cache=None, **kwargs):
        super().__init__(master, **kwargs)
        self.command = command
        self.asset_dict = asset_dict or {}
        self.template_cache = template_cache
        self.selected_indices = set()
        self.items = []
        self.item_widgets = []

        # Hover preview
        self.preview_window = None
        self.preview_label = None
        self._current_preview_asset = None
        self._preview_timer = None

        self.scrollable_frame = ctk.CTkScrollableFrame(self)
        self.scrollable_frame.pack(fill="both", expand=True)
        self.scrollable_frame.grid_columnconfigure(0, weight=1)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def insert(self, index, item):
        self.items.append(item)
        self._create_item_widget(len(self.items) - 1, item)

    def delete(self, start, end=None):
        if end is None or end == "end":
            self.items = self.items[:start]
        else:
            self.items = self.items[:start] + self.items[end + 1:]

        for widget in self.item_widgets:
            try:
                widget.grid_forget()
            except Exception:
                # Ignore errors during widget cleanup
                pass

        widgets_to_destroy = self.item_widgets
        self.item_widgets = []
        self.selected_indices.clear()

        def background_destroy(idx=0):
            if idx >= len(widgets_to_destroy):
                return
            end_idx = min(idx + 50, len(widgets_to_destroy))
            for i in range(idx, end_idx):
                try:
                    widgets_to_destroy[i].destroy()
                except Exception:
                    # Ignore errors during widget destruction
                    pass
            if end_idx < len(widgets_to_destroy):
                self.after(5, lambda: background_destroy(end_idx))

        if widgets_to_destroy:
            self.after(1, lambda: background_destroy(0))

        for i, item in enumerate(self.items):
            self._create_item_widget(i, item)

    def curselection(self):
        return sorted(list(self.selected_indices))

    def selection_clear(self, start, end=None):
        self.selected_indices.clear()
        self._update_colors()

    def select_all(self):
        self.selected_indices = set(range(len(self.items)))
        self._update_colors()
        if self.command:
            self.command()

    def deselect_all(self):
        self.selected_indices.clear()
        self._update_colors()
        if self.command:
            self.command()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _create_item_widget(self, index, item):
        label = ctk.CTkLabel(
            self.scrollable_frame,
            text=item,
            anchor="w",
            fg_color="#1f1f1f",
            text_color="white",
            corner_radius=4,
            height=24,
            padx=10
        )
        label.grid(row=index, column=0, sticky="ew", padx=2, pady=1)

        def on_click(event, idx=index):
            if idx in self.selected_indices:
                self.selected_indices.remove(idx)
            else:
                self.selected_indices.add(idx)
            self._update_colors(changed_index=idx)
            if self.command:
                self.command()

        def on_enter(event, asset_name=item):
            self._show_preview(asset_name)

        def on_leave(event):
            self._hide_preview()

        label.bind("<Button-1>", on_click)
        label.bind("<Enter>", on_enter)
        label.bind("<Leave>", on_leave)

        self.item_widgets.append(label)

    def _update_colors(self, asset_colors=None, changed_index=None):
        if changed_index is not None:
            if changed_index < len(self.item_widgets):
                label = self.item_widgets[changed_index]
                if changed_index in self.selected_indices:
                    item_name = self.items[changed_index]
                    if asset_colors and item_name in asset_colors:
                        b, g, r = asset_colors[item_name]
                        label.configure(fg_color=f"#{r:02x}{g:02x}{b:02x}", text_color="white")
                    else:
                        label.configure(fg_color="#3498db", text_color="white")
                else:
                    label.configure(fg_color="#1f1f1f", text_color="white")
            return

        for i, label in enumerate(self.item_widgets):
            if i in self.selected_indices:
                if asset_colors and i < len(self.items):
                    item_name = self.items[i]
                    if item_name in asset_colors:
                        b, g, r = asset_colors[item_name]
                        label.configure(fg_color=f"#{r:02x}{g:02x}{b:02x}", text_color="white")
                    else:
                        label.configure(fg_color="#3498db", text_color="white")
            else:
                label.configure(fg_color="#1f1f1f", text_color="white")

    # ------------------------------------------------------------------
    # Hover preview
    # ------------------------------------------------------------------

    def _show_preview(self, asset_name):
        if asset_name not in self.asset_dict:
            return

        if self._preview_timer:
            self.after_cancel(self._preview_timer)
            self._preview_timer = None

        self._current_preview_asset = asset_name
        self._preview_timer = self.after(150, lambda: self._load_preview_async(asset_name))

    def _load_preview_async(self, asset_name):
        if self._current_preview_asset != asset_name:
            return

        def load_image_task():
            try:
                img = None
                if self.template_cache is not None:
                    filename = self.asset_dict.get(asset_name)
                    if filename:
                        cached_data = self.template_cache.get(f'asset_images/{filename}')
                        if cached_data is not None:
                            img = cached_data[0]

                if img is None:
                    filename = self.asset_dict.get(asset_name)
                    if not filename:
                        return
                    asset_path = Path(f'asset_images/{filename}')
                    if not asset_path.exists():
                        return
                    img = cv2.imread(str(asset_path))

                if img is None:
                    return

                img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

                max_size = 300
                h, w = img_rgb.shape[:2]
                if h > max_size or w > max_size:
                    scale = min(max_size / h, max_size / w)
                    img_rgb = cv2.resize(img_rgb, (int(w * scale), int(h * scale)),
                                         interpolation=cv2.INTER_AREA)

                pil_image = Image.fromarray(img_rgb)

                if self._current_preview_asset == asset_name:
                    self.after(0, lambda: self._display_preview_image(pil_image, asset_name))

            except Exception as e:
                logger.error(f"Error loading preview for {asset_name}: {e}")

        threading.Thread(target=load_image_task, daemon=True).start()

    def _display_preview_image(self, pil_image, asset_name):
        if self._current_preview_asset != asset_name:
            return
        try:
            photo = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=pil_image.size)
            self._create_and_display_preview(photo)
        except Exception as e:
            logger.error(f"Error displaying preview image: {e}")

    def _create_and_display_preview(self, photo):
        if self._current_preview_asset is None:
            return

        if self.preview_window is None:
            try:
                self.preview_window = ctk.CTkToplevel(self)
                self.preview_window.withdraw()
                self.preview_window.overrideredirect(True)
                self.preview_window.attributes('-topmost', True)

                self.preview_label = ctk.CTkLabel(self.preview_window, text="")
                self.preview_label.pack(padx=5, pady=5)

                self.preview_label.bind("<Leave>", lambda e: self._hide_preview())
                self.preview_window.bind("<Leave>", lambda e: self._hide_preview())
            except Exception as e:
                logger.error(f"Error creating preview window: {e}")
                self.preview_window = None
                return

        try:
            if self._current_preview_asset is None:
                return

            self.preview_label.configure(image=photo)
            self.preview_label.image = photo

            x = self.winfo_pointerx() + 15
            y = self.winfo_pointery() + 15
            self.preview_window.geometry(f"+{x}+{y}")

            self.preview_window.deiconify()
            self.preview_window.lift()
        except Exception as e:
            logger.error(f"Error displaying preview: {e}")
            self._hide_preview()

    def _hide_preview(self):
        if self._preview_timer:
            self.after_cancel(self._preview_timer)
            self._preview_timer = None

        self._current_preview_asset = None
        if self.preview_window is not None:
            try:
                self.preview_window.withdraw()
            except Exception:
                # Ignore errors during preview window cleanup
                pass
