import customtkinter as ctk
import cv2
import numpy as np
from PIL import Image
import threading
import importlib
import inspect
import sys
import os
import subprocess
import json
from pathlib import Path
import scrcpy
from Constants import ASSET_REGIONS, Region, ASSETS


class SimpleMultiSelectListbox(ctk.CTkFrame):
    """Simple multi-select listbox implementation using CTkScrollableFrame"""
    def __init__(self, master, command=None, asset_dict=None, template_cache=None, **kwargs):
        super().__init__(master, **kwargs)
        self.command = command
        self.asset_dict = asset_dict or {}  # Maps asset name -> filename
        self.template_cache = template_cache  # Reference to controller's loaded templates
        self.selected_indices = set()
        self.items = []
        self.item_widgets = []

        # Hover preview window
        self.preview_window = None
        self.preview_label = None
        self._current_preview_asset = None  # Track which asset preview is loading

        # Create scrollable frame
        self.scrollable_frame = ctk.CTkScrollableFrame(self)
        self.scrollable_frame.pack(fill="both", expand=True)
        self.scrollable_frame.grid_columnconfigure(0, weight=1)

    def insert(self, index, item):
        """Add an item to the listbox"""
        self.items.append(item)
        self._create_item_widget(len(self.items) - 1, item)

    def delete(self, start, end=None):
        """Delete items from the listbox"""
        if end is None or end == "end":
            self.items = self.items[:start]
        else:
            self.items = self.items[:start] + self.items[end+1:]

        # Recreate all widgets
        for widget in self.item_widgets:
            widget.destroy()
        self.item_widgets = []
        self.selected_indices.clear()

        for i, item in enumerate(self.items):
            self._create_item_widget(i, item)

    def _create_item_widget(self, index, item):
        """Create a clickable label for an item"""
        frame = ctk.CTkFrame(self.scrollable_frame, fg_color="transparent", border_width=0)
        frame.grid(row=index, column=0, sticky="ew", padx=0, pady=1)
        frame.grid_columnconfigure(0, weight=1)

        # Use a fixed border frame to prevent width changes
        border_frame = ctk.CTkFrame(frame, fg_color="transparent", border_width=0)
        border_frame.grid(row=0, column=0, sticky="ew", padx=2, pady=0)
        border_frame.grid_columnconfigure(0, weight=1)
        border_frame.grid_rowconfigure(0, weight=0)  # Don't expand vertically

        label = ctk.CTkLabel(
            border_frame,
            text=item,
            anchor="w",
            fg_color="#1f1f1f",
            text_color="white",
            corner_radius=4,
            height=24,
            padx=10
        )
        label.grid(row=0, column=0, sticky="ew", padx=0, pady=0)

        # Bind click events - default multi-select (no Ctrl needed)
        def on_click(event, idx=index):
            # Toggle selection on click
            if idx in self.selected_indices:
                self.selected_indices.remove(idx)
            else:
                self.selected_indices.add(idx)
            # Only update the color of the clicked item for speed
            self._update_colors(changed_index=idx)
            if self.command:
                self.command()

        # Bind hover events for preview
        def on_enter(event, asset_name=item):
            self._show_preview(asset_name)

        def on_leave(event):
            self._hide_preview()

        label.bind("<Button-1>", on_click)
        border_frame.bind("<Button-1>", on_click)
        frame.bind("<Button-1>", on_click)
        label.bind("<Enter>", on_enter)
        label.bind("<Leave>", on_leave)

        self.item_widgets.append(frame)

    def _update_colors(self, asset_colors=None, changed_index=None):
        """Update colors based on selection"""
        # If only one item changed, update just that one for speed
        if changed_index is not None:
            if changed_index < len(self.item_widgets):
                widget = self.item_widgets[changed_index]
                # Get border_frame (first child of frame), then label (first child of border_frame)
                border_frame = widget.winfo_children()[0]
                label = border_frame.winfo_children()[0]
                if changed_index in self.selected_indices:
                    # Check if we have a specific color for this item
                    item_name = self.items[changed_index]
                    if asset_colors and item_name in asset_colors:
                        b, g, r = asset_colors[item_name]
                        hex_color = f"#{r:02x}{g:02x}{b:02x}"
                        label.configure(fg_color=hex_color, text_color="white")
                    else:
                        label.configure(fg_color="#3498db", text_color="white")
                else:
                    label.configure(fg_color="#1f1f1f", text_color="white")
            return

        # Otherwise update all
        for i, widget in enumerate(self.item_widgets):
            # Get border_frame (first child of frame), then label (first child of border_frame)
            border_frame = widget.winfo_children()[0]
            label = border_frame.winfo_children()[0]
            if i in self.selected_indices:
                # Use assigned color if available
                if asset_colors and i < len(self.items):
                    item_name = self.items[i]
                    if item_name in asset_colors:
                        # Convert BGR to hex for tkinter
                        b, g, r = asset_colors[item_name]
                        hex_color = f"#{r:02x}{g:02x}{b:02x}"
                        label.configure(fg_color=hex_color)
                        label.configure(text_color="white")
                    else:
                        label.configure(fg_color="#3498db")
                        label.configure(text_color="white")
                else:
                    label.configure(fg_color="#3498db")
                    label.configure(text_color="white")
            else:
                label.configure(fg_color="#1f1f1f")
                label.configure(text_color="white")

    def curselection(self):
        """Return currently selected indices"""
        return sorted(list(self.selected_indices))

    def selection_clear(self, start, end=None):
        """Clear selection"""
        self.selected_indices.clear()
        self._update_colors()

    def _show_preview(self, asset_name):
        """Show hover preview of asset image using cached templates"""
        if asset_name not in self.asset_dict:
            return

        # Store the current asset being previewed
        self._current_preview_asset = asset_name

        try:
            # Try to get from template cache first (already loaded in memory)
            img = None
            if self.template_cache is not None:
                filename = self.asset_dict[asset_name]
                template_key = f'assets/{filename}'
                cached_data = self.template_cache.get(template_key)
                if cached_data is not None:
                    # VisionManager stores templates as (img, height, width) tuples
                    img = cached_data[0]

            # Fallback to loading from disk if not in cache
            if img is None:
                filename = self.asset_dict[asset_name]
                asset_path = Path(f'assets/{filename}')
                if not asset_path.exists():
                    return
                img = cv2.imread(str(asset_path))

            if img is None:
                return

            # Check if user moved away
            if self._current_preview_asset != asset_name:
                return

            # Convert BGR to RGB
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

            # Resize to a reasonable preview size (max 300x300, maintain aspect ratio)
            max_size = 300
            h, w = img_rgb.shape[:2]
            if h > max_size or w > max_size:
                scale = min(max_size / h, max_size / w)
                new_w = int(w * scale)
                new_h = int(h * scale)
                img_rgb = cv2.resize(img_rgb, (new_w, new_h), interpolation=cv2.INTER_AREA)

            # Convert to PIL Image then CTkImage
            pil_image = Image.fromarray(img_rgb)
            photo = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=pil_image.size)

            # Final check before displaying
            if self._current_preview_asset == asset_name:
                self._create_and_display_preview(photo)

        except Exception as e:
            print(f"Error loading preview for {asset_name}: {e}")

    def _create_and_display_preview(self, photo):
        """Create and display the preview window"""
        # Double-check user is still hovering
        if self._current_preview_asset is None:
            return

        # Create preview window if it doesn't exist
        if self.preview_window is None:
            try:
                self.preview_window = ctk.CTkToplevel(self)
                self.preview_window.withdraw()  # Hide initially
                self.preview_window.overrideredirect(True)  # Remove window decorations
                self.preview_window.attributes('-topmost', True)

                # Create label for image
                self.preview_label = ctk.CTkLabel(self.preview_window, text="")
                self.preview_label.pack(padx=5, pady=5)

                # Bind events to hide preview when cursor leaves the preview window
                self.preview_label.bind("<Leave>", lambda e: self._hide_preview())
                self.preview_window.bind("<Leave>", lambda e: self._hide_preview())
            except Exception as e:
                print(f"Error creating preview window: {e}")
                self.preview_window = None
                return

        try:
            # Only show if still supposed to be previewing
            if self._current_preview_asset is None:
                return

            # Update image
            self.preview_label.configure(image=photo)
            self.preview_label.image = photo  # Keep a reference

            # Position window near cursor
            x = self.winfo_pointerx() + 15
            y = self.winfo_pointery() + 15
            self.preview_window.geometry(f"+{x}+{y}")

            # Show window
            self.preview_window.deiconify()
            self.preview_window.lift()  # Bring to front
        except Exception as e:
            print(f"Error displaying preview: {e}")
            self._hide_preview()

    def _hide_preview(self):
        """Hide hover preview"""
        self._current_preview_asset = None  # Clear the preview tracking
        if self.preview_window is not None:
            try:
                self.preview_window.withdraw()
            except Exception as e:
                pass  # Ignore errors during hide

    def select_all(self):
        """Select all items"""
        self.selected_indices = set(range(len(self.items)))
        self._update_colors()
        if self.command:
            self.command()

    def deselect_all(self):
        """Deselect all items"""
        self.selected_indices.clear()
        self._update_colors()
        if self.command:
            self.command()


