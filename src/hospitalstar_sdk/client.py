"""Fully async aiohttp client for HospitalStar report viewing APIs."""

from __future__ import annotations

from collections.abc import Mapping
import json
import time
from typing import Any, TypeVar
from urllib.parse import urljoin

import aiohttp
from pydantic import BaseModel

from . import endpoints
from .crypto import (
    HR_CODE_KEY,
    PHS_ID,
    PHS_SIGN_KEY,
    decrypt_sign_content,
    dumps_for_signing,
    encrypt_des_ecb_pkcs7_base64,
    encrypt_sign_content,
)
from .exceptions import HospitalStarAPIError, HospitalStarHTTPError
from .models import (
    ApiEnvelope,
    CheckoutReportDateGroup,
    CheckoutReportDetailRequest,
    CheckoutReportDetailsResult,
    CheckoutReportListRequest,
    ExamineReportDateGroup,
    ExamineReportDetailRequest,
    ExamineReportDetailsResult,
    ExamineReportListRequest,
    MedicalReportDetailsRequest,
    MedicalReportDetailsResult,
    MedicalReportListRequest,
    MedicalReportSummary,
    ScanReportListRequest,
    SharedExamineReportDetailRequest,
    SDKModel,
)

Payload = SDKModel | BaseModel | Mapping[str, Any] | None
ResponseT = TypeVar("ResponseT")


