import json
import logging
import os
import sys
import threading
import time
from datetime import datetime
import pathlib
import subprocess

import customtkinter as ctk
import cv2
import scrcpy
from PIL import Image

import AutoMonsterErrors
from AutoMonster import Controller
from Constants import GUI_COMMANDS, GUI_COMMAND_DESCRIPTIONS
from command_frame import CommandFrame
from device_selection_frame import DeviceSelectionFrame
from macro_dialog import MacroDialog
from debug_tool import DebugTool
from utils.config_manager import ConfigManager

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

        # Initialize macros before creating frames
        self.config_manager = ConfigManager()
        self.macros = self.config_manager.get_macros()
        self.macro_options = self.config_manager.get_macro_options()

        # Add macro execution state
        self.macro_running = False
        self.stop_macro = False

        # Add command running state
        self.command_running = False

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

    def on_device_selected(self, device_serial):
        # Show loading progress
        self.device_frame.disable_connect_btns()
        self.device_frame.show_loading("Connecting to device...")

        # Store error message from thread
        self._connection_error = None

        def initialize_controller():
            self.controller = None
            self._connection_error = None
            try:
                # Controller() handles everything: launch_game, wait, check resolution, open_game
                self.controller = Controller(serial=device_serial)
            except Exception as e:
                self._connection_error = str(e)
                logging.error(f"Failed to connect to device: {e}")

        thread = threading.Thread(target=initialize_controller, daemon=True)
        thread.start()

        # Use after() to check thread status without blocking UI
        self._check_connection_thread(thread)

    def _check_connection_thread(self, thread):
        """Check if connection thread is done, using after() to avoid blocking UI"""
        if thread.is_alive():
            # Check again in 100ms
            self.after(100, lambda: self._check_connection_thread(thread))
            return

        # Thread is done - handle result
        self.device_frame.hide_loading()

        if self.controller is None:
            self.device_frame.enable_connect_btns()
            error_msg = self._connection_error or "Unknown error"
            self.device_frame.status.configure(
                text=f"Connection failed: {error_msg}\nSelect a device and try again",
                text_color="red"
            )
            return

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
        self.battery = self.controller.get_battery_level()
        self.last_check_battery = datetime.now()
        self.debug_tool = None

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
        self.main_frame.grid_columnconfigure(5, weight=0, minsize=0)  # Debug panel (hidden by default)
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
        title = ctk.CTkLabel(header_frame, text="Actions", font=self.fonts["header"])
        title.pack(side="left", padx=10, pady=5)

        # Add separator
        separator = ctk.CTkFrame(self.command_inner_frame, height=2)
        separator.pack(fill="x", padx=10, pady=(0, 10))

        # Macro button frame
        macro_frame = ctk.CTkFrame(self.command_inner_frame)
        macro_frame.pack(fill="x", padx=10, pady=(0, 10))

        # Add label for macros
        macro_label = ctk.CTkLabel(
            macro_frame,
            text="Select Macro:",
            font=self.fonts["normal"]
        )
        macro_label.pack(side="top", anchor="w", padx=5, pady=(0, 5))

        # Create a horizontal frame for macro controls
        macro_controls = ctk.CTkFrame(macro_frame)
        macro_controls.pack(fill="x", padx=5, pady=(0, 5))

        # Add macro dropdown and edit button in horizontal layout
        dropdown_container = ctk.CTkFrame(macro_controls)
        dropdown_container.pack(fill="x", pady=(0, 5))

        # Add macro dropdown
        self.macro_names = ["No macros"] if not self.macros else list(self.macros.keys())
        self.selected_macro = ctk.StringVar(value=self.macro_names[0])
        self.macro_dropdown = ctk.CTkOptionMenu(
            dropdown_container,
            values=self.macro_names,
            variable=self.selected_macro,
            width=200,  # Adjusted to make room for edit button
            height=32,
            font=self.fonts["normal"]
        )
        self.macro_dropdown.pack(side="left", padx=(5, 5))

        # Add edit button with pencil symbol
        self.edit_macro_btn = ctk.CTkButton(
            dropdown_container,
            text="✎",  # Pencil symbol
            width=32,
            height=32,
            command=self.open_macro_dialog,
            font=self.fonts["normal"]
        )
        self.edit_macro_btn.pack(side="left")

        # Add run button below
        self.run_macro_btn = ctk.CTkButton(
            macro_controls,
            text="▶ Run Macro",
            height=32,
            width=140,  # Fixed width to prevent size changes between Run/Stop
            command=self.toggle_macro,
            font=self.fonts["normal"]
        )
        self.run_macro_btn.pack(fill="x", padx=5)

        # Add progress bar for macro execution
        self.macro_progress = ctk.CTkProgressBar(
            macro_controls,
            height=10,
            mode="determinate"
        )
        self.macro_progress.pack(fill="x", padx=5, pady=(5, 0))
        self.macro_progress.set(0)
        self.macro_progress.pack_forget()

        # Update button states
        self.update_macro_buttons()

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

        # Info label for screen interaction
        interaction_info = ctk.CTkLabel(
            preview_container,
            text="Click on screen to interact with game",
            font=("Arial", 11),
            text_color="gray"
        )
        interaction_info.pack(pady=(5, 0))

        # Preview label
        self.preview_label = ctk.CTkLabel(preview_container, text="")
        self.preview_label.pack(expand=True, fill="both", pady=(5, 10))

        # Create a separate frame for all buttons
        all_buttons_frame = ctk.CTkFrame(preview_container)
        all_buttons_frame.pack(fill="x", padx=5, pady=(0, 5))

        # Row for screenshot button (on top)
        screenshot_row = ctk.CTkFrame(all_buttons_frame)
        screenshot_row.pack(fill="x", pady=(0, 2))

        self.screenshot_btn = ctk.CTkButton(
            screenshot_row,
            text="Take Screenshot",
            height=35,
            font=self.fonts["button"],
            command=lambda: self.controller.save_screen(take_new=True)
        )
        
        self.open_sc_folder_btn = ctk.CTkButton(
            screenshot_row,
            text="Open Folder",
            height=35,
            font=self.fonts["button"],
            command=self.open_screenshots_folder
        )
        # Screenshot button will be managed by debug mode toggle

        # Row for brightness controls (at bottom)
        brightness_row = ctk.CTkFrame(all_buttons_frame)
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

        # Add progress tracking frame below all buttons
        self.progress_frame = ctk.CTkFrame(preview_container)
        self.progress_frame.pack(fill="x", padx=5, pady=(5, 0))
        
        # Add progress label
        self.progress_label = ctk.CTkLabel(
            self.progress_frame, 
            text="Progress:",
            font=self.fonts["normal"]
        )
        self.progress_label.pack(anchor="w", padx=5)

        # Add progress bar
        self.command_progress = ctk.CTkProgressBar(
            self.progress_frame,
            height=15,
            mode="determinate"
        )
        self.command_progress.pack(fill="x", padx=5, pady=(5, 5))
        self.command_progress.set(0)
        
        # Hide progress frame initially
        self.progress_frame.pack_forget()

        self.preview_ratio = .55
        self.img_size = int(self.controller.new_width * self.preview_ratio), int(720 * self.preview_ratio)
        self.is_portrait_frame = False
        self.actual_display_size = self.img_size  # Track actual displayed size for click mapping
        self._last_preview_size = (0, 0)  # Cache for size calculations
        self._size_recalc_needed = False  # Flag to trigger size recalculation

        # Setup preview update
        self.controller.client.add_listener(scrcpy.EVENT_FRAME, lambda frame: self.update_image_safe(frame))

        # Bind window resize to update preview scaling
        self.bind("<Configure>", self.on_window_resize)
        
        # Bind mouse events for interaction
        self.preview_label.bind("<ButtonPress-1>", self.on_mouse_down)
        self.preview_label.bind("<B1-Motion>", self.on_mouse_move)
        self.preview_label.bind("<ButtonRelease-1>", self.on_mouse_up)

        # Create logs frame (removed tabview for cleaner look)
        self.log_frame = ctk.CTkFrame(self.main_frame)
        self.log_frame.grid(row=1, column=0, columnspan=4, padx=10, pady=10, sticky="nsew")

        # Log header with auto-scroll toggle
        header_frame = ctk.CTkFrame(self.log_frame)
        header_frame.pack(fill="x", padx=10, pady=(10, 0))

        log_header = ctk.CTkLabel(header_frame, text="Execution Logs", font=self.fonts["subheader"])
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

        # Pre-create debug tool (hidden) to avoid lag when toggling F3
        self.debug_tool = DebugTool(self.main_frame, self.controller)
        # Keep it hidden initially - column 5 stays at minsize 0

        if len(sys.argv) > 1:
            self.append_log(f"Updated to the latest version: v-{__version__}")
        else:
            self.append_log(f"AutoMonster v-{__version__} started")

        if os.path.exists("debug.ban"):
            self.toggle_debug_mode()

    def override_parameter_defaults(self):
        loaded_defaults = self.config_manager.defaults
        logging.debug("Loaded defaults")
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
        self.command_running = True
        self.command_dropdown.configure(state="disabled")
        self.run_macro_btn.configure(state="disabled")  # Disable macro controls
        self.macro_dropdown.configure(state="disabled")
        self.edit_macro_btn.configure(state="disabled")

        command_name = self.command_var.get()
        try:
            # Reset progress bar only for PVP, Cavern, Breed Monsters, and Feed and Sell Monsters
            if command_name in ["PVP", "Cavern", "Breed Monsters", "Feed and Sell Monsters"]:
                self.update_command_progress(0)
            if self.param_frame and hasattr(self.param_frame, 'progress'):
                self.param_frame.progress.set(0)
            callback = self.get_command_callback(command_name)
            self.append_log(f"Starting {command_name}...", "info")
            result = callback(**params)

            # Check if exit program was called
            if result == "EXIT":
                self.append_log("Closing application...", "warning")
                self.after(1000, self.destroy)  # Close the GUI after 1 second
                return

            self.append_log(f"Completed {command_name}", "success")
        except AutoMonsterErrors.AutoMonsterError as e:
            error_msg = f"Error running {command_name}: {e}"
            self.append_log(error_msg, "error")
            logging.error(error_msg)
        except AutoMonsterErrors.ExecutionFlag:
            self.append_log(f"Execution of {command_name} stopped", "warning")
        finally:
            # Reset UI state
            self.command_running = False
            self.param_frame.is_running = False
            self.param_frame.run_button.configure(text="▶ Run", fg_color=["#3B8ED0", "#1F6AA5"])
            self.param_frame.pause_button.configure(state="disabled")
            self.param_frame.is_paused = False
            self.param_frame.pause_button.configure(text="Pause")
            self.command_dropdown.configure(state="normal")
            # Re-enable macro controls if no macro is running
            if not self.macro_running:
                self.update_macro_buttons()
                self.macro_dropdown.configure(state="normal")
                self.edit_macro_btn.configure(state="normal")
            # Hide progress bar if visible
            if command_name in ["PVP", "Cavern", "Breed Monsters", "Feed and Sell Monsters"]:
                self.progress_frame.pack_forget()

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

        # self.param_frame.run_button.configure(state="disabled")
        self.param_frame.pause_button.configure(state="normal")
        threading.Thread(target=self._run_thread, args=(params,), daemon=True).start()

    def stop_command(self):
        """Stop the current command execution"""
        if self.controller:
            self.controller.cancel_flag = True
            logging.info(f"Set cancel_flag to True. Controller: {self.controller}")
        self.append_log("Stopping command...", "warning")

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
                kwargs.pop("reduce_box_time", True),
                progress_callback=self.update_command_progress
            )
        elif command_name == "Era Saga":
            return self.controller.do_era_saga
        elif command_name == "Resource Dungeons":
            return lambda **kwargs: self.controller.do_resource_dungeons(
                wait_for_stamina_to_refill=kwargs.pop("wait_for_stamina", False)
            )
        elif command_name == "Ads":
            return self.controller.play_ads
        elif command_name == "Reduce Time":
            return lambda **kwargs: self.controller.reduce_time(
                kwargs.pop("number_of_ads", 3)
            )
        elif command_name == "Cavern":
            return lambda **kwargs: self.controller.do_cavern(
                *kwargs.pop("caverns", []),
                max_rooms=kwargs.pop("max_rooms", 3),
                change_team=kwargs.pop("change_team", True),
                progress_callback=self.update_command_progress
            )
        elif command_name == "Breed Monsters":
            return lambda **kwargs: self.controller.breed_monsters(
                kwargs.pop("num_breeds", 1),
                kwargs.pop("use_tree", False),
                progress_callback=self.update_command_progress
            )
        elif command_name == "Feed and Sell Monsters":
            return lambda **kwargs: self.controller.feed_and_sell_monsters(
                kwargs.pop("num_monsters", 10),
                progress_callback=self.update_command_progress
            )
        elif command_name == "Close Game":
            return lambda **kwargs: self.controller.close_game(
                action=kwargs.pop("action", "Close Game Only")
            )
        else:
            raise ValueError(f"Unknown command: {command_name}")

    def update_command_progress(self, progress: float):
        """Update the progress bar in the preview frame"""
        command = self.command_var.get()
        
        # For macros, get the current command from the step being executed
        if self.macro_running and hasattr(self, 'current_macro_command'):
            command = self.current_macro_command

        # Only show progress for PVP, Cavern, Breed Monsters, and Feed and Sell Monsters commands
        if command not in ["PVP", "Cavern", "Breed Monsters", "Feed and Sell Monsters"]:
            return

        def show_progress():
            if progress == 0:
                # Show and setup progress at start
                self.progress_label.configure(text=f"{command} Progress:")
                self.progress_frame.pack(fill="x", padx=5, pady=(5, 0))
                # force an update to show the progress bar
                self.progress_frame.update()
                self.command_progress.update()
            
            self.command_progress.set(progress)
            
            if progress >= 1:
                # Hide progress when complete
                self.progress_frame.pack_forget()

        # Ensure UI updates happen in main thread
        self.after(0, show_progress)

    def update_image(self, frame):
        try:
            # Draw debug tool detections on the frame BEFORE resizing
            if self.debug_mode and self.debug_tool is not None:
                frame = self.debug_tool.draw_detections_on_frame(frame.copy())
        except Exception as e:
            # Ignore errors if video stream disconnects
            pass

        self.is_portrait_frame = frame.shape[0] > frame.shape[1]

        # Calculate available space in preview frame
        available_width = self.preview_label.winfo_width()
        available_height = self.preview_label.winfo_height()

        # Only recalculate size if dimensions changed or flag is set
        current_size = (available_width, available_height)
        if self._size_recalc_needed or current_size != self._last_preview_size:
            # Use minimum size if widget hasn't been sized yet
            if available_width <= 1 or available_height <= 1:
                available_width = 800
                available_height = 600

            # Calculate aspect ratio preserving size
            game_width = self.controller.new_width
            game_height = 720

            scale_w = available_width / game_width
            scale_h = available_height / game_height
            scale = min(scale_w, scale_h)  # Use smaller scale to fit within bounds

            # Calculate final display size (what user sees)
            display_width = int(game_width * scale)
            display_height = int(game_height * scale)
            self.actual_display_size = (display_width, display_height)

            self._last_preview_size = current_size
            self._size_recalc_needed = False

        # Prepare frame for display
        img_size = (self.controller.new_width, 720)
        if self.is_portrait_frame:
            img_size = img_size[::-1]
        resized_frame = cv2.resize(frame, img_size)
        if self.is_portrait_frame:
            resized_frame = cv2.rotate(resized_frame, cv2.ROTATE_90_COUNTERCLOCKWISE)

        # check for the battery level every 60 seconds
        if (datetime.now() - self.last_check_battery).seconds > 60:
            self.battery = self.controller.get_battery_level()
            self.last_check_battery = datetime.now()

        image = Image.fromarray(cv2.cvtColor(resized_frame, cv2.COLOR_BGR2RGB))

        # CTkImage will handle the scaling to display_size
        ctk_image = ctk.CTkImage(light_image=image, dark_image=image, size=self.actual_display_size)
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
            self.screenshot_btn.pack(side="left", fill="x", expand=True, padx=(2, 1))
            self.open_sc_folder_btn.pack(side="left", fill="x", expand=True, padx=(1, 2))

            # Show debug tool (already created, just needs to be shown)
            self.main_frame.grid_columnconfigure(5, weight=0, minsize=self.panel_width)
            self.debug_tool.grid(row=0, column=5, rowspan=2, padx=(0, 10), pady=10, sticky="nsew")
            self.append_log("Debug mode enabled", "debug")
        else:
            self.screenshot_btn.pack_forget()
            self.open_sc_folder_btn.pack_forget()

            # Hide debug tool
            self.debug_tool.grid_forget()

            # Collapse column
            self.main_frame.grid_columnconfigure(5, weight=0, minsize=0)
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

    def load_macros(self):
        """Load macros from ConfigManager."""
        self.config_manager.load_configs()
        self.macro_options = self.config_manager.get_macro_options()
        return self.config_manager.get_macros()

    def run_macro(self, name):
        """Legacy method - use start_macro instead"""
        self.start_macro()

    def open_macro_dialog(self):
        """Open the macro dialog and update the macro list when closed"""
        dialog = MacroDialog(self, self.commands)

        # Wait for dialog to close
        self.wait_window(dialog)

        # Update macros
        self.macros = self.load_macros()
        self.update_macro_list()

    def update_macro_list(self):
        """Update the macro dropdown with current macros"""
        self.macros = self.load_macros()
        self.macro_names = list(self.macros.keys()) if self.macros else ["No macros"]
        self.macro_dropdown.configure(values=self.macro_names)
        self.selected_macro.set(self.macro_names[0])
        self.update_macro_buttons()

    def update_macro_buttons(self):
        """Enable/disable macro buttons based on macro existence"""
        state = "normal" if self.macro_names != ["No macros"] else "disabled"
        self.run_macro_btn.configure(state=state)

    def toggle_macro(self):
        """Toggle between running and stopping the macro"""
        if not self.macro_running:
            self.start_macro()
        else:
            self.stop_macro = True
            self.controller.cancel_flag = True

    def start_temporary_macro(self, steps, options):
        """Start running a temporary macro in a thread"""
        self.macro_running = True
        self.stop_macro = False
        self.run_macro_btn.configure(text="⬛ Stop Macro", fg_color="red")
        self.macro_dropdown.configure(state="disabled")
        self.edit_macro_btn.configure(state="disabled")
        # Disable command controls
        self.command_dropdown.configure(state="disabled")
        if self.param_frame:
            self.param_frame.run_button.configure(state="disabled")

        # Start macro thread
        threading.Thread(target=self._run_macro_thread, args=("Temporary Macro", steps, options), daemon=True).start()

    def start_macro(self):
        """Start running the selected macro in a thread"""
        macro_name = self.selected_macro.get()
        if macro_name and macro_name != "No macros":
            self.macro_running = True
            self.stop_macro = False
            self.run_macro_btn.configure(text="⬛ Stop Macro", fg_color="red")
            self.macro_dropdown.configure(state="disabled")
            self.edit_macro_btn.configure(state="disabled")
            # Disable command controls
            self.command_dropdown.configure(state="disabled")
            if self.param_frame:
                self.param_frame.run_button.configure(state="disabled")

            # Start macro thread
            threading.Thread(target=self._run_macro_thread, args=(macro_name,), daemon=True).start()

    def _run_macro_thread(self, name, steps=None, options=None):
        """Execute macro steps in a separate thread"""
        try:
            macro_steps = steps if steps is not None else self.macros[name]
            current_options = options if options is not None else self.macro_options

            # Show and reset progress bar
            self.macro_progress.pack(fill="x", padx=5, pady=(5, 0))
            self.macro_progress.set(0)
            total_steps = len(macro_steps)
            
            # Handle pre-macro options
            lowered_brightness = False
            if current_options.get("lower_brightness", False):
                lowered_brightness = True
                self.append_log("Lowering brightness before macro execution", "info")
                self.controller.lower_brightness()

            for i, step in enumerate(macro_steps):
                if self.stop_macro:
                    self.append_log("Macro execution stopped by user", "warning")
                    break

                command = step["command"]
                self.current_macro_command = command  # Store current command
                params = step["params"]
                callback = self.get_command_callback(command)
                if callback:
                    try:
                        self.append_log(f"Running macro step: {command} ({i+1}/{total_steps})", "info")

                        # Reset command progress bar for PVP, Cavern, Breed Monsters, and Feed and Sell Monsters commands
                        if command in ["PVP", "Cavern", "Breed Monsters", "Feed and Sell Monsters"]:
                            self.update_command_progress(0)

                        result = callback(**params)

                        # Check if exit program was called
                        if result == "EXIT":
                            self.append_log("Closing application...", "warning")
                            self.after(1000, self.destroy)  # Close the GUI after 1 second
                            return

                        # Hide command progress after completion
                        if command in ["PVP", "Cavern", "Breed Monsters", "Feed and Sell Monsters"]:
                            self.after(0, self.progress_frame.pack_forget)
                            
                        # Update macro progress bar
                        progress = (i + 1) / total_steps
                        self.macro_progress.set(progress)
                        
                    except AutoMonsterErrors.ExecutionFlag:
                        self.append_log(f"Macro step {command} stopped", "warning")
                        break
                    except Exception as e:
                        self.append_log(f"Error in macro step {command}: {str(e)}", "error")
                        break

            if not self.stop_macro and current_options.get("lock_device", False):
                self.append_log("Locking device after macro completion", "info")
                self.controller.lock_device()

            if lowered_brightness:
                self.controller.set_auto_brightness()
                self.append_log("Reset device brightness to auto mode", "info")

        finally:
            # Clear current macro command
            if hasattr(self, 'current_macro_command'):
                delattr(self, 'current_macro_command')
                
            # Reset UI state
            self.macro_running = False
            self.stop_macro = False
            self.run_macro_btn.configure(text="▶ Run Macro", fg_color=["#3B8ED0", "#1F6AA5"])
            self.macro_dropdown.configure(state="normal")
            self.edit_macro_btn.configure(state="normal")
            # Hide progress bar
            self.macro_progress.pack_forget()
            # Re-enable command controls if no command is running
            if not self.command_running:
                self.command_dropdown.configure(state="normal")
                if self.param_frame:
                    self.param_frame.run_button.configure(state="normal")

    def run_selected_macro(self):
        """Run the currently selected macro"""
        macro_name = self.selected_macro.get()
        if macro_name and macro_name != "No macros":
            self.run_macro(macro_name)

    def __del__(self):
        if hasattr(self, "controller"):
            self.controller.client.remove_listener(scrcpy.EVENT_FRAME)
            self.controller.client.stop()

    def _get_device_coords(self, event):
        """Convert GUI coordinates to device coordinates"""
        x_disp = event.x
        y_disp = event.y

        # Get actual display dimensions
        display_width, display_height = self.actual_display_size

        # Calculate scale from display to game resolution (720p)
        game_width = self.controller.new_width
        game_height = 720

        # Convert from display coordinates to 720p game coordinates
        x_720 = int((x_disp / display_width) * game_width)
        y_720 = int((y_disp / display_height) * game_height)

        if self.is_portrait_frame:
            # Handle portrait orientation
            final_x_720 = game_width - y_720
            final_y_720 = x_720
        else:
            final_x_720 = x_720
            final_y_720 = y_720

        # Clamp coordinates to valid range in 720p space
        final_x_720 = max(0, min(final_x_720, game_width))
        final_y_720 = max(0, min(final_y_720, game_height))

        # Scale to device resolution
        device_x = self.controller.scale_x(final_x_720)
        device_y = self.controller.scale_y(final_y_720)

        return device_x, device_y

    def on_mouse_down(self, event):
        # Clear debug tool detections if active
        if self.debug_mode and self.debug_tool is not None:
            self.debug_tool.clean_detections()

        x, y = self._get_device_coords(event)
        self.controller.client.control.touch(x, y, scrcpy.ACTION_DOWN)

    def on_mouse_move(self, event):
        x, y = self._get_device_coords(event)
        self.controller.client.control.touch(x, y, scrcpy.ACTION_MOVE)

    def on_mouse_up(self, event):
        x, y = self._get_device_coords(event)
        self.controller.client.control.touch(x, y, scrcpy.ACTION_UP)

    def on_window_resize(self, event):
        """Handle window resize events - images will scale automatically on next frame update"""
        self._size_recalc_needed = True

    def open_screenshots_folder(self):
        """Open the screenshots folder in file explorer"""
        try:
            # Determine base path to ensure we open the correct folder
            if getattr(sys, 'frozen', False):
                base_path = pathlib.Path(sys.executable).parent
            else:
                base_path = pathlib.Path(__file__).parent

            sc_dir = base_path / "sc"

            # Create if it doesn't exist
            if not sc_dir.exists():
                sc_dir.mkdir(exist_ok=True)

            # Open folder based on OS
            if os.name == 'nt':  # Windows
                os.startfile(str(sc_dir))
            elif os.name == 'posix':  # macOS/Linux
                subprocess.run(['open' if sys.platform == 'darwin' else 'xdg-open', str(sc_dir)])

            self.append_log("Opened screenshots folder", "info")
        except Exception as e:
            self.append_log(f"Error opening folder: {str(e)}", "error")
