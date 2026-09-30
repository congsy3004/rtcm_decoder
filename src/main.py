"""RTCM Decoder v1.0 — Analyze .bin files containing raw RTCM 3.x data.

Usage:
    python main.py <file.bin>                   Decode and print text report
    python main.py <file.bin> --html            Also generate HTML report
    python main.py <file.bin> -o report         Custom output name
    python main.py                              Interactive file selection

The decoder validates every frame with CRC-24Q, tracks per-message-type
statistics, and produces an integrity assessment (CLEAN / BROKEN).
"""

import argparse
import os
import sys
import time
import glob
from datetime import datetime

# Ensure console output handles Unicode on all platforms (e.g. cp932 on Windows)
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from rtcm_parser import RTCMParser
from report import generate_text_report, generate_html_report, format_bytes


# =============================================================================
# Helpers
# =============================================================================

def _get_app_dir():
    """Return the directory where the application lives.

    When running as a PyInstaller exe, sys.executable points to the exe.
    When running as a script, __file__ points to main.py inside src/.
    """
    if getattr(sys, 'frozen', False):
        return os.path.dirname(os.path.abspath(sys.executable))
    else:
        return os.path.dirname(os.path.abspath(__file__))


# =============================================================================
# Core decode
# =============================================================================

def decode_file(file_path):
    """Decode an RTCM binary file.

    Args:
        file_path: Path to the .bin file.

    Returns:
        (parser, file_size, decode_time) tuple.
    """
    file_size = os.path.getsize(file_path)
    parser = RTCMParser()

    t0 = time.perf_counter()
    with open(file_path, 'rb') as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            parser.feed(chunk)
    decode_time = time.perf_counter() - t0

    return parser, file_size, decode_time


# =============================================================================
# Report saving
# =============================================================================

def save_reports(parser, file_path, file_size, decode_time,
                 output_name=None, html=False, timestamp=None):
    """Generate and save report files next to the input .bin file.

    Args:
        parser:      RTCMParser after decoding.
        file_path:   Path of the input .bin file.
        file_size:   Size of the input file.
        decode_time: Decode duration in seconds.
        output_name: Optional base name for output files (without extension).
        html:        If True, also generate an HTML report.
        timestamp:   Optional datetime for report headers.

    Returns:
        List of saved file paths.
    """
    if output_name:
        base = os.path.join(os.path.dirname(os.path.abspath(file_path)),
                            output_name)
    else:
        base = os.path.splitext(os.path.abspath(file_path))[0] + "_report"

    saved = []

    # --- Text report ---
    text = generate_text_report(parser, file_path, file_size, decode_time,
                                timestamp=timestamp)
    txt_path = base + ".txt"
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write(text)
    saved.append(txt_path)

    # --- HTML report ---
    if html:
        html_content = generate_html_report(
            parser, file_path, file_size, decode_time,
            timestamp=timestamp,
        )
        html_path = base + ".html"
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        saved.append(html_path)

    return saved


# =============================================================================
# Interactive mode
# =============================================================================

def interactive_mode():
    """Interactive file selection and decode when no arguments are given."""
    print()
    print("  RTCM Decoder v1.0")
    print("  " + "=" * 50)
    print()

    # Look for .bin files in the current directory and ./output/
    bin_files = sorted(glob.glob("*.bin"))
    output_dir = os.path.join(_get_app_dir(), "output")
    if os.path.isdir(output_dir):
        bin_files += sorted(
            os.path.join("output", f)
            for f in os.listdir(output_dir)
            if f.endswith('.bin')
        )

    if bin_files:
        print("  Found .bin files:")
        for i, f in enumerate(bin_files, 1):
            size = os.path.getsize(f)
            print(f"    [{i}] {f}  ({format_bytes(size)})")
        print(f"    [0] Enter a custom path")
        print()

        while True:
            choice = input("  Select [0-" + str(len(bin_files)) + "]: ").strip()
            try:
                idx = int(choice)
                if idx == 0:
                    file_path = input("  Path: ").strip().strip('"')
                    break
                elif 1 <= idx <= len(bin_files):
                    file_path = bin_files[idx - 1]
                    break
            except ValueError:
                # Treat raw text as a file path
                if choice:
                    file_path = choice.strip().strip('"')
                    break
            print("  Invalid selection.")
    else:
        file_path = input("  Enter path to .bin file: ").strip().strip('"')

    if not os.path.isfile(file_path):
        print(f"  [!] File not found: {file_path}")
        return

    # Ask for output format
    print()
    print("  Output format:")
    print("    [1] Text report only")
    print("    [2] Text + HTML report")
    print()
    fmt = input("  Select [1-2] (Enter for 1): ").strip()
    html = fmt == '2'

    # Decode
    print()
    print(f"  Decoding: {file_path}")
    parser, file_size, decode_time = decode_file(file_path)
    ts = datetime.now()
    print(f"  Done in {decode_time * 1000:.1f} ms")
    print()

    # Print text report to console
    text = generate_text_report(parser, file_path, file_size, decode_time,
                                timestamp=ts)
    print(text)

    # Save reports
    saved = save_reports(parser, file_path, file_size, decode_time, html=html,
                         timestamp=ts)
    print()
    print("  Reports saved:")
    for p in saved:
        print(f"    -> {p}")
    print()


# =============================================================================
# CLI entry point
# =============================================================================

def main():
    """Entry point — supports both CLI arguments and interactive mode."""

    # If no arguments, run interactive mode
    if len(sys.argv) == 1:
        interactive_mode()
        return

    parser = argparse.ArgumentParser(
        prog="RTCM Decoder",
        description="Decode RTCM 3.x binary files and generate analysis reports.",
    )
    parser.add_argument(
        "file",
        help="Path to the .bin file containing raw RTCM data.",
    )
    parser.add_argument(
        "--html",
        action="store_true",
        help="Also generate an HTML report.",
    )
    parser.add_argument(
        "-o", "--output",
        default=None,
        help="Base name for output report files (without extension). "
             "Default: <input>_report",
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Suppress console output (only save report files).",
    )

    args = parser.parse_args()

    if not os.path.isfile(args.file):
        print(f"Error: file not found: {args.file}", file=sys.stderr)
        sys.exit(1)

    # Decode
    rtcm_parser, file_size, decode_time = decode_file(args.file)
    ts = datetime.now()

    # Console output
    if not args.quiet:
        text = generate_text_report(
            rtcm_parser, args.file, file_size, decode_time,
            timestamp=ts,
        )
        print(text)

    # Save reports
    saved = save_reports(
        rtcm_parser, args.file, file_size, decode_time,
        output_name=args.output,
        html=args.html,
        timestamp=ts,
    )

    if not args.quiet:
        print("Reports saved:")
        for p in saved:
            print(f"  -> {p}")
        print()


if __name__ == '__main__':
    main()