class DebugTool(ctk.CTkFrame):
    def __init__(self, master, controller):
        super().__init__(master)
        self.controller = controller

        # Don't pack here - let the parent handle it
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # TabView container
        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.tabview.add("Assets")
        self.tabview.add("Functions")

        # Select Assets tab by default
        self.tabview.set("Assets")

        # ===== ASSET SELECTION PANEL =====
        left_panel = ctk.CTkFrame(self.tabview.tab("Assets"))
        left_panel.pack(fill="both", expand=True)
        left_panel.grid_columnconfigure(0, weight=1)
        left_panel.grid_rowconfigure(6, weight=1)  # Make asset list expandable (row 6 now)

        # Title
        title = ctk.CTkLabel(
            left_panel,
            text="Asset Debugger",
            font=("Arial", 14, "bold")
        )
        title.grid(row=0, column=0, pady=(0, 10))

        # Refresh from disk button
        refresh_disk_btn = ctk.CTkButton(
            left_panel,
            text="Refresh from Disk",
            command=self.refresh_from_disk,
            fg_color="#2ecc71",
            hover_color="#27ae60"
        )
        refresh_disk_btn.grid(row=1, column=0, sticky="ew", padx=5, pady=(0, 5))

        # Open assets folder button
        open_folder_btn = ctk.CTkButton(
            left_panel,
            text="Open Assets Folder",
            command=self.open_assets_folder,
            fg_color="#3498db",
            hover_color="#2980b9"
        )
        open_folder_btn.grid(row=2, column=0, sticky="ew", padx=5, pady=(0, 10))

        # Search bar with clear button
        search_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        search_frame.grid(row=3, column=0, sticky="ew", padx=5, pady=(10, 5))
        search_frame.grid_columnconfigure(0, weight=1)

        search_label = ctk.CTkLabel(
            search_frame,
            text="Search Assets:",
            font=("Arial", 10)
        )
        search_label.grid(row=0, column=0, sticky="w", pady=(0, 5))

        self.search_result_label = ctk.CTkLabel(
            search_frame,
            text="",
            font=("Arial", 9),
            text_color="gray"
        )
        self.search_result_label.grid(row=0, column=1, sticky="e", pady=(0, 5))

        search_entry_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        search_entry_frame.grid(row=4, column=0, sticky="ew", padx=5, pady=(0, 10))
        search_entry_frame.grid_columnconfigure(0, weight=1)

        self.search_var = ctk.StringVar()
        self.search_var.trace("w", lambda *args: self._debounced_filter())
        self.search_entry = ctk.CTkEntry(
            search_entry_frame,
            textvariable=self.search_var,
            placeholder_text="Type to search..."
        )
        self.search_entry.grid(row=0, column=0, sticky="ew", padx=(0, 5))

        # Clear search button
        self.clear_search_btn = ctk.CTkButton(
            search_entry_frame,
            text="✕",
            width=30,
            command=self.clear_search,
            fg_color="#e74c3c",
            hover_color="#c0392b"
        )
        self.clear_search_btn.grid(row=0, column=1)

        # Asset list with multi-select
        list_label = ctk.CTkLabel(
            left_panel,
            text="Assets (Click to toggle select, hover to preview):",
            font=("Arial", 10)
        )
        list_label.grid(row=5, column=0, sticky="w", padx=5, pady=(10, 5))

        # Use custom listbox for multi-select
        self.asset_listbox = SimpleMultiSelectListbox(
            left_panel,
            command=self.on_asset_selected,
            asset_dict={},  # Will be populated in load_assets
            template_cache=controller.vision_manager.template_dict  # Use controller's loaded templates
        )
        self.asset_listbox.grid(row=6, column=0, sticky="nsew", padx=5, pady=(0, 10))

        # Control buttons
        button_frame = ctk.CTkFrame(left_panel)
        button_frame.grid(row=7, column=0, sticky="ew", padx=5, pady=(10, 0))
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)

        # Row 1: Select All / Deselect All
        select_all_btn = ctk.CTkButton(
            button_frame,
            text="Select All",
            command=self.select_all_assets,
            fg_color="#9b59b6",
            hover_color="#8e44ad",
            height=28
        )
        select_all_btn.grid(row=0, column=0, sticky="ew", padx=(0, 3), pady=(0, 5))

        deselect_all_btn = ctk.CTkButton(
            button_frame,
            text="Deselect All",
            command=self.deselect_all_assets,
            fg_color="#95a5a6",
            hover_color="#7f8c8d",
            height=28
        )
        deselect_all_btn.grid(row=0, column=1, sticky="ew", padx=(3, 0), pady=(0, 5))

        # Row 2: Scan / Clean
        scan_btn = ctk.CTkButton(
            button_frame,
            text="Scan Assets",
            command=self.scan_selected_assets,
            fg_color="#3498db",
            hover_color="#2980b9",
            height=32
        )
        scan_btn.grid(row=1, column=0, sticky="ew", padx=(0, 3))

        clean_btn = ctk.CTkButton(
            button_frame,
            text="Clean Detections",
            command=self.clean_detections,
            fg_color="#e74c3c",
            hover_color="#c0392b",
            height=32
        )
        clean_btn.grid(row=1, column=1, sticky="ew", padx=(3, 0))

        # Status label
        self.status_label = ctk.CTkLabel(
            left_panel,
            text="Ready",
            text_color="white"
        )
        self.status_label.grid(row=8, column=0, sticky="w", padx=5, pady=(10, 0))

        # Threshold Slider
        threshold_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        threshold_frame.grid(row=8, column=0, sticky="ew", padx=5, pady=(10, 0))
        threshold_frame.grid_columnconfigure(0, weight=1)
        threshold_frame.grid_columnconfigure(1, weight=0)

        self.threshold_label = ctk.CTkLabel(
            threshold_frame,
            text="Threshold: 90%",
            font=("Arial", 12)
        )
        self.threshold_label.grid(row=0, column=0, sticky="w")

        self.threshold_slider = ctk.CTkSlider(
            threshold_frame,
            from_=1,
            to=100,
            number_of_steps=99,
            command=self.update_threshold_label
        )
        self.threshold_slider.set(90)  # Default threshold is 0.9 (90%)
        self.threshold_slider.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(5, 0))

        # Grayscale option
        self.grayscale_var = ctk.BooleanVar(value=False)
        self.grayscale_checkbox = ctk.CTkCheckBox(
            threshold_frame,
            text="Grayscale Match",
            variable=self.grayscale_var,
            font=("Arial", 12)
        )
        self.grayscale_checkbox.grid(row=2, column=0, columnspan=2, sticky="w", pady=(5, 0))

        # Initialize data
        self.all_assets = {}
        self.filtered_assets = []
        self.selected_assets = []
        self.current_matches = {}
        self.gui_reference = None  # Reference to main GUI for drawing
        self.asset_colors = {}  # Maps asset name -> color
        self.available_colors = [
            (0, 255, 0),      # Green
            (255, 0, 0),      # Blue
            (0, 0, 255),      # Red
            (0, 255, 255),    # Yellow
            (255, 0, 255),    # Magenta
            (255, 255, 0),    # Cyan
            (128, 0, 255),    # Purple
            (0, 128, 255),    # Orange
            (255, 128, 0),    # Sky blue
            (128, 255, 0),    # Lime
            (255, 0, 128),    # Pink
            (0, 255, 128),    # Spring green
        ]
        self.color_index = 0

        # Debouncing for search
        self._filter_after_id = None

        # Setup Functions Tab
        self._setup_functions_tab()

        # Load assets
        self.load_assets()

    def load_assets(self):
        """Load all assets from Constants.py"""
        try:
            import Constants
            # Reload the module to get fresh data
            importlib.reload(Constants)

            self.all_assets = {}
            for attr in dir(Constants.ASSETS):
                if attr.startswith('_'):
                    continue
                value = getattr(Constants.ASSETS, attr)
                if isinstance(value, str) and value.endswith('.png'):
                    asset_path = Path(f'assets/{value}')
                    if asset_path.exists():
                        self.all_assets[attr] = value
            
            # Load ads
            ads_dir = getattr(Constants, 'ADS_DIR', 'ads')
            ads_path = Path('assets') / ads_dir
            if ads_path.exists():
                for file in ads_path.glob('*.png'):
                    key = f"{ads_dir}/{file.name}"
                    self.all_assets[key] = key

            # Update asset_dict for hover preview
            self.asset_listbox.asset_dict = self.all_assets

            self.asset_listbox.delete(0, "end")
            for asset_name in sorted(self.all_assets.keys()):
                self.asset_listbox.insert("end", asset_name)

            self.filtered_assets = sorted(self.all_assets.keys())
            self.status_label.configure(text=f"Loaded {len(self.all_assets)} assets")
        except Exception as e:
            self.status_label.configure(text=f"Error loading: {str(e)}", text_color="red")

    def open_assets_folder(self):
        """Open the assets folder in file explorer"""
        try:
            assets_path = Path("assets").absolute()
            if not assets_path.exists():
                self.status_label.configure(text="Assets folder not found!", text_color="orange")
                return

            # Open folder based on OS
            if os.name == 'nt':  # Windows
                os.startfile(str(assets_path))
            elif os.name == 'posix':  # macOS/Linux
                subprocess.run(['open' if sys.platform == 'darwin' else 'xdg-open', str(assets_path)])

            self.status_label.configure(text="Opened assets folder", text_color="#2ecc71")
        except Exception as e:
            self.status_label.configure(text=f"Error opening folder: {str(e)}", text_color="red")

    def refresh_from_disk(self):
        """Refresh assets from disk and reload Constants.py"""
        self.status_label.configure(text="Optimizing and refreshing assets...", text_color="orange")
        self.update()

        def do_refresh():
            try:
                # Import crush_assets function
                from HelperFunctions import crush_assets

                # Run crush_assets to optimize assets
                crush_assets()

                # Remove Constants from sys.modules to force reload
                if 'Constants' in sys.modules:
                    del sys.modules['Constants']

                # Reload the controller's template dict
                self.controller.load_templates()

                # Clear search and selection before reloading
                self.after(0, lambda: self.search_var.set(""))
                self.after(0, self.deselect_all_assets)

                # Load assets fresh using after to update UI on main thread
                self.after(0, self.load_assets)
                self.after(0, lambda: self.status_label.configure(
                    text="Assets optimized and refreshed!",
                    text_color="#2ecc71"
                ))
            except Exception as e:
                self.after(0, lambda: self.status_label.configure(
                    text=f"Refresh failed: {str(e)}",
                    text_color="red"
                ))

        # Run refresh in background thread to avoid blocking UI
        refresh_thread = threading.Thread(target=do_refresh, daemon=True)
        refresh_thread.start()

    def clear_search(self):
        """Clear the search box"""
        self.search_var.set("")
        self.search_entry.focus()

    def _debounced_filter(self):
        """Debounce the filter to avoid flickering during typing"""
        # Cancel any pending filter call
        if self._filter_after_id is not None:
            self.after_cancel(self._filter_after_id)

        # Show loading indicator
        current_text = self.search_result_label.cget("text")
        if not current_text.endswith("..."):
            self.search_result_label.configure(text="Searching...", text_color="#3498db")

        # Schedule new filter call after 50ms (reduced from 150ms for better responsiveness)
        self._filter_after_id = self.after(50, self.filter_assets)

    def _smart_match(self, search_term, asset_name):
        """
        Smart matching algorithm that scores matches.
        Returns (matched: bool, score: int)
        Higher score = better match
        """
        search_lower = search_term.lower()
        asset_lower = asset_name.lower()

        # Exact match - highest priority
        if search_lower == asset_lower:
            return True, 1000

        # Starts with search term - very high priority
        if asset_lower.startswith(search_lower):
            return True, 900

        # Contains search term as whole word - high priority
        if search_lower in asset_lower:
            # Bonus for word boundary match
            if f"_{search_lower}" in asset_lower or f"{search_lower}_" in asset_lower:
                return True, 800
            return True, 700

        # Fuzzy matching - check if all characters appear in order
        search_idx = 0
        for char in asset_lower:
            if search_idx < len(search_lower) and char == search_lower[search_idx]:
                search_idx += 1

        if search_idx == len(search_lower):
            # All characters found in order - medium priority
            return True, 500

        # No match
        return False, 0

    def filter_assets(self):
        """Filter assets based on search query with smart matching"""
        search_term = self.search_var.get().strip()

        if not search_term:
            # No search term - show all assets
            search_filtered = sorted(self.all_assets.keys())
            self.search_result_label.configure(text="", text_color="gray")
        else:
            # Apply smart matching
            matches = []
            for asset in self.all_assets.keys():
                matched, score = self._smart_match(search_term, asset)
                if matched:
                    matches.append((asset, score))

            # Sort by score (descending), then alphabetically
            matches.sort(key=lambda x: (-x[1], x[0]))
            search_filtered = [asset for asset, _ in matches]

            # Update result count with color feedback
            count = len(search_filtered)
            total = len(self.all_assets)
            if count == 0:
                self.search_result_label.configure(text=f"{count}/{total}", text_color="#e74c3c")  # Red for no results
            else:
                self.search_result_label.configure(text=f"{count}/{total}", text_color="gray")

        # Put selected assets first, then filtered results
        selected_assets_list = [a for a in self.selected_assets if a in self.all_assets and a in search_filtered]
        other_filtered_assets = [a for a in search_filtered if a not in selected_assets_list]

        self.filtered_assets = selected_assets_list + other_filtered_assets

        # Update listbox
        self.asset_listbox.delete(0, "end")

        for asset_name in self.filtered_assets:
            self.asset_listbox.insert("end", asset_name)

        # Re-select the assets that are at the top (the selected ones)
        for i in range(len(selected_assets_list)):
            self.asset_listbox.selected_indices.add(i)

        # Update colors for restored selection
        self.asset_listbox._update_colors(self.asset_colors)

        # Force scrollable frame to update its scrollbar and content size
        self.asset_listbox.scrollable_frame.update_idletasks()

        # Update scroll region to match actual content
        canvas = self.asset_listbox.scrollable_frame._parent_canvas
        canvas.configure(scrollregion=canvas.bbox("all"))

        # Force canvas to recalculate if scrollbar is needed
        canvas.update_idletasks()

        # Process the selection to update colors
        self._process_selection()

    def on_asset_selected(self):
        """Handle asset selection and assign colors"""
        # Schedule this to run after current event to avoid blocking
        self.after_idle(self._process_selection)

    def _process_selection(self):
        """Process selection changes"""
        selected_indices = self.asset_listbox.curselection()
        new_selected_assets = [
            self.filtered_assets[i] for i in selected_indices
        ]

        # Assign colors to newly selected assets
        for asset in new_selected_assets:
            if asset not in self.asset_colors:
                # Assign next available color
                color = self.available_colors[self.color_index % len(self.available_colors)]
                self.asset_colors[asset] = color
                self.color_index += 1

        # Remove colors from deselected assets
        for asset in list(self.asset_colors.keys()):
            if asset not in new_selected_assets:
                del self.asset_colors[asset]

        self.selected_assets = new_selected_assets

        # Update listbox colors to show assigned colors
        self.asset_listbox._update_colors(self.asset_colors)

        # Update status label
        if self.selected_assets:
            count = len(self.selected_assets)
            assets_str = ", ".join(self.selected_assets[:3])
            if count > 3:
                assets_str += f", +{count - 3} more"
            self.status_label.configure(
                text=f"Selected: {assets_str}",
                text_color="white"
            )
        else:
            self.status_label.configure(
                text="No assets selected",
                text_color="white"
            )

    def select_all_assets(self):
        """Select all visible assets"""
        self.asset_listbox.select_all()

    def deselect_all_assets(self):
        """Deselect all assets"""
        self.asset_listbox.deselect_all()
        self.selected_assets = []
        self.asset_colors = {}  # Clear color assignments
        self.color_index = 0  # Reset color index
        self.status_label.configure(text="All deselected", text_color="white")

    def clean_detections(self):
        """Clear all detection highlights from screen"""
        self.current_matches = {}
        self.status_label.configure(text="Detections cleaned", text_color="white")

    def scan_selected_assets(self):
        """Scan for selected assets in current frame"""
        if not self.selected_assets:
            self.status_label.configure(text="No assets selected!", text_color="orange")
            return

        self.status_label.configure(text="Scanning...", text_color="orange")
        self.update()

        # Run scan in thread to avoid blocking UI
        scan_thread = threading.Thread(target=self._perform_scan, daemon=True)
        scan_thread.start()

    def _perform_scan(self):
        """Perform template matching for selected assets"""
        self.current_matches = {}

        try:
            # Get current frame from controller
            frame = self.controller.take_screenshot()
            matches_found = 0

            for asset_name in self.selected_assets:
                filename = self.all_assets[asset_name]
                template_path = f'assets/{filename}'

                try:
                    template = cv2.imread(template_path, cv2.IMREAD_COLOR)
                    if template is None:
                        continue

                    h, w = template.shape[:2]
                    
                    # Use full frame for debug scanning to find assets anywhere
                    img_to_match = frame
                    crop_x, crop_y = 0, 0

                    # Apply grayscale if selected
                    if self.grayscale_var.get():
                        img_to_match = cv2.cvtColor(img_to_match, cv2.COLOR_BGR2GRAY)
                        template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)

                    result = cv2.matchTemplate(img_to_match, template, cv2.TM_CCOEFF_NORMED)
                    threshold = self.threshold_slider.get() / 100.0
                    locations = np.where(result >= threshold)

                    if len(locations[0]) > 0:
                        # --- NMS / Grouping Logic ---
                        # Zip into (y, x) tuples for sorting/grouping
                        locs = list(zip(locations[0], locations[1]))
                        
                        # Sort by score (descending)
                        locs.sort(key=lambda pt: result[pt[0]][pt[1]], reverse=True)
                        
                        # Group nearby points (within 5px)
                        location_groups = []
                        for loc in locs:
                            if not location_groups:
                                location_groups.append([loc])
                            else:
                                for group in location_groups:
                                    if abs(group[-1][0] - loc[0]) < 5 and abs(group[-1][1] - loc[1]) < 5:
                                        group.append(loc)
                                        break
                                else:
                                    location_groups.append([loc])
                        
                        # Calculate average top-left for each group and adjust to full frame
                        points = []
                        for group in location_groups:
                            avg_y = sum(l[0] for l in group) // len(group)
                            avg_x = sum(l[1] for l in group) // len(group)
                            points.append((avg_x + crop_x, avg_y + crop_y))
                        # ---------------------------
                        
                        # Calculate regions
                        frame_h, frame_w = frame.shape[:2]
                        match_regions = []
                        
                        # Prepare for scaling if needed
                        dm = self.controller.device_manager
                        scaled_points = []
                        scaled_w, scaled_h = w, h
                        
                        if dm.resized:
                            scaled_w = dm.scale_x(w)
                            scaled_h = dm.scale_y(h)

                        for x, y in points:
                            # Region logic uses unscaled coordinates (relative to the scanned frame)
                            # Check if the ENTIRE asset fits within the quadrant boundaries
                            # If it crosses the center line, it belongs to the broader region (e.g. Top instead of Top-Left)
                            
                            r = 0
                            # Vertical check
                            if y + h <= frame_h // 2:
                                r |= Region.TOP
                            elif y >= frame_h // 2:
                                r |= Region.BOTTOM
                            
                            # Horizontal check
                            if x + w <= frame_w // 2:
                                r |= Region.LEFT
                            elif x >= frame_w // 2:
                                r |= Region.RIGHT
                            
                            region_name = []
                            if r == 0:
                                region_name.append("All")
                            else:
                                if r & Region.TOP: region_name.append("Top")
                                if r & Region.BOTTOM: region_name.append("Bottom")
                                if r & Region.LEFT: region_name.append("Left")
                                if r & Region.RIGHT: region_name.append("Right")
                            
                            match_regions.append("-".join(region_name))
                            
                            # Scale points for drawing on the original frame
                            if dm.resized:
                                sx = dm.scale_x(x)
                                sy = dm.scale_y(y)
                                scaled_points.append((sx, sy))
                            else:
                                scaled_points.append((x, y))

                        self.current_matches[asset_name] = {
                            'points': scaled_points,
                            'template_size': (scaled_w, scaled_h),
                            'count': len(points),
                            'regions': match_regions
                        }
                        matches_found += len(points)
                except Exception as e:
                    print(f"Error scanning {asset_name}: {e}")

            self.after(0, self._update_scan_results, matches_found)
        except Exception as e:
            self.after(0, lambda: self.status_label.configure(
                text=f"Scan error: {str(e)}",
                text_color="red"
            ))

    def _update_scan_results(self, matches_found):
        """Update UI with scan results"""
        if self.current_matches:
            # Simplified UI message
            result_text = f"Found {matches_found} matches.\nCheck logs for details."
            
            # Detailed log message
            log_msg = f"Scan Results - Found {matches_found} matches:\n"
            
            for asset, data in self.current_matches.items():
                count = data['count']
                regions_list = data.get('regions', [])
                # Format regions string if available
                regions_str = f" [{', '.join(sorted(list(set(regions_list))))}]" if regions_list else ""
                
                log_msg += f"• {asset}: {count}{regions_str}\n"
                
            self.status_label.configure(text=result_text, text_color="#2ecc71")
            
            # Log to main GUI
            try:
                # self.master is main_frame, self.master.master is ControllerGUI
                if hasattr(self.master.master, 'append_log'):
                    self.master.master.append_log(log_msg.strip(), "info")
            except Exception as e:
                print(f"Failed to log to GUI: {e}")
        else:
            self.status_label.configure(text="No matches found", text_color="orange")
            try:
                if hasattr(self.master.master, 'append_log'):
                    self.master.master.append_log("Scan complete: No matches found", "warning")
            except Exception:
                pass

    def draw_detections_on_frame(self, frame):
        """Draw detection boxes on the given frame (called by main GUI)"""
        if not self.current_matches:
            return frame

        # Draw match highlights
        for asset_name, data in self.current_matches.items():
            # Get a color based on asset name hash
            color = self._get_color_for_asset(asset_name)
            regions = data.get('regions', [])
            
            for i, (x, y) in enumerate(data['points']):
                w, h = data['template_size']
                cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
                
                # Draw label with background for better visibility
                label = asset_name
                if i < len(regions):
                    label += f" ({regions[i]})"

                font_scale = 0.7
                thickness = 2
                (text_w, text_h), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)
                
                # Draw background rectangle
                cv2.rectangle(frame, (x, y - text_h - 10), (x + text_w, y), (255, 255, 255), -1)
                
                # Draw text in black
                cv2.putText(
                    frame,
                    label,
                    (x, y - 5),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    font_scale,
                    (0, 0, 0),  # Black text
                    thickness
                )

        return frame

    def _get_color_for_asset(self, asset_name):
        """Get the assigned color for an asset"""
        # Return the color that was assigned when the asset was selected
        return self.asset_colors.get(asset_name, (0, 255, 0))  # Default to green if not found

    def _setup_functions_tab(self):
        tab = self.tabview.tab("Functions")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1) # Code area expands
        
        # --- Code Area ---
        # Header
        ctk.CTkLabel(tab, text="Scripting (Implicit 'controller' context)", font=("Arial", 12, "bold")).grid(row=0, column=0, sticky="w", padx=10, pady=(10, 5))

        self.code_input = ctk.CTkTextbox(tab, font=("Consolas", 12))
        self.code_input.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        
        # --- Actions ---
        action_frame = ctk.CTkFrame(tab, fg_color="transparent")
        action_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=5)
        action_frame.grid_columnconfigure(0, weight=1)

        self.run_btn = ctk.CTkButton(action_frame, text="Run Code (Ctrl+Enter)", command=self.run_debug_code, height=32)
        self.run_btn.grid(row=0, column=0, sticky="ew", padx=(0, 5))

        self.stop_btn = ctk.CTkButton(
            action_frame, 
            text="Stop", 
            width=60,
            fg_color="#e67e22", 
            hover_color="#d35400",
            state="disabled",
            command=self.stop_debug_code
        )
        self.stop_btn.grid(row=0, column=1, padx=(0, 5))

        ctk.CTkButton(
            action_frame, 
            text="Clear", 
            width=60,
            fg_color="#e74c3c", 
            hover_color="#c0392b",
            command=lambda: self.code_input.delete("1.0", "end")
        ).grid(row=0, column=2)

        # Bind Ctrl+Enter to run
        self.code_input.bind("<Control-Return>", lambda e: self.run_debug_code())

        # --- Output Log ---
        ctk.CTkLabel(tab, text="Output:", font=("Arial", 12, "bold")).grid(row=3, column=0, sticky="w", padx=10, pady=(5,0))
        
        self.output_log = ctk.CTkTextbox(tab, height=120, font=("Consolas", 11), state="disabled")
        self.output_log.grid(row=4, column=0, sticky="ew", padx=10, pady=(0,10))

    def stop_debug_code(self):
        if self.controller:
            self.controller.cancel_flag = True
            self.log_output("!!! Stop signal sent to controller.")

    def run_debug_code(self):
        code = self.code_input.get("1.0", "end-1c")
        if not code.strip():
            return
            
        self.run_btn.configure(state="disabled", text="Running...")
        self.stop_btn.configure(state="normal")
        self.log_output(f">>> Running code...")
        
        # Reset cancel flag before starting
        if self.controller:
            self.controller.cancel_flag = False
        
        def thread_target():
            try:
                # Helper to log to our window safely
                def custom_print(*args, **kwargs):
                    text = " ".join(map(str, args))
                    self.after(0, lambda: self.log_output(text))
                    
                # Execute
                local_vars = {
                    'controller': self.controller,
                    'print': custom_print,
                    'ctk': ctk,
                    'cv2': cv2,
                    'np': np,
                    'self': self,
                }
                
                # Inject controller attributes for implicit access
                # e.g. battle_manager.auto_battle() instead of controller.battle_manager.auto_battle()
                for name in dir(self.controller):
                    if not name.startswith('_'): # Skip private/protected
                        try:
                            local_vars[name] = getattr(self.controller, name)
                        except Exception:
                            pass
                
                exec(code, globals(), local_vars)
                self.after(0, lambda: self.log_output(">>> Execution finished."))
            except Exception as e:
                # Catch the special ExecutionFlag error often used to stop
                if "ExecutionFlag" in str(type(e)):
                    self.after(0, lambda: self.log_output("!!! Execution stopped by user."))
                else:
                    import traceback
                    tb = traceback.format_exc()
                    self.after(0, lambda: self.log_output(f"!!! Error:\n{tb}"))
            finally:
                self.after(0, lambda: self.run_btn.configure(state="normal", text="Run Code"))
                self.after(0, lambda: self.stop_btn.configure(state="disabled"))

        threading.Thread(target=thread_target, daemon=True).start()

    def log_output(self, message):
        self.output_log.configure(state="normal")
        self.output_log.insert("end", str(message) + "\n")
        self.output_log.see("end")
        self.output_log.configure(state="disabled")

    def update_threshold_label(self, value):
        """Update the threshold label text"""
        self.threshold_label.configure(text=f"Threshold: {int(value)}%")
