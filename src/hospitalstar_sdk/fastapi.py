"""FastAPI definitions for the report-viewing SDK."""

from __future__ import annotations

import os
from collections.abc import Awaitable, Callable
from contextlib import asynccontextmanager
from typing import Any

from fastapi import APIRouter, Depends, FastAPI

from .client import HospitalStarClient
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
)

ClientProvider = Callable[[], HospitalStarClient | Awaitable[HospitalStarClient]]


async def _resolve_client(provider: ClientProvider) -> HospitalStarClient:
    client = provider()
    if isinstance(client, Awaitable):
        return await client
    return client


def create_reports_router(provider: ClientProvider) -> APIRouter:
    router = APIRouter(prefix="/reports", tags=["reports"])

    async def get_client() -> HospitalStarClient:
        return await _resolve_client(provider)

    @router.post("/checkout/list", response_model=ApiEnvelope[list[CheckoutReportDateGroup]])
    async def list_checkout_reports(
        request: CheckoutReportListRequest,
        client: HospitalStarClient = Depends(get_client),
    ) -> ApiEnvelope[list[CheckoutReportDateGroup]]:
        return await client.list_checkout_reports(request)

    @router.post("/checkout/scan", response_model=ApiEnvelope[list[CheckoutReportDateGroup]])
    async def scan_checkout_reports(
        request: ScanReportListRequest,
        client: HospitalStarClient = Depends(get_client),
    ) -> ApiEnvelope[list[CheckoutReportDateGroup]]:
        return await client.scan_checkout_reports(request)

    @router.post("/checkout/detail", response_model=ApiEnvelope[CheckoutReportDetailsResult])
    async def get_checkout_report_details(
        request: CheckoutReportDetailRequest,
        client: HospitalStarClient = Depends(get_client),
    ) -> ApiEnvelope[CheckoutReportDetailsResult]:
        return await client.get_checkout_report_details(request)

    @router.post("/examine/list", response_model=ApiEnvelope[list[ExamineReportDateGroup]])
    async def list_examine_reports(
        request: ExamineReportListRequest,
        client: HospitalStarClient = Depends(get_client),
    ) -> ApiEnvelope[list[ExamineReportDateGroup]]:
        return await client.list_examine_reports(request)

    @router.post("/examine/scan", response_model=ApiEnvelope[list[ExamineReportDateGroup]])
    async def scan_examine_reports(
        request: ScanReportListRequest,
        client: HospitalStarClient = Depends(get_client),
    ) -> ApiEnvelope[list[ExamineReportDateGroup]]:
        return await client.scan_examine_reports(request)

    @router.post("/examine/detail", response_model=ApiEnvelope[ExamineReportDetailsResult])
    async def get_examine_report_details(
        request: ExamineReportDetailRequest,
        client: HospitalStarClient = Depends(get_client),
    ) -> ApiEnvelope[ExamineReportDetailsResult]:
        return await client.get_examine_report_details(request)

    @router.post("/examine/share-detail", response_model=ApiEnvelope[ExamineReportDetailsResult])
    async def get_shared_examine_report_details(
        request: SharedExamineReportDetailRequest,
        client: HospitalStarClient = Depends(get_client),
    ) -> ApiEnvelope[ExamineReportDetailsResult]:
        return await client.get_shared_examine_report_details(request)

    @router.post("/medical/list", response_model=ApiEnvelope[list[MedicalReportSummary]])
    async def list_medical_reports(
        request: MedicalReportListRequest,
        client: HospitalStarClient = Depends(get_client),
    ) -> ApiEnvelope[list[MedicalReportSummary]]:
        return await client.list_medical_reports(request)

    @router.post("/medical/scan", response_model=ApiEnvelope[list[MedicalReportSummary]])
    async def scan_medical_reports(
        request: ScanReportListRequest,
        client: HospitalStarClient = Depends(get_client),
    ) -> ApiEnvelope[list[MedicalReportSummary]]:
        return await client.scan_medical_reports(request)

    @router.post("/medical/detail", response_model=ApiEnvelope[MedicalReportDetailsResult])
    async def get_medical_report_details(
        request: MedicalReportDetailsRequest,
        client: HospitalStarClient = Depends(get_client),
    ) -> ApiEnvelope[MedicalReportDetailsResult]:
        return await client.get_medical_report_details(request)

    return router


def create_app(
    *,
    client: HospitalStarClient | None = None,
    base_url: str | None = None,
    client_kwargs: dict[str, Any] | None = None,
) -> FastAPI:
    owns_client = client is None
    resolved_base_url = base_url or os.getenv("HOSPITALSTAR_BASE_URL")

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app_client = client
        if app_client is None:
            if not resolved_base_url:
                raise ValueError("base_url or HOSPITALSTAR_BASE_URL is required")
            app_client = HospitalStarClient(resolved_base_url, **(client_kwargs or {}))

        app.state.hospitalstar_client = app_client
        try:
            yield
        finally:
            if owns_client:
                await app_client.close()

    app = FastAPI(title="HospitalStar Report View API", lifespan=lifespan)
    app.include_router(create_reports_router(lambda: app.state.hospitalstar_client))
    return app

