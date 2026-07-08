"""UI frame construction for the main controller interface.

Extracted from controller_gui.py to keep the orchestrator thin.
"""

import customtkinter as ctk
import scrcpy
from config.config import GAME_HEIGHT


def build_main_interface(gui):
    """Build and wire all UI elements for the main interface.

    Args:
        gui: The ControllerGUI instance that owns all state.
    """
    gui.fonts = {
        "header": ("Arial", 16, "bold"),
        "subheader": ("Arial", 14, "bold"),
        "normal": ("Arial", 12),
        "button": ("Arial", 13, "bold"),
    }
    gui.battery = gui.controller.get_battery_level()
    gui.debug_tool = None

    gui.panel_width = 300
    gui.panel_visible = True
    gui.info_visible = True

    gui.commands = gui.commands  # already set on __init__ via self.commands = GUI_COMMANDS
    gui.command_descriptions = gui.command_descriptions

    gui.override_parameter_defaults()

    # ---- Grid layout ----
    mf = gui.main_frame
    mf.grid_columnconfigure(0, weight=0, minsize=30)   # Left toggle
    mf.grid_columnconfigure(1, weight=0, minsize=gui.panel_width)  # Command frame
    mf.grid_columnconfigure(2, weight=1)  # Preview
    mf.grid_columnconfigure(3, weight=0, minsize=gui.panel_width)  # Info frame
    mf.grid_columnconfigure(4, weight=0, minsize=30)  # Right toggle
    mf.grid_columnconfigure(5, weight=0, minsize=0)  # Debug panel (hidden)
    mf.grid_rowconfigure(0, weight=3)
    mf.grid_rowconfigure(1, weight=1)

    # ---- Toggle buttons ----
    gui.toggle_button = ctk.CTkButton(
        mf, text="≪", width=30, height=24, command=gui.toggle_panel
    )
    gui.toggle_button.grid(row=0, column=0, sticky="ns", padx=(2, 0), pady=10)

    gui.info_toggle_button = ctk.CTkButton(
        mf, text="≫", width=30, height=24, command=gui.toggle_info_panel
    )
    gui.info_toggle_button.grid(row=0, column=4, sticky="ns", padx=(0, 2), pady=10)

    # ---- Info panel ----
    _build_info_panel(gui)

    # ---- Command panel ----
    _build_command_panel(gui)

    # ---- Preview frame ----
    _build_preview_frame(gui)

    # ---- Logs frame ----
    _build_logs_frame(gui)

    # ---- Debug tool (pre-created, hidden) ----
    from .debug_tool import DebugTool
    gui.debug_tool = DebugTool(mf, gui.controller)


# =============================================================================
# Sub-builders
# =============================================================================

def _build_info_panel(gui):
    mf = gui.main_frame
    info = gui.info_frame = ctk.CTkFrame(mf, width=gui.panel_width)
    info.grid(row=0, column=3, padx=10, pady=10, sticky="nsew")
    info.grid_propagate(False)

    gui.info_title = ctk.CTkLabel(info, text="", font=gui.fonts["header"])
    gui.info_title.pack(padx=10, pady=(10, 5), anchor="w")

    ctk.CTkFrame(info, height=2).pack(fill="x", padx=10, pady=(0, 10))

    gui.info_description = ctk.CTkTextbox(info, wrap="word", height=200, font=("Arial", 14))
    gui.info_description.pack(fill="both", expand=True, padx=10, pady=5)
    gui.info_description.configure(state="disabled")


def _build_command_panel(gui):
    mf = gui.main_frame
    cmd = gui.command_frame = ctk.CTkFrame(mf, width=gui.panel_width)
    cmd.grid(row=0, column=1, padx=(0, 10), pady=10, sticky="nsew")
    cmd.grid_propagate(False)

    inner = gui.command_inner_frame = ctk.CTkFrame(cmd)
    inner.pack(expand=True, fill="both", padx=5, pady=5)
    inner.pack_propagate(False)

    # Header
    header = ctk.CTkFrame(inner)
    header.pack(fill="x", padx=5, pady=5)
    ctk.CTkLabel(header, text="Actions", font=gui.fonts["header"]).pack(side="left", padx=10, pady=5)
    ctk.CTkFrame(inner, height=2).pack(fill="x", padx=10, pady=(0, 10))

    # Macro controls
    _build_macro_controls(gui, inner)

    # Command dropdown
    _build_command_selector(gui, inner)


