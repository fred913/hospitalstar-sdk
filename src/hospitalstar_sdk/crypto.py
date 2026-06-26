"""Crypto helpers matching the HospitalStar mini-program transport wrapper."""

from __future__ import annotations

import base64
import json
from typing import Any

from Crypto.Cipher import DES
from Crypto.Util.Padding import pad, unpad
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.padding import PKCS7

from .exceptions import HospitalStarCryptoError

SIGN_CONTENT_SECRET = "hr895sm4c43a9fposd300k55c86ftbcc"
PHS_ID = "81681766"
PHS_SIGN_KEY = "SkpOe3I1"
HR_CODE_KEY = "hrtest22"

_BLOCK_BITS = 128
_BLOCK_BYTES = 16


def dumps_for_signing(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _sm4_key(secret: str = SIGN_CONTENT_SECRET) -> bytes:
    key = secret.encode("utf-8")
    if len(key) < _BLOCK_BYTES:
        raise HospitalStarCryptoError("signContent key must be at least 16 bytes")
    # The bundled JS helper accepts a 32-byte secret but expands only the first
    # four 32-bit words for SM4, so the effective key is the first 16 bytes.
    return key[:_BLOCK_BYTES]


def encrypt_sign_content(plaintext: str, *, secret: str = SIGN_CONTENT_SECRET) -> str:
    padder = PKCS7(_BLOCK_BITS).padder()
    padded = padder.update(plaintext.encode("utf-8")) + padder.finalize()
    encryptor = Cipher(algorithms.SM4(_sm4_key(secret)), modes.ECB()).encryptor()
    ciphertext = encryptor.update(padded) + encryptor.finalize()
    return base64.b64encode(ciphertext).decode("ascii")


def decrypt_sign_content(ciphertext: str, *, secret: str = SIGN_CONTENT_SECRET) -> str:
    try:
        decryptor = Cipher(algorithms.SM4(_sm4_key(secret)), modes.ECB()).decryptor()
        padded = decryptor.update(base64.b64decode(ciphertext)) + decryptor.finalize()
        unpadder = PKCS7(_BLOCK_BITS).unpadder()
        plaintext = unpadder.update(padded) + unpadder.finalize()
        return plaintext.decode("utf-8")
    except Exception as exc:  # noqa: BLE001 - normalize backend errors.
        raise HospitalStarCryptoError("failed to decrypt signContent payload") from exc


def encrypt_des_ecb_pkcs7_base64(plaintext: str, key: str) -> str:
    key_bytes = key.encode("utf-8")
    if len(key_bytes) != DES.key_size:
        raise HospitalStarCryptoError("DES key must be exactly 8 bytes")
    cipher = DES.new(key_bytes, DES.MODE_ECB)
    ciphertext = cipher.encrypt(pad(plaintext.encode("utf-8"), DES.block_size))
    return base64.b64encode(ciphertext).decode("ascii")


def decrypt_des_ecb_pkcs7_base64(ciphertext: str, key: str) -> str:
    key_bytes = key.encode("utf-8")
    if len(key_bytes) != DES.key_size:
        raise HospitalStarCryptoError("DES key must be exactly 8 bytes")
    try:
        cipher = DES.new(key_bytes, DES.MODE_ECB)
        plaintext = unpad(cipher.decrypt(base64.b64decode(ciphertext)), DES.block_size)
        return plaintext.decode("utf-8")
    except Exception as exc:  # noqa: BLE001 - normalize backend errors.
        raise HospitalStarCryptoError("failed to decrypt DES payload") from exc
