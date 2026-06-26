# HospitalStar SDK

Async Python 3.12 SDK extracted for the report-viewing part of the HospitalStar mini-program.

This implementation intentionally covers only the report-query surface:

- Lab report list/detail endpoints.
- Exam report list/detail endpoints.
- Physical/medical report list/detail endpoints.
- FastAPI router and app factories for the same typed operations.

## Install

```bash
pip install -e .
```

## Async client

```python
from hospitalstar_sdk import HospitalStarClient, ExamineReportListRequest

async with HospitalStarClient(
    base_url="https://netphs.eheren.com",
    token="mini-program-access-token",
) as client:
    response = await client.list_examine_reports(
        ExamineReportListRequest(
            accountId="123",
            accountType="01",
            endDate="2026-06-26",
            hosId="129163",
            id="patient-binding-id",
            patName="Patient",
            startDate="2025-06-26",
            sysCode="1001017",
        )
    )
```

By default the client matches the captured mini-program transport:

- request args are sent as SM4/ECB/PKCS7 `signContent`;
- `token` is sent as a top-level body field;
- `phsId`, `phsSign`, and `hrCode` headers are generated per request;
- encrypted response `result`/`signContent` is decrypted before Pydantic parsing.

Use `wrap_payload=False`, `sign_headers=False`, or `decrypt_responses=False` only when calling a gateway that already handles those layers.

## FastAPI

```python
from hospitalstar_sdk.fastapi import create_app

app = create_app(
    base_url="https://netphs.eheren.com",
    client_kwargs={"token": "mini-program-access-token"},
)
```

Set `HOSPITALSTAR_BASE_URL` instead of passing `base_url` when deploying.
