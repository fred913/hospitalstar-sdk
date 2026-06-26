import re

from hospitalstar_sdk.client import HospitalStarClient
from hospitalstar_sdk.crypto import (
    decrypt_des_ecb_pkcs7_base64,
    decrypt_sign_content,
    encrypt_sign_content,
)
from hospitalstar_sdk.models import MedicalReportListRequest


def test_sign_content_matches_verified_sm4_vector() -> None:
    plaintext = '{"sysCode":"1001017"}'

    encrypted = encrypt_sign_content(plaintext)

    assert encrypted == "jdCYHj94vdRsR0VrwslX9z14hT3xeqeaQ5A9/YPLAIY="
    assert decrypt_sign_content(encrypted) == plaintext


def test_hrcode_matches_captured_des_vector() -> None:
    assert decrypt_des_ecb_pkcs7_base64("A7r7xbwEa9I=", "hrtest22") == "1001017"


def test_client_wraps_report_args_and_phs_headers() -> None:
    client = HospitalStarClient(base_url="https://netphs.eheren.com", token="token-value")
    request = MedicalReportListRequest(
        endDate="2026-06-26",
        patientId="patient-1",
        startDate="2026-05-26",
        sysCode="1001017",
    )
    args = request.to_api_payload()

    body = client._make_request_body("/phs-query/examine/getMedicalReportList", args)
    headers = client._make_headers("1001017")

    assert body["args"] == {}
    assert body["token"] == "token-value"
    assert decrypt_sign_content(body["signContent"]) == (
        '{"startDate":"2026-05-26","endDate":"2026-06-26","sysCode":"1001017","patientId":"patient-1"}'
    )
    assert headers["phsId"] == "81681766"
    assert decrypt_des_ecb_pkcs7_base64(headers["hrCode"], "hrtest22") == "1001017"
    assert re.fullmatch(r"1001017_\d{13}", decrypt_des_ecb_pkcs7_base64(headers["phsSign"], "SkpOe3I1"))
