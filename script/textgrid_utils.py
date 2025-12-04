# textgrid_utils.py

import re
from typing import List, Tuple


def parse_textgrid_intervals(path: str, tier_name: str):
    """
    Parse a Praat TextGrid (short text format) and return:
        xmin, xmax, intervals
    where intervals is a list of (xmin, xmax, text) for the given tier.
    """
    with open(path, 'r', encoding='utf-8') as f:
        lines = [line.rstrip('\n') for line in f]

    # Locate tier with name = "tier_name"
    tier_start_idx = None
    for i, line in enumerate(lines):
        if 'name =' in line:
            m = re.search(r'name\s*=\s*"(.*)"', line)
            if m and m.group(1) == tier_name:
                tier_start_idx = i
                break

    if tier_start_idx is None:
        raise ValueError(f"Tier '{tier_name}' not found in {path}")

    xmin = None
    xmax = None
    intervals: List[Tuple[float, float, str]] = []

    i = tier_start_idx
    # Get tier xmin/xmax and find "intervals: size ="
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith('xmin ='):
            xmin = float(line.split('=')[1])
        elif line.startswith('xmax ='):
            xmax = float(line.split('=')[1])
        elif line.startswith('intervals: size ='):
            i += 1
            break
        i += 1

    if xmin is None or xmax is None:
        raise ValueError(f"Could not find xmin/xmax for tier '{tier_name}' in {path}")

    # Now parse intervals until next "item [" or end of file
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith('intervals ['):
            xmin_line = lines[i + 1].strip()
            xmax_line = lines[i + 2].strip()
            text_line = lines[i + 3].strip()

            ixmin = float(xmin_line.split('=')[1])
            ixmax = float(xmax_line.split('=')[1])
            m = re.search(r'text\s*=\s*"(.*)"', text_line)
            itext = m.group(1) if m else ""

            intervals.append((ixmin, ixmax, itext))
            i += 4
        elif line.startswith('item ['):
            # Next tier
            break
        else:
            i += 1

    return xmin, xmax, intervals


def get_single_target_interval(path: str,
                               tier_name: str = "target",
                               non_target_label: str = "---") -> Tuple[float, float]:
    """
    For a tier that looks like:
        --- / TARGET / ---
    return (start, end) of the unique non-'---' interval.
    """
    _, _, intervals = parse_textgrid_intervals(path, tier_name)
    target_intervals = [
        (x0, x1, txt)
        for (x0, x1, txt) in intervals
        if txt != non_target_label and txt != ""
    ]
    if len(target_intervals) != 1:
        raise ValueError(
            f"Expected exactly one target interval in {path}, found {len(target_intervals)}"
        )
    x0, x1, _ = target_intervals[0]
    return x0, x1

