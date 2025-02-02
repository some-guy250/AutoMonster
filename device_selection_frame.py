import customtkinter as ctk
from adbutils import adb


class DeviceSelectionFrame(ctk.CTkFrame):
    def __init__(self, master, on_device_selected):
        super().__init__(master)

        self.on_device_selected = on_device_selected

        # Add progress bar (hidden by default)
        self.progress_bar = ctk.CTkProgressBar(self)
        self.progress_bar.configure(mode="indeterminate")
        # Pre-configure grid position for progress bar (will be hidden initially)
        self.progress_bar.grid(row=5, column=0, padx=20, pady=(10, 0), sticky="ew")
        self.progress_bar.grid_remove()  # Hide it initially

        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        # Remove row weight for scroll frame since we're using dropdown
        self.grid_rowconfigure(2, weight=0)

        # Title label
        self.title_label = ctk.CTkLabel(
            self,
            text="Select a device:",
            font=("Arial", 14, "bold")
        )
        self.title_label.grid(row=0, column=0, pady=(20, 10))

        # Create frame for USB and wireless sections
        self.content_frame = ctk.CTkFrame(self)
        self.content_frame.grid(row=1, column=0, padx=20, sticky="nsew")
        self.content_frame.grid_columnconfigure(0, weight=1)

        # Wireless connection section
        wireless_label = ctk.CTkLabel(
            self.content_frame,
            text="Wireless Connection:",
            font=("Arial", 12)
        )
        wireless_label.grid(row=0, column=0, padx=5, pady=(5, 0), sticky="w")

        # IP address entry with example placeholder
        self.ip_entry = ctk.CTkEntry(
            self.content_frame,
            placeholder_text="192.168.1.100:5555",
        )
        self.ip_entry.bind("<Return>", lambda e: self.connect_wireless())
        self.ip_entry.grid(row=1, column=0, padx=5, pady=(0, 5), sticky="ew")

        # Connect wireless button
        self.wireless_btn = ctk.CTkButton(
            self.content_frame,
            text="Connect Wireless",
            command=self.connect_wireless
        )
        self.wireless_btn.grid(row=2, column=0, padx=5, pady=(0, 10), sticky="ew")

        # Separator
        separator = ctk.CTkFrame(self.content_frame, height=2, fg_color="gray30")
        separator.grid(row=3, column=0, padx=5, pady=10, sticky="ew")

        # USB Devices label
        usb_label = ctk.CTkLabel(
            self.content_frame,
            text="Found Devices:",
            font=("Arial", 12)
        )
        usb_label.grid(row=4, column=0, padx=5, pady=(5, 5), sticky="w")

        # Device dropdown
        self.device_var = ctk.StringVar(value="Select a device")
        self.device_dropdown = ctk.CTkOptionMenu(
            self.content_frame,
            variable=self.device_var,
            values=["No devices found"],
            command=None,  # Remove auto-connect callback
            width=200,
            height=32,
            font=("Arial", 12),
            anchor="center"
        )
        self.device_dropdown.grid(row=5, column=0, padx=5, pady=(0, 5), sticky="ew")

        # Add connect button
        self.connect_btn = ctk.CTkButton(
            self.content_frame,
            text="Connect",
            command=self.connect_selected_device,
            height=32,
        )
        self.connect_btn.grid(row=6, column=0, padx=5, pady=(0, 10), sticky="ew")

        # Refresh button at the bottom
        self.refresh_btn = ctk.CTkButton(
            self,
            text="Refresh Devices",
            command=self.refresh_devices
        )
        self.refresh_btn.grid(row=3, column=0, padx=20, pady=10, sticky="ew")

        # Status label at the bottom
        self.status = ctk.CTkLabel(self, text="", text_color="orange")
        self.status.grid(row=4, column=0, pady=10)

        # Store device serials
        self.device_serials = {}

        # Initial device load
        self.refresh_devices()

    def diable_connect_btns(self):
        self.wireless_btn.configure(state="disabled")
        self.connect_btn.configure(state="disabled")
        self.device_dropdown.configure(state="disabled")
        self.refresh_btn.configure(state="disabled")
        self.ip_entry.configure(state="disabled")

    def connect_wireless(self):
        address = self.ip_entry.get().strip()
        if not address:
            self.status.configure(text="Please enter an IP address", text_color="orange")
            return

        try:
            result = adb.connect(address)
            self.on_device_selected(result)
        except Exception as e:
            self.status.configure(text=f"Connection failed: {str(e)}", text_color="red")

    def connect_selected_device(self):
        selection = self.device_var.get()
        if selection == "Select a device" or selection == "No devices found":
            self.status.configure(text="Please select a device", text_color="orange")
            return

        if selection in self.device_serials:
            serial = self.device_serials[selection]
            result = adb.connect(serial)
            self.on_device_selected(result)

    def refresh_devices(self):
        try:
            devices = adb.device_list()
            if devices:
                self.status.configure(text="")
                # Create a list of device names and store their serials
                self.device_serials = {
                    f"Device {i + 1}: {d.serial}": d.serial
                    for i, d in enumerate(devices)
                }
                self.device_dropdown.configure(
                    values=list(self.device_serials.keys())
                )
                self.device_dropdown.set("Select a device")
                self.connect_btn.configure(state="normal")  # Enable connect button
            else:
                self.device_serials = {}
                self.device_dropdown.configure(values=["No devices found"])
                self.device_dropdown.set("No devices found")
                self.connect_btn.configure(state="disabled")  # Disable connect button
                self.status.configure(
                    text="No devices found\nMake sure your device is connected and USB debugging is enabled",
                    text_color="orange"
                )
        except Exception as e:
            self.status.configure(text=f"Error: {str(e)}", text_color="red")

    def show_loading(self, message="Opening game and connecting..."):
        """Show loading progress bar and message"""
        self.status.configure(text=message, text_color="white")
        self.progress_bar.grid()  # Show progress bar
        self.progress_bar.start()
        self.update()

    def hide_loading(self):
        """Hide loading progress bar"""
        self.progress_bar.stop()
        self.progress_bar.grid_remove()  # Hide progress bar
        self.update()
