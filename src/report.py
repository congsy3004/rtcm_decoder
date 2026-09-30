"""Report generation for RTCM Decoder — text and HTML formats.

Both generators take the same inputs (parser results, file metadata)
and produce a complete report string ready to be saved to disk.
"""

import os
import html as html_mod
from datetime import datetime
from rtcm_messages import RTCM_MESSAGE_TYPES


# =============================================================================
# Helpers
# =============================================================================

def format_bytes(n):
    """Format a byte count with an appropriate unit."""
    if n < 1024:
        return f"{n} B"
    elif n < 1024 * 1024:
        return f"{n / 1024:.1f} KB"
    else:
        return f"{n / (1024 * 1024):.2f} MB"


def _integrity_info(parser):
    """Compute integrity metrics from parser state.

    Returns:
        (success_pct, is_clean, has_data, known_count, unknown_count, unknown_types)
    """
    total = parser.total_messages + parser.sync_losses
    success_pct = (parser.total_messages / total * 100) if total > 0 else 100.0
    has_data = parser.total_messages > 0 or parser.discarded_bytes > 0

    unknown_types = sorted(
        t for t in parser.stats if t not in RTCM_MESSAGE_TYPES
    )
    known_count = sum(
        parser.stats[t] for t in parser.stats if t in RTCM_MESSAGE_TYPES
    )
    unknown_count = sum(parser.stats[t] for t in unknown_types)
    is_clean = parser.sync_losses == 0 and parser.crc_errors == 0

    return success_pct, is_clean, has_data, known_count, unknown_count, unknown_types


# =============================================================================
# Text Report
# =============================================================================

