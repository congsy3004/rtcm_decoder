# RTCM Decoder

Analyze raw RTCM 3.x binary files (`.bin`) and generate detailed integrity reports in **text** and **HTML** formats.

Designed for validating RTCM data streams — compare a clean TCP source against an MCU-processed stream to detect corruption, dropped messages, and bit errors.

## Quick Start

### Option A: Use the pre-built executable (no Python required)

1. Download `rtcm_decoder.exe` from the `dist/` folder (or build it yourself with `build.bat`)
2. Run:
   ```
   rtcm_decoder.exe data.bin --html
   ```

### Option B: Run from source

```bash
cd src
python main.py data.bin --html
```

No external dependencies — uses only the Python standard library.

## Usage

```
python main.py <file.bin> [options]
python main.py                          # Interactive mode
```

| Option | Description |
|--------|-------------|
| `<file.bin>` | Path to a raw RTCM binary file |
| `--html` | Also generate an HTML report |
| `-o NAME` | Custom base name for output files |
| `-q` | Quiet mode (save files only, no console output) |

### Examples

```bash
# Decode and print text report to console + save .txt
rtcm_decoder.exe capture.bin

# Decode with both text and HTML report
rtcm_decoder.exe capture.bin --html

# Custom output name
rtcm_decoder.exe capture.bin --html -o analysis_report

# Interactive file selection (no arguments)
rtcm_decoder.exe
```

## Output

Given `capture.bin` as input:

| File | Description |
|------|-------------|
| `capture_report.txt` | Plain-text analysis report |
| `capture_report.html` | Self-contained HTML report (with `--html`) |

Reports are saved next to the input `.bin` file.

### Sample Text Report

```
RTCM Decoder - Analysis Report
========================================================================
  File        : capture.bin
  File size   : 43.9 KB
  Decode time : 4.5 ms
========================================================================

  INTEGRITY SUMMARY
------------------------------------------------------------------------
    Valid messages : 998         Sync losses  : 2
    CRC errors    : 2           Discarded    : 106 B
    Parsed bytes  : 43.8 KB             Frame success : 99.8%
    Known types   : 998         Unknown types: 0

    Status : BROKEN (2 corruption event(s), 2 CRC error(s))

========================================================================
  MESSAGE TYPES
------------------------------------------------------------------------
    Type     Count       Bytes     Avg  Description
  ------  --------  ----------  ------  -----------
    1005       200      4.5 KB     23B  Stationary RTK Reference Station ARP
    1077       199     11.3 KB     58B  GPS MSM7
    1087       199      9.3 KB     48B  GLONASS MSM7
========================================================================
```

### HTML Report

The HTML report is fully self-contained (inline CSS, no JavaScript) and includes:
- File information card
- Color-coded integrity summary (green = CLEAN, red = BROKEN)
- Per-message-type table with distribution bars

## Integrity Metrics

| Metric | Meaning |
|--------|---------|
| **Valid messages** | Frames that passed CRC-24Q validation |
| **Sync losses** | Number of corruption *events* (parser lost synchronization) |
| **CRC errors** | Frames with valid-looking headers but failed CRC check |
| **Discarded bytes** | Bytes not part of any valid RTCM frame |
| **Frame success %** | `valid / (valid + sync_losses) × 100` |
| **Status** | `CLEAN` (zero errors) or `BROKEN` (corruption detected) |
| **Unknown types** | Message types not in the RTCM 3.x standard table, flagged with `[?]` |

## Building the Executable

Run `build.bat` from the project root. It will:
1. Install PyInstaller if not present
2. Build a single-file `rtcm_decoder.exe` in the `dist/` folder

```bash
build.bat
```

The resulting `dist/rtcm_decoder.exe` is a standalone file — share it directly, no Python installation needed on the target machine.

## Project Structure

```
RTCM_decoder/
├── README.md           Project documentation
├── .gitignore          Git ignore rules
├── build.bat           Build script (creates the .exe)
├── src/                Source code
│   ├── main.py             CLI entry point
│   ├── rtcm_parser.py      RTCM 3.x frame parser + CRC-24Q
│   ├── rtcm_messages.py    Message type definitions (104 types)
│   └── report.py           Text + HTML report generators
├── dist/               Built executable (gitignored)
└── build/              Build artifacts (gitignored)
```

## Supported RTCM 3.x Message Types

104 message types including:
- Legacy observations (1001–1012)
- Station info (1005–1008, 1033)
- Ephemerides (1019–1020, 1042–1046)
- SSR corrections (1057–1068)
- MSM: GPS (1071–1077), GLONASS (1081–1087), Galileo (1091–1097), SBAS (1101–1107), QZSS (1111–1117), BDS (1121–1127), NavIC (1131–1137)
- Proprietary: u-blox (4072–4073), IGS (4076)

Unknown message types are decoded and counted — they display as `[?] Unknown type`.
