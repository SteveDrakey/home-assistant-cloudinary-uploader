#!/usr/bin/env python3
"""Manual smoke test: upload a real image to Cloudinary.

This script is for developer use only. It performs a real upload to verify
that the Cloudinary SDK integration works end-to-end.

Usage:
    Set environment variables and run:

        export CLOUDINARY_CLOUD_NAME=your_cloud_name
        export CLOUDINARY_API_KEY=your_api_key
        export CLOUDINARY_API_SECRET=your_api_secret
        python scripts/manual_upload_test.py [path_to_image]

    If no image path is given, a tiny 1x1 PNG is generated in-memory.
"""

from __future__ import annotations

import io
import os
import struct
import sys
import zlib


def _make_tiny_png() -> bytes:
    """Create a minimal 1x1 red PNG in memory."""

    def _chunk(chunk_type: bytes, data: bytes) -> bytes:
        c = chunk_type + data
        crc = struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)
        return struct.pack(">I", len(data)) + c + crc

    header = b"\x89PNG\r\n\x1a\n"
    ihdr = _chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
    raw = zlib.compress(b"\x00\xff\x00\x00")  # filter byte + RGB
    idat = _chunk(b"IDAT", raw)
    iend = _chunk(b"IEND", b"")
    return header + ihdr + idat + iend


def main() -> None:
    cloud_name = os.environ.get("CLOUDINARY_CLOUD_NAME")
    api_key = os.environ.get("CLOUDINARY_API_KEY")
    api_secret = os.environ.get("CLOUDINARY_API_SECRET")

    if not all([cloud_name, api_key, api_secret]):
        print(
            "ERROR: Set CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, and "
            "CLOUDINARY_API_SECRET environment variables."
        )
        sys.exit(1)

    try:
        import cloudinary
        import cloudinary.uploader
    except ImportError:
        print("ERROR: cloudinary package not installed. Run: pip install cloudinary")
        sys.exit(1)

    cloudinary.config(
        cloud_name=cloud_name,
        api_key=api_key,
        api_secret=api_secret,
    )

    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        print(f"Uploading file: {file_path}")
        source = file_path
    else:
        print("No file specified — uploading a generated 1x1 PNG.")
        source = io.BytesIO(_make_tiny_png())

    public_id = "ha_cloudinary_uploader_smoke_test"

    try:
        result = cloudinary.uploader.upload(
            source,
            public_id=public_id,
            overwrite=True,
            resource_type="image",
        )
    except Exception as exc:
        print(f"UPLOAD FAILED: {exc}")
        sys.exit(1)

    print("Upload succeeded!")
    print(f"  public_id : {result['public_id']}")
    print(f"  secure_url: {result['secure_url']}")
    print(f"  version   : {result['version']}")

    # Clean up the test asset.
    try:
        cloudinary.uploader.destroy(public_id)
        print(f"  Cleaned up test asset '{public_id}'.")
    except Exception as exc:
        print(f"  Warning: cleanup failed ({exc}). Delete '{public_id}' manually.")


if __name__ == "__main__":
    main()