def generate_text_report(parser, file_path, file_size, decode_time,
                         timestamp=None):
    """Generate a plain-text report string.

    Args:
        parser:      RTCMParser instance after feeding all data.
        file_path:   Path of the decoded .bin file.
        file_size:   Size of the input file in bytes.
        decode_time: Time taken to decode, in seconds.
        timestamp:   Optional datetime for the report header.
                     Defaults to datetime.now() if not provided.

    Returns:
        Complete report as a string.
    """
    if timestamp is None:
        timestamp = datetime.now()
    pct, is_clean, has_data, known_cnt, unknown_cnt, unknown_types = _integrity_info(parser)

    lines = []
    lines.append("RTCM Decoder - Analysis Report")
    lines.append("=" * 72)
    lines.append(f"  File        : {os.path.basename(file_path)}")
    lines.append(f"  Full path   : {os.path.abspath(file_path)}")
    lines.append(f"  File size   : {format_bytes(file_size)}")
    lines.append(f"  Decoded at  : {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"  Decode time : {decode_time * 1000:.1f} ms")
    lines.append("=" * 72)

    # --- Integrity Summary ---
    lines.append("")
    lines.append("  INTEGRITY SUMMARY")
    lines.append("-" * 72)
    lines.append(
        f"    Valid messages : {parser.total_messages:<10,d}"
        f"  Sync losses  : {parser.sync_losses}"
    )
    lines.append(
        f"    CRC errors    : {parser.crc_errors:<10d}"
        f"  Discarded    : {format_bytes(parser.discarded_bytes)}"
    )
    lines.append(
        f"    Parsed bytes  : {format_bytes(parser.total_bytes_parsed):<10s}"
        f"          Frame success : {pct:.1f}%"
    )
    lines.append(
        f"    Known types   : {known_cnt:<10d}"
        f"  Unknown types: {unknown_cnt}"
    )
    lines.append("")

    if not has_data:
        lines.append("    Status : NO DATA  (file contains no RTCM frames)")
    elif is_clean:
        lines.append("    Status : CLEAN  (no corruption detected)")
    else:
        lines.append(
            f"    Status : BROKEN "
            f"({parser.sync_losses} corruption event(s), "
            f"{parser.crc_errors} CRC error(s))"
        )
    lines.append("")

    # --- Per-type table ---
    lines.append("=" * 72)
    lines.append("  MESSAGE TYPES")
    lines.append("-" * 72)

    if parser.stats:
        lines.append(
            f"  {'Type':>6}  {'Count':>8}  {'Bytes':>10}  "
            f"{'Avg':>6}  Description"
        )
        lines.append(
            f"  {'------':>6}  {'--------':>8}  {'----------':>10}  "
            f"{'------':>6}  " + "-" * 38
        )

        for msg_type in sorted(parser.stats.keys()):
            count = parser.stats[msg_type]
            total_b = parser.byte_stats.get(msg_type, 0)
            avg_b = total_b // count if count else 0
            desc = RTCM_MESSAGE_TYPES.get(msg_type, None)
            if desc is None:
                desc = "[?] Unknown type"
            lines.append(
                f"  {msg_type:>6}  {count:>8,}  "
                f"{format_bytes(total_b):>10}  "
                f"{avg_b:>5}B  {desc}"
            )

        lines.append(
            f"  {'------':>6}  {'--------':>8}  {'----------':>10}"
        )
        lines.append(
            f"  {'TOTAL':>6}  {parser.total_messages:>8,}  "
            f"{format_bytes(parser.total_bytes_parsed):>10}"
        )
    else:
        lines.append("  No RTCM messages found in file.")

    lines.append("=" * 72)
    lines.append("")
    return "\n".join(lines)


# =============================================================================
# HTML Report
# =============================================================================

_HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>RTCM Decoder Report — {filename}</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    background: #f5f5f5; color: #333; padding: 24px;
    max-width: 960px; margin: 0 auto;
  }}
  h1 {{ font-size: 22px; margin-bottom: 4px; }}
  h2 {{ font-size: 16px; margin: 20px 0 10px 0; color: #555; }}
  .subtitle {{ color: #888; font-size: 13px; margin-bottom: 20px; }}
  .card {{
    background: #fff; border: 1px solid #ddd; border-radius: 6px;
    padding: 16px; margin-bottom: 16px;
  }}
  .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }}
  .stat-label {{ font-size: 12px; color: #888; text-transform: uppercase; }}
  .stat-value {{ font-size: 20px; font-weight: 600; }}
  .stat-value.ok {{ color: #2e7d32; }}
  .stat-value.warn {{ color: #e65100; }}
  .status-clean {{
    background: #e8f5e9; border-left: 4px solid #2e7d32;
    padding: 10px 14px; border-radius: 4px; font-weight: 600;
    color: #2e7d32; margin-top: 12px;
  }}
  .status-broken {{
    background: #fbe9e7; border-left: 4px solid #c62828;
    padding: 10px 14px; border-radius: 4px; font-weight: 600;
    color: #c62828; margin-top: 12px;
  }}
  table {{
    width: 100%; border-collapse: collapse; font-size: 14px;
  }}
  th {{
    text-align: left; background: #f0f0f0; padding: 8px 12px;
    border-bottom: 2px solid #ccc; font-size: 12px;
    text-transform: uppercase; color: #666;
  }}
  th.num {{ text-align: right; }}
  td {{ padding: 7px 12px; border-bottom: 1px solid #eee; }}
  td.num {{ text-align: right; font-variant-numeric: tabular-nums; }}
  tr:hover {{ background: #fafafa; }}
  tr.unknown {{ background: #fff8e1; }}
  tr.total {{ font-weight: 700; background: #f0f0f0; border-top: 2px solid #ccc; }}
  .bar-cell {{ width: 120px; }}
  .bar {{
    height: 14px; border-radius: 2px; background: #1976d2;
    min-width: 2px;
  }}
  .bar.unknown {{ background: #ff9800; }}
  .tag {{
    display: inline-block; font-size: 11px; padding: 1px 6px;
    border-radius: 3px; background: #ff9800; color: #fff;
    margin-left: 6px; vertical-align: middle;
  }}
  .meta {{ font-size: 12px; color: #999; margin-top: 20px; }}
</style>
</head>
<body>

<h1>RTCM Decoder Report</h1>
<div class="subtitle">{filepath}</div>

<div class="card">
  <h2 style="margin-top:0;">File Information</h2>
  <div class="grid">
    <div>
      <div class="stat-label">File Size</div>
      <div class="stat-value">{file_size}</div>
    </div>
    <div>
      <div class="stat-label">Decode Time</div>
      <div class="stat-value">{decode_time}</div>
    </div>
  </div>
</div>

<div class="card">
  <h2 style="margin-top:0;">Integrity Summary</h2>
  <div class="grid">
    <div>
      <div class="stat-label">Valid Messages</div>
      <div class="stat-value {valid_class}">{valid_messages}</div>
    </div>
    <div>
      <div class="stat-label">Frame Success</div>
      <div class="stat-value {pct_class}">{success_pct}</div>
    </div>
    <div>
      <div class="stat-label">CRC Errors</div>
      <div class="stat-value {crc_class}">{crc_errors}</div>
    </div>
    <div>
      <div class="stat-label">Sync Losses</div>
      <div class="stat-value {sync_class}">{sync_losses}</div>
    </div>
    <div>
      <div class="stat-label">Parsed Bytes</div>
      <div class="stat-value">{parsed_bytes}</div>
    </div>
    <div>
      <div class="stat-label">Discarded Bytes</div>
      <div class="stat-value {disc_class}">{discarded_bytes}</div>
    </div>
    <div>
      <div class="stat-label">Known Types</div>
      <div class="stat-value">{known_count}</div>
    </div>
    <div>
      <div class="stat-label">Unknown Types</div>
      <div class="stat-value {unk_class}">{unknown_count}</div>
    </div>
  </div>
  {status_div}
</div>

<div class="card">
  <h2 style="margin-top:0;">Message Types</h2>
  {table_html}
</div>

<div class="meta">
  Generated by RTCM Decoder v1.0 on {timestamp}
</div>

</body>
</html>
"""


def generate_html_report(parser, file_path, file_size, decode_time,
                         timestamp=None):
    """Generate a self-contained HTML report string.

    Args:
        parser:      RTCMParser instance after feeding all data.
        file_path:   Path of the decoded .bin file.
        file_size:   Size of the input file in bytes.
        decode_time: Time taken to decode, in seconds.
        timestamp:   Optional datetime for the report footer.
                     Defaults to datetime.now() if not provided.

    Returns:
        Complete HTML document as a string.
    """
    if timestamp is None:
        timestamp = datetime.now()
    pct, is_clean, has_data, known_cnt, unknown_cnt, unknown_types = _integrity_info(parser)

    # Build message table rows
    max_count = max(parser.stats.values()) if parser.stats else 1

    rows = []
    for msg_type in sorted(parser.stats.keys()):
        count = parser.stats[msg_type]
        total_b = parser.byte_stats.get(msg_type, 0)
        avg_b = total_b // count if count else 0
        desc = RTCM_MESSAGE_TYPES.get(msg_type, None)
        is_unknown = desc is None
        if is_unknown:
            desc = "Unknown type"

        bar_width = int(count / max_count * 100) if max_count else 0
        row_class = ' class="unknown"' if is_unknown else ''
        bar_class = "bar unknown" if is_unknown else "bar"
        tag = '<span class="tag">?</span>' if is_unknown else ''

        rows.append(
            f'<tr{row_class}>'
            f'<td class="num">{msg_type}</td>'
            f'<td class="num">{count:,}</td>'
            f'<td class="num">{format_bytes(total_b)}</td>'
            f'<td class="num">{avg_b} B</td>'
            f'<td class="bar-cell">'
            f'<div class="{bar_class}" style="width:{bar_width}%"></div></td>'
            f'<td>{desc}{tag}</td>'
            f'</tr>'
        )

    # Total row
    rows.append(
        f'<tr class="total">'
        f'<td></td>'
        f'<td class="num">{parser.total_messages:,}</td>'
        f'<td class="num">{format_bytes(parser.total_bytes_parsed)}</td>'
        f'<td></td><td></td>'
        f'<td>Total</td>'
        f'</tr>'
    )

    if rows:
        table_html = (
            '<table>'
            '<tr>'
            '<th class="num">Type</th>'
            '<th class="num">Count</th>'
            '<th class="num">Bytes</th>'
            '<th class="num">Avg</th>'
            '<th>Distribution</th>'
            '<th>Description</th>'
            '</tr>'
            + "\n".join(rows)
            + '</table>'
        )
    else:
        table_html = '<p>No RTCM messages found in file.</p>'

    # Status banner
    if not has_data:
        status_div = (
            '<div class="status-broken">'
            '&#9888; NO DATA &mdash; file contains no RTCM frames'
            '</div>'
        )
    elif is_clean:
        status_div = (
            '<div class="status-clean">'
            '&#10004; CLEAN &mdash; no corruption detected'
            '</div>'
        )
    else:
        status_div = (
            '<div class="status-broken">'
            f'&#10008; BROKEN &mdash; {parser.sync_losses} corruption event(s), '
            f'{parser.crc_errors} CRC error(s)'
            '</div>'
        )

    return _HTML_TEMPLATE.format(
        filename=html_mod.escape(os.path.basename(file_path)),
        filepath=html_mod.escape(os.path.abspath(file_path)),
        file_size=format_bytes(file_size),
        decode_time=f"{decode_time * 1000:.1f} ms",
        valid_messages=f"{parser.total_messages:,}",
        valid_class="ok" if is_clean and has_data else "",
        success_pct=f"{pct:.1f}%",
        pct_class="ok" if pct == 100.0 and has_data else "warn",
        crc_errors=str(parser.crc_errors),
        crc_class="ok" if parser.crc_errors == 0 else "warn",
        sync_losses=str(parser.sync_losses),
        sync_class="ok" if parser.sync_losses == 0 else "warn",
        parsed_bytes=format_bytes(parser.total_bytes_parsed),
        discarded_bytes=format_bytes(parser.discarded_bytes),
        disc_class="" if parser.discarded_bytes == 0 else "warn",
        known_count=str(known_cnt),
        unknown_count=str(unknown_cnt),
        unk_class="" if unknown_cnt == 0 else "warn",
        status_div=status_div,
        table_html=table_html,
        timestamp=timestamp.strftime("%Y-%m-%d %H:%M:%S"),
    )
