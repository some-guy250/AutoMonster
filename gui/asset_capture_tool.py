"""Tool for capturing and cropping new assets from screenshots."""

import customtkinter as ctk
from tkinter import messagebox
from pathlib import Path
from typing import Optional, List, Tuple
import cv2
import numpy as np
from PIL import Image, ImageTk
from utils.logger import setup_logger
from utils.region_utils import recommend_region

logger = setup_logger()


class AssetCaptureTool(ctk.CTkToplevel):
    """Widget for capturing screenshots and cropping multiple assets."""

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.title("Capture New Assets")
        self.state('zoomed')  # Fullscreen
        self.controller = controller
        
        # Make modal (stay on top, block parent)
        self.transient(parent)
        self.grab_set()
        
        # State
        self.screenshot: Optional[np.ndarray] = None
        self.crops: List[dict] = []
        self.cropping = False
        self.crop_start: Optional[Tuple[int, int]] = None
        self.crop_end: Optional[Tuple[int, int]] = None
        self.zoom = 1.0  # Zoom level
        
        self._setup_ui()
        # Delay screenshot capture to let UI render first
        self.after(200, self.capture_screenshot)
    
    def _setup_ui(self):
        """Setup the capture tool UI."""
        # Top bar
        top_frame = ctk.CTkFrame(self)
        top_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkButton(
            top_frame,
            text="📸 Capture Screenshot",
            command=self.capture_screenshot
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            top_frame,
            text="🔄 Clear Crops",
            command=self.clear_crops
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            top_frame,
            text="💾 Save All Assets",
            command=self.save_all_assets,
            fg_color="#2ecc71"
        ).pack(side="left", padx=5)
        
        # Zoom controls
        ctk.CTkButton(
            top_frame,
            text="-",
            width=30,
            command=self.zoom_out
        ).pack(side="right", padx=2)
        
        self.zoom_label = ctk.CTkLabel(top_frame, text="100%")
        self.zoom_label.pack(side="right", padx=5)
        
        ctk.CTkButton(
            top_frame,
            text="+",
            width=30,
            command=self.zoom_in
        ).pack(side="right", padx=2)
        
        ctk.CTkButton(
            top_frame,
            text="Close",
            command=self.destroy
        ).pack(side="right", padx=5)
        
        # Main content
        content_frame = ctk.CTkFrame(self)
        content_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Left - screenshot preview
        preview_frame = ctk.CTkFrame(content_frame)
        preview_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        ctk.CTkLabel(
            preview_frame,
            text="Click and drag to crop areas (captures multiple from one screenshot)"
        ).pack(pady=5)
        
        # Canvas for screenshot + crop overlay
        self.canvas = ctk.CTkCanvas(
            preview_frame,
            bg="black",
            cursor="cross"
        )
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Button-1>", self.on_crop_start)
        self.canvas.bind("<B1-Motion>", self.on_crop_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_crop_end)
        self.canvas.bind("<MouseWheel>", self.on_scroll)
        
        # Pan state
        self.panning = False
        self.pan_start = None
        self.canvas_x_offset = 0
        self.canvas_y_offset = 0
        
        # Right - crop list
        list_frame = ctk.CTkFrame(content_frame, width=250)
        list_frame.pack(side="right", fill="y", padx=(5, 0))
        list_frame.pack_propagate(False)
        
        ctk.CTkLabel(list_frame, text="Captured Crops").pack(pady=5)
        
        # Scrollable crop list
        self.scroll_frame = ctk.CTkScrollableFrame(list_frame, height=400)
        self.scroll_frame.pack(fill="both", expand=True, padx=5, pady=5)
        self.crop_buttons = []  # Store references
    
    def capture_screenshot(self):
        """Take a new screenshot."""
        try:
            self.screenshot = self.controller.device_manager.take_screenshot()
            if self.screenshot is None or self.screenshot.size == 0:
                raise Exception("Screenshot is empty")
            self.crops.clear()
            self.update_crop_list()
            # Delay display to let window render
            self.after(100, self.display_screenshot)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to capture: {e}")
    
    def display_screenshot(self):
        """Display screenshot on canvas with crop overlays."""
        if self.screenshot is None:
            return
        
        self.canvas.delete("all")
        
        # Convert BGR to RGB (OpenCV uses BGR, PIL uses RGB)
        img_rgb = cv2.cvtColor(self.screenshot, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(img_rgb)
        
        # Get actual canvas size (may be 0 if not rendered yet)
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        # If canvas not rendered yet, use image size
        if canvas_width < 100 or canvas_height < 100:
            canvas_width = min(img_pil.size[0], 1200)
            canvas_height = min(img_pil.size[1], 700)
        
        # Calculate base scale to fit canvas
        img_width, img_height = img_pil.size
        scale_x = canvas_width / img_width
        scale_y = canvas_height / img_height
        base_scale = min(scale_x, scale_y) * 0.9
        
        # Apply zoom (start at 100% = base_scale)
        self.scale = base_scale * self.zoom
        
        # Apply pan offsets
        self.canvas.xview_scroll(self.canvas_x_offset, "units")
        self.canvas.yview_scroll(self.canvas_y_offset, "units")
        
        # Resize for display
        new_width = int(img_width * self.scale)
        new_height = int(img_height * self.scale)
        img_resized = img_pil.resize((new_width, new_height))
        
        self.photo = ImageTk.PhotoImage(image=img_resized)
        self.canvas.config(scrollregion=(0, 0, new_width, new_height))
        self.canvas.create_image(0, 0, anchor="nw", image=self.photo)
        self.canvas.xview_moveto(0)
        self.canvas.yview_moveto(0)
        
        # Draw crop overlays
        for i, crop in enumerate(self.crops):
            x1, y1 = int(crop['x1'] * self.scale), int(crop['y1'] * self.scale)
            x2, y2 = int(crop['x2'] * self.scale), int(crop['y2'] * self.scale)
            
            color = "#3498db" if i == len(self.crops) - 1 else "#2ecc71"
            self.canvas.create_rectangle(x1, y1, x2, y2, outline=color, width=3)
            self.canvas.create_text(x1 + 5, y1 + 5, text=crop['name'], fill=color, anchor="nw")
    
    def on_crop_start(self, event):
        """Start cropping."""
        self.cropping = True
        self.crop_start = (event.x, event.y)
        self.crop_end = None
    
    def on_crop_drag(self, event):
        """Draw crop rectangle while dragging."""
        if not self.cropping or self.crop_start is None:
            return
        
        # Remove previous drag rectangle
        self.canvas.delete("drag_rect")
        
        x1, y1 = self.crop_start
        x2, y2 = event.x, event.y
        self.canvas.create_rectangle(x1, y1, x2, y2, outline="#e74c3c", width=3, tags="drag_rect")
    
    def on_crop_end(self, event):
        """Finish cropping and prompt for name."""
        if not self.cropping or self.crop_start is None:
            return
        
        self.cropping = False
        self.canvas.delete("drag_rect")
        
        # Convert canvas coords back to image coords
        x1_canvas, y1_canvas = self.crop_start
        x2_canvas, y2_canvas = event.x, event.y
        
        # Normalize (ensure x1 < x2, y1 < y2)
        x1_canvas, x2_canvas = min(x1_canvas, x2_canvas), max(x1_canvas, x2_canvas)
        y1_canvas, y2_canvas = min(y1_canvas, y2_canvas), max(y1_canvas, y2_canvas)
        
        # Skip tiny crops
        if abs(x2_canvas - x1_canvas) < 10 or abs(y2_canvas - y1_canvas) < 10:
            return
        
        # Convert to image coordinates
        x1 = int(x1_canvas / self.scale)
        y1 = int(y1_canvas / self.scale)
        x2 = int(x2_canvas / self.scale)
        y2 = int(y2_canvas / self.scale)
        
        # Clamp to image bounds
        img_h, img_w = self.screenshot.shape[:2]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(img_w, x2), min(img_h, y2)
        
        # Crop the image
        cropped = self.screenshot[y1:y2, x1:x2]
        
        # Prompt for name
        from tkinter import simpledialog
        crop_num = len(self.crops) + 1
        default_name = f"Asset{crop_num}"
        name = simpledialog.askstring("Asset Name", "Enter name for this asset:", parent=self, initialvalue=default_name)
        
        if name and name.strip():
            self.crops.append({
                'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2,
                'name': name.strip(),
                'image': cropped
            })
            self.update_crop_list()
            self.display_screenshot()
        # Else: user cancelled, discard crop
    
    def zoom_in(self):
        """Zoom in."""
        self.zoom = min(3.0, self.zoom * 1.2)
        self.zoom_label.configure(text=f"{int(self.zoom*100)}%")
        self.display_screenshot()
    
    def zoom_out(self):
        """Zoom out."""
        self.zoom = max(0.5, self.zoom / 1.2)
        self.zoom_label.configure(text=f"{int(self.zoom*100)}%")
        self.display_screenshot()
    
    def on_scroll(self, event):
        """Scroll/pan the image when zoomed in."""
        if self.zoom <= 1.0:
            return
        
        # Scroll the canvas
        if event.delta > 0:
            self.canvas.yview_scroll(-1, "units")
        else:
            self.canvas.yview_scroll(1, "units")
    
    def update_crop_list(self):
        """Update the crop list with buttons."""
        # Clear existing buttons
        for btn in self.crop_buttons:
            btn.destroy()
        self.crop_buttons.clear()
        
        for i, crop in enumerate(self.crops):
            w, h = crop['x2'] - crop['x1'], crop['y2'] - crop['y1']
            
            # Create button for each crop
            btn_frame = ctk.CTkFrame(self.scroll_frame)
            btn_frame.pack(fill="x", pady=2)
            
            # Crop name label
            ctk.CTkLabel(
                btn_frame,
                text=f"{crop['name']} ({w}x{h})",
                anchor="w"
            ).pack(side="left", fill="x", expand=True, padx=(0, 3))
            
            # Delete button
            ctk.CTkButton(
                btn_frame,
                text="✕",
                width=25,
                command=lambda idx=i: self.delete_crop(idx),
                fg_color="#e74c3c",
                hover_color="#c0392b",
                height=28
            ).pack(side="right")
            
            self.crop_buttons.append(btn_frame)
    
    def delete_crop(self, index):
        """Delete a crop."""
        self.crops.pop(index)
        self.update_crop_list()
        self.display_screenshot()
    
    def clear_crops(self):
        """Clear all captured crops."""
        self.crops.clear()
        self.update_crop_list()
        self.display_screenshot()
    
    def save_all_assets(self):
        """Save all crops as assets."""
        if not self.crops:
            messagebox.showwarning("Warning", "No crops to save!")
            return
        
        saved_count = 0
        new_entries = []
        for crop in self.crops:
            if self.save_single_asset(crop):
                saved_count += 1
                new_entries.append(crop)
        
        logger.info(f"Saved {saved_count}/{len(self.crops)} asset(s)!")
        self.controller.log_gui(f"Saved {saved_count}/{len(self.crops)} asset(s)!", "success")
        
        # Log info for manual addition
        logger.info("To add these assets, give this to your AI assistant:")
        self.controller.log_gui("To add these assets, give this to your AI assistant:", "info")
        for crop in self.crops:
            name_upper = crop['name'].upper()
            filename = crop['name'].lower() + ".png"
            x1, y1, x2, y2 = crop['x1'], crop['y1'], crop['x2'], crop['y2']
            w, h = x2 - x1, y2 - y1
            region = recommend_region(x1, y1, w, h)
            msg = f"  - {name_upper} = \"{filename}\" (region: {x1},{y1},{w}x{h}, recommended: {region})"
            logger.info(msg)
            self.controller.log_gui(msg, "info")
        logger.info("Add to: utils/assets.py + config/regions.py")
        self.controller.log_gui("Add to: utils/assets.py + config/regions.py", "info")
    
    def save_single_asset(self, crop: dict) -> bool:
        """Save a single crop as an asset."""
        try:
            name = crop['name'].strip()
            if not name:
                return False
            
            # Convert to snake_case filename
            filename = "".join([f"{word[0].upper()}{word[1:]}" if word[0].islower() else word.lower() 
                               for word in name.replace('_', ' ').split()]).lower()
            # Simple conversion: SkipButton -> skipbutton.png
            filename = name.lower() + ".png"
            
            # Save to asset_images (convert BGR to RGB)
            asset_path = Path("asset_images") / filename
            rgb_image = cv2.cvtColor(crop['image'], cv2.COLOR_BGR2RGB)
            Image.fromarray(rgb_image).save(asset_path)
            
            return True
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save {crop['name']}: {e}")
            return False
    