def _build_macro_controls(gui, parent):
    macro_frame = ctk.CTkFrame(parent)
    macro_frame.pack(fill="x", padx=10, pady=(0, 10))

    ctk.CTkLabel(macro_frame, text="Select Macro:", font=gui.fonts["normal"]) \
        .pack(side="top", anchor="w", padx=5, pady=(0, 5))

    controls = ctk.CTkFrame(macro_frame)
    controls.pack(fill="x", padx=5, pady=(0, 5))

    dropdown_container = ctk.CTkFrame(controls)
    dropdown_container.pack(fill="x", pady=(0, 5))

    gui.macro_names = ["No macros"] if not gui.macros else list(gui.macros.keys())
    gui.selected_macro = ctk.StringVar(value=gui.macro_names[0])
    gui.macro_dropdown = ctk.CTkOptionMenu(
        dropdown_container, values=gui.macro_names, variable=gui.selected_macro,
        width=200, height=32, font=gui.fonts["normal"]
    )
    gui.macro_dropdown.pack(side="left", padx=(5, 5))

    gui.edit_macro_btn = ctk.CTkButton(
        dropdown_container, text="✎", width=32, height=32,
        command=gui.open_macro_dialog, font=gui.fonts["normal"]
    )
    gui.edit_macro_btn.pack(side="left")

    gui.run_macro_btn = ctk.CTkButton(
        controls, text="▶ Run Macro", height=32, width=140,
        command=gui.toggle_macro, font=gui.fonts["normal"]
    )
    gui.run_macro_btn.pack(fill="x", padx=5)

    gui.macro_progress = ctk.CTkProgressBar(controls, height=10, mode="determinate")
    gui.macro_progress.set(0)
    gui.macro_progress.pack_forget()

    gui.update_macro_buttons()


def _build_command_selector(gui, parent):
    select_frame = ctk.CTkFrame(parent)
    select_frame.pack(fill="x", padx=10, pady=(0, 10))

    ctk.CTkLabel(select_frame, text="Select Command:", font=gui.fonts["normal"]) \
        .pack(side="top", anchor="w", padx=5, pady=(0, 5))

    from .gui_config import GUI_COMMANDS
    gui.command_var = ctk.StringVar(value=next(iter(GUI_COMMANDS)))
    gui.command_dropdown = ctk.CTkOptionMenu(
        select_frame, values=list(gui.commands.keys()), variable=gui.command_var,
        command=gui.on_command_change, width=200, height=32,
        font=gui.fonts["normal"], anchor="center"
    )
    gui.command_dropdown.pack(fill="x", padx=5)

    # Parameter container
    gui.param_container = ctk.CTkFrame(parent)
    gui.param_container.pack(expand=True, fill="both", padx=5, pady=5)
    gui.param_container.pack_propagate(False)

    gui.param_frame = None
    gui.on_command_change(gui.command_var.get())

    # Update info panel
    gui.update_info_panel(gui.command_var.get())


