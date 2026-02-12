"""Encrypted secret storage using Windows DPAPI (no external deps)."""

from __future__ import annotations

import base64
import ctypes
from ctypes import wintypes
import uuid

from app.db.sqlite import connection


class DATA_BLOB(ctypes.Structure):
    _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_byte))]


CRYPTPROTECT_UI_FORBIDDEN = 0x01


def _blob_from_bytes(data: bytes) -> DATA_BLOB:
    buffer = ctypes.create_string_buffer(data, len(data))
    return DATA_BLOB(len(data), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_byte)))


def _bytes_from_blob(blob: DATA_BLOB) -> bytes:
    return ctypes.string_at(blob.pbData, blob.cbData)


def _encrypt(value: str) -> str:
    raw = value.encode("utf-8")
    in_blob = _blob_from_bytes(raw)
    out_blob = DATA_BLOB()
    if not ctypes.windll.crypt32.CryptProtectData(  # type: ignore[attr-defined]
        ctypes.byref(in_blob),
        "NeroAI",
        None,
        None,
        None,
        CRYPTPROTECT_UI_FORBIDDEN,
        ctypes.byref(out_blob),
    ):
        raise OSError("CryptProtectData failed")
    try:
        return base64.b64encode(_bytes_from_blob(out_blob)).decode("ascii")
    finally:
        ctypes.windll.kernel32.LocalFree(out_blob.pbData)  # type: ignore[attr-defined]


def _decrypt(value: str) -> str:
    raw = base64.b64decode(value.encode("ascii"))
    in_blob = _blob_from_bytes(raw)
    out_blob = DATA_BLOB()
    if not ctypes.windll.crypt32.CryptUnprotectData(  # type: ignore[attr-defined]
        ctypes.byref(in_blob),
        None,
        None,
        None,
        None,
        CRYPTPROTECT_UI_FORBIDDEN,
        ctypes.byref(out_blob),
    ):
        raise OSError("CryptUnprotectData failed")
    try:
        return _bytes_from_blob(out_blob).decode("utf-8")
    finally:
        ctypes.windll.kernel32.LocalFree(out_blob.pbData)  # type: ignore[attr-defined]


def set_secret(key_name: str, value: str) -> None:
    token = _encrypt(value)
    with connection() as conn:
        conn.execute(
            """
            INSERT INTO secrets (id, key_name, encrypted_value, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(key_name) DO UPDATE SET encrypted_value=excluded.encrypted_value, updated_at=CURRENT_TIMESTAMP
            """,
            (str(uuid.uuid4()), key_name, token),
        )


def get_secret(key_name: str) -> str | None:
    with connection() as conn:
        row = conn.execute("SELECT encrypted_value FROM secrets WHERE key_name = ?", (key_name,)).fetchone()
    if not row:
        return None
    return _decrypt(row["encrypted_value"])


def delete_secret(key_name: str) -> None:
    with connection() as conn:
        conn.execute("DELETE FROM secrets WHERE key_name = ?", (key_name,))


def has_secret(key_name: str) -> bool:
    with connection() as conn:
        row = conn.execute("SELECT 1 FROM secrets WHERE key_name = ?", (key_name,)).fetchone()
    return bool(row)


def secret_is_encrypted(key_name: str, plain: str) -> bool:
    """Test helper: ensure at-rest value differs from plain text."""
    with connection() as conn:
        row = conn.execute("SELECT encrypted_value FROM secrets WHERE key_name = ?", (key_name,)).fetchone()
    if not row:
        return False
    return plain not in row["encrypted_value"]

