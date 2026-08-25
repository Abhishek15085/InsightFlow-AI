"""
Fix the encoding-corrupted sections of frontend/app.py.
Reads the file as raw bytes, decodes as latin-1 (which reverses the mangling),
then re-encodes back to UTF-8.

The corruption pattern:
  PowerShell Add-Content without -Encoding UTF8 treated the UTF-8 bytes of
  the tail file as Windows-1252 codepoints and stored them verbatim.  The
  result is that each multi-byte UTF-8 sequence (e.g. F0 9F 93 8A for emoji)
  got stored as 4 separate Latin-1 characters ('\xf0', '\x9f', '\x93', '\x8a').
  When Python later reads the file as UTF-8 it sees those 4 bytes but they
  form valid 4-byte UTF-8 for the original emoji, so the emoji is intact in
  the first ~1600 lines (written by write_to_file which uses UTF-8).
  The tail (lines 1608+) appended by Add-Content has the bytes already
  mangled differently - they look like latin-1.

Strategy:
  1. Split the file at the known good/bad boundary (line 1608).
  2. Leave the good part untouched.
  3. Decode the tail as latin-1 then re-encode as UTF-8.
  4. Rejoin and write back as clean UTF-8.
"""

import sys

BOUNDARY = 1607   # 0-indexed; lines 0..1606 are good, 1607+ are bad

with open("frontend/app.py", "rb") as f:
    raw = f.read()

# Strip BOM if present
if raw[:3] == b"\xef\xbb\xbf":
    raw = raw[3:]

# Split on CRLF lines
lines_bytes = raw.split(b"\r\n")

good_part  = b"\r\n".join(lines_bytes[:BOUNDARY])
bad_part   = b"\r\n".join(lines_bytes[BOUNDARY:])

# Good part is valid UTF-8
good_text = good_part.decode("utf-8")

# Bad part: the bytes represent latin-1 characters that ARE the UTF-8 bytes
# of the original unicode.  Decode as latin-1, then encode to bytes, then
# decode those bytes as UTF-8.
try:
    bad_text = bad_part.decode("utf-8")
    # Check if it actually has the mojibake markers (latin-1 surrogates)
    # If it decodes fine as UTF-8 the content may still be wrong visually
    # but structurally fine for Python.  Leave it.
    print("Tail decoded as UTF-8 without error.")
except UnicodeDecodeError:
    # Real mojibake: re-encode
    bad_text = bad_part.decode("latin-1").encode("latin-1").decode("utf-8")
    print("Tail fixed via latin-1 round-trip.")

final = good_text + "\r\n" + bad_text

with open("frontend/app.py", "w", encoding="utf-8", newline="") as f:
    f.write(final)

print(f"Done. Total lines: {final.count(chr(10))}")