class HospitalStarClient:
    """Async client for the report-viewing APIs.

    The original mini-program calls these endpoints with POST requests and JSON
    bodies. The host/base URL is environment-specific, so this SDK keeps it as a
    constructor argument.
    """

    def __init__(
        self,
        base_url: str,
        *,
        headers: Mapping[str, str] | None = None,
        token: str | None = None,
        access_token: str | None = None,
        auth_header: str | None = None,
        auth_scheme: str = "Bearer",
        sys_code: str | None = None,
        phs_id: str = PHS_ID,
        wrap_payload: bool = True,
        sign_headers: bool = True,
        decrypt_responses: bool = True,
        timeout: float | aiohttp.ClientTimeout = 30.0,
        session: aiohttp.ClientSession | None = None,
        raise_on_api_error: bool = True,
    ) -> None:
        if not base_url:
            raise ValueError("base_url is required")

        self.base_url = base_url.rstrip("/") + "/"
        self.headers = dict(headers or {})
        self.token = token if token is not None else access_token
        self.access_token = access_token
        self.auth_header = auth_header
        self.auth_scheme = auth_scheme
        self.sys_code = sys_code
        self.phs_id = phs_id
        self.wrap_payload = wrap_payload
        self.sign_headers = sign_headers
        self.decrypt_responses = decrypt_responses
        self.timeout = timeout if isinstance(timeout, aiohttp.ClientTimeout) else aiohttp.ClientTimeout(total=timeout)
        self._session = session
        self._owns_session = session is None
        self.raise_on_api_error = raise_on_api_error

    async def __aenter__(self) -> "HospitalStarClient":
        await self._get_session()
        return self

    async def __aexit__(self, exc_type: object, exc: object, traceback: object) -> None:
        await self.close()

    async def close(self) -> None:
        if self._owns_session and self._session and not self._session.closed:
            await self._session.close()

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=self.timeout)
            self._owns_session = True
        return self._session

    def _make_url(self, path: str) -> str:
        return urljoin(self.base_url, path.lstrip("/"))

    def _make_headers(self, sys_code: str | None = None) -> dict[str, str]:
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            **self.headers,
        }
        resolved_sys_code = sys_code or self.sys_code
        if self.sign_headers:
            if not resolved_sys_code:
                raise ValueError("sysCode is required to generate phsSign and hrCode headers")
            millis = int(time.time() * 1000)
            headers["phsId"] = self.phs_id
            headers["phsSign"] = encrypt_des_ecb_pkcs7_base64(
                f"{resolved_sys_code}_{millis}",
                PHS_SIGN_KEY,
            )
            headers["hrCode"] = encrypt_des_ecb_pkcs7_base64(resolved_sys_code, HR_CODE_KEY)
        if self.access_token and self.auth_header:
            value = self.access_token
            if self.auth_scheme and not value.lower().startswith(self.auth_scheme.lower() + " "):
                value = f"{self.auth_scheme} {value}"
            headers[self.auth_header] = value
        return headers

    @staticmethod
    def _payload_to_json(payload: Payload) -> dict[str, Any]:
        if payload is None:
            return {}
        if isinstance(payload, SDKModel):
            return payload.to_api_payload()
        if isinstance(payload, BaseModel):
            return payload.model_dump(by_alias=True, exclude_none=True)
        return dict(payload)

    def _extract_sys_code(self, payload: Mapping[str, Any]) -> str | None:
        value = payload.get("sysCode") or payload.get("sys_code") or self.sys_code
        return str(value) if value else None

    def _make_request_body(self, path: str, args_payload: dict[str, Any]) -> dict[str, Any]:
        if not self.wrap_payload:
            return args_payload

        body_token = "" if path == endpoints.SHARE_EXAMINE_REPORT_DETAIL else (self.token or "")
        return {
            "args": {},
            "signContent": encrypt_sign_content(dumps_for_signing(args_payload)),
            "token": body_token,
        }

    def _decrypt_response_body(self, body: Any) -> Any:
        if not self.decrypt_responses or not isinstance(body, dict):
            return body

        encrypted = body.get("signContent")
        if not isinstance(encrypted, str):
            encrypted = body.get("result")
        if not isinstance(encrypted, str):
            return body

        decrypted_text = decrypt_sign_content(encrypted)
        if decrypted_text == "":
            body["result"] = None
            return body
        try:
            body["result"] = json.loads(decrypted_text)
        except json.JSONDecodeError:
            body["result"] = decrypted_text
        return body

    async def post(
        self,
        path: str,
        payload: Payload = None,
        *,
        response_model: type[ApiEnvelope[ResponseT]] = ApiEnvelope[Any],
    ) -> ApiEnvelope[ResponseT]:
        session = await self._get_session()
        url = self._make_url(path)
        args_payload = self._payload_to_json(payload)
        sys_code = self._extract_sys_code(args_payload)
        json_payload = self._make_request_body(path, args_payload)

        async with session.post(url, json=json_payload, headers=self._make_headers(sys_code)) as response:
            try:
                body = await response.json(content_type=None)
            except aiohttp.ContentTypeError:
                text = await response.text()
                raise HospitalStarHTTPError(response.status, "response was not JSON", text) from None

            if response.status >= 400:
                raise HospitalStarHTTPError(response.status, response.reason, body)

        body = self._decrypt_response_body(body)
        envelope = response_model.model_validate(body)
        if self.raise_on_api_error and not envelope.ok:
            raise HospitalStarAPIError(envelope.code or envelope.resp_code, envelope.error_message, body)
        return envelope

    async def list_checkout_reports(
        self,
        request: CheckoutReportListRequest | Mapping[str, Any],
    ) -> ApiEnvelope[list[CheckoutReportDateGroup]]:
        return await self.post(
            endpoints.GET_CHECKOUT_REPORT_LIST,
            request,
            response_model=ApiEnvelope[list[CheckoutReportDateGroup]],
        )

    async def scan_checkout_reports(
        self,
        request: ScanReportListRequest | Mapping[str, Any],
    ) -> ApiEnvelope[list[CheckoutReportDateGroup]]:
        return await self.post(
            endpoints.SCAN_GET_CHECKOUT_REPORT_LIST,
            request,
            response_model=ApiEnvelope[list[CheckoutReportDateGroup]],
        )

    async def get_checkout_report_details(
        self,
        request: CheckoutReportDetailRequest | Mapping[str, Any],
    ) -> ApiEnvelope[CheckoutReportDetailsResult]:
        return await self.post(
            endpoints.GET_CHECKOUT_REPORT_DETAILS,
            request,
            response_model=ApiEnvelope[CheckoutReportDetailsResult],
        )

    async def list_examine_reports(
        self,
        request: ExamineReportListRequest | Mapping[str, Any],
    ) -> ApiEnvelope[list[ExamineReportDateGroup]]:
        return await self.post(
            endpoints.GET_EXAMINE_REPORT_LIST,
            request,
            response_model=ApiEnvelope[list[ExamineReportDateGroup]],
        )

    async def scan_examine_reports(
        self,
        request: ScanReportListRequest | Mapping[str, Any],
    ) -> ApiEnvelope[list[ExamineReportDateGroup]]:
        return await self.post(
            endpoints.SCAN_GET_EXAMINE_REPORT_LIST,
            request,
            response_model=ApiEnvelope[list[ExamineReportDateGroup]],
        )

    async def get_examine_report_details(
        self,
        request: ExamineReportDetailRequest | Mapping[str, Any],
    ) -> ApiEnvelope[ExamineReportDetailsResult]:
        return await self.post(
            endpoints.GET_EXAMINE_REPORT_DETAILS,
            request,
            response_model=ApiEnvelope[ExamineReportDetailsResult],
        )

    async def get_shared_examine_report_details(
        self,
        request: SharedExamineReportDetailRequest | Mapping[str, Any],
    ) -> ApiEnvelope[ExamineReportDetailsResult]:
        return await self.post(
            endpoints.SHARE_EXAMINE_REPORT_DETAIL,
            request,
            response_model=ApiEnvelope[ExamineReportDetailsResult],
        )

    async def list_medical_reports(
        self,
        request: MedicalReportListRequest | Mapping[str, Any],
    ) -> ApiEnvelope[list[MedicalReportSummary]]:
        return await self.post(
            endpoints.GET_MEDICAL_REPORT_LIST,
            request,
            response_model=ApiEnvelope[list[MedicalReportSummary]],
        )

    async def scan_medical_reports(
        self,
        request: ScanReportListRequest | Mapping[str, Any],
    ) -> ApiEnvelope[list[MedicalReportSummary]]:
        return await self.post(
            endpoints.SCAN_GET_MEDICAL_REPORT_LIST,
            request,
            response_model=ApiEnvelope[list[MedicalReportSummary]],
        )

    async def get_medical_report_details(
        self,
        request: MedicalReportDetailsRequest | Mapping[str, Any],
    ) -> ApiEnvelope[MedicalReportDetailsResult]:
        return await self.post(
            endpoints.GET_MEDICAL_REPORT_DETAILS,
            request,
            response_model=ApiEnvelope[MedicalReportDetailsResult],
        )
