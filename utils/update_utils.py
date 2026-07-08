"""Utility functions for the auto-updater (launcher.py)."""

import time


def compare_versions(version1: str, version2: str) -> int:
    """Compare two semantic version strings.

    Returns:
        -1 if version1 < version2
         0 if version1 == version2
         1 if version1 > version2
    """
    v1_parts = version1.split('.')
    v2_parts = version2.split('.')
    for i in range(max(len(v1_parts), len(v2_parts))):
        v1_part = int(v1_parts[i]) if i < len(v1_parts) else 0
        v2_part = int(v2_parts[i]) if i < len(v2_parts) else 0
        if v1_part < v2_part:
            return -1
        elif v1_part > v2_part:
            return 1
    return 0


def format_time(seconds: float) -> str:
    """Convert seconds to human readable time."""
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        seconds = int(seconds % 60)
        return f"{minutes}m {seconds}s"
    else:
        hours = int(seconds / 3600)
        minutes = int((seconds % 3600) / 60)
        return f"{hours}h {minutes}m"


def calculate_eta(start_time: float, current_progress: float, total_size: float) -> str:
    """Calculate estimated time remaining."""
    if current_progress == 0:
        return "Calculating..."

    elapsed = time.time() - start_time
    rate = current_progress / elapsed  # bytes per second
    remaining_bytes = total_size - current_progress

    if rate > 0:
        eta_seconds = remaining_bytes / rate
        return format_time(eta_seconds)
    return "Calculating..."


def format_size(size: float) -> str:
    """Convert bytes to human readable size."""
    for unit in ('B', 'KB', 'MB', 'GB'):
        if size < 1024:
            return f"{size:.1f}{unit}"
        size /= 1024
    return f"{size:.1f}TB"
