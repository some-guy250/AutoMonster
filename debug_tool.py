import customtkinter as ctk
import cv2
import numpy as np
from PIL import Image
import threading
import importlib
import sys
import os
import subprocess
from pathlib import Path
import scrcpy

# Try to import CTkListbox, fallback to a simple implementation if not available
try:
    from CTkListbox import CTkListbox
    HAS_CTKLISTBOX = True
except ImportError:
    HAS_CTKLISTBOX = False


class SimpleMultiSelectListbox(ctk.CTkFrame):
    """Simple multi-select listbox implementation using CTkScrollableFrame"""
    def __init__(self, master, command=None, asset_dict=None, **kwargs):
        super().__init__(master, **kwargs)
        self.command = command
        self.asset_dict = asset_dict or {}  # Maps asset name -> filename
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
        frame = ctk.CTkFrame(self.scrollable_frame, fg_color="transparent")
        frame.grid(row=index, column=0, sticky="ew", padx=2, pady=2)
        frame.grid_columnconfigure(0, weight=1)

        label = ctk.CTkLabel(
            frame,
            text=item,
            anchor="w",
            fg_color="#1f1f1f",
            corner_radius=4
        )
        label.grid(row=0, column=0, sticky="ew", padx=5, pady=8)

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
                label = widget.winfo_children()[0]
                if changed_index in self.selected_indices:
                    label.configure(fg_color="#3498db", text_color="white")
                else:
                    label.configure(fg_color="#1f1f1f", text_color="white")
            return

        # Otherwise update all
        for i, widget in enumerate(self.item_widgets):
            label = widget.winfo_children()[0]
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

    def _sort_items(self):
        """Move selected items to the top"""
        if not self.selected_indices:
            return

        # Separate selected and unselected items
        selected_items = []
        unselected_items = []

        for i, item in enumerate(self.items):
            if i in self.selected_indices:
                selected_items.append(item)
            else:
                unselected_items.append(item)

        # Recreate items list with selected first
        self.items = selected_items + unselected_items

        # Update selected indices to match new positions
        new_selected = set(range(len(selected_items)))
        self.selected_indices = new_selected

        # Recreate widgets
        for widget in self.item_widgets:
            widget.destroy()
        self.item_widgets = []

        for i, item in enumerate(self.items):
            self._create_item_widget(i, item)

        self._update_colors()

    def _show_preview(self, asset_name):
        """Show hover preview of asset image"""
        if asset_name not in self.asset_dict:
            return

        filename = self.asset_dict[asset_name]
        asset_path = Path(f'assets/{filename}')

        if not asset_path.exists():
            return

        # Store the current asset being previewed to detect if user moved away
        self._current_preview_asset = asset_name

        def load_and_show():
            try:
                # Load image with OpenCV
                img = cv2.imread(str(asset_path))
                if img is None:
                    return

                # Convert BGR to RGB
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

                # Resize to a reasonable preview size (max 300x300, maintain aspect ratio)
                max_size = 300
                h, w = img.shape[:2]
                if h > max_size or w > max_size:
                    scale = min(max_size / h, max_size / w)
                    new_w = int(w * scale)
                    new_h = int(h * scale)
                    img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)

                # Convert to PIL Image then CTkImage for proper customtkinter support
                pil_image = Image.fromarray(img)
                photo = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=pil_image.size)

                # Only show if still hovering over the same asset
                if self._current_preview_asset != asset_name:
                    return

                # Use after to ensure this runs on main thread (create window on main thread)
                self.after(0, lambda: self._create_and_display_preview(photo))

            except Exception as e:
                print(f"Error loading preview for {asset_name}: {e}")

        # Load image in background thread to avoid blocking hover
        preview_thread = threading.Thread(target=load_and_show, daemon=True)
        preview_thread.start()

    def _create_and_display_preview(self, photo):
        """Create and display the preview window (must run on main thread)"""
        # Double-check user is still hovering
        if self._current_preview_asset is None:
            return

        # Create preview window if it doesn't exist (MUST be on main thread)
        if self.preview_window is None:
            try:
                self.preview_window = ctk.CTkToplevel(self)
                self.preview_window.withdraw()  # Hide initially
                self.preview_window.overrideredirect(True)  # Remove window decorations
                self.preview_window.attributes('-topmost', True)

                # Create label for image
                self.preview_label = ctk.CTkLabel(self.preview_window, text="")
                self.preview_label.pack(padx=5, pady=5)

                # Bind events to hide preview when it loses focus or cursor leaves
                self.preview_label.bind("<Leave>", lambda e: self._hide_preview())
            except Exception as e:
                print(f"Error creating preview window: {e}")
                self.preview_window = None
                return

        try:
            # Update image
            self.preview_label.configure(image=photo)
            self.preview_label.image = photo  # Keep a reference

            # Position window near cursor
            x = self.winfo_pointerx() + 15
            y = self.winfo_pointery() + 15
            self.preview_window.geometry(f"+{x}+{y}")
            self.preview_window.deiconify()
        except Exception as e:
            print(f"Error displaying preview: {e}")

    def _hide_preview(self):
        """Hide hover preview"""
        self._current_preview_asset = None  # Clear the preview tracking
        if self.preview_window is not None:
            self.preview_window.withdraw()

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

        # Main container - just use full width since we're reusing main viewer
        main_container = ctk.CTkFrame(self)
        main_container.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        main_container.grid_columnconfigure(0, weight=1)
        main_container.grid_rowconfigure(0, weight=1)

        # ===== ASSET SELECTION PANEL =====
        left_panel = ctk.CTkFrame(main_container)
        left_panel.grid(row=0, column=0, sticky="nsew")
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

        # Search bar
        search_label = ctk.CTkLabel(
            left_panel,
            text="Search Assets:",
            font=("Arial", 10)
        )
        search_label.grid(row=3, column=0, sticky="w", padx=5, pady=(10, 5))

        self.search_var = ctk.StringVar()
        self.search_var.trace("w", lambda *args: self.filter_assets())
        search_entry = ctk.CTkEntry(
            left_panel,
            textvariable=self.search_var,
            placeholder_text="Type to search..."
        )
        search_entry.grid(row=4, column=0, sticky="ew", padx=5, pady=(0, 10))

        # Asset list with multi-select
        list_label = ctk.CTkLabel(
            left_panel,
            text="Assets (Click to toggle select, hover to preview):",
            font=("Arial", 10)
        )
        list_label.grid(row=5, column=0, sticky="w", padx=5, pady=(10, 5))

        # Use custom or built-in listbox for multi-select
        if HAS_CTKLISTBOX:
            self.asset_listbox = CTkListbox(
                left_panel,
                font=("Arial", 10),
                command=self.on_asset_selected,
                multiple_select=True
            )
        else:
            self.asset_listbox = SimpleMultiSelectListbox(
                left_panel,
                command=self.on_asset_selected,
                asset_dict={}  # Will be populated in load_assets
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

            # Update asset_dict for hover preview
            if not HAS_CTKLISTBOX:
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

    def filter_assets(self):
        """Filter assets based on search query"""
        search_term = self.search_var.get().lower()

        # Separate selected and non-selected assets
        search_filtered = [
            asset for asset in sorted(self.all_assets.keys())
            if search_term in asset.lower()
        ]

        # Put selected assets first, then filtered results
        selected_assets_list = [a for a in self.selected_assets if a in self.all_assets]
        other_filtered_assets = [a for a in search_filtered if a not in selected_assets_list]

        self.filtered_assets = selected_assets_list + other_filtered_assets

        # Update listbox
        self.asset_listbox.delete(0, "end")
        self.asset_listbox.selected_indices.clear()  # Clear selection indices

        for asset_name in self.filtered_assets:
            self.asset_listbox.insert("end", asset_name)

        # Re-select the assets that are at the top (the selected ones)
        for i in range(len(selected_assets_list)):
            self.asset_listbox.selected_indices.add(i)

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

        # Update listbox colors to show assigned colors (only when needed)
        if not HAS_CTKLISTBOX and self.asset_colors:
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
        if HAS_CTKLISTBOX:
            # CTkListbox doesn't have select_all, manually select
            for i in range(len(self.filtered_assets)):
                self.asset_listbox.select(i)
        else:
            self.asset_listbox.select_all()
        self.on_asset_selected()

    def deselect_all_assets(self):
        """Deselect all assets"""
        if HAS_CTKLISTBOX:
            self.asset_listbox.deselect("all")
        else:
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
                    result = cv2.matchTemplate(frame, template, cv2.TM_CCOEFF_NORMED)
                    threshold = 0.9
                    locations = np.where(result >= threshold)

                    if len(locations[0]) > 0:
                        points = list(zip(locations[1], locations[0]))
                        self.current_matches[asset_name] = {
                            'points': points,
                            'template_size': (w, h),
                            'count': len(points)
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
            result_text = f"Found {matches_found} matches:\n"
            for asset, data in self.current_matches.items():
                result_text += f"  • {asset}: {data['count']}\n"
            self.status_label.configure(text=result_text, text_color="#2ecc71")
        else:
            self.status_label.configure(text="No matches found", text_color="orange")

    def draw_detections_on_frame(self, frame):
        """Draw detection boxes on the given frame (called by main GUI)"""
        if not self.current_matches:
            return frame

        # Draw match highlights
        for asset_name, data in self.current_matches.items():
            # Get a color based on asset name hash
            color = self._get_color_for_asset(asset_name)
            for x, y in data['points']:
                w, h = data['template_size']
                cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
                # Draw label
                cv2.putText(
                    frame,
                    asset_name,
                    (x, y - 5),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    color,
                    1
                )

        return frame

    def _get_color_for_asset(self, asset_name):
        """Get the assigned color for an asset"""
        # Return the color that was assigned when the asset was selected
        return self.asset_colors.get(asset_name, (0, 255, 0))  # Default to green if not found
