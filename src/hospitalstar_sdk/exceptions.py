"""Exceptions raised by the HospitalStar SDK."""

from __future__ import annotations

from typing import Any


class HospitalStarError(Exception):
    """Base exception for this SDK."""


class HospitalStarHTTPError(HospitalStarError):
    """Raised when the HTTP transport fails or returns an error status."""

    def __init__(self, status: int, message: str, payload: Any | None = None) -> None:
        super().__init__(f"HospitalStar HTTP {status}: {message}")
        self.status = status
        self.payload = payload


class HospitalStarAPIError(HospitalStarError):
    """Raised when the API response envelope reports a failure."""

    def __init__(self, code: str | int | None, message: str, payload: Any | None = None) -> None:
        super().__init__(f"HospitalStar API error {code}: {message}")
        self.code = code
        self.payload = payload


class HospitalStarCryptoError(HospitalStarError):
    """Raised when request or response encryption cannot be applied."""
