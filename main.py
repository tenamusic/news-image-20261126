#!/usr/bin/env python3
"""Entrypoint for the make.fun news-image-20261126 entry.

The bundled entry.png is the deliverable for Thursday 26 November
2026. This program checks the image is an intact PNG inside the
contest limits, then copies it to the runner's output directory.
"""

import os
import struct
import sys
import zlib

MAX_BYTES = 1024 * 1024
WANT_W = 1024
WANT_H = 1024
SIG = b"\x89PNG\r\n\x1a\n"
END = b"IEND\xaeB`\x82"


def die(msg):
    print(f"entry: {msg}", file=sys.stderr)
    raise SystemExit(1)


def read_bundled():
    folder = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(folder, "entry.png"), "rb") as fh:
        return fh.read()


def validate(data):
    if len(data) > MAX_BYTES:
        die(f"entry.png is {len(data)} bytes, over the {MAX_BYTES} limit")
    if not data.startswith(SIG):
        die("entry.png lacks the PNG signature")
    if not data.endswith(END):
        die("entry.png lacks a complete IEND chunk")
    ln, kind = struct.unpack(">I4s", data[8:16])
    if kind != b"IHDR" or ln != 13:
        die("first chunk is not a 13-byte IHDR")
    w, h = struct.unpack(">II", data[16:24])
    if (w, h) != (WANT_W, WANT_H):
        die(f"entry.png is {w}x{h}, expected {WANT_W}x{WANT_H}")
    crc, = struct.unpack(">I", data[29:33])
    if zlib.crc32(data[12:29]) & 0xFFFFFFFF != crc:
        die("IHDR CRC mismatch")
    # Walk every chunk: each must carry a valid CRC and end exactly
    # at the IEND, so a truncated or padded file cannot slip through.
    pos = 8
    while pos + 12 <= len(data):
        size, ctype = struct.unpack(">I4s", data[pos:pos + 8])
        chunk_crc, = struct.unpack(">I", data[pos + 8 + size:pos + 12 + size])
        if zlib.crc32(data[pos + 4:pos + 8 + size]) & 0xFFFFFFFF != chunk_crc:
            die(f"CRC mismatch in chunk {ctype!r}")
        pos += 12 + size
        if ctype == b"IEND":
            break
    if pos != len(data):
        die("chunk walk did not end exactly at the end of the file")


def main():
    data = read_bundled()
    validate(data)
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    target = os.path.join(out_dir, "entry.png")
    with open(target, "wb") as fh:
        fh.write(data)
    if os.path.getsize(target) != len(data):
        die("written file size differs from the bundled image")
    print(f"wrote {target} ({len(data)} bytes)")


if __name__ == "__main__":
    main()
