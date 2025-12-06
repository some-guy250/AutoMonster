import os
import json
from typing import Dict, Any
import customtkinter as ctk

DEFAULTS_FILE = "defaults.json"


class CommandFrame(ctk.CTkFrame):
    def __init__(self, master, command_name: str, params: Dict[str, Any], callback, mode="normal"):
        super().__init__(master)

        self.command_name = command_name
        self.params = params
        self.callback = callback
        self.param_widgets = {}
        self.mode = mode
        self.is_paused = False

        # Configure frame to maintain size
        self.grid_propagate(False)
        self.pack_propagate(False)

        # Create scrollable container for parameters
        self.scroll_frame = ctk.CTkScrollableFrame(self)
        self.scroll_frame.pack(expand=True, fill="both", padx=5, pady=5)

        # Add a header for parameters
        header = ctk.CTkLabel(self.scroll_frame, text="Parameters", font=("Arial", 14, "bold"))
        header.pack(pady=(5, 10), anchor="w")

        # Create parameter inputs
        for param_name, param_config in params.items():
            # Create parameter container frame
            param_frame = ctk.CTkFrame(self.scroll_frame)
            param_frame.pack(fill="x", padx=5, pady=2)
            param_frame.grid_columnconfigure(0, weight=1)

            label = ctk.CTkLabel(param_frame, text=param_name)
            label.grid(row=0, column=0, padx=5, pady=(5, 1), sticky="w")

            if param_config["type"] == "int":
                value_label = ctk.CTkLabel(param_frame, text=str(param_config.get("default", 0)), width=30)
                widget = ctk.CTkSlider(param_frame,
                                       from_=param_config.get("min", 0),
                                       to=param_config.get("max", 100),
                                       command=lambda val, lbl=value_label: lbl.configure(text=str(int(val))))
                widget.set(param_config.get("default", 0))
                widget.grid(row=1, column=0, padx=5, pady=(0, 5), sticky="ew")
                value_label.grid(row=1, column=1, padx=5, pady=(0, 5))
            elif param_config["type"] == "bool":
                widget = ctk.CTkCheckBox(param_frame, text="")
                if param_config.get("default"):
                    widget.select()
                widget.grid(row=1, column=0, padx=5, pady=(0, 5), sticky="w")
            elif param_config["type"] == "choice":
                widget = ctk.CTkOptionMenu(param_frame, values=param_config["choices"], width=150)
                widget.set(param_config.get("default", param_config["choices"][0]))
                widget.grid(row=1, column=0, padx=5, pady=(0, 5), sticky="w")
            elif param_config["type"] == "multiple_choice":
                # Create a frame for checkboxes
                checkbox_frame = ctk.CTkScrollableFrame(param_frame, height=150)
                checkbox_frame.grid(row=1, column=0, padx=5, pady=(0, 5), sticky="nsew")

                # Store checkboxes in a list
                checkbox_vars = []
                for choice in param_config["choices"]:
                    if choice.startswith("--"):  # This is a separator/header
                        label = ctk.CTkLabel(checkbox_frame, text=choice, font=("Arial", 12, "bold"))
                        label.pack(anchor="w", padx=5, pady=(10, 2))
                        continue

                    var = ctk.BooleanVar(value=choice in param_config.get("default", []))
                    checkbox = ctk.CTkCheckBox(checkbox_frame, text=choice, variable=var)
                    checkbox.pack(anchor="w", padx=20, pady=2)  # Extra padding for indentation
                    checkbox_vars.append((choice, var))
                widget = checkbox_vars

            self.param_widgets[param_name] = widget

        # Create button container at the bottom of parameters
        button_container = ctk.CTkFrame(self.scroll_frame)
        button_container.pack(fill="x", padx=5, pady=(10, 5))

        # If there are parameters and we're in normal mode, add the save defaults button
        if params and mode == "normal":
            save_button = ctk.CTkButton(
                button_container,
                text="Set Values as Defaults",
                height=35,
                font=("Arial", 13, "bold"),
                fg_color="#1f538d",  # A nice blue color
                hover_color="#2766b3",
                command=lambda: self.save_params_as_defaults(command_name)
            )
            save_button.pack(fill="x", padx=5, pady=(0, 10))

        # Container for action buttons
        action_buttons = ctk.CTkFrame(button_container)
        action_buttons.pack(fill="x", padx=5)
        action_buttons.grid_columnconfigure(0, weight=1)
        action_buttons.grid_columnconfigure(1, weight=1)
        action_buttons.grid_columnconfigure(2, weight=1)

        # Configure buttons based on mode
        if mode == "normal":
            # Run/Cancel toggle button
            self.is_running = False
            self.run_button = ctk.CTkButton(
                action_buttons,
                text="▶ Run",
                height=35,
                width=100,  # Fixed width to prevent size changes
                font=("Arial", 13, "bold"),
                command=self.toggle_execution
            )
            self.run_button.grid(row=0, column=0, padx=(0, 5), sticky="ew")

            # Pause button
            self.pause_button = ctk.CTkButton(
                action_buttons,
                text="Pause",
                height=35,
                width=100,  # Fixed width to prevent size changes between Pause/Resume
                font=("Arial", 13, "bold"),
                command=self.on_pause,
                state="disabled"
            )
            self.pause_button.grid(row=0, column=1, padx=5, sticky="ew")
        else:
            # Add Step button for macro mode
            self.add_button = ctk.CTkButton(
                action_buttons,
                text="Add Step",
                height=35,
                font=("Arial", 13, "bold"),
                command=callback
            )
            self.add_button.grid(row=0, column=0, columnspan=3, sticky="ew")

    def toggle_execution(self):
        """Toggle between running and stopping the command"""
        if not self.is_running:
            # Start execution
            self.is_running = True
            self.run_button.configure(text="⬛ Stop", fg_color="red")
            self.pause_button.configure(state="normal")
            self.master.winfo_toplevel().run_command()
        else:
            # Stop execution
            self.is_running = False
            self.run_button.configure(text="▶ Run", fg_color=["#3B8ED0", "#1F6AA5"])
            self.pause_button.configure(state="disabled")
            self.master.winfo_toplevel().stop_command()
            # Force unpause if paused
            if self.is_paused:
                self.on_pause()

    def on_pause(self):
        if self.is_paused:
            self.master.winfo_toplevel().controller.unfreeze()
            self.pause_button.configure(text="Pause")
        else:
            self.master.winfo_toplevel().controller.freeze()
            self.pause_button.configure(text="Resume")
        self.is_paused = not self.is_paused

    def save_params_as_defaults(self, command_name: str):
        current_params = {}
        for param_name, widget in self.param_widgets.items():
            if isinstance(widget, ctk.CTkSlider):
                value = int(widget.get())
            elif isinstance(widget, ctk.CTkCheckBox):
                value = widget.get()
            elif isinstance(widget, ctk.CTkOptionMenu):
                value = widget.get()
            elif isinstance(widget, list):  # Multiple choice checkboxes
                value = [choice for choice, var in widget if var.get()]
            current_params[param_name] = value

        if os.path.isfile(DEFAULTS_FILE):
            with open(DEFAULTS_FILE, "r") as f:
                data = json.load(f)
        else:
            data = {}
        data[command_name] = current_params
        with open(DEFAULTS_FILE, "w") as f:
            f.write(json.dumps(data, indent=4))
        self.master.winfo_toplevel().append_log(f"Defaults saved for {command_name}", "success")
        self.master.winfo_toplevel().override_parameter_defaults()

    def get_current_params(self):
        """Get current parameter values"""
        current_params = {}
        for param_name, widget in self.param_widgets.items():
            if isinstance(widget, ctk.CTkSlider):
                value = int(widget.get())
            elif isinstance(widget, ctk.CTkCheckBox):
                value = widget.get()
            elif isinstance(widget, ctk.CTkOptionMenu):
                value = widget.get()
            elif isinstance(widget, list):  # Multiple choice checkboxes
                value = [choice for choice, var in widget if var.get()]
            current_params[param_name] = value
        return current_params