def _build_preview_frame(gui):
    mf = gui.main_frame
    preview = gui.preview_frame = ctk.CTkFrame(mf)
    preview.grid(row=0, column=2, padx=10, pady=10, sticky="nsew")

    container = ctk.CTkFrame(preview)
    container.pack(expand=True, fill="both", padx=10, pady=10)

    ctk.CTkLabel(
        container, text="Click on screen to interact with game",
        font=("Arial", 11), text_color="gray"
    ).pack(pady=(5, 0))

    gui.preview_label = ctk.CTkLabel(container, text="")
    gui.preview_label.pack(expand=True, fill="both", pady=(5, 10))

    # Buttons frame
    buttons = ctk.CTkFrame(container)
    buttons.pack(fill="x", padx=5, pady=(0, 5))

    # Screenshot row
    ss_row = ctk.CTkFrame(buttons)
    ss_row.pack(fill="x", pady=(0, 2))

    gui.screenshot_btn = ctk.CTkButton(
        ss_row, text="Take Screenshot", height=35, font=gui.fonts["button"],
        command=lambda: gui.controller.save_screen(take_new=True)
    )
    gui.open_sc_folder_btn = ctk.CTkButton(
        ss_row, text="Open Folder", height=35, font=gui.fonts["button"],
        command=gui.open_screenshots_folder
    )

    # Brightness row
    bright_row = ctk.CTkFrame(buttons)
    bright_row.pack(fill="x", pady=(2, 0))

    gui.low_brightness_btn = ctk.CTkButton(
        bright_row, text="Lower Brightness", height=35, font=gui.fonts["button"],
        command=gui.lower_brightness
    )
    gui.low_brightness_btn.pack(side="left", fill="x", expand=True, padx=2)

    gui.reset_brightness_btn = ctk.CTkButton(
        bright_row, text="Reset Brightness", height=35, font=gui.fonts["button"],
        command=gui.reset_brightness
    )
    gui.reset_brightness_btn.pack(side="left", fill="x", expand=True, padx=2)

    # Progress frame
    gui.progress_frame = ctk.CTkFrame(container)
    gui.progress_label = ctk.CTkLabel(
        gui.progress_frame, text="Progress:", font=gui.fonts["normal"]
    )
    gui.progress_label.pack(anchor="w", padx=5)
    gui.command_progress = ctk.CTkProgressBar(
        gui.progress_frame, height=15, mode="determinate"
    )
    gui.command_progress.pack(fill="x", padx=5, pady=(5, 5))
    gui.command_progress.set(0)
    gui.progress_frame.pack_forget()

    # Preview state
    gui.preview_ratio = .55
    gui.img_size = (int(gui.controller.new_width * gui.preview_ratio), int(GAME_HEIGHT * gui.preview_ratio))
    gui.is_portrait_frame = False
    gui.actual_display_size = gui.img_size
    gui._last_preview_size = (0, 0)
    gui._size_recalc_needed = False

    # Bind events
    gui.controller.client.add_listener(scrcpy.EVENT_FRAME, lambda frame: gui.update_image_safe(frame))
    gui.bind("<Configure>", gui.on_window_resize)
    gui.bind("<F3>", gui.toggle_debug_mode)
    gui.preview_label.bind("<ButtonPress-1>", gui.on_mouse_down)
    gui.preview_label.bind("<B1-Motion>", gui.on_mouse_move)
    gui.preview_label.bind("<ButtonRelease-1>", gui.on_mouse_up)


def _build_logs_frame(gui):
    mf = gui.main_frame
    log_frame = gui.log_frame = ctk.CTkFrame(mf)
    log_frame.grid(row=1, column=0, columnspan=4, padx=10, pady=10, sticky="nsew")

    header = ctk.CTkFrame(log_frame)
    header.pack(fill="x", padx=10, pady=(10, 0))

    ctk.CTkLabel(header, text="Execution Logs", font=gui.fonts["subheader"]).pack(side="left")

    gui.auto_scroll = ctk.BooleanVar(value=True)
    gui.auto_scroll_button = ctk.CTkCheckBox(
        header, text="Auto-scroll", variable=gui.auto_scroll, command=gui.on_auto_scroll_toggle
    )
    gui.auto_scroll_button.pack(side="right", padx=10)

    ctk.CTkFrame(log_frame, height=2).pack(fill="x", padx=10, pady=5)

    gui.log_text = ctk.CTkTextbox(log_frame, height=150, wrap="word", font=("Arial", 13))
    gui.log_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    gui.log_text.tag_config("info", foreground="white")
    gui.log_text.tag_config("success", foreground="green")
    gui.log_text.tag_config("warning", foreground="orange")
    gui.log_text.tag_config("error", foreground="red")
    gui.log_text.tag_config("debug", foreground="cyan")

    gui.log_text.bind("<MouseWheel>", gui.on_log_scroll)
    gui.log_text.bind("<Button-4>", gui.on_log_scroll)
    gui.log_text.bind("<Button-5>", gui.on_log_scroll)

    gui.controller.gui_logger = gui.append_log
