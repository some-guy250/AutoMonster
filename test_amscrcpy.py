#!/usr/bin/env python3
"""Manual acceptance test for the amscrcpy package.

Run it from the repo root against a connected emulator or device:

    python test_amscrcpy.py <serial>      # use a specific device
    python test_amscrcpy.py               # use the first ADB device

Each check prints [PASS] or [FAIL] and the process exits non-zero if any core
check fails, so it can be used as a manual regression check for future jar
bumps. The touch checks turn on the system "show touches" overlay so a tap
produces a visible ripple that is easy to detect in the video stream.
"""

import hashlib
import sys
import time
from typing import Optional, Tuple

import numpy as np
from adbutils import adb

import amscrcpy

PASS = "PASS"
FAIL = "FAIL"
_results = []


def report(step: str, ok: bool, detail: str = "") -> bool:
    _results.append(ok)
    status = PASS if ok else FAIL
    line = f"[{status}] {step}"
    if detail:
        line += f"  ::  {detail}"
    print(line, flush=True)
    return ok


def frame_hash(frame: Optional[np.ndarray]) -> Optional[str]:
    if frame is None or frame.size == 0:
        return None
    return hashlib.md5(np.ascontiguousarray(frame).tobytes()).hexdigest()


def wait_for_frame(client, timeout: float = 15.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if client.last_frame is not None and client.last_frame.size > 0:
            return True
        time.sleep(0.1)
    return client.last_frame is not None and client.last_frame.size > 0


def wait_for_change(client, baseline: Optional[str], timeout: float = 4.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if frame_hash(client.last_frame) not in (None, baseline):
            return True
        time.sleep(0.1)
    return False


def physical_size(device) -> Optional[Tuple[int, int]]:
    try:
        for line in device.shell("wm size").splitlines():
            if "Physical size:" in line:
                w, h = line.split("Physical size:")[1].strip().split("x")
                return int(w), int(h)
    except Exception:
        pass
    return None


def get_device(serial: Optional[str]):
    if serial:
        return adb.device(serial=serial)
    devices = adb.device_list()
    if not devices:
        return None
    return devices[0]


def main() -> None:
    serial = sys.argv[1] if len(sys.argv) > 1 else None
    device = get_device(serial)
    if device is None:
        print(f"[{FAIL}] No ADB device found (serial={serial!r})")
        sys.exit(1)

    sdk_raw = device.shell("getprop ro.build.version.sdk").strip()
    release = device.shell("getprop ro.build.version.release").strip()
    try:
        sdk = int(sdk_raw)
    except ValueError:
        sdk = -1
    print(f"Target device: {device.serial}  (Android {release}, API {sdk})", flush=True)

    # Clean slate: kill any stale scrcpy server left over from a previous run.
    device.shell("pkill -f scrcpy 2>/dev/null")
    time.sleep(0.3)

    client = amscrcpy.Client(device=device, max_fps=10, stay_awake=True)
    try:
        client.start(threaded=True, daemon_threaded=True)
    except Exception as exc:
        report("1. Connect + stream", False, f"start() raised: {exc}")
        finish()
        return

    # -- 1. connect + stream ------------------------------------------------
    got_frame = wait_for_frame(client)
    res = client.resolution
    disp = physical_size(device)
    frame = client.last_frame
    frame_ok = got_frame and frame is not None and frame.size > 0
    shape = frame.shape if frame_ok else None
    res_match = disp is None or res is None or sorted(res) == sorted(disp)  # orientation-agnostic
    detail = f"frame shape={shape}, client.resolution={res}, wm size={disp}"
    if not report("1. Connect + stream", bool(frame_ok and res_match), detail):
        client.stop()
        finish()
        return
    if not res_match:
        print(f"       note: resolution {res} differs from display {disp}", flush=True)

    # Turn on the touch overlay so taps leave a visible, detectable ripple.
    device.shell("settings put system show_touches 1")
    time.sleep(0.5)

    width, height = res
    cx, cy = width // 2, height // 2

    # -- 2. single tap ------------------------------------------------------
    try:
        baseline = frame_hash(client.last_frame)
        client.control.touch(cx, cy, amscrcpy.ACTION_DOWN)
        time.sleep(0.5)
        client.control.touch(cx, cy, amscrcpy.ACTION_UP)
        changed = wait_for_change(client, baseline, timeout=3.0)
        report("2. Single tap lands", changed,
               "screen changed" if changed else "no change detected (verify manually)")
    except Exception as exc:
        report("2. Single tap lands", False, f"touch raised: {exc}")

    # -- 3. two-finger gesture (pinch) -------------------------------------
    try:
        baseline = frame_hash(client.last_frame)
        offset = max(60, width // 8)
        client.control.touch(cx - offset, cy, amscrcpy.ACTION_DOWN, touch_id=1)
        client.control.touch(cx + offset, cy, amscrcpy.ACTION_DOWN, touch_id=2)
        for step in range(1, 5):
            client.control.touch(cx - offset - 20 * step, cy, amscrcpy.ACTION_MOVE, touch_id=1)
            client.control.touch(cx + offset + 20 * step, cy, amscrcpy.ACTION_MOVE, touch_id=2)
            time.sleep(0.05)
        client.control.touch(cx - offset - 80, cy, amscrcpy.ACTION_UP, touch_id=1)
        client.control.touch(cx + offset + 80, cy, amscrcpy.ACTION_UP, touch_id=2)
        changed = wait_for_change(client, baseline, timeout=3.0)
        report("3. Two-finger gesture", changed,
               "screen changed" if changed else "no change detected (verify manually)")
    except Exception as exc:
        report("3. Two-finger gesture", False, f"touch raised: {exc}")

    device.shell("settings put system show_touches 0")

    # -- 4. stay_awake ------------------------------------------------------
    power = device.shell("dumpsys power")
    awake = ("mWakefulness=Awake" in power) or ("Wakefulness=Awake" in power)
    report("4. stay_awake (screen Awake while streaming)", awake,
           "Awake" if awake else "not reported as Awake")

    # -- 5. clean shutdown --------------------------------------------------
    stream_thread = client._stream_thread
    control_thread = client._control_thread
    client.stop()
    stream_dead = stream_thread is None or not stream_thread.is_alive()
    control_dead = control_thread is None or not control_thread.is_alive()
    clean = stream_dead and control_dead and not client.alive and client.control_socket is None
    report(
        "5. stop() clean shutdown",
        clean,
        f"alive={client.alive} stream_thread_alive={not stream_dead} "
        f"control_thread_alive={not control_dead} control_socket={client.control_socket!r}",
    )

    # -- 6. version / bonus -------------------------------------------------
    if sdk >= 35:
        note = ("Android 15 should work with scrcpy 4.1 (it failed on 1.20)"
                if sdk == 35 else "Android 17+ is best-effort, note the observed behavior")
        print(f"[INFO] 6. Streaming on Android {release} (API {sdk}): reached all checks above. {note}.")
    else:
        print(f"[INFO] 6. Android {release} (API {sdk}) is in the primary supported range (5.0-16).")

    finish()


def finish() -> None:
    print(flush=True)
    if _results and all(_results):
        print(f"RESULT: ALL {len(_results)} CHECKS PASSED", flush=True)
        sys.exit(0)
    failed = _results.count(False) if _results else 1
    print(f"RESULT: {failed} of {len(_results) or 1} CHECKS FAILED", flush=True)
    sys.exit(1)


if __name__ == "__main__":
    main()
