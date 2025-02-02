import json
import logging
import os
import sys
import threading
from datetime import datetime

import customtkinter as ctk
import cv2
import scrcpy
from PIL import Image

import AutoMonsterErrors
from AutoMonster import Controller
from Constants import GUI_COMMANDS, GUI_COMMAND_DESCRIPTIONS
from command_frame import CommandFrame
from device_selection_frame import DeviceSelectionFrame

DEFAULTS_FILE = "defaults.json"

if os.path.isfile("version.txt"):
    with open("version.txt", "r") as file:
        __version__ = file.read().strip()


class ControllerGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Set window icon
        if os.path.exists("assets/favicon.ico"):
            self.iconbitmap("assets/favicon.ico")

        self.title("AutoMonster")
        self.minsize(400, 450)  # Smaller initial size for device selection
        # stop resizing
        self.resizable(False, False)

        # Initialize frames
        self.device_frame = DeviceSelectionFrame(self, self.on_device_selected)
        self.main_frame = ctk.CTkFrame(self)  # Will contain all the main UI elements

        # Show device selection first
        self.show_device_selection()

    def show_device_selection(self):
        self.main_frame.pack_forget()
        self.device_frame.pack(expand=True, fill="both", padx=20, pady=20)
        self.center_window()

    def show_main_interface(self):
        self.device_frame.pack_forget()
        self.main_frame.pack(expand=True, fill="both")
        self.geometry("1200x800")  # Set size for main interface
        self.state("zoomed")  # Maximize window
        self.resizable(True, True)  

    def center_window(self):
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')

    def on_device_selected(self, device):
        # Show loading progress
        self.device_frame.diable_connect_btns()
        self.device_frame.show_loading()

        def set_controller():
            self.controller = Controller()
            
        thread = threading.Thread(target=set_controller, daemon=True)
        thread.start()

        # Wait for controller to be initialized
        while thread.is_alive():
            self.update()
            
        # Hide loading progress
        self.device_frame.hide_loading()

        self.init_main_interface()
        self.show_main_interface()

    def init_main_interface(self):
        # Move all the main interface initialization code here
        # (Everything that was previously in __init__ after device selection)
        self.fonts = {
            "header": ("Arial", 16, "bold"),
            "subheader": ("Arial", 14, "bold"),
            "normal": ("Arial", 12),
            "button": ("Arial", 13, "bold"),
        }

        # Define panel width
        self.panel_width = 300
        self.panel_visible = True

        # Define available commands and their parameters
        self.commands = GUI_COMMANDS
        self.command_descriptions = GUI_COMMAND_DESCRIPTIONS

        self.override_parameter_defaults()

        # Create main layout
        self.main_frame.grid_columnconfigure(0, weight=0, minsize=30)  # Left toggle button
        self.main_frame.grid_columnconfigure(1, weight=0, minsize=self.panel_width)  # Command frame
        self.main_frame.grid_columnconfigure(2, weight=1)  # Preview
        self.main_frame.grid_columnconfigure(3, weight=0, minsize=self.panel_width)  # Info frame
        self.main_frame.grid_columnconfigure(4, weight=0, minsize=30)  # Right toggle button
        self.main_frame.grid_rowconfigure(0, weight=3)  # Row for main content
        self.main_frame.grid_rowconfigure(1, weight=1)  # Row for logs

        # Add panel visibility states
        self.panel_visible = True
        self.info_visible = True

        # Create left toggle button
        self.toggle_button = ctk.CTkButton(
            self.main_frame,
            text="≪",
            width=30,
            height=24,
            command=self.toggle_panel
        )
        self.toggle_button.grid(row=0, column=0, sticky="ns", padx=(2, 0), pady=10)

        # Create right toggle button for info panel
        self.info_toggle_button = ctk.CTkButton(
            self.main_frame,
            text="≫",
            width=30,
            height=24,
            command=self.toggle_info_panel
        )
        self.info_toggle_button.grid(row=0, column=4, sticky="ns", padx=(0, 2), pady=10)

        # Info panel - Move this before command frame initialization
        self.info_frame = ctk.CTkFrame(self.main_frame, width=self.panel_width)
        self.info_frame.grid(row=0, column=3, padx=10, pady=10, sticky="nsew")
        self.info_frame.grid_propagate(False)

        # Info panel content
        self.info_title = ctk.CTkLabel(self.info_frame, text="", font=self.fonts["header"])
        self.info_title.pack(padx=10, pady=(10, 5), anchor="w")

        # Add separator
        info_separator = ctk.CTkFrame(self.info_frame, height=2)
        info_separator.pack(fill="x", padx=10, pady=(0, 10))

        # Description text
        self.info_description = ctk.CTkTextbox(self.info_frame, wrap="word", height=200, font=("Arial", 14))
        self.info_description.pack(fill="both", expand=True, padx=10, pady=5)
        self.info_description.configure(state="disabled")

        # Command selection frame with fixed width
        self.command_frame = ctk.CTkFrame(self.main_frame, width=self.panel_width)
        self.command_frame.grid(row=0, column=1, padx=(0, 10), pady=10, sticky="nsew")
        self.command_frame.grid_propagate(False)  # Prevent frame from shrinking

        # Create inner frame for content
        self.command_inner_frame = ctk.CTkFrame(self.command_frame)
        self.command_inner_frame.pack(expand=True, fill="both", padx=5, pady=5)
        self.command_inner_frame.pack_propagate(False)  # Prevent inner frame from shrinking

        # Header frame
        header_frame = ctk.CTkFrame(self.command_inner_frame)
        header_frame.pack(fill="x", padx=5, pady=5)

        # Title
        title = ctk.CTkLabel(header_frame, text="Commands", font=self.fonts["header"])
        title.pack(side="left", padx=10, pady=5)

        # Add separator
        separator = ctk.CTkFrame(self.command_inner_frame, height=2)
        separator.pack(fill="x", padx=10, pady=(0, 10))

        # Command selection container
        command_select_frame = ctk.CTkFrame(self.command_inner_frame)
        command_select_frame.pack(fill="x", padx=10, pady=(0, 10))

        # Command selection label
        command_label = ctk.CTkLabel(
            command_select_frame,
            text="Select Command:",
            font=self.fonts["normal"]
        )
        command_label.pack(side="top", anchor="w", padx=5, pady=(0, 5))

        # Command dropdown with consistent styling
        self.command_var = ctk.StringVar(value=next(iter(GUI_COMMANDS)))
        self.command_dropdown = ctk.CTkOptionMenu(
            command_select_frame,
            values=list(self.commands.keys()),
            variable=self.command_var,
            command=self.on_command_change,
            width=200,
            height=32,
            font=self.fonts["normal"],
            anchor="center"
        )
        self.command_dropdown.pack(fill="x", padx=5)

        # Parameter frame container with fixed height
        self.param_container = ctk.CTkFrame(self.command_inner_frame)
        self.param_container.pack(expand=True, fill="both", padx=5, pady=5)
        self.param_container.pack_propagate(False)  # Prevent container from shrinking

        # Initialize parameter frame
        self.param_frame = None
        self.on_command_change(self.command_var.get())

        # Preview frame (update column position)
        self.preview_frame = ctk.CTkFrame(self.main_frame)
        self.preview_frame.grid(row=0, column=2, padx=10, pady=10, sticky="nsew")

        # Update initial info panel
        self.update_info_panel(self.command_var.get())

        # Add debug.ban mode state
        self.debug_mode = False

        # Bind F3 key
        self.bind("<F3>", self.toggle_debug_mode)

        # Create container for preview and screenshot button
        preview_container = ctk.CTkFrame(self.preview_frame)
        preview_container.pack(expand=True, fill="both", padx=10, pady=10)

        # Preview label
        self.preview_label = ctk.CTkLabel(preview_container, text="")
        self.preview_label.pack(expand=True, fill="both", pady=(0, 10))

        # Button container for brightness controls and screenshot
        button_container = ctk.CTkFrame(preview_container)
        button_container.pack(fill="x", padx=5, pady=(0, 5), side="bottom")

        # Row for screenshot button (on top)
        screenshot_row = ctk.CTkFrame(button_container)
        screenshot_row.pack(fill="x", pady=(0, 2))

        self.screenshot_btn = ctk.CTkButton(
            screenshot_row,
            text="Take Screenshot",
            height=35,
            font=self.fonts["button"],
            command=lambda: self.controller.save_screen(take_new=True)
        )
        # Screenshot button will be managed by debug mode toggle

        # Row for brightness controls (at bottom)
        brightness_row = ctk.CTkFrame(button_container)
        brightness_row.pack(fill="x", pady=(2, 0))

        # Brightness control buttons
        self.low_brightness_btn = ctk.CTkButton(
            brightness_row,
            text="Lower Brightness",
            height=35,
            font=self.fonts["button"],
            command=self.lower_brightness
        )
        self.low_brightness_btn.pack(side="left", fill="x", expand=True, padx=2)

        self.reset_brightness_btn = ctk.CTkButton(
            brightness_row,
            text="Reset Brightness",
            height=35,
            font=self.fonts["button"],
            command=self.reset_brightness
        )
        self.reset_brightness_btn.pack(side="left", fill="x", expand=True, padx=2)

        ratio = .55
        self.img_size = int(self.controller.new_width * ratio), int(720 * ratio)

        # Setup preview update
        self.controller.client.add_listener(scrcpy.EVENT_FRAME, lambda frame: self.update_image_safe(frame))

        # Log frame
        self.log_frame = ctk.CTkFrame(self.main_frame)
        self.log_frame.grid(row=1, column=0, columnspan=4, padx=10, pady=10, sticky="nsew")

        # Log header with auto-scroll toggle
        header_frame = ctk.CTkFrame(self.log_frame)
        header_frame.pack(fill="x", padx=10, pady=(5, 0))

        log_header = ctk.CTkLabel(header_frame, text="Logs", font=self.fonts["subheader"])
        log_header.pack(side="left")

        self.auto_scroll = ctk.BooleanVar(value=True)
        self.auto_scroll_button = ctk.CTkCheckBox(
            header_frame,
            text="Auto-scroll",
            variable=self.auto_scroll,
            command=self.on_auto_scroll_toggle
        )
        self.auto_scroll_button.pack(side="right", padx=10)

        # Add separator
        separator = ctk.CTkFrame(self.log_frame, height=2)
        separator.pack(fill="x", padx=10, pady=5)

        # Create scrollable text widget for logs with bigger font
        self.log_text = ctk.CTkTextbox(
            self.log_frame,
            height=150,
            wrap="word",
            font=("Arial", 13)  # Increased from 12 to 14
        )
        self.log_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Configure tags for different log levels (colors only)
        self.log_text.tag_config("info", foreground="white")
        self.log_text.tag_config("success", foreground="green")
        self.log_text.tag_config("warning", foreground="orange")
        self.log_text.tag_config("error", foreground="red")
        self.log_text.tag_config("debug", foreground="cyan")

        # Bind scroll events
        self.log_text.bind("<MouseWheel>", self.on_log_scroll)
        self.log_text.bind("<Button-4>", self.on_log_scroll)  # Linux scroll up
        self.log_text.bind("<Button-5>", self.on_log_scroll)  # Linux scroll down

        self.controller.gui_logger = self.append_log

        if len(sys.argv) > 1:
            self.append_log(f"Updated to the latest version: v-{__version__}")
        else:
            self.append_log(f"AutoMonster v-{__version__} started")

        if os.path.exists("debug.ban"):
            self.toggle_debug_mode()

    def override_parameter_defaults(self):
        loaded_defaults = {}
        if os.path.isfile(DEFAULTS_FILE):
            with open(DEFAULTS_FILE, "r") as f:
                print("Loaded defaults")
                loaded_defaults = json.load(f)
        for cmd_name, params in self.commands.items():
            saved = loaded_defaults.get(cmd_name, {})
            for param_name, config in params.items():
                if param_name in saved:
                    config["default"] = saved[param_name]

    def append_log(self, message: str, level: str = "info"):
        """Add a new message to the log with timestamp and color"""
        # Skip debug messages if debug mode is off
        if level == "debug" and not self.debug_mode:
            return

        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"

        self.log_text.insert("end", log_entry, level)

        if self.auto_scroll.get():
            self.log_text.see("end")

    def on_log_scroll(self, event):
        """Disable auto-scroll when user manually scrolls"""
        if self.auto_scroll.get():
            self.auto_scroll.set(False)
            self.auto_scroll_button.deselect()

    def on_auto_scroll_toggle(self):
        """Handle auto-scroll toggle"""
        if self.auto_scroll.get():
            self.log_text.see("end")

    def _run_thread(self, params):
        # disable the dropdown
        self.command_dropdown.configure(state="disabled")

        command_name = self.command_var.get()
        try:
            callback = self.get_command_callback(command_name)
            self.append_log(f"Starting {command_name}...", "info")
            callback(**params)
            self.append_log(f"Completed {command_name}", "success")
        except AutoMonsterErrors.AutoMonsterError as e:
            error_msg = f"Error running {command_name}: {e}"
            self.append_log(error_msg, "error")
            logging.error(error_msg)
        except AutoMonsterErrors.ExecutionFlag:
            self.append_log(f"Execution of {command_name} stopped", "warning")

        self.param_frame.run_button.configure(state="normal")
        self.param_frame.cancel_button.configure(state="disabled")
        self.command_dropdown.configure(state="normal")

    def toggle_panel(self):
        if self.panel_visible:
            self.command_frame.grid_remove()
            self.toggle_button.configure(text="≫")
            self.main_frame.grid_columnconfigure(1, weight=0, minsize=0)  # Remove minsize when hidden
            self.main_frame.grid_columnconfigure(2, weight=1)
        else:
            self.command_frame.grid()
            self.toggle_button.configure(text="≪")
            self.main_frame.grid_columnconfigure(1, weight=0, minsize=self.panel_width)  # Restore minsize
            self.main_frame.grid_columnconfigure(2, weight=1)
        self.panel_visible = not self.panel_visible
        # Keep log frame visible in both states
        self.log_frame.grid(row=1, column=0, columnspan=4, padx=10, pady=10, sticky="nsew")

    def toggle_info_panel(self):
        if self.info_visible:
            self.info_frame.grid_forget()  # Changed from grid_remove() to grid_forget()
            self.info_toggle_button.configure(text="≪")
            self.main_frame.grid_columnconfigure(3, weight=0, minsize=0)
            self.main_frame.grid_columnconfigure(2, weight=1)  # Give more weight to preview when info is hidden
        else:
            self.info_frame.grid(row=0, column=3, padx=10, pady=10, sticky="nsew")
            self.info_toggle_button.configure(text="≫")
            self.main_frame.grid_columnconfigure(3, weight=0, minsize=self.panel_width)
            self.main_frame.grid_columnconfigure(2, weight=1)  # Reset preview weight
        self.info_visible = not self.info_visible

    def on_command_change(self, command_name):
        # Clear existing parameter frame
        if self.param_frame:
            self.param_frame.destroy()

        # Create new parameter frame
        self.param_frame = CommandFrame(
            self.param_container,  # Changed parent to param_container
            command_name,
            self.commands[command_name],
            self.get_command_callback(command_name)
        )
        self.param_frame.pack(expand=True, fill="both")
        self.update_info_panel(command_name)

    def get_command_callback(self, command_name):
        if command_name == "PVP":
            return lambda **kwargs: self.controller.do_pvp(
                kwargs.pop("num_battles", 2),
                kwargs.pop("handle_boxes", True),
                kwargs.pop("reduce_box_time", True)
            )
        elif command_name == "Era Saga":
            return self.controller.do_era_saga
        elif command_name == "Resource Dungeons":
            return self.controller.do_resource_dungeons
        elif command_name == "Ads":
            return self.controller.play_ads
        elif command_name == "Cavern":
            return lambda **kwargs: self.controller.do_cavern(
                *kwargs.pop("ancestral", []) + kwargs.pop("era", []),
                max_rooms=kwargs.pop("max_rooms", 3),
                change_team=kwargs.pop("change_team", True)
            )

    def run_command(self):
        if not self.param_frame:
            return

        params = {}
        for param_name, widget in self.param_frame.param_widgets.items():
            if isinstance(widget, ctk.CTkSlider):
                params[param_name] = int(widget.get())
            elif isinstance(widget, ctk.CTkCheckBox):
                params[param_name] = widget.get()
            elif isinstance(widget, ctk.CTkOptionMenu):
                params[param_name] = widget.get()
            elif isinstance(widget, list):  # Multiple choice checkboxes
                selected = [choice for choice, var in widget if var.get()]
                params[param_name] = selected

        command_name = self.command_var.get()
        self.append_log(f"Running {command_name} with parameters: {params}", "debug")

        self.param_frame.run_button.configure(state="disabled")
        self.param_frame.cancel_button.configure(state="normal")
        threading.Thread(target=self._run_thread, args=(params,), daemon=True).start()

    def update_image(self, frame):
        resized_frame = cv2.resize(frame, self.img_size)
        image = Image.fromarray(cv2.cvtColor(resized_frame, cv2.COLOR_BGR2RGB))
        ctk_image = ctk.CTkImage(light_image=image, dark_image=image, size=self.img_size)
        self.preview_label.configure(image=ctk_image)
        self.preview_label.image = ctk_image

    def update_image_safe(self, frame):
        self.after(0, self.update_image, frame)

    def lower_brightness(self):
        """Lower the device brightness"""
        self.controller.lower_brightness()
        self.append_log("Lowered device brightness", "info")

    def reset_brightness(self):
        """Reset the device brightness to auto mode"""
        self.controller.set_auto_brightness()
        self.append_log("Reset device brightness to auto mode", "info")

    def toggle_debug_mode(self, event=None):
        """Toggle debug.ban mode on/off"""
        self.debug_mode = not self.debug_mode

        # Toggle debug buttons visibility
        if self.debug_mode:
            self.screenshot_btn.pack(fill="x", expand=True, padx=2)
            self.append_log("Debug mode enabled", "debug")
        else:
            self.screenshot_btn.pack_forget()
            self.append_log("Debug mode disabled", "success")

    def update_info_panel(self, command_name):
        """Update the info panel with the selected command's information"""
        info = self.command_descriptions.get(command_name, {})

        # Update title
        self.info_title.configure(text=info.get("title", command_name))

        # Update description
        self.info_description.configure(state="normal")
        self.info_description.delete("1.0", "end")

        description = info.get("description", "No description available.")
        parameters = info.get("parameters", {})

        text = f"{description}\n\n"
        if parameters:
            text += "Parameters:\n"
            for param, desc in parameters.items():
                text += f"• {param}: {desc}\n"

        self.info_description.insert("1.0", text)
        self.info_description.configure(state="disabled")

    def __del__(self):
        self.controller.client.remove_listener(scrcpy.EVENT_FRAME)