"""Event handlers and image update logic for the controller GUI.

Extracted from controller_gui.py to separate UI construction from runtime events.
"""

import logging

import cv2
import amscrcpy
import customtkinter as ctk
from PIL import Image
from config.config import GAME_HEIGHT

logger = logging.getLogger("AutoMonster")


# =============================================================================
# Image update
# =============================================================================

def on_scrcpy_frame(gui, frame):
    """Scrcpy stream thread callback: render the newest frame off the main thread.

    All heavy pixel work (debug overlay, resize, rotate, color conversion)
    runs here on the scrcpy stream thread, which is idle right after
    decoding, instead of on the tkinter main thread. Only the finished
    image is handed over. At most one main thread blit callback is
    scheduled per burst of frames, so stale frames are dropped and the
    preview can never fall more than one frame behind.
    """
    if frame is None:
        return

    try:
        if gui.debug_mode and gui.debug_tool is not None:
            frame = gui.debug_tool.draw_detections_on_frame(frame.copy())
    except Exception:
        # Ignore debug drawing errors, continue with normal frame
        pass

    gui.is_portrait_frame = frame.shape[0] > frame.shape[1]

    # Render at the last known display size. The main thread updates
    # gui._render_size when the label is resized; at most the first frame
    # after a resize is rendered at the old size and CTkImage rescales it.
    display_width, display_height = gui._render_size
    if gui.is_portrait_frame:
        resized_frame = cv2.resize(frame, (display_height, display_width))
        resized_frame = cv2.rotate(resized_frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
    else:
        resized_frame = cv2.resize(frame, (display_width, display_height))

    gui._pending_image = Image.fromarray(cv2.cvtColor(resized_frame, cv2.COLOR_BGR2RGB))

    if not gui._frame_cb_scheduled:
        gui._frame_cb_scheduled = True
        try:
            gui.after(0, gui.blit_pending_frame)
        except Exception:
            # Tk not ready to accept the callback: reset the flag so the
            # next frame retries scheduling instead of freezing the preview.
            gui._frame_cb_scheduled = False


def blit_pending_frame(gui):
    """Main thread callback: display the newest rendered image.

    tkinter widgets may only be touched from the main thread, so this is
    the only part of the frame pipeline that runs here: the label size
    check and the CTkImage blit.
    """
    gui._frame_cb_scheduled = False
    image = gui._pending_image
    gui._pending_image = None
    if image is None:
        return

    # Only recalculate size when explicitly needed or widget size changes significantly
    available_width = gui.preview_label.winfo_width()
    available_height = gui.preview_label.winfo_height()

    current_size = (available_width, available_height)
    if gui._size_recalc_needed or current_size != gui._last_preview_size:
        if available_width <= 1 or available_height <= 1:
            available_width = 800
            available_height = 600

        game_width = gui.controller.new_width
        game_height = GAME_HEIGHT

        scale_w = available_width / game_width
        scale_h = available_height / game_height
        scale = min(scale_w, scale_h)

        display_width = int(game_width * scale)
        display_height = int(game_height * scale)
        gui.actual_display_size = (display_width, display_height)
        gui._last_preview_size = current_size
        gui._size_recalc_needed = False
        # Tell the scrcpy thread to render at the new size from the next frame
        gui._render_size = (display_width, display_height)
    else:
        display_width, display_height = gui.actual_display_size

    if display_width <= 0 or display_height <= 0:
        # Fallback to initial size from gui_frames
        display_width, display_height = gui.img_size if gui.img_size != (0, 0) else (800, 600)
        gui._render_size = (display_width, display_height)

    ctk_image = ctk.CTkImage(light_image=image, dark_image=image, size=(display_width, display_height))
    gui.preview_label.configure(image=ctk_image)
    gui.preview_label.image = ctk_image


# =============================================================================
# Mouse interaction
# =============================================================================

def _get_device_coords(gui, event):
    """Convert GUI preview coordinates to device coordinates."""
    x_disp = event.x
    y_disp = event.y

    display_width, display_height = gui.actual_display_size
    game_width = gui.controller.new_width
    game_height = GAME_HEIGHT

    x_720 = int((x_disp / display_width) * game_width)
    y_720 = int((y_disp / display_height) * game_height)

    if gui.is_portrait_frame:
        final_x_720 = game_width - y_720
        final_y_720 = x_720
    else:
        final_x_720 = x_720
        final_y_720 = y_720

    final_x_720 = max(0, min(final_x_720, game_width))
    final_y_720 = max(0, min(final_y_720, game_height))

    return gui.controller.scale_x(final_x_720), gui.controller.scale_y(final_y_720)


def on_mouse_down(gui, event):
    if gui.debug_mode and gui.debug_tool is not None:
        gui.debug_tool.clean_detections()
    x, y = _get_device_coords(gui, event)
    gui.controller.client.control.touch(x, y, amscrcpy.ACTION_DOWN)


def on_mouse_move(gui, event):
    x, y = _get_device_coords(gui, event)
    gui.controller.client.control.touch(x, y, amscrcpy.ACTION_MOVE)


def on_mouse_up(gui, event):
    x, y = _get_device_coords(gui, event)
    gui.controller.client.control.touch(x, y, amscrcpy.ACTION_UP)


# =============================================================================
# Window / log events
# =============================================================================

def on_window_resize(gui, event):
    """Mark that preview size needs recalculation on next frame."""
    gui._size_recalc_needed = True


def on_log_scroll(gui, event):
    """Disable auto-scroll when user manually scrolls."""
    if gui.auto_scroll.get():
        gui.auto_scroll.set(False)
        gui.auto_scroll_button.deselect()


def on_auto_scroll_toggle(gui):
    """Scroll to bottom when auto-scroll is re-enabled."""
    if gui.auto_scroll.get():
        gui.log_text.see("end")
