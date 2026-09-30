"""RTCM 3.x frame parser with CRC-24Q validation.

RTCM 3.x Frame Format:
    [0xD3] [00LLLLLL LLLLLLLL] [data (L bytes)] [CRC-24Q (3 bytes)]

    - Preamble:  1 byte  (always 0xD3)
    - Reserved:  6 bits  (must be 0)
    - Length:    10 bits  (data length, 0-1023)
    - Data:      L bytes (message payload, first 12 bits = message type)
    - CRC-24Q:   3 bytes (over header + data)

Total frame size = 3 (header) + L (data) + 3 (CRC) = L + 6 bytes
"""


# =============================================================================
# CRC-24Q Implementation
# =============================================================================
# Polynomial: x^24 + x^23 + x^18 + x^17 + x^14 + x^11 + x^10
#           + x^7  + x^6  + x^5  + x^4  + x^3  + x   + 1
# Hex: 0x1864CFB

_CRC24Q_POLY = 0x1864CFB


def _build_crc24q_table():
    """Pre-compute CRC-24Q lookup table (256 entries) for fast calculation."""
    table = []
    for i in range(256):
        crc = i << 16
        for _ in range(8):
            crc <<= 1
            if crc & 0x1000000:
                crc ^= _CRC24Q_POLY
        table.append(crc & 0xFFFFFF)
    return table


_CRC24Q_TABLE = _build_crc24q_table()


def crc24q(data):
    """Calculate CRC-24Q checksum over the given bytes.

    Args:
        data: bytes or bytearray to checksum.

    Returns:
        24-bit CRC value as an integer.
    """
    crc = 0
    for byte in data:
        crc = ((crc << 8) & 0xFFFFFF) ^ _CRC24Q_TABLE[(crc >> 16) ^ byte]
    return crc


# =============================================================================
# RTCM 3.x Frame Constants
# =============================================================================

RTCM3_PREAMBLE = 0xD3
RTCM3_HEADER_LEN = 3       # preamble (1) + reserved/length (2)
RTCM3_CRC_LEN = 3          # CRC-24Q checksum
RTCM3_MIN_FRAME = RTCM3_HEADER_LEN + RTCM3_CRC_LEN  # 6 bytes minimum
RTCM3_MAX_DATA_LEN = 1023  # 10-bit length field maximum


# =============================================================================
# Parsed Message Container
# =============================================================================

class RTCMMessage:
    """Represents a single decoded RTCM 3.x message."""

    __slots__ = ('msg_type', 'data_length', 'frame_length')

    def __init__(self, msg_type, data_length, frame_length):
        self.msg_type = msg_type
        self.data_length = data_length
        self.frame_length = frame_length

    def __repr__(self):
        return (f"RTCMMessage(type={self.msg_type}, "
                f"data_len={self.data_length}, "
                f"frame_len={self.frame_length})")


# =============================================================================
# Streaming Frame Parser
# =============================================================================

class RTCMParser:
    """Streaming RTCM 3.x frame parser.

    Feed raw bytes via feed(). The parser maintains an internal buffer
    to handle partial frames spanning across feed() boundaries.

    Usage:
        parser = RTCMParser()
        messages = parser.feed(raw_data_chunk)
        for msg in messages:
            print(f"Type {msg.msg_type}, {msg.frame_length} bytes")
    """

    def __init__(self):
        self._buffer = bytearray()
        self.stats = {}           # msg_type -> message count
        self.byte_stats = {}      # msg_type -> total frame bytes
        self.total_messages = 0
        self.total_bytes_parsed = 0
        self.crc_errors = 0
        self.discarded_bytes = 0
        self.sync_losses = 0      # number of corruption events (sync lost)
        self._in_sync = False     # whether parser is currently synchronized

    def feed(self, data):
        """Feed raw bytes into the parser.

        Args:
            data: bytes or bytearray of raw serial data.

        Returns:
            List of RTCMMessage objects for each valid frame found.
            Incomplete frames remain buffered for the next call.
        """
        self._buffer.extend(data)
        messages = []

        while len(self._buffer) >= RTCM3_MIN_FRAME:
            # --- Step 1: Find the 0xD3 preamble ---
            preamble_idx = self._buffer.find(b'\xD3')
            if preamble_idx == -1:
                if self._in_sync and len(self._buffer) > 0:
                    self.sync_losses += 1
                    self._in_sync = False
                self.discarded_bytes += len(self._buffer)
                self._buffer.clear()
                break
            if preamble_idx > 0:
                if self._in_sync:
                    self.sync_losses += 1
                    self._in_sync = False
                self.discarded_bytes += preamble_idx
                del self._buffer[:preamble_idx]

            # --- Step 2: Read the header (3 bytes) ---
            if len(self._buffer) < RTCM3_HEADER_LEN:
                break

            # Byte 1 bits [7:2] are reserved and must be 0
            reserved_bits = (self._buffer[1] >> 2) & 0x3F
            # Byte 1 bits [1:0] + Byte 2 = 10-bit data length
            data_length = ((self._buffer[1] & 0x03) << 8) | self._buffer[2]

            if reserved_bits != 0 or data_length > RTCM3_MAX_DATA_LEN:
                # Invalid header — skip this preamble byte
                if self._in_sync:
                    self.sync_losses += 1
                    self._in_sync = False
                self.discarded_bytes += 1
                del self._buffer[:1]
                continue

            # --- Step 3: Wait for the complete frame ---
            frame_length = RTCM3_HEADER_LEN + data_length + RTCM3_CRC_LEN
            if len(self._buffer) < frame_length:
                break

            frame = bytes(self._buffer[:frame_length])

            # --- Step 4: Validate CRC-24Q ---
            computed_crc = crc24q(frame[:-RTCM3_CRC_LEN])
            received_crc = (
                (frame[-3] << 16) | (frame[-2] << 8) | frame[-1]
            )

            if computed_crc != received_crc:
                # CRC mismatch — this 0xD3 was a false preamble
                self.crc_errors += 1
                if self._in_sync:
                    self.sync_losses += 1
                    self._in_sync = False
                self.discarded_bytes += 1
                del self._buffer[:1]
                continue

            # --- Step 5: Extract message type (12 bits) ---
            msg_type = 0
            if data_length >= 2:
                msg_type = (frame[3] << 4) | ((frame[4] >> 4) & 0x0F)

            msg = RTCMMessage(
                msg_type=msg_type,
                data_length=data_length,
                frame_length=frame_length,
            )
            messages.append(msg)

            # --- Step 6: Update statistics ---
            self._in_sync = True
            self.stats[msg_type] = self.stats.get(msg_type, 0) + 1
            self.byte_stats[msg_type] = (
                self.byte_stats.get(msg_type, 0) + frame_length
            )
            self.total_messages += 1
            self.total_bytes_parsed += frame_length

            # Consume the frame
            del self._buffer[:frame_length]

        return messages

    def reset(self):
        """Reset all parser state and statistics."""
        self._buffer.clear()
        self.stats.clear()
        self.byte_stats.clear()
        self.total_messages = 0
        self.total_bytes_parsed = 0
        self.crc_errors = 0
        self.discarded_bytes = 0
        self.sync_losses = 0
        self._in_sync = False
